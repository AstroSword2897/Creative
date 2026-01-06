#!/usr/bin/env python3
"""
Direct 3D Visualization Viewer
Run this script to see the simulation in 3D immediately.
"""

import sys
from pathlib import Path
import json

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from simulation.model import SpecialOlympicsModel
from simulation.visualization_3d import Visualization3D
from IPython.display import display
import time

def main():
    print("=" * 70)
    print("🏆 Special Olympics Las Vegas - 3D Visualization")
    print("=" * 70)
    print()
    
    # Load scenario
    print("📋 Loading scenario...")
    scenario_path = Path(__file__).parent / "scenarios/baseline.json"
    with open(scenario_path, 'r') as f:
        scenario_config = json.load(f)
    
    # Add events for demonstration
    scenario_config['events'].extend([
        {"t": "09:15", "type": "medical_event", "venue": "mgm_grand", "severity": 2},
        {"t": "10:30", "type": "suspicious_person", "location": [36.1027, -115.171]},
        {"t": "11:00", "type": "medical_event", "venue": "unlv_cox", "severity": 1},
        {"t": "14:30", "type": "medical_event", "venue": "thomas_mack", "severity": 3},
    ])
    
    print(f"   Scenario: {scenario_config.get('name', 'Unknown')}")
    print(f"   Events: {len(scenario_config.get('events', []))}")
    print()
    
    # Create model
    print("🔧 Creating simulation model...")
    model = SpecialOlympicsModel(scenario_config)
    print(f"   ✅ {len(model.athletes)} athletes, {len(model.volunteers)} volunteers")
    print(f"   ✅ {len(model.hotel_security)} security, {len(model.lvmpd_units)} LVMPD, {len(model.amr_units)} AMR")
    print()
    
    # Create visualization
    print("🎨 Creating 3D visualization...")
    viz = Visualization3D(model, width=1400, height=900)
    viz.initialize_venues()
    viz.initialize_agents()
    viz.set_camera_view("isometric", smooth=False)
    print(f"   ✅ Ready with {len(viz.agent_3d)} agents and {len(viz.venue_markers)} venues")
    print()
    
    # Display
    print("🚀 Displaying 3D scene...")
    print()
    print("💡 Controls:")
    print("   • Click & drag to rotate")
    print("   • Scroll to zoom")
    print("   • Right-click & drag to pan")
    print()
    print("🎨 Legend:")
    print("   🟡 Gold = Athletes | 🔵 Teal = Volunteers | 🟢 Mint = Security")
    print("   🔵 Blue = LVMPD | 🔴 Coral = AMR | 🟣 Purple = Buses")
    print("   ⚠️  Pulsing = Incidents | ✨ Glowing = Venues")
    print()
    print("=" * 70)
    print()
    
    # Display the scene
    viz.display()
    
    # Run simulation
    print("\n🔄 Running simulation (watch the 3D scene update)...")
    print("   Press Ctrl+C to stop\n")
    
    try:
        for i in range(300):
            model.step()
            viz.update()
            
            if (i + 1) % 20 == 0:
                print(f"   Step {i+1:3d} | {model.current_time.strftime('%H:%M:%S')} | "
                      f"Safety: {model.metrics['safety_score']:5.1f} | "
                      f"Incidents: {len(model.active_incidents):2d}")
            
            time.sleep(0.05)
        
        print("\n✅ Simulation complete!")
        print(f"   Final Safety Score: {model.metrics['safety_score']:.1f}/100")
        print(f"   Incidents Resolved: {model.metrics['incidents_resolved']}")
        print(f"   Medical Events: {model.metrics['medical_events_count']}")
        
    except KeyboardInterrupt:
        print("\n\n⏸️  Simulation paused by user")
        print("   The 3D scene is still interactive - explore it!")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\n💡 Make sure you're running this in a Jupyter notebook or JupyterLab")
        print("   The 3D visualization requires a Jupyter environment.")
        print("\n   To run:")
        print("   1. Start Jupyter: jupyter notebook")
        print("   2. Open this file as a notebook, or")
        print("   3. Run: jupyter notebook view_3d_simulation.py")
        import traceback
        traceback.print_exc()

