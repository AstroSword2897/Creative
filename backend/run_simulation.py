"""
Run the Special Olympics Las Vegas simulation with 3D visualization.
"""

import sys
import json
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from simulation.model import SpecialOlympicsModel
from simulation.visualization_3d import Visualization3D


def run_simulation(scenario_file: str = "scenarios/baseline.json", steps: int = 50):
    """Run simulation with 3D visualization."""
    
    print("=" * 60)
    print("Special Olympics Las Vegas Security Simulation")
    print("=" * 60)
    print()
    
    # Load scenario
    scenario_path = Path(__file__).parent / scenario_file
    if not scenario_path.exists():
        print(f"❌ Scenario file not found: {scenario_file}")
        return None
    
    print(f"📋 Loading scenario: {scenario_file}")
    with open(scenario_path, 'r') as f:
        scenario_config = json.load(f)
    
    print(f"   Scenario: {scenario_config.get('name', 'Unknown')}")
    print(f"   Duration: {scenario_config.get('duration_hours', 8)} hours")
    print()
    
    # Create model
    print("🔧 Creating simulation model...")
    try:
        model = SpecialOlympicsModel(scenario_config)
        print(f"   ✅ Model created successfully")
        print(f"   Agents initialized:")
        print(f"     - Athletes: {len(model.athletes)}")
        print(f"     - Volunteers: {len(model.volunteers)}")
        print(f"     - Hotel Security: {len(model.hotel_security)}")
        print(f"     - LVMPD Units: {len(model.lvmpd_units)}")
        print(f"     - AMR Units: {len(model.amr_units)}")
        print(f"     - Buses: {len(model.buses)}")
        print()
    except Exception as e:
        print(f"   ❌ Error creating model: {e}")
        import traceback
        traceback.print_exc()
        return None
    
    # Create 3D visualization
    print("🎨 Creating 3D visualization...")
    try:
        viz = Visualization3D(model, width=1000, height=700)
        viz.initialize_venues()
        viz.initialize_agents()
        viz.set_camera_view("top_down", smooth=False)
        print(f"   ✅ Visualization created")
        print(f"     - Agent representations: {len(viz.agent_3d)}")
        print(f"     - Venue markers: {len(viz.venue_markers)}")
        print()
    except Exception as e:
        print(f"   ⚠️  Visualization error (continuing without 3D): {e}")
        viz = None
    
    # Run simulation
    print("🚀 Running simulation...")
    print()
    
    try:
        for i in range(steps):
            # Step simulation
            continue_sim = model.step()
            
            # Update visualization
            if viz:
                viz.update()
            
            # Print status every 10 steps
            if (i + 1) % 10 == 0 or i == 0:
                print(f"   Step {i+1:3d} | Time: {model.current_time.strftime('%H:%M:%S')} | "
                      f"Incidents: {len(model.active_incidents):2d} | "
                      f"Safety: {model.metrics['safety_score']:5.1f}")
            
            if not continue_sim:
                print(f"\n   ✅ Simulation completed at step {i+1}")
                break
        
        print()
        print("=" * 60)
        print("📊 Final Metrics")
        print("=" * 60)
        print(f"   Safety Score: {model.metrics['safety_score']:.1f}/100")
        print(f"   Avg Response Time: {model.metrics['avg_response_time']/60:.1f} minutes")
        print(f"   Containment Rate: {model.metrics['containment_rate']*100:.1f}%")
        print(f"   Medical Events: {model.metrics['medical_events_count']}")
        print(f"   Incidents Resolved: {model.metrics['incidents_resolved']}")
        print()
        
        # Display visualization if available
        if viz:
            print("=" * 60)
            print("🎨 3D Visualization")
            print("=" * 60)
            print("   To display in Jupyter notebook, run:")
            print("     viz.display()")
            print()
            print("   Or use the visualization object directly:")
            print("     from IPython.display import display")
            print("     display(viz.render())")
            print()
        
        return model, viz
        
    except Exception as e:
        print(f"\n   ❌ Error during simulation: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Run Special Olympics simulation")
    parser.add_argument(
        "--scenario",
        type=str,
        default="scenarios/baseline.json",
        help="Scenario file to run"
    )
    parser.add_argument(
        "--steps",
        type=int,
        default=50,
        help="Number of simulation steps"
    )
    
    args = parser.parse_args()
    
    result = run_simulation(args.scenario, args.steps)
    
    if result:
        print("✅ Simulation completed successfully!")
    else:
        print("❌ Simulation failed")
        sys.exit(1)

