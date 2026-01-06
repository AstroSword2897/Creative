"""
Test script for 3D visualization.
Run this to verify the visualization works correctly.
"""

import sys
import json
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from simulation.model import SpecialOlympicsModel
from simulation.visualization_3d import Visualization3D


def test_visualization():
    """Test the 3D visualization system."""
    print("Loading scenario...")
    
    # Load baseline scenario
    scenario_path = Path(__file__).parent.parent / "backend" / "scenarios" / "baseline.json"
    with open(scenario_path, 'r') as f:
        scenario_config = json.load(f)
    
    print("Creating simulation model...")
    model = SpecialOlympicsModel(scenario_config)
    
    print("Creating 3D visualization...")
    viz = Visualization3D(model, width=1000, height=700)
    
    print("Initializing venues...")
    viz.initialize_venues()
    
    print("Initializing agents...")
    viz.initialize_agents()
    
    print(f"Created {len(viz.agent_3d)} agent representations")
    print(f"Created {len(viz.venue_markers)} venue markers")
    
    print("\nSetting camera view...")
    viz.set_camera_view("top_down", smooth=False)
    
    print("\nRunning simulation for 10 steps...")
    for i in range(10):
        model.step()
        viz.update()
        print(f"  Step {i+1}: Time = {model.current_time.strftime('%H:%M:%S')}")
        print(f"    Active incidents: {len(model.active_incidents)}")
        print(f"    Safety score: {model.metrics['safety_score']:.1f}")
    
    print("\n✅ Visualization test completed successfully!")
    print("\nTo display in Jupyter notebook, run:")
    print("  viz.display()")
    
    return model, viz


if __name__ == "__main__":
    try:
        model, viz = test_visualization()
        print("\n🎉 All tests passed!")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

