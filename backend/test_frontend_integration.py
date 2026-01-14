"""
Test frontend integration - verify data format matches frontend expectations.
"""

import requests
import json
import time

BASE_URL = "http://localhost:3333"

def test_state_format():
    """Verify state format matches frontend TypeScript interfaces."""
    print("=" * 60)
    print("Frontend Integration Test")
    print("=" * 60)
    print()
    
    # Start a simulation
    print("1. Starting simulation...")
    response = requests.post(f"{BASE_URL}/api/scenarios/baseline/run", timeout=10)
    assert response.status_code == 200, f"Failed to start simulation: {response.status_code}"
    data = response.json()
    run_id = data["run_id"]
    print(f"   ✅ Run ID: {run_id}")
    
    # Wait for initialization
    time.sleep(0.5)
    
    # Get state
    print("\n2. Getting simulation state...")
    response = requests.get(f"{BASE_URL}/api/runs/{run_id}/state", timeout=5)
    assert response.status_code == 200, f"Failed to get state: {response.status_code}"
    state = response.json()
    
    # Verify structure matches frontend types
    print("\n3. Verifying state structure...")
    
    # Check top-level keys
    assert "time" in state, "Missing 'time'"
    assert "agents" in state, "Missing 'agents'"
    assert "incidents" in state, "Missing 'incidents'"
    assert "metrics" in state, "Missing 'metrics'"
    print("   ✅ Top-level structure correct")
    
    # Check agents structure
    agents = state["agents"]
    assert isinstance(agents, dict), "agents should be a dict"
    required_agent_types = ["athletes", "volunteers", "security", "lvmpd", "amr", "buses"]
    for agent_type in required_agent_types:
        assert agent_type in agents, f"Missing agent type: {agent_type}"
        assert isinstance(agents[agent_type], list), f"{agent_type} should be a list"
    print("   ✅ Agent types structure correct")
    
    # Check athlete structure (sample)
    if len(agents["athletes"]) > 0:
        athlete = agents["athletes"][0]
        assert "id" in athlete, "Athlete missing 'id'"
        assert "type" in athlete, "Athlete missing 'type'"
        assert "location" in athlete, "Athlete missing 'location'"
        assert "status" in athlete, "Athlete missing 'status'"
        
        # Verify location format
        location = athlete["location"]
        assert location is not None, "Location should not be None"
        assert isinstance(location, list), "Location should be a list"
        assert len(location) == 2, "Location should be [lat, lon]"
        assert all(isinstance(coord, (int, float)) for coord in location), "Location coords should be numbers"
        print(f"   ✅ Athlete structure correct (sample: {athlete['id']})")
    
    # Check incidents structure
    incidents = state["incidents"]
    assert isinstance(incidents, list), "incidents should be a list"
    if len(incidents) > 0:
        incident = incidents[0]
        assert "id" in incident, "Incident missing 'id'"
        assert "type" in incident, "Incident missing 'type'"
        assert "location" in incident, "Incident missing 'location'"
        assert "timestamp" in incident, "Incident missing 'timestamp'"
        print(f"   ✅ Incident structure correct (sample: {incident['id']})")
    
    # Check metrics structure
    metrics = state["metrics"]
    assert isinstance(metrics, dict), "metrics should be a dict"
    required_metrics = ["safety_score", "avg_response_time", "containment_rate"]
    for metric in required_metrics:
        assert metric in metrics, f"Missing metric: {metric}"
        assert isinstance(metrics[metric], (int, float)), f"{metric} should be a number"
    print("   ✅ Metrics structure correct")
    
    # Verify JSON serialization (frontend will receive JSON)
    print("\n4. Verifying JSON serialization...")
    try:
        json_str = json.dumps(state)
        parsed = json.loads(json_str)
        assert parsed == state, "JSON round-trip failed"
        print("   ✅ JSON serialization works correctly")
    except Exception as e:
        print(f"   ❌ JSON serialization failed: {e}")
        return False
    
    print("\n" + "=" * 60)
    print("✅ All frontend integration tests passed!")
    print("=" * 60)
    print("\nThe backend state format matches frontend expectations.")
    print("Frontend should be able to receive and display this data correctly.")
    print()
    
    return True

if __name__ == "__main__":
    try:
        success = test_state_format()
        exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        exit(1)

