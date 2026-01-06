"""
Example usage of 3D visualization system.
Run this in a Jupyter notebook to see the interactive 3D simulation.
"""

from simulation.model import SpecialOlympicsModel
from simulation.visualization_3d import Visualization3D
import json
from pathlib import Path


def create_3d_visualization(scenario_file: str = "scenarios/baseline.json"):
    """Create and display 3D visualization of simulation."""
    
    # Load scenario
    scenario_path = Path(__file__).parent.parent / scenario_file
    with open(scenario_path, 'r') as f:
        scenario_config = json.load(f)
    
    # Create model
    model = SpecialOlympicsModel(scenario_config)
    
    # Create 3D visualization
    viz = Visualization3D(model, width=1000, height=700)
    
    # Initialize visualization
    viz.initialize_venues()
    viz.initialize_agents()
    
    # Set camera view
    viz.set_camera_view("top_down")
    
    # Display
    viz.display()
    
    return model, viz


def run_simulation_step(model, viz, steps: int = 10):
    """Run simulation for N steps and update visualization."""
    for i in range(steps):
        # Step simulation
        model.step()
        
        # Update visualization
        viz.update()
        
        print(f"Step {i+1}: Time = {model.current_time.strftime('%H:%M:%S')}")
        print(f"  Active incidents: {len(model.active_incidents)}")
        print(f"  Safety score: {model.metrics['safety_score']:.1f}")
    
    return model, viz


# Example usage in Jupyter:
# model, viz = create_3d_visualization()
# model, viz = run_simulation_step(model, viz, steps=50)

