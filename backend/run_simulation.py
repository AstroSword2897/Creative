"""
Run the Special Olympics Las Vegas simulation with live 3D visualization.
Supports real-time animation in Jupyter notebooks.
"""

import sys
import json
import time
from pathlib import Path
from typing import Optional, Tuple

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from simulation.model import SpecialOlympicsModel
from simulation.visualization_3d import Visualization3D

# Check if running in Jupyter/IPython
try:
    from IPython.display import display, clear_output
    import ipywidgets as widgets
    JUPYTER_AVAILABLE = True
except ImportError:
    JUPYTER_AVAILABLE = False
    clear_output = None
    display = None


def run_simulation(
    scenario_file: str = "scenarios/baseline.json",
    steps: int = 50,
    live_animation: bool = False,
    log_interval: int = 10,
    step_delay: float = 0.0,
    enable_hooks: bool = False
) -> Tuple[Optional[SpecialOlympicsModel], Optional[Visualization3D]]:
    """
    Run simulation with optional live 3D visualization.
    
    Args:
        scenario_file: Path to scenario JSON file (relative or absolute)
        steps: Number of simulation steps to run
        live_animation: Enable live animation in Jupyter (requires IPython)
        log_interval: Log status every N steps (0 = log all steps)
        step_delay: Delay between steps in seconds (0 = run as fast as possible)
        enable_hooks: Enable agent/incident event hooks
    
    Returns:
        Tuple of (model, visualization) or (None, None) on error
    """
    
    print("=" * 60)
    print("Special Olympics Las Vegas Security Simulation")
    print("=" * 60)
    print()
    
    # Resolve scenario path (supports relative and absolute paths)
    scenario_path = Path(scenario_file)
    if not scenario_path.is_absolute():
        scenario_path = Path(__file__).parent / scenario_file
    
    if not scenario_path.exists():
        print(f"❌ Scenario file not found: {scenario_path}")
        print(f"   Tried: {scenario_path.absolute()}")
        return None, None
    
    print(f"📋 Loading scenario: {scenario_path.name}")
    try:
        with open(scenario_path, 'r') as f:
            scenario_config = json.load(f)
    except Exception as e:
        print(f"❌ Error loading scenario: {e}")
        return None, None
    
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
        return None, None
    
    # Create 3D visualization
    print("🎨 Creating 3D visualization...")
    viz = None
    try:
        viz = Visualization3D(model, width=1000, height=700)
        viz.initialize_venues()
        viz.initialize_agents()
        viz.set_camera_view("top_down", smooth=False)
        print(f"   ✅ Visualization created")
        print(f"     - Agent representations: {len(viz.agent_3d)}")
        print(f"     - Venue markers: {len(viz.venue_markers)}")
        
        # Set up event hooks if enabled
        if enable_hooks:
            def on_agent_moved(agent, agent_3d):
                """Hook for agent movement events."""
                if hasattr(agent, 'status') and agent.status == 'emergency':
                    print(f"   🚨 Emergency agent {agent.unique_id} at {agent.current_location}")
            
            def on_incident_triggered(incident, marker):
                """Hook for incident events."""
                print(f"   ⚠️  Incident: {incident.get('type')} at {incident.get('location')}")
            
            viz.on_agent_moved = on_agent_moved
            viz.on_incident_triggered = on_incident_triggered
            print(f"     - Event hooks enabled")
        
        print()
    except Exception as e:
        print(f"   ⚠️  Visualization error (continuing without 3D): {e}")
        if live_animation:
            print(f"   ⚠️  Live animation disabled (visualization unavailable)")
            live_animation = False
        viz = None
    
    # Check if live animation is possible
    if live_animation and not JUPYTER_AVAILABLE:
        print("   ⚠️  Live animation requires IPython/Jupyter. Disabling...")
        live_animation = False
    
    # Run simulation
    print("🚀 Running simulation...")
    if live_animation:
        print("   🎬 Live animation enabled - watch agents move in real-time!")
    if step_delay > 0:
        print(f"   ⏱️  Step delay: {step_delay:.2f}s (realistic timing)")
    if log_interval > 0:
        print(f"   📝 Logging every {log_interval} steps")
    else:
        print(f"   📝 Verbose logging enabled (all steps)")
    print()
    
    # Track statistics
    total_step_time = 0.0
    step_times = []
    previous_incidents = set()
    
    try:
        # Display initial state if live animation
        if live_animation and viz:
            display(viz.render())
        
        for i in range(steps):
            step_start = time.time()
            
            # Step simulation
            continue_sim = model.step()
            
            # Calculate step duration
            step_duration = time.time() - step_start
            total_step_time += step_duration
            step_times.append(step_duration)
            
            # Track new incidents
            current_incident_ids = {inc.get('id', str(inc)) for inc in model.active_incidents}
            new_incidents = current_incident_ids - previous_incidents
            previous_incidents = current_incident_ids.copy()
            
            # Update visualization
            if viz:
                viz.update()
            
            # Live animation update
            if live_animation and viz:
                clear_output(wait=True)
                display(viz.render())
                # Show compact status in output
                progress_pct = ((i + 1) / steps) * 100
                print(f"Step {i+1:3d}/{steps} ({progress_pct:5.1f}%) | "
                      f"Time: {model.current_time.strftime('%H:%M:%S')} | "
                      f"Incidents: {len(model.active_incidents):2d} | "
                      f"Safety: {model.metrics['safety_score']:5.1f} | "
                      f"Step: {step_duration*1000:.1f}ms")
            
            # Print detailed status (respecting log_interval)
            elif log_interval == 0 or (i + 1) % log_interval == 0 or i == 0:
                progress_pct = ((i + 1) / steps) * 100
                progress_bar_length = 30
                filled = int(progress_pct / 100 * progress_bar_length)
                progress_bar = "█" * filled + "░" * (progress_bar_length - filled)
                
                print(f"   Step {i+1:3d}/{steps} [{progress_bar}] {progress_pct:5.1f}%")
                print(f"      ⏰ Time: {model.current_time.strftime('%H:%M:%S')} | "
                      f"⏱️  Step: {step_duration*1000:.1f}ms | "
                      f"📊 Avg: {sum(step_times[-10:])*1000/len(step_times[-10:]):.1f}ms")
                
                # Agent counts
                athlete_count = len(model.athletes)
                volunteer_count = len(model.volunteers)
                security_count = len(model.hotel_security)
                lvmpd_count = len(model.lvmpd_units)
                amr_count = len(model.amr_units)
                bus_count = len(model.buses)
                
                print(f"      👥 Agents: "
                      f"Athletes: {athlete_count:3d} | "
                      f"Volunteers: {volunteer_count:2d} | "
                      f"Security: {security_count:2d} | "
                      f"LVMPD: {lvmpd_count:2d} | "
                      f"AMR: {amr_count:2d} | "
                      f"Buses: {bus_count:2d}")
                
                # Metrics
                print(f"      📈 Metrics: "
                      f"Safety: {model.metrics['safety_score']:5.1f} | "
                      f"Response: {model.metrics['avg_response_time']/60:.1f}m | "
                      f"Containment: {model.metrics['containment_rate']*100:5.1f}%")
                
                # Incidents
                incident_count = len(model.active_incidents)
                medical_count = len(model.medical_events)
                if incident_count > 0 or medical_count > 0:
                    print(f"      🚨 Active: "
                          f"Incidents: {incident_count:2d} | "
                          f"Medical: {medical_count:2d}")
                    
                    # Show new incidents
                    if new_incidents:
                        for inc in model.active_incidents:
                            inc_id = inc.get('id', str(inc))
                            if inc_id in new_incidents:
                                inc_type = inc.get('type', 'unknown')
                                inc_loc = inc.get('location', [0, 0])
                                print(f"         ⚠️  NEW: {inc_type} at ({inc_loc[0]:.3f}, {inc_loc[1]:.3f})")
                
                # Performance summary every 10 logged steps
                if log_interval > 0 and (i + 1) % (log_interval * 10) == 0:
                    avg_step_time = sum(step_times) / len(step_times)
                    min_step_time = min(step_times)
                    max_step_time = max(step_times)
                    print(f"      ⚡ Performance: "
                          f"Avg: {avg_step_time*1000:.1f}ms | "
                          f"Min: {min_step_time*1000:.1f}ms | "
                          f"Max: {max_step_time*1000:.1f}ms")
                
                print()  # Blank line for readability
            
            # Step delay for realistic timing
            if step_delay > 0:
                elapsed = time.time() - step_start
                sleep_time = max(0, step_delay - elapsed)
                if sleep_time > 0:
                    time.sleep(sleep_time)
            
            if not continue_sim:
                print(f"\n   ✅ Simulation completed at step {i+1}")
                break
        
        # Final display if live animation
        if live_animation and viz:
            clear_output(wait=True)
            display(viz.render())
            print("=" * 60)
            print("✅ Simulation Complete")
            print("=" * 60)
        
        # Calculate final statistics
        avg_step_time = total_step_time / len(step_times) if step_times else 0
        total_sim_time = total_step_time
        steps_per_second = len(step_times) / total_sim_time if total_sim_time > 0 else 0
        
        print()
        print("=" * 60)
        print("📊 Final Metrics")
        print("=" * 60)
        print(f"   🎯 Safety Score: {model.metrics['safety_score']:.1f}/100")
        print(f"   ⏱️  Avg Response Time: {model.metrics['avg_response_time']/60:.1f} minutes")
        print(f"   🛡️  Containment Rate: {model.metrics['containment_rate']*100:.1f}%")
        print(f"   🏥 Medical Events: {model.metrics['medical_events_count']}")
        print(f"   ✅ Incidents Resolved: {model.metrics['incidents_resolved']}")
        print(f"   📍 Active Incidents: {len(model.active_incidents)}")
        print()
        print("=" * 60)
        print("⚡ Performance Statistics")
        print("=" * 60)
        print(f"   Total Steps: {len(step_times)}")
        print(f"   Total Time: {total_sim_time:.2f}s")
        print(f"   Avg Step Time: {avg_step_time*1000:.1f}ms")
        if step_times:
            print(f"   Min Step Time: {min(step_times)*1000:.1f}ms")
            print(f"   Max Step Time: {max(step_times)*1000:.1f}ms")
        print(f"   Steps/Second: {steps_per_second:.1f}")
        print()
        
        # Display visualization instructions if not live animation
        if viz and not live_animation:
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
            print("   For live animation, run with:")
            print("     run_simulation(live_animation=True)")
            print()
        
        return model, viz
        
    except KeyboardInterrupt:
        print(f"\n\n   ⏸️  Simulation interrupted by user at step {i+1}")
        if step_times:
            avg_step_time = sum(step_times) / len(step_times)
            print(f"   ⚡ Average step time: {avg_step_time*1000:.1f}ms")
            print(f"   📊 Completed {len(step_times)} steps before interruption")
        return model, viz
    except Exception as e:
        print(f"\n   ❌ Error during simulation at step {i+1 if 'i' in locals() else 'unknown'}: {e}")
        import traceback
        traceback.print_exc()
        if step_times:
            print(f"\n   📊 Completed {len(step_times)} steps before error")
            print(f"   ⚡ Average step time: {sum(step_times)/len(step_times)*1000:.1f}ms")
        return model, viz  # Return what we have so far


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Run Special Olympics simulation with optional live visualization",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run baseline scenario with default settings
  python run_simulation.py
  
  # Run specific scenario for 100 steps
  python run_simulation.py --scenario scenarios/stress_test.json --steps 100
  
  # Run with verbose logging (every step)
  python run_simulation.py --log-interval 1
  
  # Run with realistic timing (1 second per step)
  python run_simulation.py --step-delay 1.0
        """
    )
    parser.add_argument(
        "--scenario",
        type=str,
        default="scenarios/baseline.json",
        help="Scenario file to run (relative or absolute path)"
    )
    parser.add_argument(
        "--steps",
        type=int,
        default=50,
        help="Number of simulation steps"
    )
    parser.add_argument(
        "--live-animation",
        action="store_true",
        help="Enable live animation in Jupyter (requires IPython)"
    )
    parser.add_argument(
        "--log-interval",
        type=int,
        default=10,
        help="Log status every N steps (0 = log all steps)"
    )
    parser.add_argument(
        "--step-delay",
        type=float,
        default=0.0,
        help="Delay between steps in seconds (0 = run as fast as possible)"
    )
    parser.add_argument(
        "--enable-hooks",
        action="store_true",
        help="Enable agent/incident event hooks"
    )
    
    args = parser.parse_args()
    
    result = run_simulation(
        scenario_file=args.scenario,
        steps=args.steps,
        live_animation=args.live_animation,
        log_interval=args.log_interval,
        step_delay=args.step_delay,
        enable_hooks=args.enable_hooks
    )
    
    model, viz = result
    
    if model:
        print("✅ Simulation completed successfully!")
        if viz:
            print("   Visualization available via 'viz' object")
    else:
        print("❌ Simulation failed")
        sys.exit(1)
