import { SimulationState } from '../types'

interface MetricsPanelProps {
  state: SimulationState | null
}

export default function MetricsPanel({ state }: MetricsPanelProps) {
  if (!state) {
    return (
      <div
        className="panel-elevated"
        style={{
          padding: 'var(--spacing-xl)',
          borderRadius: 'var(--radius-md)',
          textAlign: 'center',
          marginTop: 'var(--spacing-2xl)',
          background: 'rgba(18, 20, 23, 0.45)',
          border: '1px solid rgba(255, 255, 255, 0.08)',
        }}
      >
        <div className="text-h3" style={{ marginBottom: 'var(--spacing-sm)', opacity: 0.7 }}>
          Live Metrics
        </div>
        <div className="text-small" style={{ opacity: 0.6, lineHeight: '1.6' }}>
          Metrics will appear here once you start a simulation.
        </div>
        <div className="text-small" style={{ marginTop: 'var(--spacing-md)', opacity: 0.5 }}>
          Click a scenario button ← to begin
        </div>
      </div>
    )
  }

  const metrics = state.metrics ?? ({} as any)
  const time = state.time
  const incidents = Array.isArray((state as any).incidents) ? (state as any).incidents : []

  const safetyScore =
    typeof metrics.safety_score === 'number' ? metrics.safety_score : 0
  const avgResponseTime =
    typeof metrics.avg_response_time === 'number' ? metrics.avg_response_time : 0
  const containmentRate =
    typeof metrics.containment_rate === 'number' ? metrics.containment_rate : 0
  const medicalEventsCount =
    typeof metrics.medical_events_count === 'number' ? metrics.medical_events_count : 0
  const incidentsResolved =
    typeof metrics.incidents_resolved === 'number' ? metrics.incidents_resolved : 0

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--spacing-xl)' }}>
      <h2 className="text-h2">Metrics</h2>

      {/* Safety Score - Large Display with Glow */}
      <div 
        className="card-kpi animate-fade-in glow-blue"
        style={{
          background: 'linear-gradient(135deg, var(--color-electric-blue) 0%, #0052CC 100%)',
          padding: 'var(--spacing-xl)',
          position: 'relative',
          overflow: 'hidden',
        }}
      >
        <div className="text-small" style={{ opacity: 0.9, marginBottom: 'var(--spacing-sm)' }}>
          Safety Score
        </div>
        <div className="text-kpi" style={{ marginBottom: 'var(--spacing-xs)' }}>
          {safetyScore.toFixed(1)}
        </div>
        <div className="text-small" style={{ opacity: 0.75 }}>
          out of 100
        </div>
      </div>

      {/* Other Metrics */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--spacing-md)' }}>
        <div className="card-kpi animate-fade-in" style={{ background: 'rgba(18, 20, 23, 0.45)', border: '1px solid rgba(255, 255, 255, 0.08)', padding: 'var(--spacing-md)', borderRadius: 'var(--radius-md)' }}>
          <div className="text-small" style={{ opacity: 0.7, marginBottom: 'var(--spacing-xs)', fontSize: '12px' }}>
            Average Response Time
          </div>
          <div className="text-h3" style={{ color: '#00F5D4', fontSize: '20px', fontWeight: 600 }}>
            {(avgResponseTime / 60).toFixed(1)} min
          </div>
        </div>

        <div className="card-kpi animate-fade-in" style={{ background: 'rgba(18, 20, 23, 0.45)', border: '1px solid rgba(255, 255, 255, 0.08)', padding: 'var(--spacing-md)', borderRadius: 'var(--radius-md)' }}>
          <div className="text-small" style={{ opacity: 0.7, marginBottom: 'var(--spacing-xs)', fontSize: '12px' }}>
            Containment Rate
          </div>
          <div className="text-h3" style={{ color: '#2ECC71', fontSize: '20px', fontWeight: 600 }}>
            {(containmentRate * 100).toFixed(1)}%
          </div>
        </div>

        <div className="card-kpi animate-fade-in" style={{ background: 'rgba(18, 20, 23, 0.45)', border: '1px solid rgba(255, 255, 255, 0.08)', padding: 'var(--spacing-md)', borderRadius: 'var(--radius-md)' }}>
          <div className="text-small" style={{ opacity: 0.7, marginBottom: 'var(--spacing-xs)', fontSize: '12px' }}>
            Medical Events
          </div>
          <div className="text-h3" style={{ color: '#E74C3C', fontSize: '20px', fontWeight: 600 }}>
            {medicalEventsCount}
          </div>
        </div>

        <div className="card-kpi animate-fade-in" style={{ background: 'rgba(18, 20, 23, 0.45)', border: '1px solid rgba(255, 255, 255, 0.08)', padding: 'var(--spacing-md)', borderRadius: 'var(--radius-md)' }}>
          <div className="text-small" style={{ opacity: 0.7, marginBottom: 'var(--spacing-xs)', fontSize: '12px' }}>
            Incidents Resolved
          </div>
          <div className="text-h3" style={{ color: '#F4C430', fontSize: '20px', fontWeight: 600 }}>
            {incidentsResolved}
          </div>
        </div>
      </div>

      {/* Active Incidents */}
      {incidents.length > 0 && (
        <div style={{ marginTop: 'var(--spacing-lg)' }}>
          <h3 className="text-h3" style={{ marginBottom: 'var(--spacing-sm)' }}>
            Active Incidents
          </h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--spacing-sm)' }}>
            {incidents.map(incident => (
              <div
                key={incident.id}
                className="card-incident animate-slide-in"
              >
                <div className="text-body" style={{ color: 'var(--color-alert-red)', fontWeight: 600 }}>
                  {incident.type}
                </div>
                <div className="text-small" style={{ color: 'var(--color-alert-red)', marginTop: 'var(--spacing-xs)', opacity: 0.8 }}>
                  {new Date(incident.timestamp).toLocaleTimeString()}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Current Time */}
      <div style={{ 
        marginTop: 'var(--spacing-lg)', 
        paddingTop: 'var(--spacing-md)', 
        borderTop: '1px solid rgba(255, 255, 255, 0.1)' 
      }}>
        <div className="text-small" style={{ opacity: 0.6, marginBottom: 'var(--spacing-xs)' }}>
          Simulation Time
        </div>
        <div className="text-body" style={{ fontFamily: 'monospace', opacity: 0.9 }}>
          {time ? new Date(time).toLocaleString() : '—'}
        </div>
      </div>
    </div>
  )
}

