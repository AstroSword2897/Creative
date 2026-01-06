import { useEffect, useRef, useState } from 'react'
import * as THREE from 'three'
import { SimulationState } from '../types'

interface View3DProps {
  state: SimulationState | null
}

// Shared geometry cache (created once, reused)
const geometryCache = {
  athlete: new THREE.SphereGeometry(0.018, 16, 16),
  bus: new THREE.BoxGeometry(0.05, 0.024, 0.08),
  responder: new THREE.CylinderGeometry(0.012, 0.0108, 0.03, 16),
  default: new THREE.BoxGeometry(0.024, 0.04, 0.024),
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

  // Normalize coordinates from lat/lon to 0-1 space
  const normalizeCoords = (lat: number, lon: number): [number, number] => {
    const latMin = 36.0
    const latMax = 36.2
    const lonMin = -115.3
    const lonMax = -115.1
    
    const x = (lon - lonMin) / (lonMax - lonMin)
    const y = (lat - latMin) / (latMax - latMin)
    return [x, y]
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

  // Create agent mesh (called once per agent)
  const createAgentMesh = (agent: any, x: number, z: number): THREE.Mesh => {
    let geometry: THREE.BufferGeometry
    let material: THREE.Material

    if (agent.type === 'athlete') {
      geometry = geometryCache.athlete
      material = materialCache.athlete
    } else if (agent.type === 'bus') {
      geometry = geometryCache.bus
      material = materialCache.bus
    } else if (agent.type === 'lvmpd' || agent.type === 'amr') {
      geometry = geometryCache.responder
      material = materialCache[agent.type] || materialCache.default
    } else {
      geometry = geometryCache.default
      material = materialCache[agent.type] || materialCache.default
    }

    const mesh = new THREE.Mesh(geometry, material)
    mesh.position.set(x, 0.03, z)
    mesh.castShadow = true
    mesh.receiveShadow = true
    return mesh
  }

  // Initialize scene (runs once)
  useEffect(() => {
    if (!containerRef.current || isInitialized) return

    const scene = new THREE.Scene()
    scene.background = new THREE.Color(0x0a0a0f)
    scene.fog = new THREE.Fog(0x0a0a0f, 10, 50)
    sceneRef.current = scene

    const camera = new THREE.PerspectiveCamera(
      60,
      containerRef.current.clientWidth / containerRef.current.clientHeight,
      0.1,
      1000
    )
    camera.position.set(0.5, 1.2, 0.8)
    camera.lookAt(0.5, 0, 0.5)
    cameraRef.current = camera

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true })
    renderer.setSize(containerRef.current.clientWidth, containerRef.current.clientHeight)
    renderer.setPixelRatio(Math.min(2, window.devicePixelRatio)) // Clamp for performance
    renderer.shadowMap.enabled = true
    renderer.shadowMap.type = THREE.PCFSoftShadowMap
    containerRef.current.appendChild(renderer.domElement)
    rendererRef.current = renderer

    // Lighting
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.6)
    scene.add(ambientLight)

    const directionalLight = new THREE.DirectionalLight(0xfff8e1, 0.8)
    directionalLight.position.set(1, 2, 1)
    directionalLight.castShadow = true
    directionalLight.shadow.camera.left = -2
    directionalLight.shadow.camera.right = 2
    directionalLight.shadow.camera.top = 2
    directionalLight.shadow.camera.bottom = -2
    scene.add(directionalLight)

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

    // Grid helper
    const gridHelper = new THREE.GridHelper(1, 20, 0x333344, 0x222233)
    gridHelper.position.set(0.5, 0.01, 0.5)
    scene.add(gridHelper)

    // Initialize venues (static)
    const venues = [
      { name: 'MGM Grand', lat: 36.1027, lon: -115.171, type: 'hotel' },
      { name: 'UNLV Cox', lat: 36.102, lon: -115.150, type: 'venue' },
      { name: 'Thomas & Mack', lat: 36.104, lon: -115.152, type: 'venue' },
      { name: 'Airport', lat: 36.084, lon: -115.153, type: 'airport' },
    ]

    venues.forEach((venue) => {
      const [x, z] = normalizeCoords(venue.lat, venue.lon)
      const color = venue.type === 'hotel' ? '#FFD700' : venue.type === 'venue' ? '#4ECDC4' : '#ffffff'
      
      const geometry = new THREE.CylinderGeometry(0.02, 0.02, 0.1, 16)
      const material = new THREE.MeshStandardMaterial({
        color: color,
        emissive: color,
        emissiveIntensity: 0.25,
        roughness: 0.3,
      })

      const mesh = new THREE.Mesh(geometry, material)
      mesh.position.set(x, 0.05, z)
      mesh.castShadow = true
      scene.add(mesh)
      venuesRef.current.set(venue.name, mesh)
    })

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
      controls.target.set(0.5, 0, 0.5)
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
        camera.lookAt(0.5, 0, 0.5)
        previousMousePosition = { x: e.clientX, y: e.clientY }
      }
      
      const onMouseUp = () => {
        isDragging = false
      }
      
      const onWheel = (e: WheelEvent) => {
        camera.position.multiplyScalar(1 + e.deltaY * 0.001)
        camera.lookAt(0.5, 0, 0.5)
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

    setIsInitialized(true)

    // Animation loop
    const animate = () => {
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

      renderer.render(scene, camera)
    }
    animate()

    // Handle resize
    const handleResize = () => {
      if (!containerRef.current || !camera || !renderer) return
      camera.aspect = containerRef.current.clientWidth / containerRef.current.clientHeight
      camera.updateProjectionMatrix()
      renderer.setSize(containerRef.current.clientWidth, containerRef.current.clientHeight)
    }
    window.addEventListener('resize', handleResize)

    return () => {
      window.removeEventListener('resize', handleResize)
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current)
      }
      if (controlsRef.current && controlsRef.current.dispose) {
        controlsRef.current.dispose()
      }
      if (containerRef.current && renderer.domElement) {
        containerRef.current.removeChild(renderer.domElement)
      }
      renderer.dispose()
    }
  }, [isInitialized])

  // Update agents (DIFF-BASED: only create/update/remove as needed)
  useEffect(() => {
    if (!sceneRef.current || !state) {
      console.log('View3D: No scene or state', { hasScene: !!sceneRef.current, hasState: !!state })
      return
    }

    const scene = sceneRef.current
    const allAgents = [
      ...state.agents.athletes,
      ...state.agents.volunteers,
      ...state.agents.security,
      ...state.agents.lvmpd,
      ...state.agents.amr,
      ...state.agents.buses,
    ]

    console.log('View3D: Updating agents', {
      total: allAgents.length,
      athletes: state.agents.athletes.length,
      volunteers: state.agents.volunteers.length,
      security: state.agents.security.length,
      lvmpd: state.agents.lvmpd.length,
      amr: state.agents.amr.length,
      buses: state.agents.buses.length,
    })

    // Track which agents exist in current state
    const seen = new Set<number>()

    // Update or create agents
    let created = 0
    let updated = 0
    let skipped = 0
    
    allAgents.forEach((agent) => {
      if (!agent.location) {
        skipped++
        return
      }

      const parsedLoc = parseLocation(agent.location)
      if (!parsedLoc) {
        skipped++
        return
      }

      const [x, z] = normalizeCoords(parsedLoc[0], parsedLoc[1])
      seen.add(agent.id)
      
      // Debug first few agents
      if (created + updated < 3) {
        console.log(`Agent ${agent.id} (${agent.type}):`, {
          location: agent.location,
          parsed: parsedLoc,
          normalized: [x, z],
          position: [x, 0.03, z]
        })
      }

      const existing = agentsRef.current.get(agent.id)
      
      if (!existing) {
        // Create new agent mesh
        const mesh = createAgentMesh(agent, x, z)
        scene.add(mesh)
        agentsRef.current.set(agent.id, mesh)
        created++

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
        // Update existing agent position
        existing.position.set(x, 0.03, z)
        updated++

        // Update trail for athletes
        if (agent.type === 'athlete') {
          const trail = trailsRef.current.get(agent.id)
          if (trail) {
            const { line, buffer, maxPoints } = trail
            const pos = line.geometry.attributes.position as THREE.BufferAttribute
            
            // Shift buffer (ring buffer)
            for (let i = 0; i < (maxPoints - 1) * 3; i++) {
              buffer[i] = buffer[i + 3]
            }
            
            // Add new point at end
            const endIdx = (maxPoints - 1) * 3
            buffer[endIdx] = x
            buffer[endIdx + 1] = 0.04
            buffer[endIdx + 2] = z
            
            pos.needsUpdate = true
            trail.index = Math.min(trail.index + 1, maxPoints)
            
            // Update draw range
            line.geometry.setDrawRange(0, trail.index)
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
  }, [state])

  // Update incidents (DIFF-BASED)
  useEffect(() => {
    if (!sceneRef.current || !state) return

    const scene = sceneRef.current
    const seen = new Set<string>()

    if (state.incidents && Array.isArray(state.incidents)) {
      state.incidents.forEach((incident: any) => {
        if (!incident.location || !Array.isArray(incident.location)) return

        const parsedLoc = parseLocation(incident.location as [number, number])
        if (!parsedLoc) return

        const [x, z] = normalizeCoords(parsedLoc[0], parsedLoc[1])
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
  }, [state])

  return (
    <div 
      ref={containerRef} 
      className="w-full h-full relative"
      style={{
        background: 'linear-gradient(135deg, #0a0a0f 0%, #1a1a2e 100%)',
        minHeight: '100%',
        minWidth: '100%',
      }}
    >
      {/* Info overlay */}
      <div className="absolute top-4 left-4 z-10 text-white text-sm bg-black/50 px-3 py-2 rounded backdrop-blur-sm">
        <div className="font-semibold mb-1">3D Visualization</div>
        <div className="text-xs opacity-75">
          Click & drag to rotate • Scroll to zoom • Right-click to pan
        </div>
        {!state && (
          <div className="text-xs mt-2 opacity-90" style={{ color: '#FFD700' }}>
            Select a scenario to start simulation
          </div>
        )}
        {state && (
          <div className="text-xs mt-2 opacity-90" style={{ color: '#2ECC71' }}>
            Simulation active • {Object.values(state.agents).flat().length} agents
          </div>
        )}
      </div>

      {/* Legend */}
      <div className="absolute bottom-4 left-4 z-10 text-white text-xs bg-black/50 px-3 py-2 rounded backdrop-blur-sm">
        <div className="font-semibold mb-2">Legend</div>
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-[#F4C430]"></div>
            <span>Athletes</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-[#2ECC71]"></div>
            <span>Volunteers</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-[#00F5D4]"></div>
            <span>Security</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-[#0077FF]"></div>
            <span>LVMPD</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-[#E74C3C]"></div>
            <span>AMR</span>
          </div>
        </div>
      </div>
    </div>
  )
}
