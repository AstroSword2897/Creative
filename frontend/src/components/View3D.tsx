import { useEffect, useRef, useState } from 'react'
import * as THREE from 'three'
import { SimulationState } from '../types'

interface View3DProps {
  state: SimulationState | null
}

// Shared geometry cache (created once, reused)
// Increased base sizes significantly for better visibility
const geometryCache = {
  athlete: new THREE.SphereGeometry(0.04, 16, 16), // Increased to 0.04 for visibility
  bus: new THREE.BoxGeometry(0.12, 0.06, 0.18), // Increased for visibility
  responder: new THREE.CylinderGeometry(0.025, 0.022, 0.06, 16), // Increased for visibility
  default: new THREE.BoxGeometry(0.05, 0.08, 0.05), // Increased for visibility
}

// Shared material cache (created once, reused)
const createMaterialCache = () => {
  const colors: Record<string, string> = {
    athlete: '#F4C430',
    volunteer: '#2ECC71',
    hotel_security: '#00F5D4',
    lvmpd: '#0077FF',
    amr: '#E74C3C',
    bus: '#6366F1',
  }

  const cache: Record<string, THREE.Material> = {}
  
  Object.entries(colors).forEach(([type, color]) => {
    const threeColor = new THREE.Color(color)
    
    if (type === 'athlete') {
      cache[type] = new THREE.MeshStandardMaterial({
        color: threeColor,
        emissive: threeColor,
        emissiveIntensity: 0.2,
        roughness: 0.3,
        metalness: 0.1,
      })
    } else if (type === 'bus') {
      cache[type] = new THREE.MeshStandardMaterial({
        color: threeColor,
        roughness: 0.3,
        metalness: 0.7,
      })
    } else if (type === 'lvmpd' || type === 'amr') {
      cache[type] = new THREE.MeshStandardMaterial({
        color: threeColor,
        roughness: 0.4,
        metalness: 0.5,
      })
    } else {
      cache[type] = new THREE.MeshStandardMaterial({
        color: threeColor,
        emissive: threeColor,
        emissiveIntensity: 0.15,
        roughness: 0.5,
      })
    }
  })
  
  // Add default material for unknown agent types
  cache.default = new THREE.MeshStandardMaterial({
    color: new THREE.Color('#888888'),
    roughness: 0.5,
    metalness: 0.3,
  })
  
  return cache
}

const materialCache = createMaterialCache()

