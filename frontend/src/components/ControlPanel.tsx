import React from 'react'
import { Scenario } from '../types'

interface ControlPanelProps {
  scenarios: Scenario[]
  selectedScenario: string | null
  onStartSimulation: (scenarioId: string) => void
  isRunning: boolean
  isLoading?: boolean
  error?: string | null
  wsError?: string | null
  wsConnecting?: boolean
}

// StatusPanel component for reusable status displays
interface StatusPanelProps {
  type: 'error' | 'warning' | 'loading' | 'running'
  message: string
  details?: string
}

function StatusPanel({ type, message, details }: StatusPanelProps) {
  // ✅ ENHANCED: Color-coded status styles
  const styles = {
    error: {
      background: 'rgba(231, 76, 60, 0.15)',
      border: '1px solid var(--color-alert-red)',
      color: 'var(--color-alert-red)',
    },
    warning: {
      background: 'rgba(255, 193, 7, 0.15)',
      border: '1px solid #FFC107',
      color: '#FFC107',
    },
    loading: {
      background: 'rgba(255, 212, 48, 0.15)',
      border: '1px solid var(--color-vegas-gold)',
      color: 'var(--color-vegas-gold)',
    },
    running: {
      background: 'rgba(46, 204, 113, 0.15)',
      border: '1px solid var(--color-safe-green)',
      color: 'var(--color-safe-green)',
    },
  }

  const style = styles[type]

  return (
    <div 
      className="panel-elevated animate-slide-in"
      style={{
        padding: 'var(--spacing-md)',
        borderRadius: 'var(--radius-md)',
        marginTop: 'var(--spacing-md)',
        ...style,
      }}
      role="status"
      aria-live="polite"
    >
      <div className="text-body" style={{ fontWeight: 600, display: 'flex', alignItems: 'center', gap: '8px' }}>
        {type === 'running' && <span className="animate-pulse">●</span>}
        {type === 'loading' && <span>⏳</span>}
        <span>{message}</span>
      </div>
      {details && (
        <div className="text-small" style={{ marginTop: 'var(--spacing-xs)', opacity: 0.8 }}>
          {details}
        </div>
      )}
    </div>
  )
}

// ScenarioButton component for cleaner button rendering
interface ScenarioButtonProps {
  scenario: Scenario
  isSelected: boolean
  isDisabled: boolean
  isLoading: boolean
  onSelect: () => void
}

function ScenarioButton({ scenario, isSelected, isDisabled, isLoading, onSelect }: ScenarioButtonProps) {
  const [interactionState, setInteractionState] = React.useState<'idle' | 'hover' | 'focus'>('idle')

  const baseStyles: React.CSSProperties = {
    padding: 'var(--spacing-md)',
    borderRadius: 'var(--radius-md)',
    border: isSelected 
      ? '2px solid var(--color-neon-teal)' 
      : '1px solid rgba(255, 255, 255, 0.1)',
    background: isSelected
      ? 'rgba(0, 245, 212, 0.1)'
      : 'rgba(45, 47, 51, 0.6)',
    cursor: isDisabled ? 'not-allowed' : 'pointer',
    opacity: isDisabled ? 0.55 : 1,
    transition: 'all 0.2s ease',
    boxShadow: isSelected 
      ? 'var(--shadow-glow-teal)' 
      : (interactionState !== 'idle' && !isDisabled ? 'var(--shadow-md)' : 'none'),
    transform: (interactionState === 'hover' && !isDisabled && !isSelected) ? 'translateY(-2px)' : 'translateY(0)',
    position: 'relative',
    zIndex: 1,
    pointerEvents: isDisabled ? 'none' : 'auto',
    outline: interactionState === 'focus' ? '2px solid var(--color-neon-teal)' : 'none',
    outlineOffset: interactionState === 'focus' ? '2px' : '0',
  }

  return (
    <button
      type="button"
      data-scenario-id={scenario.id}
      disabled={isDisabled || isLoading}
      className="panel-elevated text-left animate-fade-in"
      style={baseStyles}
      onClick={onSelect}
      onMouseEnter={() => !isDisabled && !isLoading && setInteractionState('hover')}
      onMouseLeave={() => setInteractionState('idle')}
      onFocus={() => !isDisabled && !isLoading && setInteractionState('focus')}
      onBlur={() => setInteractionState('idle')}
      aria-pressed={isSelected}
      aria-label={`Start simulation: ${scenario.name}`}
    >
      <div 
        className="text-h3" 
        style={{ 
          color: 'var(--color-soft-white)', 
          marginBottom: 'var(--spacing-xs)',
          pointerEvents: 'none',
          userSelect: 'none',
        }}
      >
        {scenario.name}
      </div>
      <div 
        className="text-small" 
        style={{ 
          opacity: 0.7,
          pointerEvents: 'none',
          userSelect: 'none',
        }}
      >
        {scenario.description}
      </div>
      {isLoading && isSelected && (
        <div className="text-small" style={{ marginTop: 'var(--spacing-xs)', opacity: 0.9, color: 'var(--color-vegas-gold)' }}>
          ⏳ Starting...
        </div>
      )}
    </button>
  )
}

