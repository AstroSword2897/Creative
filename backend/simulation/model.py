"""
Main simulation model for Special Olympics Las Vegas.
Coordinates agents, events, and metrics.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
import random
import asyncio
from mesa import Model
from mesa.space import ContinuousSpace

# Mesa 3.x compatibility - create simple scheduler
class RandomActivation:
    """Simple random activation scheduler for Mesa 3.x compatibility."""
    def __init__(self, model):
        self.model = model
        self.agents = []
    
    def add(self, agent):
        """Add agent to scheduler."""
        self.agents.append(agent)
    
    def step(self):
        """Step all agents in random order."""
        import random
        random.shuffle(self.agents)
        for agent in self.agents:
            if hasattr(agent, 'step'):
                try:
                    agent.step()
                except Exception as e:
                    # Log but don't crash - allow simulation to continue
                    import warnings
                    warnings.warn(f"Error in agent {getattr(agent, 'unique_id', 'unknown')} step(): {e}")

from .agents import (
    Athlete, Volunteer, HotelSecurity, LVMPDUnit, AMRUnit, Bus, SecurityCommandCenter
)
from .route_planner import RoutePlanner
from .scheduling import DynamicScheduler
from .alert_prioritization import GlobalAlertManager
from .analytics import AnalyticsEngine
from .graph_routing import RoutingGraph


class SpecialOlympicsModel(Model):
    """Main simulation model."""
    
    def __init__(self, scenario_config: Dict[str, Any]):
        super().__init__()
        
        # Time management
        self.start_time = datetime.strptime(
            scenario_config.get("start_time", "2024-06-01 08:00:00"),
            "%Y-%m-%d %H:%M:%S"
        )
        self.current_time = self.start_time
        self.step_duration = timedelta(seconds=scenario_config.get("step_duration_seconds", 10))
        self.end_time = self.start_time + timedelta(
            hours=scenario_config.get("duration_hours", 8)
        )
        
        # Random seed
        random.seed(scenario_config.get("seed", 42))
        
        # Weather
        self.weather = scenario_config.get("weather", {"temp_C": 25, "heat_alert": False})
        
        # Venues
        self.venues = scenario_config.get("venues", {})
        
        # Space (continuous 2D space for Las Vegas area)
        # Normalize coordinates: Las Vegas area is roughly 36.0-36.2 lat, -115.3 to -115.1 lon
        # Map to 0-1 space for simulation
        self.lat_min, self.lat_max = 36.0, 36.2
        self.lon_min, self.lon_max = -115.3, -115.1
        
        self.space = ContinuousSpace(
            x_max=1.0, y_max=1.0, torus=False
        )
        
        # Scheduler
        self.schedule = RandomActivation(self)
        
        # Route planner (legacy - kept for compatibility)
        self.route_planner = RoutePlanner(self.venues)
        
        # Enhanced systems
        self.graph_router = RoutingGraph(self.venues)
        self.scheduler = DynamicScheduler(self)
        self.alert_manager = GlobalAlertManager(self)
        self.analytics = AnalyticsEngine(self, grid_size=20)
        
        # Agent tracking
        self.athletes = []
        self.volunteers = []
        self.hotel_security = []
        self.lvmpd_units = []
        self.amr_units = []
        self.buses = []
        self.command_center = None
        
        # Simulation state tracking (for Mesa 3.x compatibility)
        self._should_continue = True
        
        # Events and incidents
        self.scheduled_events = scenario_config.get("events", [])
        self.active_incidents = []
        self.active_alerts = {}  # hotel_id -> list of alerts
        self.medical_events = []
        self.completed_transports = []
        
        # Metrics
        self.metrics = {
            "safety_score": 100.0,
            "avg_response_time": 0.0,
            "containment_rate": 1.0,
            "athlete_delay_minutes": 0.0,
            "accessibility_coverage": 1.0,
            "medical_events_count": 0,
            "incidents_resolved": 0,
            # ✅ ENHANCED: Additional real-time metrics
            "avg_venue_density": 0.0,
            "max_venue_density": 0.0,
            "athletes_per_hour": 0.0,
            "avg_incident_age_seconds": 0.0,
        }
        
        # Access control
        self.access_control = scenario_config.get("access_control", {})
        
        # Initialize agents
        self._initialize_agents(scenario_config.get("agents", {}))
        
        # Initialize scheduled events
        self._initialize_events()
        
        # Hospital locations (hardcoded for now)
        self.hospitals = [
            (36.1447, -115.1481),  # UMC
            (36.1694, -115.1231),  # Sunrise Hospital
        ]
    
    def _normalize_coords(self, lat: float, lon: float) -> Tuple[float, float]:
        """Normalize lat/lon coordinates to 0-1 space."""
        x = (lon - self.lon_min) / (self.lon_max - self.lon_min)
        y = (lat - self.lat_min) / (self.lat_max - self.lat_min)
        return (x, y)
    
    def _denormalize_coords(self, x: float, y: float) -> Tuple[float, float]:
        """Convert 0-1 coordinates back to lat/lon."""
        lat = y * (self.lat_max - self.lat_min) + self.lat_min
        lon = x * (self.lon_max - self.lon_min) + self.lon_min
        return (lat, lon)
    
    def _initialize_agents(self, agent_config: Dict):
        """Initialize all agents based on scenario config."""
        agent_id = 0
        
        # Athletes
        athlete_count = agent_config.get("athletes", 0)
        for i in range(athlete_count):
            athlete = Athlete(
                unique_id=agent_id,
                model=self,
                mobility=random.choice(["walking", "walking", "wheelchair", "assisted"]),
                medical_risk=random.uniform(0.05, 0.2),
            )
            # Start at airport (Harry Reid International)
            if "harry_reid_airport" in self.venues:
                airport = self.venues["harry_reid_airport"]
                athlete.current_location = (airport["lat"], airport["lon"])
            elif "las_airport" in self.venues:  # Legacy support
                airport = self.venues["las_airport"]
                athlete.current_location = (airport["lat"], airport["lon"])
            # Normalize coordinates for space
            athlete.pos = self._normalize_coords(athlete.current_location[0], athlete.current_location[1])
            self.athletes.append(athlete)
            self.schedule.add(athlete)
            self.space.place_agent(athlete, athlete.pos)
            agent_id += 1
        
        # Volunteers
        volunteer_count = agent_config.get("volunteers", 0)
        for i in range(volunteer_count):
            volunteer = Volunteer(
                unique_id=agent_id,
                model=self,
                assignment=random.choice(["general", "venue", "transport"]),
            )
            # Random initial location (normalized)
            volunteer.pos = (
                random.uniform(0.3, 0.7),
                random.uniform(0.3, 0.7)
            )
            volunteer.current_location = self._denormalize_coords(volunteer.pos[0], volunteer.pos[1])
            self.volunteers.append(volunteer)
            self.schedule.add(volunteer)
            self.space.place_agent(volunteer, volunteer.pos)
            agent_id += 1
        
        # Hotel Security
        hotel_security_count = agent_config.get("hotel_rovers", 0)
        for i in range(hotel_security_count):
            hotel_id = f"hotel_{i % 3}"  # Distribute across hotels
            security = HotelSecurity(
                unique_id=agent_id,
                model=self,
                hotel_id=hotel_id,
            )
            # Start at hotel
            hotel_key = f"{hotel_id}_hotel"
            if hotel_key in self.venues:
                hotel = self.venues[hotel_key]
                security.current_location = (hotel["lat"], hotel["lon"])
                security.pos = self._normalize_coords(hotel["lat"], hotel["lon"])
            else:
                security.pos = (random.uniform(0.4, 0.6), random.uniform(0.4, 0.6))
                security.current_location = self._denormalize_coords(security.pos[0], security.pos[1])
            self.hotel_security.append(security)
            self.schedule.add(security)
            self.space.place_agent(security, security.pos)
            agent_id += 1
        
        # LVMPD Units
        lvmpd_count = agent_config.get("lvmpd_units", 0)
        for i in range(lvmpd_count):
            unit = LVMPDUnit(
                unique_id=agent_id,
                model=self,
            )
            # Start at central location (normalized)
            unit.pos = (0.5, 0.5)
            unit.current_location = self._denormalize_coords(0.5, 0.5)
            self.lvmpd_units.append(unit)
            self.schedule.add(unit)
            self.space.place_agent(unit, unit.pos)
            agent_id += 1
        
        # AMR Units
        amr_count = agent_config.get("amr_units", 0)
        for i in range(amr_count):
            unit = AMRUnit(
                unique_id=agent_id,
                model=self,
            )
            # Start at central location (normalized)
            unit.pos = (0.5, 0.5)
            unit.current_location = self._denormalize_coords(0.5, 0.5)
            self.amr_units.append(unit)
            self.schedule.add(unit)
            self.space.place_agent(unit, unit.pos)
            agent_id += 1
        
        # Buses
        bus_count = agent_config.get("buses", 0)
        for i in range(bus_count):
            # Create route between airport and venues
            route = []
            airport_key = "harry_reid_airport" if "harry_reid_airport" in self.venues else "las_airport"
            if airport_key in self.venues and "unlv_cox" in self.venues:
                airport = self.venues[airport_key]
                venue = self.venues["unlv_cox"]
                route = [
                    (airport["lat"], airport["lon"]),
                    (venue["lat"], venue["lon"]),
                ]
            bus = Bus(
                unique_id=agent_id,
                model=self,
                route=route,
            )
            if route:
                bus.current_location = route[0]
                bus.pos = self._normalize_coords(route[0][0], route[0][1])
            self.buses.append(bus)
            self.schedule.add(bus)
            if bus.current_location:
                self.space.place_agent(bus, bus.pos)
            agent_id += 1
        
        # Initialize Security Command Center
        command_center = SecurityCommandCenter(
            unique_id=agent_id,
            model=self,
            location=(0.5, 0.5),  # Central location (normalized)
        )
        self.command_center = command_center
        command_center.pos = (0.5, 0.5)  # Already normalized
        command_center.current_location = self._denormalize_coords(0.5, 0.5)
        self.schedule.add(command_center)
        self.space.place_agent(command_center, command_center.pos)
    
    def _initialize_events(self):
        """Initialize scheduled events."""
        # Events will be processed during step()
        pass
    
    def step(self):
        """Advance simulation by one step with enhanced dynamics."""
        # Advance time
        self.current_time += self.step_duration
        
        # Process scheduled events
        self._process_scheduled_events()
        
        # ✅ ENHANCED: Check for dynamic event generation (crowd-based incidents)
        self._check_dynamic_events()
        
        # Step all agents
        self.schedule.step()
        
        # ✅ ENHANCED: Update crowd dynamics and congestion effects
        self._update_crowd_dynamics()
        
        # Update enhanced systems
        self.alert_manager.update_all_alerts()
        self.analytics.record_step()
        
        # Update metrics
        self._update_metrics()
        
        # Check if simulation should end (Mesa 3.x wraps step() and doesn't return value)
        if self.current_time >= self.end_time:
            self._should_continue = False
        else:
            self._should_continue = True
    
    def should_continue(self) -> bool:
        """Check if simulation should continue (Mesa 3.x compatibility)."""
        return self._should_continue
    
    def _process_scheduled_events(self):
        """Process events scheduled for current time."""
        current_time_str = self.current_time.strftime("%H:%M")
        
        # Process events safely without modifying list while iterating
        events_to_process = []
        for event in self.scheduled_events:
            event_time = event.get("t", "")
            if event_time == current_time_str or abs(
                (datetime.strptime(f"2024-06-01 {event_time}", "%Y-%m-%d %H:%M") - self.current_time).total_seconds()
            ) < self.step_duration.total_seconds():
                events_to_process.append(event)
        
        # Process and remove events
        for event in events_to_process:
            self._handle_event(event)
            if event in self.scheduled_events:
                self.scheduled_events.remove(event)
    
    def _handle_event(self, event: Dict):
        """Handle a scheduled event."""
        event_type = event.get("type")
        
        if event_type == "arrival_batch":
            count = event.get("count", 0)
            self._spawn_athletes_at_airport(count)
        
        elif event_type == "event_start":
            venue = event.get("venue")
            # Trigger athletes to move to venue
            for athlete in self.athletes:
                if athlete.status == "waiting" and venue in self.venues:
                    athlete.target_location = (
                        self.venues[venue]["lat"],
                        self.venues[venue]["lon"]
                    )
                    athlete.status = "traveling"
                    athlete._plan_route()
        
        elif event_type == "medical_event":
            venue = event.get("venue")
            severity = event.get("severity", 1)
            self._trigger_medical_event_at_venue(venue, severity)
        
        elif event_type == "suspicious_person":
            location = event.get("location")
            self._trigger_suspicious_person(location)
    
    def _spawn_athletes_at_airport(self, count: int):
        """Spawn new athletes at airport (Harry Reid International)."""
        airport_key = "harry_reid_airport" if "harry_reid_airport" in self.venues else "las_airport"
        if airport_key not in self.venues:
            return
        
        airport = self.venues[airport_key]
        airport_loc = (airport["lat"], airport["lon"])
        
        max_id = max([a.unique_id for a in self.athletes] + [0])
        
        for i in range(count):
            athlete = Athlete(
                unique_id=max_id + i + 1,
                model=self,
                mobility=random.choice(["walking", "walking", "wheelchair", "assisted"]),
                medical_risk=random.uniform(0.05, 0.2),
            )
            athlete.current_location = airport_loc
            athlete.pos = self._normalize_coords(airport_loc[0], airport_loc[1])
            athlete.status = "waiting"
            self.athletes.append(athlete)
            self.schedule.add(athlete)
            self.space.place_agent(athlete, athlete.pos)
    
    def _trigger_medical_event_at_venue(self, venue: str, severity: int):
        """Trigger medical event at specific venue."""
        if venue not in self.venues:
            return
        
        venue_loc = (self.venues[venue]["lat"], self.venues[venue]["lon"])
        nearby_athletes = self.get_agents_near(venue_loc, 0.01, agent_type=Athlete)
        
        if nearby_athletes:
            athlete = random.choice(nearby_athletes)
            athlete.medical_event = True
            athlete.status = "emergency"
            self.trigger_medical_event(athlete)
    
    def _trigger_suspicious_person(self, location: Tuple[float, float]):
        """Trigger suspicious person incident."""
        incident = {
            "id": f"incident_{len(self.active_incidents)}",
            "type": "suspicious_person",
            "location": location,
            "reported_by": "volunteer",
            "timestamp": self.current_time,
        }
        self.active_incidents.append(incident)
        
        # Dispatch nearest LVMPD unit
        self._dispatch_lvmpd(incident)
    
    def trigger_medical_event(self, athlete: Athlete):
        """Handle medical event for athlete."""
        self.medical_events.append({
            "id": f"med_{len(self.medical_events)}",
            "athlete_id": athlete.unique_id,
            "location": athlete.current_location,
            "timestamp": self.current_time,
        })
        self.metrics["medical_events_count"] += 1
        
        # Dispatch nearest AMR unit
        self._dispatch_amr(athlete)
        
        # Assign volunteer if available
        self._assign_volunteer(athlete)
    
    def _dispatch_amr(self, athlete: Athlete):
        """Dispatch nearest available AMR unit."""
        if not athlete.current_location:
            return
        
        available_units = [u for u in self.amr_units if u.status == "available"]
        if not available_units:
            return
        
        # Find nearest
        nearest = min(
            available_units,
            key=lambda u: self._distance(
                u.current_location or (0.5, 0.5),
                athlete.current_location
            ) if u.current_location else float('inf')
        )
        
        nearest.status = "dispatched"
        nearest.current_patient = athlete
        nearest.current_location = nearest.current_location or (0.5, 0.5)
    
    def _dispatch_lvmpd(self, incident: Dict):
        """Dispatch nearest LVMPD unit to incident."""
        incident_loc = incident.get("location")
        if not incident_loc:
            return
        
        available_units = [u for u in self.lvmpd_units if u.status == "available"]
        if not available_units:
            return
        
        nearest = min(
            available_units,
            key=lambda u: self._distance(
                u.current_location or (0.5, 0.5),
                incident_loc
            ) if u.current_location else float('inf')
        )
        
        nearest.status = "dispatched"
        nearest.current_incident = incident
        nearest.dispatch_start_time = self.current_time
    
    def _assign_volunteer(self, athlete: Athlete):
        """Assign volunteer to assist athlete."""
        available = [v for v in self.volunteers if v.status == "patrolling"]
        if not available:
            return
        
        nearest = min(
            available,
            key=lambda v: self._distance(
                v.current_location or (0.5, 0.5),
                athlete.current_location
            ) if v.current_location else float('inf')
        )
        
        nearest.status = "responding"
        nearest.current_assignment = {
            "athlete": athlete,
            "location": athlete.current_location,
        }
    
    def get_nearest_hospital(self, location: Tuple[float, float]) -> Tuple[float, float]:
        """Get nearest hospital to location."""
        return min(
            self.hospitals,
            key=lambda h: self._distance(location, h)
        )
    
    def get_agents_near(self, location: Tuple[float, float], radius: float, agent_type=None) -> List:
        """Get agents near a location."""
        nearby = []
        for agent in self.schedule.agents:
            if agent_type and not isinstance(agent, agent_type):
                continue
            if hasattr(agent, 'current_location') and agent.current_location:
                dist = self._distance(location, agent.current_location)
                if dist <= radius:
                    nearby.append(agent)
        return nearby
    
    def get_active_alert(self, hotel_id: str) -> Optional[Dict]:
        """Get active alert for hotel."""
        alerts = self.active_alerts.get(hotel_id, [])
        return alerts[0] if alerts else None
    
    def resolve_alert(self, hotel_id: str, alert_id: str):
        """Resolve alert."""
        alerts = self.active_alerts.get(hotel_id, [])
        self.active_alerts[hotel_id] = [a for a in alerts if a.get("id") != alert_id]
    
    def resolve_incident(self, incident_id: str):
        """Resolve incident."""
        self.active_incidents = [i for i in self.active_incidents if i.get("id") != incident_id]
        self.metrics["incidents_resolved"] += 1
    
    def complete_medical_transport(self, athlete_id: int):
        """Complete medical transport."""
        self.completed_transports.append({
            "athlete_id": athlete_id,
            "timestamp": self.current_time,
        })
    
    def validate_access_token(self, token: str, location: str) -> bool:
        """Validate access token (simulated)."""
        if not self.access_control.get("athlete_badge_required", False):
            return True
        
        # Check if token is valid athlete badge
        if token.startswith("ATH_"):
            return True
        
        # Invalid token - trigger alert
        hotel_id = location.split("_")[0] if "_" in location else "unknown"
        hotel_venue = self.venues.get(f"{hotel_id}_hotel", {})
        alert = {
            "id": f"alert_{len(self.active_alerts.get(hotel_id, []))}",
            "type": "access_denied",
            "location": (hotel_venue.get("lat", 36.1), hotel_venue.get("lon", -115.15)),
            "timestamp": self.current_time,
        }
        if hotel_id not in self.active_alerts:
            self.active_alerts[hotel_id] = []
        self.active_alerts[hotel_id].append(alert)
        
        # Dispatch security
        for security in self.hotel_security:
            if security.hotel_id == hotel_id and security.status == "patrolling":
                security.status = "responding"
                break
        
        return False
    
    def _update_metrics(self):
        """Update computed metrics with enhanced security metrics."""
        # Safety score (simplified)
        base_score = 100.0
        
        # Penalties
        if self.active_incidents:
            base_score -= len(self.active_incidents) * 5
        
        if self.medical_events:
            base_score -= len([e for e in self.medical_events if e not in self.completed_transports]) * 3
        
        # Enhanced response time calculation from security units
        all_response_times = []
        for lvmpd in self.lvmpd_units:
            if hasattr(lvmpd, 'response_times') and lvmpd.response_times:
                all_response_times.extend([r["time"] for r in lvmpd.response_times])
        
        for security in self.hotel_security:
            if hasattr(security, 'response_times') and security.response_times:
                all_response_times.extend(security.response_times)
        
        if all_response_times:
            self.metrics["avg_response_time"] = sum(all_response_times) / len(all_response_times)
        elif self.completed_transports:
            # Fallback: assume 5 min average
            self.metrics["avg_response_time"] = 300.0
        else:
            self.metrics["avg_response_time"] = 0.0
        
        self.metrics["safety_score"] = max(0.0, base_score)
        
        # Containment rate
        total_incidents = len(self.active_incidents) + len(self.medical_events)
        resolved = self.metrics["incidents_resolved"] + len(self.completed_transports)
        if total_incidents > 0:
            self.metrics["containment_rate"] = resolved / total_incidents
        else:
            self.metrics["containment_rate"] = 1.0
        
        # Security-specific metrics
        if self.command_center:
            cmd_metrics = self.command_center.get_command_center_metrics()
            self.metrics["security_hotspots"] = cmd_metrics.get("hotspots_identified", 0)
            self.metrics["active_threats"] = cmd_metrics.get("active_threats", 0)
        
        # Security coverage metrics
        security_coverage = 0.0
        if self.hotel_security:
            avg_threat_level = sum(
                s.threat_level for s in self.hotel_security
                if hasattr(s, 'threat_level')
            ) / len(self.hotel_security)
            security_coverage = 1.0 - avg_threat_level  # Higher coverage = lower threat
        
        self.metrics["security_coverage"] = max(0.0, min(1.0, security_coverage))
        
        # ✅ ENHANCED: Real-time crowd density metrics
        total_agents = len(self.athletes) + len(self.volunteers) + len(self.hotel_security)
        if total_agents > 0:
            # Calculate average crowd density at key venues
            venue_densities = []
            for venue_key, venue_data in self.venues.items():
                venue_loc = (venue_data["lat"], venue_data["lon"])
                nearby = self.get_agents_near(venue_loc, 0.02)
                density = len(nearby) / max(1, venue_data.get("capacity", 100))
                venue_densities.append(density)
            
            if venue_densities:
                self.metrics["avg_venue_density"] = sum(venue_densities) / len(venue_densities)
                self.metrics["max_venue_density"] = max(venue_densities)
            else:
                self.metrics["avg_venue_density"] = 0.0
                self.metrics["max_venue_density"] = 0.0
        
        # ✅ ENHANCED: Throughput metrics (athletes processed per hour)
        step_hours = self.step_duration.total_seconds() / 3600.0
        if step_hours > 0:
            athletes_at_venues = sum(1 for a in self.athletes if a.status == "at_venue")
            self.metrics["athletes_per_hour"] = athletes_at_venues / (step_hours * max(1, (self.current_time - self.start_time).total_seconds() / 3600.0))
        
        # ✅ ENHANCED: Response efficiency (time from incident to resolution)
        if self.active_incidents:
            avg_age = sum(
                (self.current_time - inc.get("timestamp", self.current_time)).total_seconds()
                for inc in self.active_incidents
                if isinstance(inc.get("timestamp"), datetime)
            ) / len(self.active_incidents)
            self.metrics["avg_incident_age_seconds"] = avg_age
        else:
            self.metrics["avg_incident_age_seconds"] = 0.0
    
    def _check_dynamic_events(self):
        """✅ ENHANCED: Generate dynamic events based on crowd density and conditions."""
        # Check for crowd-based incidents (high density areas)
        for venue_key, venue_data in self.venues.items():
            venue_loc = (venue_data["lat"], venue_data["lon"])
            nearby_athletes = self.get_agents_near(venue_loc, 0.02, agent_type=Athlete)
            
            # High crowd density can trigger incidents
            if len(nearby_athletes) > venue_data.get("capacity", 100) * 0.8:
                # 5% chance per step of crowd-related incident
                if random.random() < 0.05 * (self.step_duration.total_seconds() / 60.0):
                    self._trigger_crowd_incident(venue_key, venue_loc)
        
        # Weather-based dynamic events
        weather = self.weather
        if weather.get("temp_C", 20) > 38:
            # Extreme heat increases medical event probability
            for athlete in self.athletes:
                if athlete.status in ["traveling", "at_venue"] and not athlete.medical_event:
                    heat_risk = (weather["temp_C"] - 38) * 0.01
                    if random.random() < heat_risk * (self.step_duration.total_seconds() / 3600.0):
                        athlete.medical_event = True
                        athlete.status = "emergency"
                        self.trigger_medical_event(athlete)
    
    def _trigger_crowd_incident(self, venue_key: str, location: Tuple[float, float]):
        """Trigger a crowd-related incident."""
        incident_types = ["crowd_congestion", "access_control_issue", "lost_person"]
        incident_type = random.choice(incident_types)
        
        incident = {
            "id": f"crowd_{len(self.active_incidents)}",
            "type": incident_type,
            "location": location,
            "venue": venue_key,
            "reported_by": "crowd_monitoring",
            "timestamp": self.current_time,
            "severity": "medium",
        }
        self.active_incidents.append(incident)
        
        # Dispatch security if available
        self._dispatch_lvmpd(incident)
        
        # Create alert
        if hasattr(self, 'alert_manager'):
            asyncio.create_task(self.alert_manager.register_alert(
                alert_id=incident["id"],
                alert_type=incident_type,
                location=location,
                timestamp=self.current_time,
                metadata={"venue": venue_key, "severity": "medium"}
            ))
    
    def _update_crowd_dynamics(self):
        """✅ ENHANCED: Update crowd dynamics and apply congestion effects to agents."""
        # Calculate congestion at key locations
        congestion_map = {}
        
        for venue_key, venue_data in self.venues.items():
            venue_loc = (venue_data["lat"], venue_data["lon"])
            nearby = self.get_agents_near(venue_loc, 0.02)
            capacity = venue_data.get("capacity", 100)
            congestion = min(1.0, len(nearby) / capacity)
            congestion_map[venue_key] = congestion
        
        # Apply congestion effects to athletes (slow movement in crowded areas)
        for athlete in self.athletes:
            if athlete.status == "traveling" and athlete.current_location:
                # Find nearest venue
                nearest_venue = None
                min_dist = float('inf')
                for venue_key, venue_data in self.venues.items():
                    venue_loc = (venue_data["lat"], venue_data["lon"])
                    dist = self._distance(athlete.current_location, venue_loc)
                    if dist < min_dist and dist < 0.02:
                        min_dist = dist
                        nearest_venue = venue_key
                
                if nearest_venue and nearest_venue in congestion_map:
                    congestion = congestion_map[nearest_venue]
                    # Reduce speed based on congestion (0-30% reduction)
                    speed_multiplier = 1.0 - (congestion * 0.3)
                    athlete.walking_speed = athlete._get_speed() * speed_multiplier
    
    def _distance(self, p1: Tuple[float, float], p2: Tuple[float, float]) -> float:
        """Calculate distance between two points."""
        return ((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)**0.5
    
    def get_state(self) -> Dict:
        """Get current simulation state for API."""
        # Helper to ensure JSON serializable
        def make_serializable(obj):
            """Convert objects to JSON-serializable format."""
            if isinstance(obj, tuple):
                return list(obj)
            elif isinstance(obj, dict):
                return {str(k): make_serializable(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [make_serializable(item) for item in obj]
            elif hasattr(obj, 'isoformat'):  # datetime
                return obj.isoformat()
            else:
                return obj
        
        # Helper to get normalized location (frontend expects [0-1] coordinates)
        def get_normalized_location(agent):
            """Get normalized position for frontend - use pos if available, otherwise normalize current_location."""
            if hasattr(agent, 'pos') and agent.pos:
                return list(agent.pos)
            elif hasattr(agent, 'current_location') and agent.current_location:
                # Fallback: normalize current_location
                return list(self._normalize_coords(agent.current_location[0], agent.current_location[1]))
            else:
                # Last resort: return center
                return [0.5, 0.5]
        
        # Serialize command center data
        command_center_data = None
        if self.command_center:
            # Convert threat_map tuples to lists
            threat_map_serialized = {
                str(list(k)): v for k, v in self.command_center.threat_map.items()
            }
            # Convert hotspots location tuples to lists
            hotspots_serialized = [
                {
                    "location": list(self._normalize_coords(h["location"][0], h["location"][1])) if isinstance(h["location"], (tuple, list)) and len(h["location"]) == 2 else h.get("location", [0.5, 0.5]),
                    "threat_level": h["threat_level"],
                }
                for h in self.command_center.hotspots
            ]
            command_center_data = {
                "location": get_normalized_location(self.command_center),  # ✅ Send normalized coordinates
                "threat_map": threat_map_serialized,
                "hotspots": hotspots_serialized,
            }
        
        return {
            "time": self.current_time.isoformat(),
            "agents": {
                "athletes": [
                    {
                        "id": a.unique_id,
                        "type": "athlete",
                        "location": get_normalized_location(a),  # ✅ Send normalized coordinates
                        "status": a.status,
                        "medical_event": a.medical_event,
                    }
                    for a in self.athletes if hasattr(a, 'pos') or (hasattr(a, 'current_location') and a.current_location)
                ],
                "volunteers": [
                    {
                        "id": v.unique_id,
                        "type": "volunteer",
                        "location": get_normalized_location(v),  # ✅ Send normalized coordinates
                        "status": v.status,
                    }
                    for v in self.volunteers if hasattr(v, 'pos') or (hasattr(v, 'current_location') and v.current_location)
                ],
                "security": [
                    {
                        "id": s.unique_id,
                        "type": "hotel_security",
                        "location": get_normalized_location(s),  # ✅ Send normalized coordinates
                        "status": s.status,
                        "hotel_id": s.hotel_id,
                    }
                    for s in self.hotel_security if hasattr(s, 'pos') or (hasattr(s, 'current_location') and s.current_location)
                ],
                "lvmpd": [
                    {
                        "id": u.unique_id,
                        "type": "lvmpd",
                        "location": get_normalized_location(u),  # ✅ Send normalized coordinates
                        "status": u.status,
                    }
                    for u in self.lvmpd_units if hasattr(u, 'pos') or (hasattr(u, 'current_location') and u.current_location)
                ],
                "amr": [
                    {
                        "id": u.unique_id,
                        "type": "amr",
                        "location": get_normalized_location(u),  # ✅ Send normalized coordinates
                        "status": u.status,
                    }
                    for u in self.amr_units if hasattr(u, 'pos') or (hasattr(u, 'current_location') and u.current_location)
                ],
                "buses": [
                    {
                        "id": b.unique_id,
                        "type": "bus",
                        "location": get_normalized_location(b),  # ✅ Send normalized coordinates
                        "status": b.status,
                    }
                    for b in self.buses if hasattr(b, 'pos') or (hasattr(b, 'current_location') and b.current_location)
                ],
            },
            "incidents": [
                {
                    **incident,
                    "location": (
                        list(self._normalize_coords(incident["location"][0], incident["location"][1]))
                        if isinstance(incident.get("location"), (list, tuple)) and len(incident["location"]) == 2
                        else incident.get("location", [0.5, 0.5])
                    )
                }
                for incident in make_serializable(self.active_incidents)
            ],
            "metrics": make_serializable(self.metrics),
            "command_center": command_center_data,
            "security_metrics": {
                "hotel_security": [
                    make_serializable(s.get_security_metrics() if hasattr(s, 'get_security_metrics') else {})
                    for s in self.hotel_security
                ],
                "lvmpd": [
                    make_serializable(u.get_lvmpd_metrics() if hasattr(u, 'get_lvmpd_metrics') else {})
                    for u in self.lvmpd_units
                ],
            },
        }

