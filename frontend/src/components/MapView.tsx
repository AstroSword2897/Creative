import { useEffect, useRef } from 'react'
import mapboxgl from 'mapbox-gl'
import { SimulationState } from '../types'

interface MapViewProps {
  state: SimulationState | null
}

export default function MapView({ state }: MapViewProps) {
  const mapContainer = useRef<HTMLDivElement>(null)
  const map = useRef<mapboxgl.Map | null>(null)
  const markers = useRef<Map<number, mapboxgl.Marker>>(new Map())

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

    // Add custom styling for premium look
    map.current.on('load', () => {
      // Add glow effect to map container
      if (mapContainer.current) {
        mapContainer.current.style.boxShadow = 'inset 0 0 100px rgba(0, 119, 255, 0.1)'
      }
    })

    return () => {
      map.current?.remove()
    }
  }, [])

  useEffect(() => {
    if (!map.current || !state) return

    // Clear existing markers
    markers.current.forEach(marker => marker.remove())
    markers.current.clear()

    // Add markers for all agents
    const allAgents = [
      ...state.agents.athletes,
      ...state.agents.volunteers,
      ...state.agents.security,
      ...state.agents.lvmpd,
      ...state.agents.amr,
      ...state.agents.buses,
    ]

    allAgents.forEach(agent => {
      if (!agent.location) return

      const color = getAgentColor(agent.type)
      const el = document.createElement('div')
      el.style.width = '12px'
      el.style.height = '12px'
      el.style.borderRadius = '50%'
      el.style.backgroundColor = color
      el.style.border = '2px solid rgba(255, 255, 255, 0.9)'
      el.style.boxShadow = `0 0 12px ${color}80, 0 2px 8px rgba(0,0,0,0.4)`
      el.style.transition = 'all 0.2s ease-out'
      
      // Add glow effect for athletes
      if (agent.type === 'athlete') {
        el.style.boxShadow = `0 0 16px ${color}CC, 0 0 8px ${color}80, 0 2px 8px rgba(0,0,0,0.4)`
      }

      const marker = new mapboxgl.Marker(el)
        .setLngLat([agent.location[0], agent.location[1]])
        .addTo(map.current!)

      markers.current.set(agent.id, marker)
    })
  }, [state])

  return (
    <div ref={mapContainer} className="w-full h-full" />
  )
}

function getAgentColor(type: string): string {
  const colors: Record<string, string> = {
    athlete: '#F4C430',      // Vegas Gold - Special Olympics athletes
    volunteer: '#2ECC71',   // Safe Green - Volunteers
    hotel_security: '#00F5D4', // Neon Teal - Hotel security teams
    lvmpd: '#0077FF',       // Electric Blue - LVMPD (Las Vegas Metropolitan Police Department)
    amr: '#E74C3C',         // Alert Red - AMR Las Vegas (American Medical Response)
    bus: '#6366F1',         // Indigo - RTC Buses / Transportation
    fire_rescue: '#E74C3C', // Alert Red - Las Vegas Fire & Rescue
  }
  return colors[type] || '#6B7280'
}

