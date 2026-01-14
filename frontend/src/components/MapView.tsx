import { useEffect, useRef } from 'react'
import mapboxgl from 'mapbox-gl'
import { SimulationState } from '../types'

interface MapViewProps {
  state: SimulationState | null
}

// ✅ OPTIMIZED: Memoized color lookup for performance
const AGENT_COLORS: Record<string, string> = {
  athlete: '#F4C430',      // Vegas Gold - Special Olympics athletes
  volunteer: '#2ECC71',   // Safe Green - Volunteers
  hotel_security: '#00F5D4', // Neon Teal - Hotel security teams
  lvmpd: '#0077FF',       // Electric Blue - LVMPD
  amr: '#E74C3C',         // Alert Red - AMR Las Vegas
  bus: '#6366F1',         // Indigo - RTC Buses
  fire_rescue: '#E74C3C', // Alert Red - Fire & Rescue
}

function getAgentColor(type: string): string {
  return AGENT_COLORS[type] || '#6B7280'
}

// ✅ OPTIMIZED: Create marker element with consistent styling
function createMarkerElement(agentType: string, color: string): HTMLDivElement {
  const el = document.createElement('div')
  el.style.width = '12px'
  el.style.height = '12px'
  el.style.borderRadius = '50%'
  el.style.backgroundColor = color
  el.style.border = '2px solid rgba(255, 255, 255, 0.9)'
  el.style.transition = 'all 0.2s ease-out'
  el.style.cursor = 'pointer'
  
  // Enhanced glow effect for athletes
  if (agentType === 'athlete') {
    el.style.boxShadow = `0 0 16px ${color}CC, 0 0 8px ${color}80, 0 2px 8px rgba(0,0,0,0.4)`
  } else {
    el.style.boxShadow = `0 0 12px ${color}80, 0 2px 8px rgba(0,0,0,0.4)`
  }
  
  return el
}

export default function MapView({ state }: MapViewProps) {
  const mapContainer = useRef<HTMLDivElement>(null)
  const map = useRef<mapboxgl.Map | null>(null)
  const markers = useRef<Map<number, mapboxgl.Marker>>(new Map())
  const markerAnimations = useRef<Map<number, { start: [number, number], end: [number, number], startTime: number }>>(new Map())

  useEffect(() => {
    if (!mapContainer.current || map.current) return

    // Initialize map
    mapboxgl.accessToken = (import.meta as any).env?.VITE_MAPBOX_TOKEN || 'pk.eyJ1IjoibWFwYm94IiwiYSI6ImNpejY4NXV4NTIyMmY2Zm5lOXhmNTY3ZmEifQ.rJcFIG214AriISLbB6B5aw'
    
    map.current = new mapboxgl.Map({
      container: mapContainer.current,
      style: 'mapbox://styles/mapbox/dark-v11', // Dark theme for premium look
      center: [-115.153, 36.102], // Las Vegas Strip
      zoom: 12,
    })

    // Add custom styling for premium look and resize on load
    map.current.on('load', () => {
      // Add glow effect to map container
      if (mapContainer.current) {
        mapContainer.current.style.boxShadow = 'inset 0 0 100px rgba(0, 119, 255, 0.1)'
      }
      // ✅ CRITICAL: Resize map after load to ensure it renders
      map.current?.resize()
    })

    return () => {
      // Cleanup animations
      markerAnimations.current.clear()
      map.current?.remove()
    }
  }, [])

  // ✅ ENHANCED: Smooth animated marker updates with diff-based approach
  useEffect(() => {
    if (!map.current || !state) return

    // ✅ CRITICAL: Resize map when state updates to ensure visibility
    map.current.resize()

    // Collect all agents
    const allAgents = [
      ...state.agents.athletes,
      ...state.agents.volunteers,
      ...state.agents.security,
      ...state.agents.lvmpd,
      ...state.agents.amr,
      ...state.agents.buses,
    ].filter(agent => agent.location) // Filter out agents without locations

    const newAgentIds = new Set<number>()
    const animationDuration = 1000 // 1 second animation

    // Update or create markers
    allAgents.forEach(agent => {
      if (!agent.location) return

      newAgentIds.add(agent.id)
      const color = getAgentColor(agent.type)
      const newLocation: [number, number] = [agent.location[0], agent.location[1]]

      if (markers.current.has(agent.id)) {
        // ✅ OPTIMIZED: Update existing marker position with smooth animation
        const marker = markers.current.get(agent.id)!
        const currentLocation = marker.getLngLat()
        const currentPos: [number, number] = [currentLocation.lng, currentLocation.lat]
        
        // Check if position actually changed
        const distance = Math.sqrt(
          Math.pow(currentPos[0] - newLocation[0], 2) + 
          Math.pow(currentPos[1] - newLocation[1], 2)
        )
        
        if (distance > 0.0001) { // Only animate if moved significantly
          // Store animation state
          markerAnimations.current.set(agent.id, {
            start: currentPos,
            end: newLocation,
            startTime: Date.now()
          })
          
          // Use Mapbox's easeTo for smooth camera-like movement, or manual interpolation
          // For markers, we'll use requestAnimationFrame for smooth interpolation
          animateMarker(marker, currentPos, newLocation, animationDuration)
        }
      } else {
        // Create new marker
        const el = createMarkerElement(agent.type, color)
        const marker = new mapboxgl.Marker(el)
          .setLngLat(newLocation)
          .addTo(map.current!)
        
        markers.current.set(agent.id, marker)
      }
    })

    // ✅ OPTIMIZED: Remove markers for agents no longer present
    markers.current.forEach((marker, id) => {
      if (!newAgentIds.has(id)) {
        marker.remove()
        markers.current.delete(id)
        markerAnimations.current.delete(id)
      }
    })
  }, [state])

  // ✅ ENHANCED: Smooth marker animation function
  function animateMarker(
    marker: mapboxgl.Marker,
    start: [number, number],
    end: [number, number],
    duration: number
  ) {
    const startTime = Date.now()
    
    function animate() {
      const elapsed = Date.now() - startTime
      const progress = Math.min(elapsed / duration, 1)
      
      // Ease-out cubic for smooth deceleration
      const eased = 1 - Math.pow(1 - progress, 3)
      
      const currentLng = start[0] + (end[0] - start[0]) * eased
      const currentLat = start[1] + (end[1] - start[1]) * eased
      
      marker.setLngLat([currentLng, currentLat])
      
      if (progress < 1) {
        requestAnimationFrame(animate)
      }
    }
    
    animate()
  }

  return (
    <div 
      ref={mapContainer} 
      style={{
        width: '100%',
        height: '100%',
        minHeight: '400px', // ✅ Ensure minimum height
        position: 'relative',
      }}
    />
  )
}