// ✅ ENHANCED: Compute single status with color-coded messages
function computeStatus(
  error: string | null,
  wsError: string | null,
  isLoading: boolean,
  wsConnecting: boolean,
  isRunning: boolean,
): StatusPanelProps | null {
  // Priority: errors > loading > running
  if (error) {
    // ✅ ENHANCED: Color-code error messages
    const isWarning = error.toLowerCase().includes('reconnect') || error.toLowerCase().includes('attempting')
    return { 
      type: isWarning ? 'warning' : 'error', 
      message: isWarning ? `⚠️ ${error}` : `❌ Error: ${error}` 
    }
  }
  
  if (wsError) {
    return {
      type: 'error',
      message: '❌ WebSocket Connection Failed',
      details: wsError || 'Unable to connect to simulation stream. Check backend or network.'
    }
  }
  
  if (isLoading) {
    return {
      type: 'loading',
      message: '⏳ Starting simulation...',
      details: wsConnecting ? 'Connecting to simulation stream...' : 'Initializing simulation...'
    }
  }
  
  if (wsConnecting) {
    return {
      type: 'loading',
      message: '⏳ Connecting to simulation...',
      details: 'Establishing WebSocket connection...'
    }
  }
  
  if (isRunning) {
    return {
      type: 'running',
      message: '✅ Simulation Running',
      details: 'Watch agents move in the 3D view as the model processes events'
    }
  }
  
  return null
}

export default function ControlPanel({
  scenarios,
  selectedScenario,
  onStartSimulation,
  isRunning,
  isLoading = false,
  error = null,
  wsError = null,
  wsConnecting = false,
}: ControlPanelProps) {
  const handleScenarioClick = (scenarioId: string) => {
    // ✅ ENHANCED: Allow clicking even if simulation is running (switches scenarios)
    // Only prevent if already loading the same scenario
    if (isLoading && selectedScenario === scenarioId) {
      return
    }
    
    if (process.env.NODE_ENV === 'development') {
      console.log('🔘 Scenario button clicked:', scenarioId, isRunning ? '(switching scenario)' : '(starting new)')
    }
    
    // Immediately start simulation - no confirmation needed
    onStartSimulation(scenarioId)
  }

  const status = computeStatus(error, wsError, isLoading, wsConnecting, isRunning)

  return (
    <div 
      style={{ 
        display: 'flex', 
        flexDirection: 'column', 
        gap: 'var(--spacing-lg)',
        position: 'relative',
        zIndex: 0,
      }}
    >
      <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--spacing-xs)' }}>
        <div className="text-h2">Scenarios</div>
        <div className="text-small" style={{ opacity: 0.7, lineHeight: '1.5' }}>
          Click any scenario below to launch a live 3D simulation. Watch agents move in real-time as the model processes events.
        </div>
      </div>
      
      {scenarios.length === 0 ? (
        <div 
          className="panel-elevated"
          style={{
            padding: 'var(--spacing-md)',
            borderRadius: 'var(--radius-md)',
            background: 'rgba(255, 212, 48, 0.15)',
            border: '1px solid var(--color-vegas-gold)',
          }}
        >
          <div className="text-body" style={{ color: 'var(--color-vegas-gold)' }}>
            ⏳ Loading scenarios...
          </div>
        </div>
      ) : (
        <div style={{ 
          display: 'flex', 
          flexDirection: 'column', 
          gap: 'var(--spacing-sm)',
        }}>
          {scenarios.map(scenario => (
            <ScenarioButton
              key={scenario.id}
              scenario={scenario}
              isSelected={selectedScenario === scenario.id}
              isDisabled={isLoading && selectedScenario === scenario.id} // ✅ Only disable if loading THIS scenario
              isLoading={isLoading && selectedScenario === scenario.id}
              onSelect={() => handleScenarioClick(scenario.id)}
            />
          ))}
        </div>
      )}

      {status && <StatusPanel {...status} />}
    </div>
  )
}
