"""
Comprehensive test suite for simulation flow.
Tests backend API, WebSocket, and data flow.
"""

import requests
import json
import time
import asyncio
import websockets
from typing import Dict, Any, Optional

BASE_URL = "http://localhost:3333"
WS_URL = "ws://localhost:3333"

def test_scenarios_endpoint():
    """Test /api/scenarios endpoint."""
    print("=" * 60)
    print("Test 1: Scenarios Endpoint")
    print("=" * 60)
    
    try:
        response = requests.get(f"{BASE_URL}/api/scenarios", timeout=5)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "scenarios" in data, "Response missing 'scenarios' key"
        
        scenarios = data["scenarios"]
        assert len(scenarios) > 0, "No scenarios returned"
        
        print(f"✅ Found {len(scenarios)} scenarios")
        for scenario in scenarios[:3]:
            print(f"   - {scenario.get('name')} ({scenario.get('id')})")
        
        return scenarios[0]["id"] if scenarios else None
    except Exception as e:
        print(f"❌ Failed: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_start_simulation(scenario_id: str):
    """Test starting a simulation."""
    print("\n" + "=" * 60)
    print("Test 2: Start Simulation")
    print("=" * 60)
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/scenarios/{scenario_id}/run",
            timeout=10
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "run_id" in data, "Response missing 'run_id'"
        assert "status" in data, "Response missing 'status'"
        assert data["status"] == "running", f"Expected 'running', got '{data['status']}'"
        
        run_id = data["run_id"]
        print(f"✅ Simulation started: {run_id}")
        print(f"   Status: {data['status']}")
        
        return run_id
    except Exception as e:
        print(f"❌ Failed: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_get_state(run_id: str):
    """Test getting simulation state."""
    print("\n" + "=" * 60)
    print("Test 3: Get State")
    print("=" * 60)
    
    try:
        # Wait a moment for simulation to initialize
        time.sleep(0.5)
        
        response = requests.get(f"{BASE_URL}/api/runs/{run_id}/state", timeout=5)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        state = response.json()
        assert "agents" in state, "State missing 'agents'"
        assert "time" in state, "State missing 'time'"
        
        agents = state["agents"]
        athlete_count = len(agents.get("athletes", []))
        volunteer_count = len(agents.get("volunteers", []))
        
        print(f"✅ State retrieved")
        print(f"   Time: {state.get('time', 'unknown')}")
        print(f"   Athletes: {athlete_count}")
        print(f"   Volunteers: {volunteer_count}")
        print(f"   Security: {len(agents.get('security', []))}")
        print(f"   LVMPD: {len(agents.get('lvmpd', []))}")
        print(f"   AMR: {len(agents.get('amr', []))}")
        print(f"   Buses: {len(agents.get('buses', []))}")
        
        # Verify agents have locations
        if athlete_count > 0:
            athlete = agents["athletes"][0]
            assert "location" in athlete, "Athlete missing 'location'"
            location = athlete["location"]
            assert location is not None, "Athlete location is None"
            assert len(location) == 2, f"Location should be [lat, lon], got {location}"
            print(f"   ✅ Sample athlete location: {location}")
        
        return state
    except Exception as e:
        print(f"❌ Failed: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_websocket_connection(run_id: str, max_messages: int = 5):
    """Test WebSocket connection and message streaming."""
    print("\n" + "=" * 60)
    print("Test 4: WebSocket Connection")
    print("=" * 60)
    
    async def test_ws():
        try:
            uri = f"{WS_URL}/ws/runs/{run_id}"
            print(f"   Connecting to: {uri}")
            
            async with websockets.connect(uri) as websocket:
                print("   ✅ WebSocket connected")
                
                messages_received = 0
                last_state = None
                
                # Wait for initial state
                try:
                    initial_message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    initial_data = json.loads(initial_message)
                    
                    if initial_data.get("type") == "state":
                        print("   ✅ Received initial state")
                        last_state = initial_data.get("data")
                        messages_received += 1
                    elif initial_data.get("type") == "error":
                        print(f"   ❌ Error message: {initial_data.get('error')}")
                        return False
                except asyncio.TimeoutError:
                    print("   ⚠️  Timeout waiting for initial state")
                
                # Receive a few update messages
                for i in range(max_messages):
                    try:
                        message = await asyncio.wait_for(websocket.recv(), timeout=3.0)
                        data = json.loads(message)
                        
                        if data.get("type") == "update":
                            state = data.get("data", {})
                            agents = state.get("agents", {})
                            athletes = agents.get("athletes", [])
                            
                            messages_received += 1
                            print(f"   ✅ Update {messages_received}: {len(athletes)} athletes, time: {state.get('time', 'unknown')}")
                            
                            # Check if agents are moving
                            if last_state and athletes:
                                last_athlete = last_state.get("agents", {}).get("athletes", [{}])[0] if last_state.get("agents", {}).get("athletes") else {}
                                current_athlete = athletes[0] if athletes else {}
                                
                                if last_athlete.get("location") != current_athlete.get("location"):
                                    print(f"   ✅ Agents are moving! Location changed")
                            
                            last_state = state
                        elif data.get("type") == "error":
                            print(f"   ❌ Error: {data.get('error')}")
                            return False
                        elif data.get("type") == "completed":
                            print(f"   ✅ Simulation completed")
                            return True
                    except asyncio.TimeoutError:
                        print(f"   ⚠️  Timeout waiting for update {i+1}")
                        break
                
                print(f"   ✅ Received {messages_received} messages total")
                return messages_received > 0
                
        except Exception as e:
            print(f"   ❌ WebSocket error: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    return asyncio.run(test_ws())

def test_step_simulation(run_id: str):
    """Test manual step endpoint."""
    print("\n" + "=" * 60)
    print("Test 5: Step Simulation")
    print("=" * 60)
    
    try:
        # Get initial state
        initial_response = requests.get(f"{BASE_URL}/api/runs/{run_id}/state", timeout=5)
        if initial_response.status_code != 200:
            print(f"   ⚠️  Cannot get state (run may have completed): {initial_response.status_code}")
            return False
        
        initial_state = initial_response.json()
        initial_time = initial_state.get("time")
        
        # Step simulation
        step_response = requests.post(f"{BASE_URL}/api/runs/{run_id}/step", timeout=5)
        
        # 400 means simulation is not running (likely completed)
        if step_response.status_code == 400:
            error_data = step_response.json()
            print(f"   ⚠️  Simulation not running: {error_data.get('error', 'unknown')}")
            print(f"   (This is expected if simulation completed during WebSocket test)")
            return True  # This is acceptable - simulation may have completed
        
        assert step_response.status_code == 200, f"Expected 200, got {step_response.status_code}"
        
        step_data = step_response.json()
        assert "state" in step_data, "Step response missing 'state'"
        
        new_state = step_data["state"]
        new_time = new_state.get("time")
        
        print(f"✅ Simulation stepped")
        print(f"   Initial time: {initial_time}")
        print(f"   New time: {new_time}")
        print(f"   Time advanced: {initial_time != new_time}")
        
        return True
    except AssertionError as e:
        print(f"❌ Failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_metrics_endpoint(run_id: str):
    """Test metrics endpoint."""
    print("\n" + "=" * 60)
    print("Test 6: Metrics Endpoint")
    print("=" * 60)
    
    try:
        response = requests.get(f"{BASE_URL}/api/runs/{run_id}/metrics", timeout=5)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "metrics" in data, "Response missing 'metrics'"
        
        metrics = data["metrics"]
        print(f"✅ Metrics retrieved")
        print(f"   Safety Score: {metrics.get('safety_score', 'N/A')}")
        print(f"   Avg Response Time: {metrics.get('avg_response_time', 'N/A')}")
        print(f"   Containment Rate: {metrics.get('containment_rate', 'N/A')}")
        print(f"   Medical Events: {metrics.get('medical_events_count', 'N/A')}")
        
        return True
    except Exception as e:
        print(f"❌ Failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def run_all_tests():
    """Run all tests in sequence."""
    print("\n" + "=" * 60)
    print("COMPREHENSIVE SIMULATION FLOW TEST")
    print("=" * 60)
    print()
    
    results = {}
    
    # Test 1: Scenarios
    scenario_id = test_scenarios_endpoint()
    results["scenarios"] = scenario_id is not None
    
    if not scenario_id:
        print("\n❌ Cannot continue without scenarios")
        return results
    
    # Test 2: Start simulation
    run_id = test_start_simulation(scenario_id)
    results["start_simulation"] = run_id is not None
    
    if not run_id:
        print("\n❌ Cannot continue without run_id")
        return results
    
    # Test 3: Get state
    state = test_get_state(run_id)
    results["get_state"] = state is not None
    
    # Test 4: WebSocket
    ws_success = test_websocket_connection(run_id, max_messages=5)
    results["websocket"] = ws_success
    
    # Test 5: Step simulation
    step_success = test_step_simulation(run_id)
    results["step_simulation"] = step_success
    
    # Test 6: Metrics
    metrics_success = test_metrics_endpoint(run_id)
    results["metrics"] = metrics_success
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"   {status}: {test_name}")
    
    total_tests = len(results)
    passed_tests = sum(1 for v in results.values() if v)
    print(f"\n   Total: {passed_tests}/{total_tests} tests passed")
    
    return results

if __name__ == "__main__":
    try:
        results = run_all_tests()
        exit(0 if all(results.values()) else 1)
    except KeyboardInterrupt:
        print("\n\n⏸️  Tests interrupted by user")
        exit(1)
    except Exception as e:
        print(f"\n\n❌ Test suite error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)

