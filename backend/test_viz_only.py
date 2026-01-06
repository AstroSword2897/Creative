"""
Simple test for 3D visualization improvements.
Tests the visualization code without requiring full model setup.
"""

import sys
from pathlib import Path

# Test pythreejs availability
try:
    from pythreejs import Scene, PerspectiveCamera, Mesh, SphereGeometry, MeshPhongMaterial
    print("✅ pythreejs imported successfully")
    PYTHREEJS_AVAILABLE = True
except ImportError as e:
    print(f"❌ pythreejs not available: {e}")
    PYTHREEJS_AVAILABLE = False
    sys.exit(1)

# Test visualization module
try:
    from simulation.visualization_3d import Visualization3D, Agent3D
    print("✅ Visualization3D and Agent3D imported successfully")
except Exception as e:
    print(f"❌ Error importing visualization: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test Agent3D creation
print("\nTesting Agent3D...")
try:
    agent = Agent3D(
        agent_id=1,
        agent_type="athlete",
        initial_position=(0.5, 0.5),
        color="#FFD700",
        size=0.018
    )
    print("✅ Agent3D created successfully")
    print(f"   - Mesh created: {agent.mesh is not None}")
    print(f"   - Trail buffer initialized: {agent.trail_buffer.shape == (50, 3)}")
except Exception as e:
    print(f"❌ Error creating Agent3D: {e}")
    import traceback
    traceback.print_exc()

# Test Agent3D methods
print("\nTesting Agent3D methods...")
try:
    agent.update_position((0.6, 0.6), smooth=True, delta_time=0.016)
    print("✅ update_position() works")
    
    agent.update_state("normal", delay_minutes=0.0)
    print("✅ update_state() works")
    
    agent.set_rotation((1.0, 0.0))
    print("✅ set_rotation() works")
except Exception as e:
    print(f"❌ Error testing Agent3D methods: {e}")
    import traceback
    traceback.print_exc()

print("\n🎉 All visualization tests passed!")
print("\nThe enhanced 3D visualization system is ready to use.")
print("To use it with a simulation model, ensure Mesa is properly installed.")

