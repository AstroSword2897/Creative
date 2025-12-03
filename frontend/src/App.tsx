import { useState, useEffect } from 'react'
import MapView from './components/MapView'
import ControlPanel from './components/ControlPanel'
import MetricsPanel from './components/MetricsPanel'
import { SimulationState } from './types'

function App() {
  const [scenarios, setScenarios] = useState<any[]>([])
  const [selectedScenario, setSelectedScenario] = useState<string | null>(null)
  const [runId, setRunId] = useState<string | null>(null)
  const [simulationState, setSimulationState] = useState<SimulationState | null>(null)
  const [isRunning, setIsRunning] = useState(false)

  useEffect(() => {
    // Load scenarios
    fetch('/api/scenarios')
      .then(res => res.json())
      .then(data => setScenarios(data.scenarios || []))
      .catch(err => console.error('Failed to load scenarios:', err))
  }, [])

  const startSimulation = async (scenarioId: string) => {
    try {
      const response = await fetch(`/api/scenarios/${scenarioId}/run`, {
        method: 'POST',
      })
      const data = await response.json()
      setRunId(data.run_id)
      setSelectedScenario(scenarioId)
      setIsRunning(true)
      
      // Connect WebSocket
      connectWebSocket(data.run_id)
    } catch (error) {
      console.error('Failed to start simulation:', error)
    }
  }

  const connectWebSocket = (runId: string) => {
    const ws = new WebSocket(`ws://localhost:8000/ws/runs/${runId}`)
    
    ws.onmessage = (event) => {
      const message = JSON.parse(event.data)
      if (message.type === 'state' || message.type === 'update') {
        setSimulationState(message.data)
      } else if (message.type === 'completed') {
        setIsRunning(false)
      }
    }
    
    ws.onerror = (error) => {
      console.error('WebSocket error:', error)
    }
    
    ws.onclose = () => {
      console.log('WebSocket closed')
    }
  }

  return (
    <div className="flex h-screen w-screen" style={{ background: 'var(--gradient-night)' }}>
      {/* Left Control Panel */}
      <div 
        className="panel-glass overflow-y-auto"
        style={{ 
          width: 'var(--sidebar-width)', 
          padding: 'var(--spacing-lg)',
          borderRight: '1px solid rgba(255, 255, 255, 0.1)'
        }}
      >
        <ControlPanel
          scenarios={scenarios}
          selectedScenario={selectedScenario}
          onStartSimulation={startSimulation}
          isRunning={isRunning}
        />
      </div>

      {/* Center Map */}
      <div className="flex-1 relative">
        <MapView state={simulationState} />
      </div>

      {/* Right Metrics Panel */}
      <div 
        className="panel-glass overflow-y-auto"
        style={{ 
          width: 'var(--kpi-panel-width)', 
          padding: 'var(--spacing-lg)',
          borderLeft: '1px solid rgba(255, 255, 255, 0.1)'
        }}
      >
        <MetricsPanel state={simulationState} />
      </div>
    </div>
  )
}

export default App

