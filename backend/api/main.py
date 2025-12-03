"""
FastAPI main application.
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import Dict, List
import json
import asyncio
from pathlib import Path

from simulation.model import SpecialOlympicsModel

app = FastAPI(title="Special Olympics Las Vegas Simulation API")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Active simulation runs
active_runs: Dict[str, Dict] = {}


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Special Olympics Las Vegas Simulation API", "version": "0.1.0"}


@app.get("/api/scenarios")
async def list_scenarios():
    """List available scenarios."""
    scenarios_dir = Path(__file__).parent.parent / "scenarios"
    scenarios = []
    
    for scenario_file in scenarios_dir.glob("*.json"):
        with open(scenario_file, 'r') as f:
            scenario = json.load(f)
            scenarios.append({
                "id": scenario.get("id"),
                "name": scenario.get("name"),
                "description": scenario.get("description"),
            })
    
    return {"scenarios": scenarios}


@app.get("/api/scenarios/{scenario_id}")
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


@app.post("/api/scenarios/{scenario_id}/run")
async def start_run(scenario_id: str):
    """Start a simulation run."""
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
    import uuid
    run_id = str(uuid.uuid4())
    
    # Store run
    active_runs[run_id] = {
        "model": model,
        "scenario_id": scenario_id,
        "status": "running",
    }
    
    return {
        "run_id": run_id,
        "scenario_id": scenario_id,
        "status": "running",
    }


@app.get("/api/runs/{run_id}/state")
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


@app.get("/api/runs/{run_id}/metrics")
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


@app.post("/api/runs/{run_id}/step")
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
    
    # Step simulation
    continue_sim = model.step()
    
    if not continue_sim:
        run["status"] = "completed"
    
    return {
        "run_id": run_id,
        "status": run["status"],
        "state": model.get_state(),
    }


@app.websocket("/ws/runs/{run_id}")
async def websocket_stream(websocket: WebSocket, run_id: str):
    """WebSocket stream for real-time simulation updates."""
    await websocket.accept()
    
    if run_id not in active_runs:
        await websocket.send_json({"error": f"Run {run_id} not found"})
        await websocket.close()
        return
    
    run = active_runs[run_id]
    model = run["model"]
    
    try:
        # Send initial state
        await websocket.send_json({
            "type": "state",
            "data": model.get_state(),
        })
        
        # Stream updates
        while run["status"] == "running":
            # Step simulation
            continue_sim = model.step()
            
            # Send state update
            await websocket.send_json({
                "type": "update",
                "data": model.get_state(),
            })
            
            if not continue_sim:
                run["status"] = "completed"
                await websocket.send_json({
                    "type": "completed",
                    "data": {"metrics": model.metrics},
                })
                break
            
            # Wait before next step (adjust for desired speed)
            await asyncio.sleep(0.1)  # 100ms = 10x real-time if step is 1 second
    
    except WebSocketDisconnect:
        pass
    finally:
        # Cleanup if needed
        pass


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

