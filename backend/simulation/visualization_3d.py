"""
High-Performance 3D Visualization system using pythreejs.
Smooth animations, natural visuals, and modular structure.
"""

from typing import Dict, List, Tuple, Any, Optional
import numpy as np
import time

try:
    from pythreejs import (
        Scene, PerspectiveCamera, AmbientLight, DirectionalLight,
        Mesh, BoxGeometry, SphereGeometry, PlaneGeometry, CylinderGeometry,
        MeshStandardMaterial, MeshPhongMaterial, Line, LineBasicMaterial,
        OrbitControls, Group, BufferGeometry, Float32BufferAttribute
    )
    from IPython.display import display
    PYTHREEJS_AVAILABLE = True
except ImportError:
    PYTHREEJS_AVAILABLE = False
    print("Warning: pythreejs not available. Install with: pip install pythreejs")


class Agent3D:
    """Next-gen 3D agent with shared materials, delta-time movement, and preallocated trails."""
    
    # Shared material pool for performance
    shared_materials: Dict[str, Any] = {}
    
    def __init__(
        self,
        agent_id: int,
        agent_type: str,
        initial_position: Tuple[float, float],
        color: str = "#ffffff",
        size: float = 0.02,
        trail_max_len: int = 50
    ):
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.size = size
        self.color = color
        self.mesh = None
        self.glow_mesh = None
        self.trail_line = None
        self.trail_max_len = trail_max_len
        self.trail_buffer = np.zeros((trail_max_len, 3), dtype=np.float32)
        self.trail_count = 0
        self.last_position = np.array([*initial_position, 0.03])
        self.animation_time = 0.0
        self.current_status = "normal"
        
        self._create_mesh(initial_position)
    
    def _get_shared_material(self):
        """Get or create shared material for this agent type."""
        key = f"{self.agent_type}_{self.color}"
        if key not in Agent3D.shared_materials:
            if self.agent_type == "athlete":
                mat = MeshPhongMaterial(
                    color=self.color,
                    emissive=self.color,
                    emissiveIntensity=0.2,
                    shininess=100,
                    specular="#ffffff"
                )
            elif self.agent_type == "bus":
                mat = MeshStandardMaterial(
                    color=self.color,
                    roughness=0.3,
                    metalness=0.7
                )
            elif self.agent_type in ["lvmpd", "amr"]:
                mat = MeshStandardMaterial(
                    color=self.color,
                    roughness=0.4,
                    metalness=0.5
                )
            else:
                mat = MeshPhongMaterial(
                    color=self.color,
                    emissive=self.color,
                    emissiveIntensity=0.15,
                    shininess=80
                )
            Agent3D.shared_materials[key] = mat
        return Agent3D.shared_materials[key]
    
    def _create_mesh(self, position: Tuple[float, float]):
        """Create 3D mesh with shared materials."""
        if not PYTHREEJS_AVAILABLE:
            return
        
        x, y = position
        height = 0.03
        
        # Geometry based on type
        if self.agent_type == "athlete":
            geometry = SphereGeometry(radius=self.size, widthSegments=16, heightSegments=16)
        elif self.agent_type == "bus":
            geometry = BoxGeometry(
                width=self.size * 2.5,
                height=self.size * 1.2,
                depth=self.size * 4
            )
        elif self.agent_type in ["lvmpd", "amr"]:
            geometry = CylinderGeometry(
                radiusTop=self.size * 0.9,
                radiusBottom=self.size,
                height=self.size * 2.5,
                radialSegments=16
            )
        else:
            geometry = BoxGeometry(
                width=self.size * 1.2,
                height=self.size * 2,
                depth=self.size * 1.2
            )
        
        material = self._get_shared_material()
        self.mesh = Mesh(geometry=geometry, material=material)
        self.mesh.position = [x, height, y]
        self.mesh.castShadow = True
        self.mesh.receiveShadow = True
    
    def update_position(self, position: Tuple[float, float], smooth: bool = True, delta_time: float = 0.016):
        """Smooth, delta-time driven movement."""
        if not self.mesh:
            return
        
        target_pos = np.array([position[0], 0.03, position[1]])
        
        if smooth:
            # Delta-time based interpolation
            alpha = min(1.0, 0.25 + delta_time * 10)
            new_pos = self.last_position * (1 - alpha) + target_pos * alpha
        else:
            new_pos = target_pos
        
        self.mesh.position = list(new_pos)
        if self.glow_mesh:
            self.glow_mesh.position = list(new_pos)
        
        # Update trail for athletes only
        if self.agent_type == "athlete":
            self._update_trail(new_pos)
        
        self.last_position = new_pos
        self.animation_time += delta_time
    
    def _update_trail(self, new_pos: np.ndarray):
        """Update trail using preallocated buffer with shift operation."""
        if not PYTHREEJS_AVAILABLE:
            return
        
        # Shift buffer and add new point
        self.trail_buffer = np.roll(self.trail_buffer, -1, axis=0)
        self.trail_buffer[-1] = new_pos + np.array([0, 0.01, 0])  # Slight elevation
        self.trail_count = min(self.trail_count + 1, self.trail_max_len)
        
        # Update or create trail line
        if self.trail_line:
            vertices = self.trail_buffer[-self.trail_count:] if self.trail_count < self.trail_max_len else self.trail_buffer
            self.trail_line.geometry.attributes['position'].array = vertices.flatten()
            self.trail_line.geometry.attributes['position'].needsUpdate = True
        else:
            vertices = self.trail_buffer[-self.trail_count:] if self.trail_count < self.trail_max_len else self.trail_buffer
            geom = BufferGeometry(attributes={
                'position': Float32BufferAttribute(vertices.flatten(), 3)
            })
            mat = LineBasicMaterial(
                color=self.color,
                linewidth=1,
                transparent=True,
                opacity=0.3
            )
            self.trail_line = Line(geometry=geom, material=mat)
    
    def update_state(self, status: str, color: str = None, delay_minutes: float = 0.0):
        """Update visual state with dynamic color and glow effects."""
        if not self.mesh:
            return
        
        # Dynamic color based on delay (for athletes)
        if self.agent_type == "athlete" and delay_minutes > 0:
            if delay_minutes < 5:
                color = "#FFD700"  # Gold
            elif delay_minutes < 15:
                color = "#FFA500"  # Orange
            else:
                color = "#E74C3C"  # Red
        
        if color and color != self.color:
            self.color = color
            # Update material color
            if hasattr(self.mesh.material, 'color'):
                self.mesh.material.color = color
            if hasattr(self.mesh.material, 'emissive'):
                self.mesh.material.emissive = color
        
        # Scale and glow based on status
        scale_map = {"emergency": 1.3, "responding": 1.15, "normal": 1.0}
        scale = scale_map.get(status, 1.0)
        self.mesh.scale = [scale] * 3
        
        # Update emissive intensity for status
        if hasattr(self.mesh.material, 'emissiveIntensity'):
            if status == "emergency":
                self.mesh.material.emissiveIntensity = 0.4
                self._add_glow_effect(0.5)
            elif status == "responding":
                self.mesh.material.emissiveIntensity = 0.25
            else:
                self.mesh.material.emissiveIntensity = 0.2
                if self.glow_mesh:
                    self.mesh.remove(self.glow_mesh)
                    self.glow_mesh = None
        
        self.current_status = status
    
    def _add_glow_effect(self, intensity: float = 0.3):
        """Add subtle glow effect for emphasis."""
        if not PYTHREEJS_AVAILABLE or self.glow_mesh or self.agent_type != "athlete":
            return
        
        geom = SphereGeometry(radius=self.size * 1.3, widthSegments=12, heightSegments=12)
        mat = MeshPhongMaterial(
            color=self.color,
            emissive=self.color,
            emissiveIntensity=intensity,
            transparent=True,
            opacity=0.3,
            side=2  # DoubleSide
        )
        self.glow_mesh = Mesh(geometry=geom, material=mat)
        self.glow_mesh.position = self.mesh.position
        self.mesh.add(self.glow_mesh)
    
    def set_rotation(self, direction: Tuple[float, float]):
        """Rotate agent to face movement direction."""
        if not self.mesh or not direction:
            return
        dx, dy = direction
        self.mesh.rotation = [0, np.arctan2(dy, dx), 0]


