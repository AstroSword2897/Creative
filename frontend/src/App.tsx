import { useState, useEffect, useRef } from 'react'
import View3D from './components/View3D'
import ControlPanel from './components/ControlPanel'
import MetricsPanel from './components/MetricsPanel'
import { SimulationState } from './types'

type ScenarioSummary = {
  id: string
  name: string
  description?: string
}

// WebSocket base URL helper
const getWsBaseUrl = (): string => {
  if (typeof window === 'undefined') return 'ws://localhost:8000'
  
  // In development, use explicit port 8000
  // In production, use same host as frontend (behind proxy)
  if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
    return `ws://${window.location.hostname}:8000`
  }
  
  // Production: use same protocol/host as frontend
  return `${window.location.protocol === 'https:' ? 'wss' : 'ws'}://${window.location.host}`
}

function App() {
  const [scenarios, setScenarios] = useState<ScenarioSummary[]>([])
  const [selectedScenario, setSelectedScenario] = useState<string | null>(null)
  const [simulationState, setSimulationState] = useState<SimulationState | null>(null)
  const [isRunning, setIsRunning] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  
  // WebSocket lifecycle management
  const wsRef = useRef<WebSocket | null>(null)
  // AbortController for race condition prevention
  const abortRef = useRef<AbortController | null>(null)

  useEffect(() => {
    // Load scenarios
    fetch('/api/scenarios')
      .then(res => res.json())
      .then(data => setScenarios(data.scenarios || []))
      .catch(err => console.error('Failed to load scenarios:', err))
  }, [])

  // Cleanup WebSocket and abort controller on unmount
  useEffect(() => {
    return () => {
      abortRef.current?.abort()
      if (wsRef.current) {
        wsRef.current.close()
        wsRef.current = null
      }
    }
  }, [])

  const startSimulation = async (scenarioId: string) => {
    try {
      console.log('🚀 Starting simulation for scenario:', scenarioId)
      
      // Abort any in-flight requests
      abortRef.current?.abort()
      abortRef.current = new AbortController()
      
      setError(null)
      setIsLoading(true)
      setSelectedScenario(scenarioId) // Set immediately for visual feedback
      
      // Close existing WebSocket if any
      if (wsRef.current) {
        console.log('Closing existing WebSocket')
        wsRef.current.close()
        wsRef.current = null
      }

      // Clear previous state
      setSimulationState(null)
      setIsRunning(false)

      console.log('📡 Calling API to start simulation...')
      const response = await fetch(`/api/scenarios/${scenarioId}/run`, {
        method: 'POST',
        signal: abortRef.current.signal,
      })
      
      console.log('📡 API Response status:', response.status, response.statusText)
      
      if (!response.ok) {
        const errorText = await response.text()
        console.error('❌ API Error Response:', errorText)
        throw new Error(`API error: ${response.status} ${response.statusText} - ${errorText}`)
      }
      
      const data = await response.json()
      console.log('✅ Simulation started:', data)
      
      if (!data.run_id) {
        throw new Error('No run_id returned from API')
      }
      
      setIsRunning(true)
      setIsLoading(false)
      
      // Connect WebSocket
      console.log('🔌 Connecting WebSocket for run_id:', data.run_id)
      connectWebSocket(data.run_id)
    } catch (error: any) {
      // Don't set error if it was an abort
      if (error.name === 'AbortError') {
        console.log('Request aborted (new simulation started)')
        return
      }
      
      console.error('❌ Failed to start simulation:', error)
      setIsRunning(false)
      setIsLoading(false)
      setError(error.message || 'Failed to start simulation')
      // Don't reset selectedScenario on error - let user see what they clicked
    }
  }

  const connectWebSocket = (runId: string, attempt = 0): void => {
    // Close existing socket
    if (wsRef.current) {
      wsRef.current.close()
      wsRef.current = null
    }

    const MAX_ATTEMPTS = 5
    const RETRY_DELAY = 200

    // Verify backend run exists before connecting WebSocket
    const verifyAndConnect = async () => {
      try {
        // First verify the run exists
        console.log(`🔍 Verifying run exists (attempt ${attempt + 1}/${MAX_ATTEMPTS}):`, runId)
        const verifyRes = await fetch(`http://localhost:8000/api/runs/${runId}/state`)
        
        if (!verifyRes.ok) {
          if (attempt < MAX_ATTEMPTS - 1) {
            console.log(`⏳ Run not ready, retrying in ${RETRY_DELAY}ms...`)
            setTimeout(() => connectWebSocket(runId, attempt + 1), RETRY_DELAY)
            return
          }
          
          const errorText = await verifyRes.text()
          console.error('❌ Backend run not found after retries:', verifyRes.status, errorText)
          setError(`Run ${runId} not found on backend (${verifyRes.status})`)
          setIsRunning(false)
          setIsLoading(false)
          return
        }
        
        console.log('✅ Backend run exists, connecting WebSocket...')
        
        // Now connect WebSocket
        const wsUrl = `${getWsBaseUrl()}/ws/runs/${runId}`
        console.log('Connecting to WebSocket:', wsUrl)
        
        const ws = new WebSocket(wsUrl)
        wsRef.current = ws
        
        ws.onopen = () => {
          console.log('✅ WebSocket connected successfully')
          setError(null) // Clear any previous errors
        }
        
        ws.onmessage = (event) => {
          try {
            const message = JSON.parse(event.data)
            console.log('WebSocket message received:', message.type)
            
            if (message.error) {
              console.error('WebSocket error message:', message.error)
              setError(`WebSocket error: ${message.error}`)
              setIsRunning(false)
              setIsLoading(false)
              return
            }
            
            // Validate message shape
            if (!message.data || !message.data.agents || typeof message.data.agents !== 'object') {
              console.warn('Invalid message shape, skipping:', message)
              return
            }
            
            if (message.type === 'state' || message.type === 'update') {
              console.log('Setting simulation state:', {
                agents: Object.keys(message.data.agents || {}),
                agentCounts: message.data.agents ? {
                  athletes: message.data.agents.athletes?.length || 0,
                  volunteers: message.data.agents.volunteers?.length || 0,
                  security: message.data.agents.security?.length || 0,
                  lvmpd: message.data.agents.lvmpd?.length || 0,
                  amr: message.data.agents.amr?.length || 0,
                  buses: message.data.agents.buses?.length || 0,
                } : {},
              })
              setSimulationState(message.data)
            } else if (message.type === 'completed') {
              setIsRunning(false)
              setIsLoading(false)
              setSimulationState(message.data)
            }
          } catch (error) {
            console.error('Error parsing WebSocket message:', error, event.data)
            setError('Failed to parse WebSocket message')
          }
        }
        
        ws.onerror = (error) => {
          console.error('❌ WebSocket error:', error)
          console.error('WebSocket readyState:', ws.readyState)
          
          // Retry connection if not exceeded max attempts
          if (attempt < MAX_ATTEMPTS - 1) {
            console.log(`⏳ WebSocket error, retrying in ${RETRY_DELAY}ms...`)
            setTimeout(() => connectWebSocket(runId, attempt + 1), RETRY_DELAY)
            return
          }
          
          setError('WebSocket connection failed after retries')
          setIsRunning(false)
          setIsLoading(false)
        }
        
        ws.onclose = (event) => {
          console.log('WebSocket closed:', {
            code: event.code,
            reason: event.reason,
            wasClean: event.wasClean,
          })
          wsRef.current = null
          
          // Always update state - React setters are idempotent
          setIsRunning(false)
          setIsLoading(false)
          
          if (!event.wasClean && event.code !== 1000) {
            if (event.code === 1006) {
              setError('WebSocket connection closed unexpectedly. Check backend logs.')
            } else {
              setError(`WebSocket closed with code ${event.code}`)
            }
          }
        }
        
      } catch (err: any) {
        // Don't retry on non-network errors
        if (attempt < MAX_ATTEMPTS - 1 && err.name !== 'AbortError') {
          console.log(`⏳ Connection error, retrying in ${RETRY_DELAY}ms...`)
          setTimeout(() => connectWebSocket(runId, attempt + 1), RETRY_DELAY)
          return
        }
        
        console.error('❌ Error verifying/connecting:', err)
        setError(`Connection error: ${err.message}`)
        setIsRunning(false)
        setIsLoading(false)
      }
    }
    
    // Start immediately (no magic delay)
    verifyAndConnect()
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
          isLoading={isLoading}
          error={error}
        />
      </div>

      {/* Center 3D Visualization */}
      <div className="flex-1 relative">
        <View3D state={simulationState} />
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
