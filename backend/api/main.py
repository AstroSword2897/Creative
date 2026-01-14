"""
FastAPI main application.
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import Dict, List, Set, Optional
import json
import asyncio
import uuid
from pathlib import Path
from datetime import datetime, timedelta

from simulation.model import SpecialOlympicsModel
from simulation.async_alert_manager import AsyncGlobalAlertManager

app = FastAPI(
    title="Special Olympics Las Vegas Simulation API",
    version="0.1.0",
    tags=["simulation", "scenarios", "runs"]
)

# CORS middleware - configure for production
ALLOWED_ORIGINS = ["*"]  # In production: ["https://yourdomain.com", "https://app.yourdomain.com"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Active simulation runs
active_runs: Dict[str, Dict] = {}

# Pre-initialized simulations (ready to go on click)
preinitialized_runs: Dict[str, Dict] = {}

# WebSocket connections per run (for multiple viewers)
ws_connections: Dict[str, Set[WebSocket]] = {}

# Cleanup task
cleanup_task: asyncio.Task = None


async def cleanup_completed_runs():
    """Periodically clean up completed simulations."""
    while True:
        await asyncio.sleep(300)  # Check every 5 minutes
        try:
            completed_runs = [
                run_id for run_id, run in active_runs.items()
                if run.get("status") == "completed"
            ]
            for run_id in completed_runs:
                # Keep completed runs for 10 minutes before cleanup
                run = active_runs[run_id]
                completed_time = run.get("completed_at")
                if completed_time:
                    if datetime.now() - completed_time > timedelta(minutes=10):
                        del active_runs[run_id]
                        if run_id in ws_connections:
                            del ws_connections[run_id]
                        print(f"🧹 Cleaned up completed run: {run_id}")
                else:
                    # Mark completion time if not set
                    run["completed_at"] = datetime.now()
        except Exception as e:
            print(f"Error in cleanup task: {e}")


@app.on_event("startup")
async def startup_event():
    """Start background tasks on startup."""
    global cleanup_task
    cleanup_task = asyncio.create_task(cleanup_completed_runs())
    print("✅ Background cleanup task started")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    global cleanup_task
    if cleanup_task:
        cleanup_task.cancel()
    print("🛑 Shutting down background tasks")


@app.get("/", tags=["info"])
async def root():
    """Root endpoint."""
    return {
        "message": "Special Olympics Las Vegas Simulation API",
        "version": "0.1.0",
        "active_runs": len(active_runs),
        "preinitialized": len(preinitialized_runs),
        "status": "running",
        "frontend_url": "http://localhost:5173",
        "websocket_endpoint": "/ws/runs/{run_id}"
    }

@app.get("/api/health", tags=["info"])
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "backend": "running",
        "active_runs": len(active_runs),
        "preinitialized_runs": len(preinitialized_runs),
        "websocket_connections": sum(len(conns) for conns in ws_connections.values())
    }


@app.get("/api/scenarios", tags=["scenarios"])
async def list_scenarios():
    """List available scenarios and pre-initialize them for instant launch."""
    scenarios_dir = Path(__file__).parent.parent / "scenarios"
    scenarios = []
    
    # Pre-initialize ALL scenarios for instant boot (increased from 5)
    MAX_PREINIT = 10
    
    # Load scenarios first
    scenario_configs = {}
    for scenario_file in scenarios_dir.glob("*.json"):
        with open(scenario_file, 'r') as f:
            scenario = json.load(f)
            scenario_id = scenario.get("id")
            scenarios.append({
                "id": scenario_id,
                "name": scenario.get("name"),
                "description": scenario.get("description"),
            })
            scenario_configs[scenario_id] = scenario
    
    # Pre-initialize scenarios in background (non-blocking)
    async def preinit_scenarios():
        for scenario_id, scenario in scenario_configs.items():
            if (scenario_id and 
                scenario_id not in preinitialized_runs and 
                len(preinitialized_runs) < MAX_PREINIT):
                try:
                    model = SpecialOlympicsModel(scenario)
                    run_id = str(uuid.uuid4())
                    preinitialized_runs[scenario_id] = {
                        "model": model,
                        "run_id": run_id,
                        "scenario_id": scenario_id,
                        "status": "ready",
                    }
                    print(f"✅ Pre-initialized simulation for scenario: {scenario_id}")
                except Exception as e:
                    print(f"⚠️ Failed to pre-initialize {scenario_id}: {e}")
                    import traceback
                    traceback.print_exc()
    
    # Start pre-initialization in background (don't await - return immediately)
    asyncio.create_task(preinit_scenarios())
    
    return {"scenarios": scenarios}


@app.get("/api/scenarios/{scenario_id}", tags=["scenarios"])
async def get_scenario(scenario_id: str):
    """Get scenario configuration."""
    scenarios_dir = Path(__file__).parent.parent / "scenarios"
    scenario_file = scenarios_dir / f"{scenario_id}.json"
    
    if not scenario_file.exists():
        return JSONResponse(
            status_code=404,
            content={"error": f"Scenario {scenario_id} not found"}
        )
    
    with open(scenario_file, 'r') as f:
        scenario = json.load(f)
    
    return scenario


@app.post("/api/scenarios/{scenario_id}/run", tags=["runs"])
async def start_run(scenario_id: str):
    """Start a simulation run - uses pre-initialized if available."""
    # Check if we have a pre-initialized simulation ready
    if scenario_id in preinitialized_runs:
        preinit = preinitialized_runs[scenario_id]
        run_id = preinit["run_id"]
        
        # Initialize alert manager for pre-initialized run
        alert_manager = AsyncGlobalAlertManager(preinit["model"])
        
        # Move from pre-initialized to active
        active_runs[run_id] = {
            "model": preinit["model"],
            "scenario_id": scenario_id,
            "status": "running",
            "created_at": datetime.now(),
            "alert_manager": alert_manager,
        }
        
        # Initialize WebSocket connections set
        ws_connections[run_id] = set()
        
        # Remove from pre-initialized (will be recreated on next scenarios list)
        del preinitialized_runs[scenario_id]
        
        print(f"✅ Using pre-initialized simulation for {scenario_id}, run_id: {run_id}")
        print(f"📋 Active runs: {list(active_runs.keys())}")
        print(f"⏱️ Run {run_id} is now available for WebSocket connections")
        
        # ✅ FIXED: Small delay to ensure run is fully registered before returning
        await asyncio.sleep(0.1)
        
        return {
            "run_id": run_id,
            "scenario_id": scenario_id,
            "status": "running",
        }
    
    # Fallback: create new simulation (if pre-init failed)
    scenarios_dir = Path(__file__).parent.parent / "scenarios"
    scenario_file = scenarios_dir / f"{scenario_id}.json"
    
    if not scenario_file.exists():
        return JSONResponse(
            status_code=404,
            content={"error": f"Scenario {scenario_id} not found"}
        )
    
    with open(scenario_file, 'r') as f:
        scenario_config = json.load(f)
    
    # Create model
    model = SpecialOlympicsModel(scenario_config)
    
    # Generate run ID
    run_id = str(uuid.uuid4())
    
    # Initialize alert manager for this run
    alert_manager = AsyncGlobalAlertManager(model)
    
    # Store run BEFORE returning (critical for WebSocket timing)
    active_runs[run_id] = {
        "model": model,
        "scenario_id": scenario_id,
        "status": "running",
        "created_at": datetime.now(),
        "alert_manager": alert_manager,
    }
    
    # Initialize WebSocket connections set
    ws_connections[run_id] = set()
    
    print(f"✅ Created new simulation for {scenario_id}, run_id: {run_id}")
    print(f"📋 Active runs: {list(active_runs.keys())}")
    print(f"⏱️ Run {run_id} is now available for WebSocket connections")
    
    # ✅ FIXED: Small delay to ensure run is fully registered before returning
    await asyncio.sleep(0.1)
    
    return {
        "run_id": run_id,
        "scenario_id": scenario_id,
        "status": "running",
    }


@app.get("/api/runs/{run_id}/state", tags=["runs"])
async def get_state(run_id: str):
    """Get current simulation state."""
    if run_id not in active_runs:
        return JSONResponse(
            status_code=404,
            content={"error": f"Run {run_id} not found"}
        )
    
    run = active_runs[run_id]
    model = run["model"]
    
    return model.get_state()


@app.get("/api/runs/{run_id}/metrics", tags=["runs"])
async def get_metrics(run_id: str):
    """Get computed metrics."""
    if run_id not in active_runs:
        return JSONResponse(
            status_code=404,
            content={"error": f"Run {run_id} not found"}
        )
    
    run = active_runs[run_id]
    model = run["model"]
    
    return {
        "run_id": run_id,
        "metrics": model.metrics,
        "time": model.current_time.isoformat(),
    }


@app.post("/api/runs/{run_id}/step", tags=["runs"])
async def step_run(run_id: str):
    """Advance simulation by one step."""
    if run_id not in active_runs:
        return JSONResponse(
            status_code=404,
            content={"error": f"Run {run_id} not found"}
        )
    
    run = active_runs[run_id]
    model = run["model"]
    
    if run["status"] != "running":
        return JSONResponse(
            status_code=400,
            content={"error": f"Run {run_id} is not running"}
        )
    
    try:
        # Step simulation (Mesa 3.x compatibility - step() doesn't return value)
        model.step()
        continue_sim = model.should_continue()
        
        if not continue_sim:
            run["status"] = "completed"
        
        # Get state with error handling
        try:
            state = model.get_state()
        except Exception as e:
            print(f"❌ Error getting state: {e}")
            import traceback
            traceback.print_exc()
            return JSONResponse(
                status_code=500,
                content={"error": f"Failed to get state: {str(e)}"}
            )
        
        return {
            "run_id": run_id,
            "status": run["status"],
            "state": state,
        }
    except Exception as e:
        print(f"❌ Error stepping simulation: {e}")
        import traceback
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"error": f"Failed to step simulation: {str(e)}"}
        )


@app.websocket("/ws/runs/{run_id}")
async def websocket_stream(websocket: WebSocket, run_id: str):
    """WebSocket stream for real-time simulation updates."""
    print(f"🔌 WebSocket connection attempt for run_id: {run_id}")
    print(f"📋 Current active runs: {list(active_runs.keys())}")
    
    # ✅ FIXED: Increased wait time and better logging for WebSocket connection
    import asyncio
    max_wait = 3.0  # Increased to 3 seconds to handle slower backend initialization
    wait_interval = 0.1  # Check every 100ms
    waited = 0.0
    
    print(f"⏳ Waiting for run {run_id} to be registered (max {max_wait}s)...")
    while run_id not in active_runs and waited < max_wait:
        await asyncio.sleep(wait_interval)
        waited += wait_interval
        if waited % 0.5 < wait_interval:  # Log every 0.5 seconds
            print(f"⏳ Still waiting for run {run_id}... ({waited:.1f}s / {max_wait}s)")
    
    if run_id not in active_runs:
        print(f"⚠️ Run {run_id} not found after {waited:.1f}s. Available runs: {list(active_runs.keys())}")
    
    try:
        await websocket.accept()
        print(f"✅ WebSocket connection accepted for run_id: {run_id}")
    except Exception as e:
        print(f"❌ Error accepting WebSocket connection: {e}")
        import traceback
        traceback.print_exc()
        return
    
    if run_id not in active_runs:
        error_msg = {
            "type": "error",
            "error": f"Run {run_id} not found after waiting {waited:.1f}s",
            "available_runs": list(active_runs.keys())
        }
        print(f"❌ Run {run_id} not found in active_runs. Available: {list(active_runs.keys())}")
        try:
            await websocket.send_json(error_msg)
            await websocket.close(code=1008, reason="Run not found")
        except Exception as e:
            print(f"❌ Error sending error message: {e}")
        return
    
    run = active_runs[run_id]
    model = run["model"]
    alert_manager: Optional[AsyncGlobalAlertManager] = run.get("alert_manager")
    
    async def send_safe(ws: WebSocket, message: dict):
        """Safely send message with backpressure handling."""
        try:
            # ✅ ENHANCED: Check connection state before sending
            if hasattr(ws, 'client_state'):
                # WebSocketState.CONNECTED = 1, CONNECTING = 0, DISCONNECTED = 2
                if ws.client_state != 1:  # Not connected
                    return False
            
            await ws.send_json(message)
            return True
        except WebSocketDisconnect:
            print(f"⚠️ WebSocket disconnected while sending message")
            return False
        except RuntimeError as e:
            # Connection already closed
            if "closed" in str(e).lower() or "disconnect" in str(e).lower():
                print(f"⚠️ WebSocket connection closed: {e}")
                return False
            print(f"⚠️ Runtime error sending message: {e}")
            return False
        except Exception as e:
            print(f"⚠️ Error sending message: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    # Register this WebSocket connection
    if run_id not in ws_connections:
        ws_connections[run_id] = set()
    ws_connections[run_id].add(websocket)
    print(f"📡 Registered WebSocket for run {run_id} (total connections: {len(ws_connections[run_id])})")
    
    # ✅ ENHANCED: Send initial connection confirmation
    try:
        await send_safe(websocket, {
            "type": "connected",
            "run_id": run_id,
            "message": "WebSocket connected successfully"
        })
    except Exception as e:
        print(f"⚠️ Failed to send initial connection message: {e}")
    
    # Subscribe to alert updates
    async def send_alert_update(message: dict):
        """Send alert update to this WebSocket."""
        return await send_safe(websocket, message)
    
    if alert_manager:
        alert_manager.subscribe(send_alert_update)
    
    try:
        # Send initial state
        print(f"Sending initial state for run {run_id}")
        try:
            state = model.get_state()
            # Ensure JSON serializable
            state_json = json.loads(json.dumps(state, default=str))
            success = await send_safe(websocket, {
                "type": "state",
                "data": state_json,
            })
            if not success:
                return
            print(f"Initial state sent successfully for run {run_id}")
        except Exception as e:
            print(f"Error sending initial state for run {run_id}: {e}")
            import traceback
            traceback.print_exc()
            await send_safe(websocket, {
                "type": "error",
                "error": f"Failed to serialize initial state: {str(e)}"
            })
            return
        
        # Stream updates with dynamic timing and alert updates
        step_count = 0
        last_step_time = datetime.now()
        
        # Get step duration from model if available
        step_duration = getattr(model, 'step_duration', timedelta(seconds=1))
        if isinstance(step_duration, timedelta):
            step_duration_seconds = step_duration.total_seconds()
        elif isinstance(step_duration, (int, float)):
            step_duration_seconds = float(step_duration)
        else:
            step_duration_seconds = 1.0
        
        # Target update rate (10x real-time by default)
        target_speed_multiplier = 10.0
        target_step_interval = step_duration_seconds / target_speed_multiplier
        
        # Background task for alert updates
        async def update_alerts_periodically():
            """Periodically update alerts and check for expiration."""
            while run["status"] == "running":
                try:
                    if alert_manager:
                        await alert_manager.update_all_alerts()
                        await alert_manager.expire_alerts()
                    await asyncio.sleep(2)  # ✅ ENHANCED: Update every 2 seconds instead of 5 for faster metrics
                except Exception as e:
                    print(f"Error in alert update task: {e}")
                    import traceback
                    traceback.print_exc()
                    await asyncio.sleep(5)
        
        alert_task = asyncio.create_task(update_alerts_periodically())
        
        while run["status"] == "running":
            try:
                # Step simulation
                step_count += 1
                step_start = datetime.now()
                
                # Step simulation (Mesa 3.x compatibility - step() doesn't return value)
                model.step()
                continue_sim = model.should_continue()
                
                # Send state update with backpressure handling
                try:
                    state = model.get_state()
                    # Ensure JSON serializable
                    state_json = json.loads(json.dumps(state, default=str))
                    
                    success = await send_safe(websocket, {
                        "type": "update",
                        "data": state_json,
                    })
                    
                    if not success:
                        print(f"⚠️ WebSocket disconnected while sending update, stopping stream for run {run_id}")
                        break
                    
                    # Send alert metrics periodically
                    if alert_manager and step_count % 10 == 0:
                        try:
                            alert_metrics = await alert_manager.get_alert_metrics()
                            top_alerts = await alert_manager.get_alerts_by_priority(limit=5)
                            await send_safe(websocket, {
                                "type": "alert_metrics",
                                "data": {
                                    "metrics": alert_metrics,
                                    "top_alerts": [alert.to_dict() for alert in top_alerts],
                                }
                            })
                        except Exception as e:
                            print(f"Error sending alert metrics: {e}")
                            import traceback
                            traceback.print_exc()
                    
                    if step_count % 10 == 0:  # Log every 10 steps
                        print(f"✅ Step {step_count} for run {run_id} - {len(state_json.get('agents', {}).get('athletes', []))} athletes")
                        
                except Exception as e:
                    print(f"Error serializing/sending state update for run {run_id}: {e}")
                    import traceback
                    traceback.print_exc()
                    # Try to send error message
                    await send_safe(websocket, {
                        "type": "error",
                        "error": f"Failed to serialize state: {str(e)}"
                    })
                    # Continue anyway - don't break the loop
                
                if not continue_sim:
                    print(f"Simulation completed for run {run_id} after {step_count} steps")
                    run["status"] = "completed"
                    run["completed_at"] = datetime.now()
                    await send_safe(websocket, {
                        "type": "completed",
                        "data": {"metrics": model.metrics},
                    })
                    break
                
                # ✅ ENHANCED: Much faster updates - minimal delay for real-time metrics
                step_elapsed = (datetime.now() - step_start).total_seconds()
                # Use very short sleep (10ms max) to allow other tasks but keep updates fast
                sleep_time = max(0, min(0.01, target_step_interval - step_elapsed))
                if sleep_time > 0:
                    await asyncio.sleep(sleep_time)
                
                # ✅ ENHANCED: Periodic connection health check (every 50 steps)
                if step_count % 50 == 0:
                    try:
                        # Send a ping-like message to check connection
                        ping_success = await send_safe(websocket, {
                            "type": "ping",
                            "step": step_count,
                            "timestamp": datetime.now().isoformat()
                        })
                        if not ping_success:
                            print(f"⚠️ WebSocket ping failed for run {run_id}, stopping stream")
                            break
                    except Exception as e:
                        print(f"⚠️ Error during connection health check for run {run_id}: {e}")
                        break
                    
            except WebSocketDisconnect:
                print(f"WebSocket disconnected during streaming for run {run_id}")
                break
            except Exception as e:
                print(f"Error in WebSocket stream loop for run {run_id}: {e}")
                import traceback
                traceback.print_exc()
                # Try to send error and break
                await send_safe(websocket, {
                    "type": "error",
                    "error": f"Stream error: {str(e)}"
                })
                break
    
    except WebSocketDisconnect:
        print(f"WebSocket disconnected for run {run_id}")
    except Exception as e:
        print(f"Error in WebSocket stream for run {run_id}: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Cancel alert update task
        if 'alert_task' in locals():
            alert_task.cancel()
            try:
                await alert_task
            except asyncio.CancelledError:
                pass
        
        # Unsubscribe from alert updates
        if alert_manager:
            alert_manager.unsubscribe(send_alert_update)
        
        # Unregister WebSocket connection
        if run_id in ws_connections:
            ws_connections[run_id].discard(websocket)
            if len(ws_connections[run_id]) == 0:
                # No more connections, could optionally pause simulation
                pass
            print(f"📡 Unregistered WebSocket for run {run_id} (remaining connections: {len(ws_connections.get(run_id, set()))})")
        print(f"WebSocket connection closed for run {run_id}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3333)

