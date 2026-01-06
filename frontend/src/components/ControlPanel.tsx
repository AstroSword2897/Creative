interface ControlPanelProps {
  scenarios: any[]
  selectedScenario: string | null
  onStartSimulation: (scenarioId: string) => void
  isRunning: boolean
  isLoading?: boolean
  error?: string | null
}

export default function ControlPanel({
  scenarios,
  selectedScenario,
  onStartSimulation,
  isRunning,
  isLoading = false,
  error = null,
}: ControlPanelProps) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--spacing-lg)' }}>
      <h2 className="text-h2" style={{ marginBottom: 'var(--spacing-md)' }}>
        Scenarios
      </h2>
      
      <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--spacing-sm)' }}>
        {scenarios.map(scenario => (
          <button
            key={scenario.id}
            onClick={() => {
              console.log('🔘 Scenario button clicked:', scenario.id)
              onStartSimulation(scenario.id)
            }}
            disabled={isRunning}
            className={`panel-elevated text-left animate-fade-in`}
            style={{
              padding: 'var(--spacing-md)',
              borderRadius: 'var(--radius-md)',
              border: selectedScenario === scenario.id 
                ? '2px solid var(--color-neon-teal)' 
                : '1px solid rgba(255, 255, 255, 0.1)',
              background: selectedScenario === scenario.id
                ? 'rgba(0, 245, 212, 0.1)'
                : 'rgba(45, 47, 51, 0.6)',
              cursor: isRunning ? 'not-allowed' : 'pointer',
              opacity: isRunning ? 0.5 : 1,
              transition: 'all var(--transition-fast)',
              boxShadow: selectedScenario === scenario.id ? 'var(--shadow-glow-teal)' : 'none',
            }}
            onMouseEnter={(e) => {
              if (!isRunning) {
                e.currentTarget.style.transform = 'translateY(-2px)';
                e.currentTarget.style.boxShadow = 'var(--shadow-md)';
              }
            }}
            onMouseLeave={(e) => {
              if (!isRunning && selectedScenario !== scenario.id) {
                e.currentTarget.style.transform = 'translateY(0)';
                e.currentTarget.style.boxShadow = 'none';
              }
            }}
          >
            <div className="text-h3" style={{ color: 'var(--color-soft-white)', marginBottom: 'var(--spacing-xs)' }}>
              {scenario.name}
            </div>
            <div className="text-small" style={{ opacity: 0.7 }}>
              {scenario.description}
            </div>
          </button>
        ))}
      </div>

      {error && (
        <div 
          className="panel-elevated animate-slide-in"
          style={{
            padding: 'var(--spacing-md)',
            borderRadius: 'var(--radius-md)',
            background: 'rgba(231, 76, 60, 0.15)',
            border: '1px solid var(--color-alert-red)',
            marginTop: 'var(--spacing-md)',
          }}
        >
          <div className="text-body" style={{ color: 'var(--color-alert-red)', fontWeight: 600 }}>
            Error: {error}
          </div>
        </div>
      )}

      {isLoading && (
        <div 
          className="panel-elevated animate-slide-in"
          style={{
            padding: 'var(--spacing-md)',
            borderRadius: 'var(--radius-md)',
            background: 'rgba(255, 212, 48, 0.15)',
            border: '1px solid var(--color-vegas-gold)',
            marginTop: 'var(--spacing-md)',
          }}
        >
          <div className="text-body" style={{ color: 'var(--color-vegas-gold)', fontWeight: 600 }}>
            ⏳ Starting simulation...
          </div>
        </div>
      )}

      {isRunning && !isLoading && (
        <div 
          className="panel-elevated animate-slide-in"
          style={{
            padding: 'var(--spacing-md)',
            borderRadius: 'var(--radius-md)',
            background: 'rgba(46, 204, 113, 0.15)',
            border: '1px solid var(--color-safe-green)',
            marginTop: 'var(--spacing-md)',
          }}
        >
          <div className="text-body" style={{ color: 'var(--color-safe-green)', fontWeight: 600 }}>
            ✅ Simulation Running
          </div>
          <div className="text-small" style={{ color: 'var(--color-safe-green)', marginTop: 'var(--spacing-xs)', opacity: 0.8 }}>
            Real-time updates active
          </div>
        </div>
      )}
    </div>
  )
}

