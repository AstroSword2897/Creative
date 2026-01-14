import { useState, useEffect, useRef } from 'react'
import View3D from './components/View3D'
import ControlPanel from './components/ControlPanel'
import MetricsPanel from './components/MetricsPanel'
import { SimulationState } from './types'

import { Scenario } from './types'

// ✅ ENHANCED: Debug mode flag (can be controlled via environment variable)
const DEBUG_MODE = process.env.NODE_ENV === 'development' || 
                   (typeof window !== 'undefined' && window.location.search.includes('debug=true'))

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
  // ✅ ENHANCED: Store current run ID for reconnection
  const currentRunIdRef = useRef<string | null>(null)

  useEffect(() => {
    // Load scenarios
    if (DEBUG_MODE) {
      console.log('Loading scenarios...')
    }
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
      // ✅ FIXED: Always start simulation - removed blocking condition
      console.log('🚀 Starting simulation for scenario:', scenarioId, isRunning ? '(switching from running sim)' : '(new simulation)')
      
      // ✅ ENHANCED: Abort any in-flight requests and close existing connections
      abortRef.current?.abort()
      abortRef.current = new AbortController()
      
      // Close existing WebSocket immediately to allow switching scenarios
      if (wsRef.current) {
        if (DEBUG_MODE) {
          console.log('Closing existing WebSocket to switch scenario')
        }
        wsRef.current.close()
        wsRef.current = null
      }
      
      // ✅ CRITICAL: Clear previous simulation state when starting new one
      setSimulationState(null)
      
      // Set loading state immediately to prevent double-clicks
      setIsLoading(true)
      setError(null)
      setConnectionLost(false)
      setWsError(null)
      setWsConnecting(false)
      setSelectedScenario(scenarioId) // Set immediately for visual feedback
      
      // ✅ ENHANCED: Reset running state when switching scenarios
      setIsRunning(false) // Will be set to true after API call succeeds

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
      
      if (!data.run_id) {
        throw new Error('No run_id returned from API')
      }
      
      if (DEBUG_MODE) {
        console.log('✅ Simulation started:', data.run_id)
      }
      
      setIsRunning(true)
      setIsLoading(false)
      setWsConnecting(true)
      
      // ✅ ENHANCED: Store run_id for reconnection
      currentRunIdRef.current = data.run_id
      
      // Connect WebSocket immediately (no delay)
      if (DEBUG_MODE) {
        console.log('🔌 Connecting WebSocket for run_id:', data.run_id)
      }
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

    const MAX_ATTEMPTS = 5  // ✅ ENHANCED: Increased retries for better reliability
    // ✅ ENHANCED: Exponential backoff for retries (200ms, 400ms, 800ms, 1600ms, 3000ms)
    // Note: RETRY_DELAY calculated inline below for each retry

    // Verify backend run exists before connecting WebSocket
    const verifyAndConnect = async () => {
      try {
        // First verify the run exists (with shorter timeout)
        if (DEBUG_MODE) {
          console.log(`🔍 Verifying run exists (attempt ${attempt + 1}/${MAX_ATTEMPTS}):`, runId)
        }
        const controller = new AbortController()
        const timeoutId = setTimeout(() => controller.abort(), 1000) // 1 second timeout
        const verifyRes = await fetch(`/api/runs/${runId}/state`, { signal: controller.signal })
        clearTimeout(timeoutId)
        
        if (!verifyRes.ok) {
          if (attempt < MAX_ATTEMPTS - 1) {
            const backoffDelay = Math.min(200 * Math.pow(2, attempt), 3000)
            if (DEBUG_MODE) {
              console.log(`⏳ Run not ready, retrying in ${backoffDelay}ms (attempt ${attempt + 1}/${MAX_ATTEMPTS})...`)
            }
            setTimeout(() => connectWebSocket(runId, attempt + 1), backoffDelay)
            return
          }
          
          const errorText = await verifyRes.text()
          console.error('❌ Backend run not found after retries:', verifyRes.status, errorText)
          setError(`Run ${runId} not found on backend (${verifyRes.status})`)
          setIsRunning(false)
          setIsLoading(false)
          return
        }
        
        if (DEBUG_MODE) {
          console.log('✅ Backend run exists, connecting WebSocket...')
        }
        
        // Now connect WebSocket immediately
        const wsUrl = `${getWsBaseUrl()}/ws/runs/${runId}`
        if (DEBUG_MODE) {
          console.log('Connecting to WebSocket:', wsUrl)
        }
        
        const ws = new WebSocket(wsUrl)
        wsRef.current = ws
        
        ws.onopen = () => {
          if (DEBUG_MODE) {
            console.log('✅ WebSocket connected successfully')
          }
          setError(null) // Clear any previous errors
          setWsError(null)
          setWsConnecting(false)
          setConnectionLost(false)
        }
        
        // ✅ ENHANCED: Handle connection confirmation message
        ws.addEventListener('message', (event) => {
          try {
            const message = JSON.parse(event.data)
            if (message.type === 'connected') {
              if (DEBUG_MODE) {
                console.log('✅ WebSocket connection confirmed:', message.message)
              }
            }
          } catch (e) {
            // Not a JSON message or not a connection confirmation, continue normal processing
          }
        }, { once: true })
        
        ws.onmessage = (event) => {
          try {
            const message = JSON.parse(event.data)
            
            // ✅ ENHANCED: Handle ping messages (keepalive)
            if (message.type === 'ping') {
              if (DEBUG_MODE) {
                console.log('🏓 WebSocket ping received, connection alive')
              }
              // Optionally send pong back (not required, but good practice)
              try {
                if (ws.readyState === WebSocket.OPEN) {
                  ws.send(JSON.stringify({ type: 'pong', step: message.step }))
                }
              } catch (e) {
                // Ignore pong send errors
              }
              return
            }
            
            if (DEBUG_MODE) {
              console.log('WebSocket message received:', message.type)
            }
            
            if (message.error) {
              console.error('WebSocket error message:', message.error)
              setError(`WebSocket error: ${message.error}`)
              setIsRunning(false)
              setIsLoading(false)
              return
            }
            
            // Handle completed message separately (doesn't have agents structure)
            if (message.type === 'completed') {
              if (DEBUG_MODE) {
                console.log('✅ Simulation completed')
              }
              setIsRunning(false)
              setIsLoading(false)
              setWsConnecting(false)
              setConnectionLost(false)
              // Keep the final state visible
              if (message.data && message.data.metrics && DEBUG_MODE) {
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
              // ✅ ENHANCED: Validate message structure and sanitize data
              if (!message.data || !message.data.agents || typeof message.data.agents !== 'object') {
                console.warn('Invalid message shape, skipping:', message)
                return
              }
              
              // ✅ ENHANCED: Validate and sanitize agent coordinates
              const sanitizeAgent = (agent: any) => {
                if (!agent || !agent.location) return null
                const [lat, lon] = Array.isArray(agent.location) ? agent.location : [agent.location[0], agent.location[1]]
                // Validate coordinates are numbers and within reasonable bounds
                if (typeof lat !== 'number' || typeof lon !== 'number' || 
                    isNaN(lat) || isNaN(lon) || !isFinite(lat) || !isFinite(lon)) {
                  return null
                }
                // Clamp coordinates to reasonable bounds (Las Vegas area)
                const validLat = Math.max(36.0, Math.min(36.2, lat))
                const validLon = Math.max(-115.3, Math.min(-115.1, lon))
                return { ...agent, location: [validLat, validLon] }
              }
              
              // Sanitize all agent arrays
              const sanitizedData = {
                ...message.data,
                agents: {
                  athletes: (message.data.agents.athletes || []).map(sanitizeAgent).filter(Boolean),
                  volunteers: (message.data.agents.volunteers || []).map(sanitizeAgent).filter(Boolean),
                  security: (message.data.agents.security || []).map(sanitizeAgent).filter(Boolean),
                  lvmpd: (message.data.agents.lvmpd || []).map(sanitizeAgent).filter(Boolean),
                  amr: (message.data.agents.amr || []).map(sanitizeAgent).filter(Boolean),
                  buses: (message.data.agents.buses || []).map(sanitizeAgent).filter(Boolean),
                }
              }
              
              const agentCounts = {
                athletes: sanitizedData.agents.athletes.length,
                volunteers: sanitizedData.agents.volunteers.length,
                security: sanitizedData.agents.security.length,
                lvmpd: sanitizedData.agents.lvmpd.length,
                amr: sanitizedData.agents.amr.length,
                buses: sanitizedData.agents.buses.length,
              }
              
              const totalAgents = Object.values(agentCounts).reduce((sum, count) => sum + count, 0)
              
              // ✅ ENHANCED: Debug logging only in debug mode
              if (DEBUG_MODE) {
                console.log('✅ Setting simulation state:', {
                  type: message.type,
                  agentKeys: Object.keys(sanitizedData.agents || {}),
                  totalAgents,
                  agentCounts,
                  hasTime: !!sanitizedData.time,
                  time: sanitizedData.time,
                })
              }
              
              setSimulationState(sanitizedData)
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
          
          // ✅ ENHANCED: Retry with exponential backoff
          if (attempt < MAX_ATTEMPTS - 1) {
            const backoffDelay = Math.min(200 * Math.pow(2, attempt), 3000)
            if (DEBUG_MODE) {
              console.log(`⏳ WebSocket error, retrying in ${backoffDelay}ms (attempt ${attempt + 1}/${MAX_ATTEMPTS})...`)
            }
            setTimeout(() => connectWebSocket(runId, attempt + 1), backoffDelay)
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
          if (DEBUG_MODE) {
            console.log('WebSocket closed:', {
              code: event.code,
              reason: event.reason,
              wasClean: event.wasClean,
            })
          }
          wsRef.current = null
          
          // ✅ ENHANCED: Auto-reconnect on unexpected disconnect if simulation is still running
          // Only reconnect for unexpected disconnects (not clean closes or normal shutdowns)
          const shouldReconnect = (
            !event.wasClean && 
            event.code !== 1000 && // Not a normal closure
            event.code !== 1001 && // Not "going away"
            isRunning && 
            selectedScenario && 
            currentRunIdRef.current
          )
          
          if (shouldReconnect) {
            if (DEBUG_MODE) {
              console.log('🔄 Attempting to reconnect WebSocket...')
            }
            setConnectionLost(true)
            setWsConnecting(true)
            // ✅ ENHANCED: Use exponential backoff for reconnection (1s, 2s, 4s, max 8s)
            const reconnectDelay = Math.min(1000 * Math.pow(2, Math.min(attempt, 3)), 8000)
            setTimeout(() => {
              // Double-check state hasn't changed
              if (isRunning && selectedScenario && currentRunIdRef.current && !wsRef.current) {
                connectWebSocket(currentRunIdRef.current, attempt + 1)
              } else {
                setWsConnecting(false)
                setConnectionLost(false)
              }
            }, reconnectDelay)
            return
          }
          
          // Clean close or intentional shutdown
          setIsRunning(false)
          setIsLoading(false)
          setWsConnecting(false)
          
          // Only show error for unexpected disconnects
          if (!event.wasClean && event.code !== 1000 && event.code !== 1001) {
            setConnectionLost(true)
            if (event.code === 1006) {
              setError('WebSocket connection closed unexpectedly. Attempting to reconnect...')
            } else {
              setError(`WebSocket closed with code ${event.code}. Attempting to reconnect...`)
            }
          } else {
            // Clean close - simulation completed or intentional shutdown
            if (DEBUG_MODE) {
              console.log('✅ WebSocket closed cleanly')
            }
            setConnectionLost(false)
            setError(null) // Clear any previous errors
          }
        }
        
      } catch (err: any) {
        // ✅ ENHANCED: Retry with exponential backoff (don't retry on non-network errors)
        if (attempt < MAX_ATTEMPTS - 1 && err.name !== 'AbortError') {
          const backoffDelay = Math.min(200 * Math.pow(2, attempt), 3000)
          if (DEBUG_MODE) {
            console.log(`⏳ Connection error, retrying in ${backoffDelay}ms (attempt ${attempt + 1}/${MAX_ATTEMPTS})...`)
          }
          setTimeout(() => connectWebSocket(runId, attempt + 1), backoffDelay)
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
