import { useState, useEffect, useRef } from 'react'
import View3D from './components/View3D'
import ControlPanel from './components/ControlPanel'
import MetricsPanel from './components/MetricsPanel'
import { SimulationState } from './types'

import { Scenario } from './types'

// WebSocket base URL helper
const getWsBaseUrl = (): string => {
  if (typeof window === 'undefined') return 'ws://localhost:3333'
  
  // In development, use explicit port 3333
  // In production, use same host as frontend (behind proxy)
  if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
    return `ws://${window.location.hostname}:3333`
  }
  
  // Production: use same protocol/host as frontend
  return `${window.location.protocol === 'https:' ? 'wss' : 'ws'}://${window.location.host}`
}

function App() {
  const [scenarios, setScenarios] = useState<Scenario[]>([])
  const [selectedScenario, setSelectedScenario] = useState<string | null>(null)
  const [simulationState, setSimulationState] = useState<SimulationState | null>(null)
  const [isRunning, setIsRunning] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [connectionLost, setConnectionLost] = useState(false)
  const [wsError, setWsError] = useState<string | null>(null)
  const [wsConnecting, setWsConnecting] = useState(false)
  
  // WebSocket lifecycle management
  const wsRef = useRef<WebSocket | null>(null)
  // AbortController for race condition prevention
  const abortRef = useRef<AbortController | null>(null)

  useEffect(() => {
    // Load scenarios
    console.log('Loading scenarios...')
    fetch('/api/scenarios')
      .then(res => {
        console.log('Scenarios API response status:', res.status)
        if (!res.ok) {
          throw new Error(`Failed to fetch scenarios: ${res.status} ${res.statusText}`)
        }
        return res.json()
      })
      .then(data => {
        console.log('Scenarios loaded:', data.scenarios?.length || 0, 'scenarios')
        setScenarios(data.scenarios || [])
      })
      .catch(err => {
        console.error('Failed to load scenarios:', err)
        setError(`Failed to load scenarios: ${err.message}`)
      })
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
      
      // Set loading state immediately to prevent double-clicks
      setIsLoading(true)
      setError(null)
      setConnectionLost(false)
      setWsError(null)
      setWsConnecting(false)
      setSelectedScenario(scenarioId) // Set immediately for visual feedback
      
      // Close existing WebSocket if any
      if (wsRef.current) {
        console.log('Closing existing WebSocket')
        wsRef.current.close()
        wsRef.current = null
      }

      // Set running to true immediately to prevent multiple clicks
      setIsRunning(true)

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
      setWsConnecting(true)
      
      // Connect WebSocket immediately (no delay)
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
      setConnectionLost(false)
      // Don't reset selectedScenario on error - let user see what they clicked
      // Don't clear simulationState - keep last visualization visible
    }
  }

  const connectWebSocket = (runId: string, attempt = 0): void => {
    // Close existing socket
    if (wsRef.current) {
      wsRef.current.close()
      wsRef.current = null
    }

    const MAX_ATTEMPTS = 3  // Reduced from 5 for faster boot
    const RETRY_DELAY = 100  // Reduced from 200ms for faster boot

    // Verify backend run exists before connecting WebSocket
    const verifyAndConnect = async () => {
      try {
        // First verify the run exists (with shorter timeout)
        console.log(`🔍 Verifying run exists (attempt ${attempt + 1}/${MAX_ATTEMPTS}):`, runId)
        const controller = new AbortController()
        const timeoutId = setTimeout(() => controller.abort(), 1000) // 1 second timeout
        const verifyRes = await fetch(`/api/runs/${runId}/state`, { signal: controller.signal })
        clearTimeout(timeoutId)
        
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
        
        // Now connect WebSocket immediately
        const wsUrl = `${getWsBaseUrl()}/ws/runs/${runId}`
        console.log('Connecting to WebSocket:', wsUrl)
        
        const ws = new WebSocket(wsUrl)
        wsRef.current = ws
        
        ws.onopen = () => {
          console.log('✅ WebSocket connected successfully')
          setError(null) // Clear any previous errors
          setWsError(null)
          setWsConnecting(false)
          setConnectionLost(false)
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
            
            // Handle completed message separately (doesn't have agents structure)
            if (message.type === 'completed') {
              console.log('✅ Simulation completed')
              setIsRunning(false)
              setIsLoading(false)
              setWsConnecting(false)
              // Keep the final state visible
              if (message.data && message.data.metrics) {
                // Update metrics if provided
                console.log('Final metrics:', message.data.metrics)
              }
              return
            }
            
            // Validate message shape for state/update messages
            if (!message.data || !message.data.agents || typeof message.data.agents !== 'object') {
              console.warn('Invalid message shape, skipping:', message)
              return
            }
            
            if (message.type === 'state' || message.type === 'update') {
              const agentCounts = message.data.agents ? {
                athletes: message.data.agents.athletes?.length || 0,
                volunteers: message.data.agents.volunteers?.length || 0,
                security: message.data.agents.security?.length || 0,
                lvmpd: message.data.agents.lvmpd?.length || 0,
                amr: message.data.agents.amr?.length || 0,
                buses: message.data.agents.buses?.length || 0,
              } : {}
              
              console.log('✅ Setting simulation state:', {
                type: message.type,
                agents: Object.keys(message.data.agents || {}),
                agentCounts,
                totalAgents: Object.values(agentCounts).reduce((a: number, b: number) => a + b, 0),
                time: message.data.time,
              })
              setSimulationState(message.data)
            } else if (message.type === 'completed') {
              console.log('✅ Simulation completed')
              setIsRunning(false)
              setIsLoading(false)
              // Keep the final state visible
              setSimulationState(message.data)
            } else if (message.type === 'error') {
              console.error('WebSocket error message:', message.error)
              setError(`WebSocket error: ${message.error}`)
              // Don't clear state - keep visualization visible
              setIsRunning(false)
              setIsLoading(false)
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
          
          const errorMsg = 'WebSocket connection failed after retries. Check backend logs.'
          setError(errorMsg)
          setWsError(errorMsg)
          setIsRunning(false)
          setIsLoading(false)
          setWsConnecting(false)
          setConnectionLost(true)
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
          
          // DON'T clear simulationState - keep the last state visible
          // Only show error if it wasn't a clean close
          if (!event.wasClean && event.code !== 1000) {
            setConnectionLost(true)
            if (event.code === 1006) {
              setError('WebSocket connection closed unexpectedly. Visualization shows last known state.')
            } else {
              setError(`WebSocket closed with code ${event.code}. Visualization shows last known state.`)
            }
          } else if (event.wasClean) {
            // Clean close - simulation completed
            console.log('✅ WebSocket closed cleanly - simulation completed')
            setConnectionLost(false)
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
        setConnectionLost(true)
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
          wsError={wsError}
          wsConnecting={wsConnecting}
        />
      </div>

      {/* Center 3D Visualization */}
      <div className="flex-1 relative" style={{ minHeight: 0, minWidth: 0, height: '100vh' }}>
        <View3D state={simulationState} />
        {connectionLost && simulationState && (
          <div className="absolute top-20 left-4 z-20 text-white text-xs bg-orange-500/80 px-3 py-2 rounded backdrop-blur-sm border border-orange-400">
            ⚠️ Connection lost - showing last known state
          </div>
        )}
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
