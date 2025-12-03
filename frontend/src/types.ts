export interface Agent {
  id: number
  type: string
  location: [number, number] | null
  status: string
  medical_event?: boolean
  hotel_id?: string
}

export interface Incident {
  id: string
  type: string
  location: [number, number]
  timestamp: string
}

export interface Metrics {
  safety_score: number
  avg_response_time: number
  containment_rate: number
  athlete_delay_minutes: number
  accessibility_coverage: number
  medical_events_count: number
  incidents_resolved: number
}

export interface SimulationState {
  time: string
  agents: {
    athletes: Agent[]
    volunteers: Agent[]
    security: Agent[]
    lvmpd: Agent[]
    amr: Agent[]
    buses: Agent[]
  }
  incidents: Incident[]
  metrics: Metrics
}

