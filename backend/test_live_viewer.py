"""
Simple live viewer script that connects via WebSocket and displays agent movement.
Run this to see agents moving in real-time without needing a browser.
"""

import asyncio
import websockets
import json
import sys
from datetime import datetime
import requests

BASE_URL = "http://localhost:3333"
WS_URL = "ws://localhost:3333"

def print_agent_summary(state):
    """Print a summary of agent positions."""
    agents = state.get("agents", {})
    print(f"\n   👥 Agents:")
    print(f"      Athletes: {len(agents.get('athletes', []))}")
    print(f"      Volunteers: {len(agents.get('volunteers', []))}")
    print(f"      Security: {len(agents.get('security', []))}")
    print(f"      LVMPD: {len(agents.get('lvmpd', []))}")
    print(f"      AMR: {len(agents.get('amr', []))}")
    print(f"      Buses: {len(agents.get('buses', []))}")
    
    # Show sample athlete locations
    athletes = agents.get("athletes", [])
    if athletes:
        print(f"\n   📍 Sample athlete locations:")
        for i, athlete in enumerate(athletes[:3]):
            loc = athlete.get("location", [0, 0])
            print(f"      Athlete {athlete.get('id')}: ({loc[0]:.4f}, {loc[1]:.4f}) - {athlete.get('status', 'unknown')}")

def print_metrics(metrics):
    """Print simulation metrics."""
    print(f"\n   📊 Metrics:")
    print(f"      Safety Score: {metrics.get('safety_score', 0):.1f}/100")
    print(f"      Avg Response Time: {metrics.get('avg_response_time', 0)/60:.1f} minutes")
    print(f"      Containment Rate: {metrics.get('containment_rate', 0)*100:.1f}%")
    print(f"      Medical Events: {metrics.get('medical_events_count', 0)}")
    print(f"      Incidents Resolved: {metrics.get('incidents_resolved', 0)}")

async def watch_simulation(run_id: str, max_updates: int = 50):
    """Watch simulation via WebSocket and display updates."""
    uri = f"{WS_URL}/ws/runs/{run_id}"
    
    print("=" * 60)
    print("Live Simulation Viewer")
    print("=" * 60)
    print(f"\nConnecting to: {uri}")
    print("Press Ctrl+C to stop\n")
    
    try:
        async with websockets.connect(uri) as websocket:
            print("✅ Connected to simulation stream\n")
            
            update_count = 0
            last_athlete_locations = {}
            
            while update_count < max_updates:
                try:
                    # Receive message with timeout
                    message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    data = json.loads(message)
                    
                    if data.get("type") == "error":
                        print(f"❌ Error: {data.get('error')}")
                        break
                    
                    elif data.get("type") == "state":
                        state = data.get("data", {})
                        print(f"\n{'='*60}")
                        print(f"📡 Initial State")
                        print(f"{'='*60}")
                        print(f"   ⏰ Time: {state.get('time', 'unknown')}")
                        print_agent_summary(state)
                        if "metrics" in state:
                            print_metrics(state["metrics"])
                        
                        # Store initial locations
                        for athlete in state.get("agents", {}).get("athletes", []):
                            last_athlete_locations[athlete.get("id")] = athlete.get("location")
                    
                    elif data.get("type") == "update":
                        state = data.get("data", {})
                        update_count += 1
                        
                        print(f"\n{'='*60}")
                        print(f"📡 Update #{update_count}")
                        print(f"{'='*60}")
                        print(f"   ⏰ Time: {state.get('time', 'unknown')}")
                        
                        # Check for movement
                        athletes = state.get("agents", {}).get("athletes", [])
                        moved_count = 0
                        for athlete in athletes:
                            athlete_id = athlete.get("id")
                            current_loc = athlete.get("location")
                            last_loc = last_athlete_locations.get(athlete_id)
                            
                            if last_loc and current_loc:
                                if current_loc != last_loc:
                                    moved_count += 1
                                    last_athlete_locations[athlete_id] = current_loc
                        
                        if moved_count > 0:
                            print(f"   ✅ {moved_count} athletes moved!")
                        
                        print_agent_summary(state)
                        
                        if "metrics" in state:
                            print_metrics(state["metrics"])
                        
                        # Show incidents if any
                        incidents = state.get("incidents", [])
                        if incidents:
                            print(f"\n   🚨 Active Incidents: {len(incidents)}")
                            for incident in incidents[:3]:
                                print(f"      - {incident.get('type', 'unknown')} at {incident.get('location', [0, 0])}")
                    
                    elif data.get("type") == "completed":
                        print(f"\n{'='*60}")
                        print(f"✅ Simulation Completed")
                        print(f"{'='*60}")
                        if "data" in data and "metrics" in data["data"]:
                            print_metrics(data["data"]["metrics"])
                        break
                    
                    elif data.get("type") == "alert_metrics":
                        # Alert updates (optional)
                        pass
                    
                except asyncio.TimeoutError:
                    print("⏳ Waiting for updates...")
                    continue
                except KeyboardInterrupt:
                    print("\n\n⏸️  Stopped by user")
                    break
            
            print(f"\n{'='*60}")
            print(f"📊 Summary: Received {update_count} updates")
            print(f"{'='*60}\n")
            
    except websockets.exceptions.InvalidStatusCode as e:
        print(f"❌ Connection failed: {e}")
        print(f"   Make sure the backend is running on port 3333")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

def main():
    """Main entry point."""
    if len(sys.argv) > 1:
        run_id = sys.argv[1]
    else:
        # Start a new simulation
        print("Starting new simulation...")
        try:
            response = requests.post(f"{BASE_URL}/api/scenarios/baseline/run", timeout=10)
            if response.status_code != 200:
                print(f"❌ Failed to start simulation: {response.status_code}")
                print(response.text)
                sys.exit(1)
            
            data = response.json()
            run_id = data["run_id"]
            print(f"✅ Started simulation: {run_id}\n")
        except Exception as e:
            print(f"❌ Failed to start simulation: {e}")
            sys.exit(1)
    
    # Watch the simulation
    success = asyncio.run(watch_simulation(run_id))
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()