export default function View3D({ state }: View3DProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  const sceneRef = useRef<THREE.Scene | null>(null)
  const rendererRef = useRef<THREE.WebGLRenderer | null>(null)
  const cameraRef = useRef<THREE.PerspectiveCamera | null>(null)
  const controlsRef = useRef<any>(null)
  const agentsRef = useRef<Map<number, THREE.Mesh>>(new Map())
  const venuesRef = useRef<Map<string, THREE.Mesh>>(new Map())
  const incidentsRef = useRef<Map<string, THREE.Mesh>>(new Map())
  const trailsRef = useRef<Map<number, { line: THREE.Line, buffer: Float32Array, index: number, maxPoints: number }>>(new Map())
  const animationFrameRef = useRef<number | null>(null)
  const [isInitialized, setIsInitialized] = useState(false)
  // Use a ref to track initialization to prevent dependency loops
  const isInitializedRef = useRef(false)
  // Store target positions for smooth interpolation
  const agentTargetsRef = useRef<Map<number, { x: number, z: number, startX: number, startZ: number, startTime: number, duration: number }>>(new Map())
  // Track last processed state time to prevent duplicate updates
  const lastProcessedTimeRef = useRef<string | null>(null)

  // Normalize coordinates from lat/lon to 0-1 space
  // Clamps coordinates to 0-1 to prevent off-plane agents
  const normalizeCoords = (lat: number, lon: number): [number, number] => {
    const latMin = 36.0
    const latMax = 36.2
    const lonMin = -115.3
    const lonMax = -115.1
    
    let x = (lon - lonMin) / (lonMax - lonMin)
    let z = (lat - latMin) / (latMax - latMin)
    
    // Clamp to 0-1 to prevent off-plane agents
    x = Math.min(Math.max(x, 0), 1)
    z = Math.min(Math.max(z, 0), 1)
    
    return [x, z]
  }

  // Handle coordinate format - backend sends [lat, lon]
  const parseLocation = (location: [number, number] | null): [number, number] | null => {
    if (!location || location.length !== 2) return null
    // If first value is around -115, it's [lon, lat], otherwise [lat, lon]
    if (Math.abs(location[0]) > 100) {
      return [location[1], location[0]]
    }
    return location
  }

  // Helper: parse and normalize coordinates in one step
  const getNormalizedPos = (loc: [number, number] | null): [number, number] | null => {
    const parsed = parseLocation(loc)
    return parsed ? normalizeCoords(parsed[0], parsed[1]) : null
  }

  // Create agent mesh (called once per agent)
  // Lifts agents above ground and scales for visibility
  const createAgentMesh = (agent: any, x: number, z: number): THREE.Mesh => {
    let geometry: THREE.BufferGeometry
    let baseMaterial: THREE.Material

    if (agent.type === 'athlete') {
      geometry = geometryCache.athlete
      baseMaterial = materialCache.athlete
    } else if (agent.type === 'bus') {
      geometry = geometryCache.bus
      baseMaterial = materialCache.bus
    } else if (agent.type === 'lvmpd' || agent.type === 'amr') {
      geometry = geometryCache.responder
      baseMaterial = materialCache[agent.type] || materialCache.default
    } else {
      geometry = geometryCache.default
      baseMaterial = materialCache[agent.type] || materialCache.default
    }

    // ✅ Clone material to avoid mutating shared cache
    const material = baseMaterial.clone()
    
    // Make materials brighter and more visible (safe - we're modifying cloned material)
    if (material instanceof THREE.MeshStandardMaterial) {
      material.emissiveIntensity = 0.8 // Very bright emissive
      material.roughness = 0.2 // More reflective
      material.metalness = 0.1
    }

    const mesh = new THREE.Mesh(geometry, material)
    
    // Raise above ground for better visibility
    const baseHeight = 0.05
    mesh.position.set(x, baseHeight, z)
    
    // Scale for visibility (very large scale to ensure visibility)
    // Scale based on agent type - larger for better visibility
    const scale = agent.type === 'bus' ? 12 : agent.type === 'athlete' ? 10 : 8
    mesh.scale.set(scale, scale, scale)
    
    mesh.castShadow = false // Disable shadows for better performance
    mesh.receiveShadow = false
    mesh.visible = true // Ensure visibility
    return mesh
  }

  // Initialize scene (runs once)
  useEffect(() => {
    // Use ref to prevent re-initialization loops
    if (!containerRef.current || isInitializedRef.current) return

    // Debug: Check container dimensions
    const width = containerRef.current.clientWidth
    const height = containerRef.current.clientHeight
    console.log(`📐 View3D: Container dimensions - width: ${width}, height: ${height}`)
    
    if (width === 0 || height === 0) {
      console.warn('⚠️ View3D: Container has zero dimensions, retrying...')
      // Retry after a short delay
      setTimeout(() => {
        if (containerRef.current && !isInitializedRef.current) {
          const retryWidth = containerRef.current.clientWidth
          const retryHeight = containerRef.current.clientHeight
          console.log('📐 View3D: Retry dimensions', { retryWidth, retryHeight })
          if (retryWidth > 0 && retryHeight > 0) {
            // Force re-run by resetting the ref
            isInitializedRef.current = false
          }
        }
      }, 100)
      return
    }

    const scene = new THREE.Scene()
    scene.background = new THREE.Color(0x0a0a0f)
    scene.fog = new THREE.Fog(0x0a0a0f, 10, 50)
    sceneRef.current = scene

    const camera = new THREE.PerspectiveCamera(
      60,
      width / height,
      0.1,
      1000
    )
    // Camera positioned to see the full 0-1 plane - top-down view for maximum visibility
    // Position camera high above, looking straight down at the entire scene
    camera.position.set(0.5, 2.0, 0.5) // Directly above center, high up
    camera.lookAt(0.5, 0, 0.5) // Look straight down at ground level
    cameraRef.current = camera

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false }) // Solid background
    renderer.setSize(width, height)
    renderer.setPixelRatio(Math.min(2, window.devicePixelRatio)) // Clamp for performance
    renderer.shadowMap.enabled = true
    renderer.shadowMap.type = THREE.PCFSoftShadowMap
    
    // Ensure canvas is visible and properly positioned
    renderer.domElement.style.display = 'block'
    renderer.domElement.style.width = '100%'
    renderer.domElement.style.height = '100%'
    renderer.domElement.style.position = 'absolute'
    renderer.domElement.style.top = '0'
    renderer.domElement.style.left = '0'
    renderer.domElement.style.zIndex = '0'
    renderer.domElement.style.outline = 'none' // Remove focus outline
    renderer.domElement.style.background = '#0a0a0f' // Ensure background color
    
    // Clear the container before appending
    if (containerRef.current) {
      // Remove any existing canvas
      const existingCanvas = containerRef.current.querySelector('canvas')
      if (existingCanvas) {
        containerRef.current.removeChild(existingCanvas)
      }
      containerRef.current.appendChild(renderer.domElement)
    }
    rendererRef.current = renderer
    
    // Force initial render to ensure canvas is visible
    renderer.render(scene, camera)
    
    console.log(`✅ View3D: Renderer created - canvas: ${renderer.domElement.width}x${renderer.domElement.height}, pixelRatio: ${renderer.getPixelRatio()}, style: ${renderer.domElement.style.display}`)

    // Lighting - brighter for better visibility
    // Lighting - very bright for maximum visibility
    const ambientLight = new THREE.AmbientLight(0xffffff, 1.0) // Maximum ambient
    scene.add(ambientLight)

    const directionalLight = new THREE.DirectionalLight(0xfff8e1, 1.2) // Increased intensity
    directionalLight.position.set(1, 2, 1)
    directionalLight.castShadow = false // Disable shadows for better performance
    scene.add(directionalLight)
    
    // Add additional point light for better visibility
    const pointLight = new THREE.PointLight(0xffffff, 0.8, 10)
    pointLight.position.set(0.5, 1.5, 0.5)
    scene.add(pointLight)
    
    // Add hemisphere light for even better visibility
    const hemisphereLight = new THREE.HemisphereLight(0xffffff, 0x444444, 0.6)
    scene.add(hemisphereLight)

    // Ground plane
    const groundGeometry = new THREE.PlaneGeometry(1, 1)
    const groundMaterial = new THREE.MeshStandardMaterial({
      color: 0x1a1a2e,
      roughness: 0.9,
      metalness: 0.1,
    })
    const ground = new THREE.Mesh(groundGeometry, groundMaterial)
    ground.rotation.x = -Math.PI / 2
    ground.position.set(0.5, 0, 0.5)
    ground.receiveShadow = true
    scene.add(ground)

    // Grid helper - larger and more visible to show coordinate system
    const gridHelper = new THREE.GridHelper(1, 10, 0x00ff00, 0x008800) // Green grid for visibility
    gridHelper.position.set(0.5, 0.01, 0.5)
    scene.add(gridHelper)
    
    // Add coordinate markers at corners to show the map bounds
    const cornerMarkers = [
      [0, 0.05, 0], // SW
      [1, 0.05, 0], // SE
      [0, 0.05, 1], // NW
      [1, 0.05, 1], // NE
    ]
    cornerMarkers.forEach((pos) => {
      const markerGeometry = new THREE.SphereGeometry(0.02, 8, 8)
      const markerMaterial = new THREE.MeshBasicMaterial({ color: 0x00ff00, transparent: true, opacity: 0.5 })
      const marker = new THREE.Mesh(markerGeometry, markerMaterial)
      marker.position.set(pos[0], pos[1], pos[2])
      scene.add(marker)
    })
    
    // DEBUG: Add bright test objects to verify scene renders (larger, longer-lasting)
    const testCubeGeometry = new THREE.BoxGeometry(0.1, 0.1, 0.1)
    const testCubeMaterial = new THREE.MeshBasicMaterial({ color: 0xff0000 })
    const testCube = new THREE.Mesh(testCubeGeometry, testCubeMaterial)
    testCube.position.set(0.5, 0.15, 0.5)
    scene.add(testCube)
    console.log('🔴 View3D: RED TEST CUBE added at center (0.5, 0.15, 0.5) - should be visible!')
    
    // Also add a green sphere
    const testSphereGeometry = new THREE.SphereGeometry(0.06, 16, 16)
    const testSphereMaterial = new THREE.MeshBasicMaterial({ color: 0x00ff00 })
    const testSphere = new THREE.Mesh(testSphereGeometry, testSphereMaterial)
    testSphere.position.set(0.6, 0.15, 0.5)
    scene.add(testSphere)
    console.log('🟢 View3D: GREEN TEST SPHERE added at (0.6, 0.15, 0.5)')
    
    // Remove test objects after 5 seconds (faster cleanup)
    setTimeout(() => {
      if (scene.children.includes(testCube)) {
        scene.remove(testCube)
        testCubeGeometry.dispose()
        testCubeMaterial.dispose()
        console.log('🔴 View3D: Test cube removed')
      }
      if (scene.children.includes(testSphere)) {
        scene.remove(testSphere)
        testSphereGeometry.dispose()
        testSphereMaterial.dispose()
        console.log('🟢 View3D: Test sphere removed')
      }
    }, 5000) // Reduced from 10 seconds to 5 seconds

    // Venues removed - they were confusing in the visualization
    // Focus is on agents and their movement only

    // Orbit controls
    import('three/examples/jsm/controls/OrbitControls.js').then((module) => {
      const OrbitControls = module.OrbitControls
      const controls = new OrbitControls(camera, renderer.domElement)
      controls.enableDamping = true
      controls.dampingFactor = 0.05
      controls.enableZoom = true
      controls.enablePan = true
      controls.minDistance = 0.3
      controls.maxDistance = 5
      controls.target.set(0.5, 0, 0.5) // Look at ground level
      controls.minDistance = 0.5
      controls.maxDistance = 5
      controlsRef.current = controls
    }).catch(() => {
      // Fallback: basic mouse controls
      let isDragging = false
      let previousMousePosition = { x: 0, y: 0 }
      
      const onMouseDown = (e: MouseEvent) => {
        isDragging = true
        previousMousePosition = { x: e.clientX, y: e.clientY }
      }
      
      const onMouseMove = (e: MouseEvent) => {
        if (!isDragging) return
        const deltaX = e.clientX - previousMousePosition.x
        const deltaY = e.clientY - previousMousePosition.y
        camera.position.x -= deltaX * 0.001
        camera.position.y += deltaY * 0.001
        camera.lookAt(0.5, 0.05, 0.5)
        previousMousePosition = { x: e.clientX, y: e.clientY }
      }
      
      const onMouseUp = () => {
        isDragging = false
      }
      
      const onWheel = (e: WheelEvent) => {
        const zoomFactor = Math.max(0.3, Math.min(5, 1 + e.deltaY * 0.001))
        camera.position.multiplyScalar(zoomFactor)
        camera.lookAt(0.5, 0.05, 0.5)
      }
      
      renderer.domElement.addEventListener('mousedown', onMouseDown)
      renderer.domElement.addEventListener('mousemove', onMouseMove)
      renderer.domElement.addEventListener('mouseup', onMouseUp)
      renderer.domElement.addEventListener('wheel', onWheel)
      
      // Store cleanup function
      controlsRef.current = {
        update: () => {},
        dispose: () => {
          renderer.domElement.removeEventListener('mousedown', onMouseDown)
          renderer.domElement.removeEventListener('mousemove', onMouseMove)
          renderer.domElement.removeEventListener('mouseup', onMouseUp)
          renderer.domElement.removeEventListener('wheel', onWheel)
        }
      }
    })

    // Mark as initialized using both state and ref
    isInitializedRef.current = true
    setIsInitialized(true)

    // Animation loop - ensure it always runs
    const animate = () => {
      if (!renderer || !camera || !scene) {
        // Retry if not ready yet
        animationFrameRef.current = requestAnimationFrame(animate)
        return
      }
      
      animationFrameRef.current = requestAnimationFrame(animate)
      
      if (controlsRef.current && controlsRef.current.update) {
        controlsRef.current.update()
      }

      // Animate incidents (pulsing)
      const time = Date.now() * 0.001
      incidentsRef.current.forEach((mesh) => {
        const scale = 1 + Math.sin(time * 3) * 0.15
        mesh.scale.set(scale, scale, scale)
        if ((mesh.material as THREE.MeshStandardMaterial).emissive) {
          const intensity = 0.3 + Math.sin(time * 3) * 0.1
          ;(mesh.material as THREE.MeshStandardMaterial).emissiveIntensity = intensity
        }
      })

      // Smoothly interpolate agent positions
      const now = Date.now()
      agentTargetsRef.current.forEach((target, agentId) => {
        const mesh = agentsRef.current.get(agentId)
        if (!mesh) return

        const elapsed = now - target.startTime
        const progress = Math.min(elapsed / target.duration, 1)
        
        // Ease-out cubic for smooth deceleration
        const eased = 1 - Math.pow(1 - progress, 3)
        
        const currentX = target.startX + (target.x - target.startX) * eased
        const currentZ = target.startZ + (target.z - target.startZ) * eased
        
        // Use same baseHeight as in createAgentMesh
        mesh.position.set(currentX, 0.05, currentZ)
        
        // Remove completed interpolations
        if (progress >= 1) {
          agentTargetsRef.current.delete(agentId)
        }
      })

      // Always render - even if no agents yet, show the ground and venues
      try {
        renderer.render(scene, camera)
      } catch (error) {
        if (process.env.NODE_ENV === 'development') {
          console.error('⚠️ View3D: Render error:', error)
        }
      }
    }
    // Start animation immediately
    animate()
    
    console.log(`✅ View3D: Scene initialized - children: ${scene.children.length}, ground: ${scene.children.some(c => c.type === 'Mesh' && c.position.y === 0)}, grid: ${scene.children.some(c => c.type === 'GridHelper')}`)

    // Handle resize
    const handleResize = () => {
      if (!containerRef.current || !camera || !renderer) return
      camera.aspect = containerRef.current.clientWidth / containerRef.current.clientHeight
      camera.updateProjectionMatrix()
      renderer.setSize(containerRef.current.clientWidth, containerRef.current.clientHeight)
    }
    window.addEventListener('resize', handleResize)

    return () => {
      // Cleanup: Remove event listeners
      window.removeEventListener('resize', handleResize)
      
      // Cancel animation frame
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current)
        animationFrameRef.current = null
      }
      
      // Dispose controls
      if (controlsRef.current && controlsRef.current.dispose) {
        controlsRef.current.dispose()
        controlsRef.current = null
      }
      
      // Clean up all agents and their trails
      agentsRef.current.forEach((mesh, id) => {
        scene.remove(mesh)
        const trail = trailsRef.current.get(id)
        if (trail) {
          scene.remove(trail.line)
          trail.line.geometry.dispose()
          if (Array.isArray(trail.line.material)) {
            trail.line.material.forEach(m => m.dispose())
          } else {
            trail.line.material.dispose()
          }
        }
      })
      agentsRef.current.clear()
      trailsRef.current.clear()
      agentTargetsRef.current.clear()
      
      // Clean up incidents
      incidentsRef.current.forEach((mesh) => {
        scene.remove(mesh)
        mesh.geometry.dispose()
        if (Array.isArray(mesh.material)) {
          mesh.material.forEach(m => m.dispose())
        } else {
          mesh.material.dispose()
        }
      })
      incidentsRef.current.clear()
      
      // Clean up venues (they use shared geometry/material, so just remove from scene)
      venuesRef.current.forEach((mesh) => {
        scene.remove(mesh)
      })
      venuesRef.current.clear()
      
      // Remove renderer from DOM
      if (containerRef.current && renderer.domElement) {
        try {
          containerRef.current.removeChild(renderer.domElement)
        } catch (e) {
          // Element may already be removed
        }
      }
      
      // Dispose renderer (this also disposes the WebGL context)
      renderer.dispose()
      
      // Clear refs (but don't clear sceneRef if we're just re-initializing)
      // sceneRef.current = null // Don't clear - let it persist
      rendererRef.current = null
      cameraRef.current = null
      // Only reset refs on actual unmount - don't reset state to prevent re-initialization loop
      isInitializedRef.current = false
      // Don't reset isInitialized state here - it will be reset when component unmounts
    }
    // Empty dependency array - this effect should only run once on mount
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  // Update agents (DIFF-BASED: only create/update/remove as needed)
  useEffect(() => {
    // Check both state and ref for initialization
    if (!isInitialized || !isInitializedRef.current) {
      if (process.env.NODE_ENV === 'development') {
        console.log('⚠️ View3D: Agent update skipped - not initialized')
      }
      return
    }
    
    if (!sceneRef.current) {
      if (process.env.NODE_ENV === 'development') {
        console.warn('⚠️ View3D: Agent update skipped - no scene ref', {
          isInitialized,
          isInitializedRef: isInitializedRef.current,
          sceneRefExists: !!sceneRef.current,
          hasState: !!state
        })
      }
      // Don't set timeout - just return and wait for next state update
      return
    }
    
    if (!state) {
      if (process.env.NODE_ENV === 'development') {
        console.log('⚠️ View3D: Agent update skipped - no state')
      }
      return
    }

    // Prevent duplicate processing of the same state
    const currentTime = state.time || ''
    if (lastProcessedTimeRef.current === currentTime) {
      if (process.env.NODE_ENV === 'development') {
        console.log('⚠️ View3D: Agent update skipped - duplicate time:', currentTime)
      }
      return // Skip duplicate updates
    }
    lastProcessedTimeRef.current = currentTime
    
    if (process.env.NODE_ENV === 'development') {
      console.log('🎨 View3D: Processing agents for time:', currentTime)
    }

    const scene = sceneRef.current
    
    // Safely extract agents with null checks
    const allAgents = [
      ...(state.agents?.athletes || []),
      ...(state.agents?.volunteers || []),
      ...(state.agents?.security || []),
      ...(state.agents?.lvmpd || []),
      ...(state.agents?.amr || []),
      ...(state.agents?.buses || []),
    ]
    
    if (process.env.NODE_ENV === 'development') {
      console.log('🔍 View3D: State check', {
        hasState: !!state,
        hasAgents: !!state?.agents,
        agentKeys: state?.agents ? Object.keys(state.agents) : [],
        allAgentsLength: allAgents.length,
        sceneChildren: scene.children.length,
        agentsRefSize: agentsRef.current.size,
      })
    }

    // Track which agents exist in current state
    const seen = new Set<number>()

    // Update or create agents
    let created = 0
    let updated = 0
    let skipped = 0
    
    // Debug logging (only log when state actually changes)
    if (process.env.NODE_ENV === 'development') {
      console.log('🎨 View3D: Processing agents', {
        total: allAgents.length,
        athletes: state.agents.athletes.length,
        volunteers: state.agents.volunteers.length,
        security: state.agents.security.length,
        lvmpd: state.agents.lvmpd.length,
        amr: state.agents.amr.length,
        buses: state.agents.buses.length,
        time: state.time,
      })
      
      // Log first few agent locations for debugging
      if (allAgents.length > 0) {
        const sample = allAgents.slice(0, 3)
        sample.forEach((a, i) => {
          const norm = getNormalizedPos(a.location)
          console.log(`  Agent ${i}: id=${a.id}, type=${a.type}, location=${JSON.stringify(a.location)}, normalized=${norm ? JSON.stringify(norm) : 'null'}`)
        })
      }
    }
    
    allAgents.forEach((agent) => {
      if (!agent.location) {
        skipped++
        if (process.env.NODE_ENV === 'development' && skipped <= 3) {
          console.warn('⚠️ View3D: Agent missing location', { id: agent.id, type: agent.type })
        }
        return
      }

      const normalizedPos = getNormalizedPos(agent.location)
      if (!normalizedPos) {
        skipped++
        if (process.env.NODE_ENV === 'development' && skipped <= 3) {
          console.warn('⚠️ View3D: Failed to normalize position', { 
            id: agent.id, 
            type: agent.type,
            location: agent.location 
          })
        }
        return
      }

      const [x, z] = normalizedPos
      
      // Coordinates are already clamped in normalizeCoords, so they should always be in [0,1]
      // But add extra safety check
      if (isNaN(x) || isNaN(z) || !isFinite(x) || !isFinite(z)) {
        if (process.env.NODE_ENV === 'development') {
          console.warn('⚠️ View3D: Agent position invalid (NaN/Infinity)', {
            id: agent.id,
            type: agent.type,
            normalized: [x, z],
            original: agent.location,
          })
        }
        skipped++
        return
      }
      
      seen.add(agent.id)

      const existing = agentsRef.current.get(agent.id)
      
      if (!existing) {
        // Create new agent mesh
        const mesh = createAgentMesh(agent, x, z)
        scene.add(mesh)
        agentsRef.current.set(agent.id, mesh)
        created++
        
        if (process.env.NODE_ENV === 'development' && created <= 5) {
          console.log('✨ View3D: Created agent mesh', {
            id: agent.id,
            type: agent.type,
            position: [x, 0.05, z],
            scale: mesh.scale.toArray(),
            meshInScene: scene.children.includes(mesh),
            materialColor: mesh.material instanceof THREE.MeshStandardMaterial ? mesh.material.color.getHexString() : 'N/A',
            geometryType: mesh.geometry.type,
            geometrySize: mesh.geometry instanceof THREE.SphereGeometry ? (mesh.geometry as THREE.SphereGeometry).parameters.radius : 'N/A',
          })
          
          // Verify mesh is actually in scene after adding
          setTimeout(() => {
            const inScene = scene.children.includes(mesh)
            const meshPos = mesh.position.toArray()
            console.log(`🔍 View3D: Mesh ${agent.id} verification - inScene: ${inScene}, position: [${meshPos[0].toFixed(3)}, ${meshPos[1].toFixed(3)}, ${meshPos[2].toFixed(3)}], visible: ${mesh.visible}`)
          }, 100)
        }

        // Create trail for athletes
        if (agent.type === 'athlete') {
          const maxPoints = 30
          const buffer = new Float32Array(maxPoints * 3)
          const geometry = new THREE.BufferGeometry()
          geometry.setAttribute('position', new THREE.BufferAttribute(buffer, 3))
          const material = new THREE.LineBasicMaterial({
            color: new THREE.Color('#F4C430'),
            transparent: true,
            opacity: 0.3,
            linewidth: 1,
          })
          const line = new THREE.Line(geometry, material)
          scene.add(line)
          trailsRef.current.set(agent.id, { line, buffer, index: 0, maxPoints })
        }
      } else {
        // Smooth interpolation: store target position
        const currentPos = existing.position
        const currentX = currentPos.x
        const currentZ = currentPos.z
        
        // Only interpolate if position actually changed
        const distance = Math.sqrt(Math.pow(x - currentX, 2) + Math.pow(z - currentZ, 2))
        if (distance > 0.001) {
          // Dynamic interpolation duration based on distance (min 300ms, max 800ms)
          const baseDuration = 500
          const distanceFactor = Math.min(distance * 2000, 1) // Scale distance to 0-1
          const duration = baseDuration + (distanceFactor * 300)
          
          agentTargetsRef.current.set(agent.id, {
            x, z,
            startX: currentX,
            startZ: currentZ,
            startTime: Date.now(),
            duration,
          })
        } else {
          // Very small movement, set directly (use same baseHeight)
          existing.position.set(x, 0.05, z)
        }
        updated++

        // Update trail for athletes (circular buffer - O(1) instead of O(n))
        if (agent.type === 'athlete') {
          const trail = trailsRef.current.get(agent.id)
          if (trail) {
            const { line, buffer, maxPoints } = trail
            
            // Use circular buffer: write to current index, wrap around
            const idx = trail.index % maxPoints
            buffer[idx * 3] = x
            buffer[idx * 3 + 1] = 0.04
            buffer[idx * 3 + 2] = z
            
            trail.index++
            const drawCount = Math.min(trail.index, maxPoints)
            
            // Update geometry
            const pos = line.geometry.attributes.position as THREE.BufferAttribute
            pos.needsUpdate = true
            line.geometry.setDrawRange(0, drawCount)
          }
        }
      }
    })

    // Remove agents that no longer exist
    agentsRef.current.forEach((mesh, id) => {
      if (!seen.has(id)) {
        scene.remove(mesh)
        // Don't dispose geometry/material (they're shared)
        agentsRef.current.delete(id)

        // Remove trail
        const trail = trailsRef.current.get(id)
        if (trail) {
          scene.remove(trail.line)
          trail.line.geometry.dispose()
          if (Array.isArray(trail.line.material)) {
            trail.line.material.forEach(m => m.dispose())
          } else {
            trail.line.material.dispose()
          }
          trailsRef.current.delete(id)
        }
      }
    })
    
    // Log summary
    if (process.env.NODE_ENV === 'development') {
      if (created > 0 || updated > 0 || skipped > 0) {
        console.log(`✅ View3D: Agents processed - Created: ${created}, Updated: ${updated}, Skipped: ${skipped}, Total in scene: ${agentsRef.current.size}`)
      }
      if (allAgents.length > 0 && created === 0 && updated === 0) {
        console.warn(`⚠️ View3D: ${allAgents.length} agents in state but none processed!`)
      }
    }
    // Only depend on state - isInitialized is checked via ref to prevent loops
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [state])

  // Update incidents (DIFF-BASED)
  useEffect(() => {
    if (!isInitialized || !isInitializedRef.current || !sceneRef.current || !state) return

    const scene = sceneRef.current
    const seen = new Set<string>()

    if (state.incidents && Array.isArray(state.incidents)) {
      state.incidents.forEach((incident: any) => {
        if (!incident.location || !Array.isArray(incident.location)) return

        const normalizedPos = getNormalizedPos(incident.location as [number, number])
        if (!normalizedPos) return

        const [x, z] = normalizedPos
        const incidentId = incident.id || Math.random().toString()
        seen.add(incidentId)

        const existing = incidentsRef.current.get(incidentId)
        
        if (!existing) {
          // Create new incident
          const color = incident.type === 'medical_event' ? '#F8B88B' : '#F1948A'
          const geometry = new THREE.SphereGeometry(0.015, 16, 16)
          const material = new THREE.MeshStandardMaterial({
            color: color,
            emissive: color,
            emissiveIntensity: 0.3,
            transparent: true,
            opacity: 0.85,
            roughness: 0.2,
          })

          const mesh = new THREE.Mesh(geometry, material)
          mesh.position.set(x, 0.15, z)
          mesh.castShadow = true
          scene.add(mesh)
          incidentsRef.current.set(incidentId, mesh)
        } else {
          // Update existing incident position
          existing.position.set(x, 0.15, z)
        }
      })
    }

    // Remove resolved incidents
    incidentsRef.current.forEach((mesh, id) => {
      if (!seen.has(id)) {
        scene.remove(mesh)
        mesh.geometry.dispose()
        if (Array.isArray(mesh.material)) {
          mesh.material.forEach(m => m.dispose())
        } else {
          mesh.material.dispose()
        }
        incidentsRef.current.delete(id)
      }
    })
    // Only depend on state - isInitialized is checked via ref to prevent loops
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [state])

  return (
    <div 
      ref={containerRef} 
      style={{
        position: 'absolute',
        top: 0,
        left: 0,
        width: '100%',
        height: '100%', // ✅ Uses parent's explicit height - fixes blank canvas issue
        overflow: 'hidden',
        background: 'linear-gradient(135deg, #0a0a0f 0%, #1a1a2e 100%)',
      }}
    >
      {/* Info overlay - pointer-events-none so it doesn't block canvas */}
      <div className="absolute top-4 left-4 z-10 text-white text-sm bg-black/60 px-4 py-3 rounded-lg backdrop-blur-md border border-white/10 pointer-events-none">
        <div className="font-semibold mb-1 text-base">3D Live Simulation</div>
        <div className="text-xs opacity-80 mb-2">
          Click & drag to rotate • Scroll to zoom • Right-click to pan
        </div>
        {isInitialized && (
          <div className="text-xs mt-2 text-green-400">
            ✓ Scene: {agentsRef.current.size} agents rendered
          </div>
        )}
        {!state && isInitialized && (
          <div className="text-xs mt-2 opacity-90 flex items-center gap-2" style={{ color: '#FFD700' }}>
            <span className="animate-pulse">●</span>
            <span>Click a scenario button to start</span>
          </div>
        )}
        {state && (
          <div className="text-xs mt-2 opacity-90 flex items-center gap-2" style={{ color: '#2ECC71' }}>
            <span className="animate-pulse">●</span>
            <span>{Object.values(state.agents || {}).flat().length} agents in state</span>
          </div>
        )}
      </div>

      {/* Legend */}
      <div className="absolute bottom-4 left-4 z-10 text-white text-xs bg-black/70 px-3 py-2 rounded backdrop-blur-sm border border-white/10">
        <div className="font-semibold mb-2" style={{ fontSize: '13px', fontWeight: 600 }}>Legend</div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <div style={{ width: '12px', height: '12px', borderRadius: '50%', backgroundColor: '#F4C430', flexShrink: 0 }}></div>
            <span>Athletes</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <div style={{ width: '12px', height: '12px', borderRadius: '50%', backgroundColor: '#2ECC71', flexShrink: 0 }}></div>
            <span>Volunteers</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <div style={{ width: '12px', height: '12px', borderRadius: '50%', backgroundColor: '#00F5D4', flexShrink: 0 }}></div>
            <span>Security</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <div style={{ width: '12px', height: '12px', borderRadius: '50%', backgroundColor: '#0077FF', flexShrink: 0 }}></div>
            <span>LVMPD</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <div style={{ width: '12px', height: '12px', borderRadius: '50%', backgroundColor: '#E74C3C', flexShrink: 0 }}></div>
            <span>AMR</span>
          </div>
        </div>
      </div>
    </div>
  )
}
