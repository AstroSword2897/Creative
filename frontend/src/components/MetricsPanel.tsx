import { SimulationState } from '../types'

interface MetricsPanelProps {
  state: SimulationState | null
}

export default function MetricsPanel({ state }: MetricsPanelProps) {
  if (!state) {
    return (
      <div className="text-small" style={{ 
        textAlign: 'center', 
        marginTop: 'var(--spacing-2xl)',
        opacity: 0.5 
      }}>
        No simulation data. Start a scenario to see metrics.
      </div>
    )
  }

  const { metrics, time, incidents } = state

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
          {metrics.safety_score.toFixed(1)}
        </div>
        <div className="text-small" style={{ opacity: 0.75 }}>
          out of 100
        </div>
      </div>

      {/* Other Metrics */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--spacing-md)' }}>
        <div className="card-kpi animate-fade-in">
          <div className="text-small" style={{ opacity: 0.7, marginBottom: 'var(--spacing-xs)' }}>
            Average Response Time
          </div>
          <div className="text-h3" style={{ color: 'var(--color-neon-teal)' }}>
            {(metrics.avg_response_time / 60).toFixed(1)} min
          </div>
        </div>

        <div className="card-kpi animate-fade-in">
          <div className="text-small" style={{ opacity: 0.7, marginBottom: 'var(--spacing-xs)' }}>
            Containment Rate
          </div>
          <div className="text-h3" style={{ color: 'var(--color-safe-green)' }}>
            {(metrics.containment_rate * 100).toFixed(1)}%
          </div>
        </div>

        <div className="card-kpi animate-fade-in">
          <div className="text-small" style={{ opacity: 0.7, marginBottom: 'var(--spacing-xs)' }}>
            Medical Events
          </div>
          <div className="text-h3" style={{ color: 'var(--color-warm-coral)' }}>
            {metrics.medical_events_count}
          </div>
        </div>

        <div className="card-kpi animate-fade-in">
          <div className="text-small" style={{ opacity: 0.7, marginBottom: 'var(--spacing-xs)' }}>
            Incidents Resolved
          </div>
          <div className="text-h3" style={{ color: 'var(--color-vegas-gold)' }}>
            {metrics.incidents_resolved}
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
          {new Date(time).toLocaleString()}
        </div>
      </div>
    </div>
  )
}

