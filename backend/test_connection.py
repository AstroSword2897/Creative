"""
Quick test script to verify backend-frontend connection.
Run this to check if everything is set up correctly.
"""

import requests
import json
from pathlib import Path

def test_backend():
    """Test backend API endpoints."""
    base_url = "http://localhost:3333"
    
    print("=" * 60)
    print("Testing Backend Connection")
    print("=" * 60)
    print()
    
    # Test root endpoint
    try:
        response = requests.get(f"{base_url}/")
        print(f"✅ Root endpoint: {response.status_code}")
        data = response.json()
        print(f"   Message: {data.get('message')}")
        print(f"   Active runs: {data.get('active_runs')}")
        print(f"   Preinitialized: {data.get('preinitialized')}")
    except Exception as e:
        print(f"❌ Root endpoint failed: {e}")
        return False
    
    # Test health endpoint
    try:
        response = requests.get(f"{base_url}/api/health")
        print(f"✅ Health check: {response.status_code}")
        data = response.json()
        print(f"   Status: {data.get('status')}")
        print(f"   WebSocket connections: {data.get('websocket_connections')}")
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False
    
    # Test scenarios endpoint
    try:
        response = requests.get(f"{base_url}/api/scenarios")
        print(f"✅ Scenarios endpoint: {response.status_code}")
        data = response.json()
        scenarios = data.get('scenarios', [])
        print(f"   Available scenarios: {len(scenarios)}")
        for scenario in scenarios[:3]:  # Show first 3
            print(f"     - {scenario.get('name')} ({scenario.get('id')})")
    except Exception as e:
        print(f"❌ Scenarios endpoint failed: {e}")
        return False
    
    print()
    print("=" * 60)
    print("Backend Status: ✅ Ready")
    print("=" * 60)
    print()
    print("Next steps:")
    print("1. Open http://localhost:5173 in your browser")
    print("2. Click a scenario button to start simulation")
    print("3. Watch agents move in real-time in the 3D view!")
    print()
    
    return True

if __name__ == "__main__":
    try:
        import requests
    except ImportError:
        print("❌ 'requests' library not installed")
        print("   Install with: pip install requests")
        exit(1)
    
    success = test_backend()
    exit(0 if success else 1)

