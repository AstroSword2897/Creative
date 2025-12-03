"""
Script to run a scenario from command line.
Usage: python -m simulation.run_scenario scenarios/baseline.json
"""

import json
import sys
from pathlib import Path
from .model import SpecialOlympicsModel


def run_scenario(scenario_path: str, max_steps: int = 1000):
    """Run a scenario and print progress."""
    # Load scenario
    with open(scenario_path, 'r') as f:
        scenario = json.load(f)
    
    print(f"Running scenario: {scenario.get('id', 'unknown')}")
    print(f"Duration: {scenario.get('duration_hours', 8)} hours")
    print(f"Agents: {scenario.get('agents', {})}")
    print("-" * 50)
    
    # Create model
    model = SpecialOlympicsModel(scenario)
    
    # Run simulation
    step_count = 0
    while step_count < max_steps:
        if not model.step():
            break
        
        step_count += 1
        
        # Print progress every 10 steps
        if step_count % 10 == 0:
            print(f"Step {step_count}: Time={model.current_time.strftime('%H:%M:%S')}, "
                  f"Safety Score={model.metrics['safety_score']:.1f}, "
                  f"Active Incidents={len(model.active_incidents)}")
    
    # Final metrics
    print("-" * 50)
    print("Simulation Complete")
    print(f"Final Safety Score: {model.metrics['safety_score']:.1f}")
    print(f"Medical Events: {model.metrics['medical_events_count']}")
    print(f"Incidents Resolved: {model.metrics['incidents_resolved']}")
    print(f"Average Response Time: {model.metrics['avg_response_time']:.1f}s")
    print(f"Containment Rate: {model.metrics['containment_rate']:.2%}")
    
    return model


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python -m simulation.run_scenario <scenario.json>")
        sys.exit(1)
    
    scenario_path = sys.argv[1]
    run_scenario(scenario_path)

