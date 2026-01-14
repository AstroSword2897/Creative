import { SimulationState, Incident } from '../types'

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
        {/* Average Response Time */}
        <div className="card-kpi animate-fade-in" style={{ 
          background: 'rgba(18, 20, 23, 0.65)', 
          border: '2px solid rgba(0, 245, 212, 0.3)', 
          padding: '16px', 
          borderRadius: '8px',
          minHeight: '80px',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'center'
        }}>
          <div style={{ 
            fontSize: '11px', 
            fontWeight: 600,
            textTransform: 'uppercase',
            letterSpacing: '0.5px',
            marginBottom: '8px', 
            color: 'rgba(255, 255, 255, 0.8)' 
          }}>
            Average Response Time
          </div>
          <div style={{ 
            color: '#00F5D4', 
            fontSize: '24px', 
            fontWeight: 700,
            fontFamily: 'monospace'
          }}>
            {avgResponseTime > 0 
              ? `${(avgResponseTime / 60).toFixed(1)} min` 
              : medicalEventsCount > 0 || incidents.length > 0
              ? '< 1 min'
              : '—'}
          </div>
          {avgResponseTime === 0 && (medicalEventsCount > 0 || incidents.length > 0) && (
            <div style={{ fontSize: '10px', color: 'rgba(0, 245, 212, 0.6)', marginTop: '4px' }}>
              Active responses in progress
            </div>
          )}
        </div>

        {/* Containment Rate */}
        <div className="card-kpi animate-fade-in" style={{ 
          background: 'rgba(18, 20, 23, 0.65)', 
          border: '2px solid rgba(46, 204, 113, 0.3)', 
          padding: '16px', 
          borderRadius: '8px',
          minHeight: '80px',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'center'
        }}>
          <div style={{ 
            fontSize: '11px', 
            fontWeight: 600,
            textTransform: 'uppercase',
            letterSpacing: '0.5px',
            marginBottom: '8px', 
            color: 'rgba(255, 255, 255, 0.8)' 
          }}>
            Containment Rate
          </div>
          <div style={{ 
            color: containmentRate > 0 ? '#2ECC71' : 'rgba(255, 255, 255, 0.4)', 
            fontSize: '24px', 
            fontWeight: 700,
            fontFamily: 'monospace'
          }}>
            {containmentRate > 0 ? `${(containmentRate * 100).toFixed(1)}%` : '0.0%'}
          </div>
          {containmentRate === 0 && (medicalEventsCount > 0 || incidents.length > 0) && (
            <div style={{ fontSize: '10px', color: 'rgba(255, 255, 255, 0.3)', marginTop: '4px' }}>
              {incidentsResolved} of {medicalEventsCount + incidents.length} resolved
            </div>
          )}
        </div>

        {/* Medical Events */}
        <div className="card-kpi animate-fade-in" style={{ 
          background: 'rgba(18, 20, 23, 0.65)', 
          border: '2px solid rgba(231, 76, 60, 0.3)', 
          padding: '16px', 
          borderRadius: '8px',
          minHeight: '80px',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'center'
        }}>
          <div style={{ 
            fontSize: '11px', 
            fontWeight: 600,
            textTransform: 'uppercase',
            letterSpacing: '0.5px',
            marginBottom: '8px', 
            color: 'rgba(255, 255, 255, 0.8)' 
          }}>
            Medical Events
          </div>
          <div style={{ 
            color: '#E74C3C', 
            fontSize: '28px', 
            fontWeight: 700,
            fontFamily: 'monospace'
          }}>
            {medicalEventsCount}
          </div>
        </div>

        {/* Incidents Resolved */}
        <div className="card-kpi animate-fade-in" style={{ 
          background: 'rgba(18, 20, 23, 0.65)', 
          border: '2px solid rgba(244, 196, 48, 0.3)', 
          padding: '16px', 
          borderRadius: '8px',
          minHeight: '80px',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'center'
        }}>
          <div style={{ 
            fontSize: '11px', 
            fontWeight: 600,
            textTransform: 'uppercase',
            letterSpacing: '0.5px',
            marginBottom: '8px', 
            color: 'rgba(255, 255, 255, 0.8)' 
          }}>
            Incidents Resolved
          </div>
          <div style={{ 
            color: incidentsResolved > 0 ? '#F4C430' : 'rgba(255, 255, 255, 0.4)', 
            fontSize: '28px', 
            fontWeight: 700,
            fontFamily: 'monospace'
          }}>
            {incidentsResolved}
          </div>
          {incidentsResolved === 0 && (medicalEventsCount > 0 || incidents.length > 0) && (
            <div style={{ fontSize: '10px', color: 'rgba(255, 255, 255, 0.3)', marginTop: '4px' }}>
              {medicalEventsCount + incidents.length} active
            </div>
          )}
        </div>
      </div>

      {/* Active Incidents */}
      {incidents.length > 0 && (
        <div style={{ marginTop: 'var(--spacing-lg)' }}>
          <h3 className="text-h3" style={{ marginBottom: 'var(--spacing-sm)' }}>
            Active Incidents
          </h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--spacing-sm)' }}>
            {incidents.map((incident: Incident) => (
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