class Visualization3D:
    """Next-gen 3D visualization with subgrouped agents, delta-time updates, and smooth camera."""
    
    def __init__(self, model, width: int = 800, height: int = 600):
        self.model = model
        self.width = width
        self.height = height
        
        # Agent storage
        self.agent_3d: Dict[int, Agent3D] = {}
        self.agent_groups: Dict[str, Group] = {}
        
        # Markers
        self.incident_markers = []
        self.venue_markers = []
        
        # Natural color scheme
        self.colors = {
            "athlete": "#FFD700",
            "volunteer": "#4ECDC4",
            "hotel_security": "#95E1D3",
            "lvmpd": "#5DADE2",
            "amr": "#F1948A",
            "bus": "#A569BD",
        }
        
        # Animation state
        self.last_update_time = time.time()
        self.animation_time = 0.0
        
        # Camera transition
        self.camera_target: Optional[Dict] = None
        self.camera_alpha = 0.05
        
        # Toggle settings
        self.show_trails = True
        self.show_incidents = True
        self.show_venues = True
        
        # Scene components
        self.scene = None
        self.camera = None
        self.controls = None
        self.agent_group = None
        self.incident_group = None
        
        # Event hooks
        self.on_agent_moved = None
        self.on_incident_triggered = None
        
        if PYTHREEJS_AVAILABLE:
            self._create_scene()
    
    def _create_scene(self):
        """Create beautiful 3D scene with natural lighting."""
        self.scene = Scene()
        self.scene.background = "#0f0f1e"
        
        # Camera
        self.camera = PerspectiveCamera(
            position=[0.5, 1.2, 0.8],
            fov=60,
            aspect=self.width / self.height,
            near=0.1,
            far=10
        )
        self.camera.lookAt([0.5, 0, 0.5])
        
        # Lighting
        ambient = AmbientLight(color="#ffffff", intensity=0.7)
        directional = DirectionalLight(color="#fff8e1", intensity=0.6, position=[1, 2, 1])
        directional.castShadow = True
        self.scene.add([ambient, directional])
        
        # Ground plane
        ground = Mesh(
            PlaneGeometry(1.0, 1.0),
            MeshStandardMaterial(color="#1a1a2e", roughness=0.9, metalness=0.1)
        )
        ground.rotation = [-np.pi / 2, 0, 0]
        ground.position = [0.5, 0, 0.5]
        ground.receiveShadow = True
        self.scene.add(ground)
        
        # Create agent subgroups for better organization
        self.agent_group = Group()
        self.incident_group = Group()
        
        # Subgroups for each agent type
        for agent_type in ["athlete", "volunteer", "hotel_security", "lvmpd", "amr", "bus"]:
            group = Group()
            self.agent_groups[agent_type] = group
            self.agent_group.add(group)
        
        self.scene.add([self.agent_group, self.incident_group])
        
        # Smooth camera controls
        self.controls = OrbitControls(controlling=self.camera)
        self.controls.enableDamping = True
        self.controls.dampingFactor = 0.08
        self.controls.enableZoom = True
        self.controls.enablePan = True
        self.controls.minDistance = 0.5
        self.controls.maxDistance = 3.0
    
    def _init_agents(self, agents: List, agent_type: str, size_factor: float):
        """Generic agent initializer - DRY principle."""
        if not PYTHREEJS_AVAILABLE:
            return
        
        for agent in agents:
            if agent.current_location:
                agent_3d = Agent3D(
                    agent_id=agent.unique_id,
                    agent_type=agent_type,
                    initial_position=agent.current_location,
                    color=self.colors.get(agent_type, "#ffffff"),
                    size=size_factor
                )
                self.agent_3d[agent.unique_id] = agent_3d
                
                # Add to appropriate subgroup
                if agent_type in self.agent_groups:
                    self.agent_groups[agent_type].add(agent_3d.mesh)
                    if agent_3d.trail_line and self.show_trails:
                        self.agent_groups[agent_type].add(agent_3d.trail_line)
    
    def initialize_agents(self):
        """Initialize all agents using generic function."""
        self._init_agents(self.model.athletes, "athlete", 0.018)
        self._init_agents(self.model.volunteers, "volunteer", 0.012)
        self._init_agents(self.model.hotel_security, "hotel_security", 0.01)
        self._init_agents(self.model.lvmpd_units, "lvmpd", 0.012)
        self._init_agents(self.model.amr_units, "amr", 0.012)
        self._init_agents(self.model.buses, "bus", 0.02)
    
    def initialize_venues(self):
        """Add venue markers to scene."""
        if not PYTHREEJS_AVAILABLE or not self.show_venues:
            return
        
        for venue_id, venue_data in self.model.venues.items():
            x, y = venue_data.get("lat"), venue_data.get("lon")
            height = 0.1
            venue_type = venue_data.get("type", "venue")
            
            if venue_type == "hotel":
                geom = BoxGeometry(0.04, 0.12, 0.04)
                mat = MeshPhongMaterial(
                    color="#FFD700",
                    emissive="#FFA500",
                    emissiveIntensity=0.3,
                    shininess=150,
                    specular="#ffffff"
                )
            elif venue_type == "venue":
                geom = CylinderGeometry(0.025, 0.025, 0.1, 16)
                mat = MeshPhongMaterial(
                    color="#4ECDC4",
                    emissive="#4ECDC4",
                    emissiveIntensity=0.25,
                    shininess=120
                )
            else:
                geom = SphereGeometry(0.018, 16, 16)
                mat = MeshPhongMaterial(
                    color="#ffffff",
                    emissive="#e0e0e0",
                    emissiveIntensity=0.15,
                    shininess=100
                )
            
            marker = Mesh(geom, mat)
            marker.position = [x, height, y]
            marker.castShadow = True
            self.venue_markers.append(marker)
            self.scene.add(marker)
    
    def update(self):
        """Update all agents and incidents with smooth delta-time animations."""
        if not PYTHREEJS_AVAILABLE:
            return
        
        # Calculate delta time
        current_time = time.time()
        delta_time = min(current_time - self.last_update_time, 0.1)
        self.last_update_time = current_time
        self.animation_time += delta_time
        
        # Get all agents
        all_agents = (
            self.model.athletes + self.model.volunteers +
            self.model.hotel_security + self.model.lvmpd_units +
            self.model.amr_units + self.model.buses
        )
        
        # Update agents
        for agent in all_agents:
            if agent.unique_id in self.agent_3d and agent.current_location:
                agent_3d = self.agent_3d[agent.unique_id]
                
                # Update position
                agent_3d.update_position(agent.current_location, delta_time=delta_time)
                
                # Update state
                status = getattr(agent, "status", "normal")
                delay_minutes = 0.0
                if hasattr(agent, "delay_minutes"):
                    delay_minutes = agent.delay_minutes
                elif hasattr(self.model, "scheduler"):
                    schedule_metrics = self.model.scheduler.get_schedule_metrics(agent.unique_id)
                    delay_minutes = schedule_metrics.get("total_delay_minutes", 0.0)
                
                agent_3d.update_state(status, delay_minutes=delay_minutes)
                
                # Event hook
                if self.on_agent_moved:
                    self.on_agent_moved(agent, agent_3d)
        
        # Update incidents with delta-time animation
        if self.show_incidents:
            self._update_incidents()
            self._animate_incidents(delta_time)
        
        # Smooth camera transition
        if self.camera_target:
            cp = np.array(self.camera.position)
            tp = np.array(self.camera_target["position"])
            new_pos = cp * (1 - self.camera_alpha) + tp * self.camera_alpha
            self.camera.position = list(new_pos)
            self.camera.lookAt(self.camera_target["lookAt"])
            
            # Check if transition complete
            if np.linalg.norm(new_pos - tp) < 0.01:
                self.camera_target = None
        
        # Update controls
        if self.controls:
            self.controls.update()
    
    def _update_incidents(self):
        """Update incident markers."""
        if not PYTHREEJS_AVAILABLE:
            return
        
        # Remove old markers
        for marker in self.incident_markers:
            self.incident_group.remove(marker)
        self.incident_markers.clear()
        
        # Add new markers
        for incident in getattr(self.model, "active_incidents", []):
            loc = incident.get("location")
            if not loc:
                continue
            
            x, y = loc
            incident_type = incident.get("type", "")
            
            # Color mapping
            color_map = {
                "suspicious_person": "#F1948A",
                "medical_event": "#F8B88B"
            }
            color = color_map.get(incident_type, "#F7DC6F")
            
            geom = SphereGeometry(0.015, 16, 16)
            mat = MeshPhongMaterial(
                color=color,
                emissive=color,
                emissiveIntensity=0.3,
                transparent=True,
                opacity=0.85,
                shininess=100
            )
            marker = Mesh(geom, mat)
            marker.position = [x, 0.15, y]
            marker.castShadow = True
            
            self.incident_markers.append(marker)
            self.incident_group.add(marker)
            
            # Event hook
            if self.on_incident_triggered:
                self.on_incident_triggered(incident, marker)
    
    def _animate_incidents(self, delta_time: float):
        """Animate incident markers with delta-time driven pulsing."""
        for marker in self.incident_markers:
            # Continuous pulsing
            pulse = np.sin(2 * np.pi * self.animation_time * 1.5)
            scale = 1.0 + 0.15 * pulse
            marker.scale = [scale] * 3
            
            # Pulsing glow
            if hasattr(marker.material, 'emissiveIntensity'):
                marker.material.emissiveIntensity = 0.3 + 0.1 * pulse
    
    def set_camera_target(self, target_view: Dict, alpha: float = 0.05):
        """Set camera target for smooth non-blocking transition."""
        self.camera_target = target_view
        self.camera_alpha = alpha
    
    def set_camera_view(self, view_type: str = "top_down", smooth: bool = True):
        """Set camera to specific view."""
        view = self.get_camera_view(view_type)
        if smooth:
            self.set_camera_target(view)
        else:
            self.camera.position = view["position"]
            self.camera.lookAt(view["lookAt"])
            self.camera_target = None
    
    def get_camera_view(self, view_type: str = "top_down") -> Dict:
        """Get camera position for different views."""
        views = {
            "top_down": {"position": [0.5, 1.8, 0.5], "lookAt": [0.5, 0, 0.5]},
            "isometric": {"position": [0.7, 0.9, 0.7], "lookAt": [0.5, 0, 0.5]},
            "cinematic": {"position": [0.4, 0.6, 0.8], "lookAt": [0.5, 0, 0.5]},
        }
        return views.get(view_type, views["top_down"])
    
    def toggle_trails(self, show: bool = None):
        """Toggle trail visibility."""
        self.show_trails = not self.show_trails if show is None else show
        for agent_3d in self.agent_3d.values():
            if agent_3d.trail_line:
                agent_3d.trail_line.visible = self.show_trails
    
    def toggle_incidents(self, show: bool = None):
        """Toggle incident marker visibility."""
        self.show_incidents = not self.show_incidents if show is None else show
        self.incident_group.visible = self.show_incidents
    
    def toggle_venues(self, show: bool = None):
        """Toggle venue marker visibility."""
        self.show_venues = not self.show_venues if show is None else show
        for marker in self.venue_markers:
            marker.visible = self.show_venues
    
    def toggle_agent_type(self, agent_type: str, show: bool = None):
        """Toggle visibility of specific agent type."""
        if agent_type in self.agent_groups:
            if show is None:
                show = not self.agent_groups[agent_type].visible
            self.agent_groups[agent_type].visible = show
    
    def render(self):
        """Render the 3D scene."""
        return self.scene if PYTHREEJS_AVAILABLE else None
    
    def display(self):
        """Display the 3D visualization."""
        if not PYTHREEJS_AVAILABLE:
            print("pythreejs not available. Install with: pip install pythreejs")
            return
        display(self.scene)
