"""
Agent classes for the Special Olympics simulation.
Each agent type represents a different role in the security and support system.
"""

import random
from typing import Dict, Optional, Tuple, List
from mesa import Agent
import numpy as np


class Athlete(Agent):
    """Represents a Special Olympics athlete."""
    
    def __init__(
        self,
        unique_id: int,
        model,
        role: str = "athlete",
        mobility: str = "walking",  # "walking", "wheelchair", "assisted"
        medical_risk: float = 0.1,
        badge_token: Optional[str] = None,
        schedule: Optional[Dict] = None,
    ):
        # Mesa 3.4.0 workaround - direct initialization (super() has bug)
        self.model = model
        self.unique_id = unique_id
        self.role = role
        self.mobility = mobility
        self.medical_risk = medical_risk
        self.badge_token = badge_token or f"ATH_{unique_id:04d}"
        self.schedule = schedule or {}
        self.current_location = None
        self.target_location = None
        self.status = "waiting"  # waiting, traveling, at_venue, emergency
        self.medical_event = False
        self.escorted = False
        
        # Movement parameters
        self.walking_speed = self._get_speed()
        self.current_path = []
        self.path_index = 0
        
    def _get_speed(self) -> float:
        """Get movement speed based on mobility type."""
        base_speeds = {
            "walking": 1.4,  # m/s
            "wheelchair": 1.0,
            "assisted": 0.8,
        }
        base = base_speeds.get(self.mobility, 1.0)
        # Add variance
        return base * random.uniform(0.85, 1.15)
    
    def step(self):
        """✅ ENHANCED: Agent behavior with crowd awareness and interactions."""
        # Check for medical event based on risk and weather
        if not self.medical_event:
            self._check_medical_risk()
        
        # ✅ ENHANCED: Check for nearby athletes who need help
        if self.status == "at_venue" and not self.medical_event:
            self._check_nearby_assistance()
        
        # Handle movement
        if self.status == "traveling":
            self._move()
        elif self.status == "waiting":
            self._check_schedule()
        
        # Update position in model (normalize coordinates)
        if self.current_location:
            self.pos = self.model._normalize_coords(self.current_location[0], self.current_location[1])
            self.model.space.move_agent(self, self.pos)
    
    def _check_nearby_assistance(self):
        """✅ ENHANCED: Check if nearby athletes need help and assist if possible."""
        if not self.current_location:
            return
        
        # Look for nearby athletes in emergency
        nearby = self.model.get_agents_near(self.current_location, 0.01, agent_type=Athlete)
        for other_athlete in nearby:
            if other_athlete.medical_event and not other_athlete.escorted:
                # 30% chance of helping (athletes can help each other)
                if random.random() < 0.3:
                    other_athlete.escorted = True
                    # Stay near the athlete in need
                    self.status = "assisting"
                    self.target_location = other_athlete.current_location
                    break
    
    def _check_medical_risk(self):
        """Check if athlete experiences medical event based on risk factors."""
        weather = self.model.weather
        temp_factor = 1.0
        if weather.get("temp_C", 20) > 35:
            temp_factor = 1.5 + (weather["temp_C"] - 35) * 0.1
        
        risk = self.medical_risk * temp_factor
        step_seconds = self.model.step_duration.total_seconds() if hasattr(self.model.step_duration, 'total_seconds') else self.model.step_duration
        if random.random() < risk * step_seconds / 3600:  # Per hour probability
            self.medical_event = True
            self.status = "emergency"
            self.model.trigger_medical_event(self)
    
    def _check_schedule(self):
        """Check if it's time to move to next scheduled location."""
        current_time = self.model.current_time
        # Simplified: check if time matches schedule
        for event_time, location in self.schedule.items():
            if abs((current_time - event_time).total_seconds()) < 300:  # 5 min window
                self.target_location = location
                self.status = "traveling"
                self._plan_route()
                break
    
    def _plan_route(self):
        """Plan route to target location using model's routing."""
        if self.current_location and self.target_location:
            self.current_path = self.model.route_planner.find_path(
                self.current_location, self.target_location
            )
            self.path_index = 0
    
    def _move(self):
        """✅ ENHANCED: Move along planned path with congestion awareness."""
        if not self.current_path or self.path_index >= len(self.current_path):
            # Arrived
            self.status = "at_venue"
            self.current_location = self.target_location
            return
        
        # Move towards next waypoint (with bounds checking)
        if self.path_index < 0 or self.path_index >= len(self.current_path):
            self.status = "at_venue"
            self.current_location = self.target_location
            return
        
        next_point = self.current_path[self.path_index]
        distance = self._distance(self.current_location, next_point)
        step_seconds = self.model.step_duration.total_seconds() if hasattr(self.model.step_duration, 'total_seconds') else self.model.step_duration
        
        # ✅ ENHANCED: Check for congestion ahead and adjust speed
        effective_speed = self.walking_speed
        if self.current_location:
            # Check for nearby agents (congestion)
            nearby = self.model.get_agents_near(self.current_location, 0.005)
            if len(nearby) > 5:  # More than 5 agents nearby = congestion
                congestion_factor = min(0.5, len(nearby) / 20.0)  # Up to 50% speed reduction
                effective_speed *= (1.0 - congestion_factor)
        
        step_distance = effective_speed * step_seconds
        
        if distance <= step_distance:
            self.current_location = next_point
            self.path_index += 1
        else:
            # Move partway
            ratio = step_distance / distance
            self.current_location = self._interpolate(
                self.current_location, next_point, ratio
            )
    
    def _distance(self, p1: Tuple[float, float], p2: Tuple[float, float]) -> float:
        """Calculate distance between two points (simplified)."""
        return np.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)
    
    def _interpolate(self, p1: Tuple[float, float], p2: Tuple[float, float], ratio: float) -> Tuple[float, float]:
        """Interpolate between two points."""
        return (
            p1[0] + (p2[0] - p1[0]) * ratio,
            p1[1] + (p2[1] - p1[1]) * ratio,
        )


class Volunteer(Agent):
    """Represents a volunteer providing support and security."""
    
    def __init__(
        self,
        unique_id: int,
        model,
        assignment: str = "general",
        patrol_area: Optional[List[Tuple[float, float]]] = None,
        response_speed: float = 1.5,
    ):
        # Mesa 3.4.0 workaround
        self.model = model
        self.unique_id = unique_id
        self.assignment = assignment
        self.patrol_area = patrol_area or []
        self.response_speed = response_speed
        self.current_location = None
        self.status = "patrolling"  # patrolling, responding, assisting
        self.current_assignment = None
        
    def step(self):
        """✅ ENHANCED: Volunteer behavior with coordination and crowd management."""
        if self.status == "responding":
            self._respond_to_incident()
        elif self.status == "patrolling":
            self._patrol()
            # ✅ ENHANCED: Check for nearby incidents while patrolling
            self._check_nearby_incidents()
        elif self.status == "assisting":
            self._assist_athlete()
        
        # ✅ CRITICAL: Sync position to Mesa space (frontend needs this)
        if self.current_location:
            self.pos = self.model._normalize_coords(self.current_location[0], self.current_location[1])
            self.model.space.move_agent(self, self.pos)
    
    def _check_nearby_incidents(self):
        """✅ ENHANCED: Check for nearby incidents and coordinate with other volunteers."""
        if not self.current_location or not self.model.active_incidents:
            return
        
        # Check for incidents within response radius
        for incident in self.model.active_incidents:
            incident_loc = incident.get("location")
            if incident_loc:
                distance = self._distance(self.current_location, incident_loc)
                if distance < 0.02:  # Within response radius
                    # Check if other volunteers are already responding
                    responding_count = sum(
                        1 for v in self.model.volunteers
                        if v.status == "responding" and v.current_assignment and
                        v.current_assignment.get("incident_id") == incident.get("id")
                    )
                    
                    # If no one responding or need backup, respond
                    if responding_count == 0 or (responding_count < 2 and incident.get("severity") == "high"):
                        self.status = "responding"
                        self.current_assignment = {
                            "incident": incident,
                            "incident_id": incident.get("id"),
                        }
                        break
    
    def _patrol(self):
        """Patrol assigned area."""
        # Simplified: move randomly within patrol area
        if self.patrol_area:
            target = random.choice(self.patrol_area)
            if self.current_location:
                # Move towards target
                self.current_location = self._move_towards(
                    self.current_location, target, self.response_speed
                )
            else:
                self.current_location = target
    
    def _respond_to_incident(self):
        """Respond to assigned incident."""
        if self.current_assignment:
            incident_loc = self.current_assignment.get("location")
            if incident_loc and self.current_location:
                distance = self._distance(self.current_location, incident_loc)
                if distance < 0.01:  # Arrived (threshold in degrees)
                    self.status = "assisting"
                else:
                    self.current_location = self._move_towards(
                        self.current_location, incident_loc, self.response_speed
                    )
    
    def _assist_athlete(self):
        """Provide assistance to athlete."""
        # Stay with athlete until incident resolved
        if self.current_assignment:
            athlete = self.current_assignment.get("athlete")
            if athlete and athlete.status != "emergency":
                self.status = "patrolling"
                self.current_assignment = None
    
    def _move_towards(self, start: Tuple[float, float], end: Tuple[float, float], speed: float) -> Tuple[float, float]:
        """Move towards target location."""
        distance = self._distance(start, end)
        step_seconds = self.model.step_duration.total_seconds() if hasattr(self.model.step_duration, 'total_seconds') else self.model.step_duration
        step_distance = speed * step_seconds
        if distance <= step_distance:
            return end
        ratio = step_distance / distance
        return self._interpolate(start, end, ratio)
    
    def _distance(self, p1: Tuple[float, float], p2: Tuple[float, float]) -> float:
        """Calculate distance."""
        return np.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)
    
    def _interpolate(self, p1: Tuple[float, float], p2: Tuple[float, float], ratio: float) -> Tuple[float, float]:
        """Interpolate between points."""
        return (
            p1[0] + (p2[0] - p1[0]) * ratio,
            p1[1] + (p2[1] - p1[1]) * ratio,
        )


class HotelSecurity(Agent):
    """Enhanced hotel security personnel with threat assessment and dynamic patrols."""
    
    def __init__(
        self,
        unique_id: int,
        model,
        hotel_id: str,
        patrol_route: Optional[List[Tuple[float, float]]] = None,
        alert_threshold: float = 0.7,
    ):
        # Mesa 3.4.0 workaround
        self.model = model
        self.unique_id = unique_id
        self.hotel_id = hotel_id
        self.base_patrol_route = patrol_route or []
        self.patrol_route = list(self.base_patrol_route)  # Dynamic route
        self.alert_threshold = alert_threshold
        self.current_location = None
        self.status = "patrolling"  # patrolling, responding, coordinating, crowd_management
        self.route_index = 0
        
        # Enhanced capabilities
        self.threat_level = 0.0  # Current threat assessment (0-1)
        self.last_threat_check = None
        self.coverage_radius = 0.02  # Coverage area
        self.response_times = []  # Track response times
        self.access_control_checks = {"success": 0, "failed": 0}
        self.coordinating_with = []  # Other agents being coordinated with
        
    def step(self):
        """Enhanced security rover behavior with threat assessment."""
        # Check for high-priority threats first
        if self.status == "patrolling":
            self._assess_threats()
            if self._should_respond_to_threat():
                self._switch_to_response_mode()
            else:
                self._dynamic_patrol()
        elif self.status == "responding":
            self._respond_to_alert()
        elif self.status == "coordinating":
            self._coordinate_with_units()
        elif self.status == "crowd_management":
            self._manage_crowd_flow()
        
        # ✅ CRITICAL: Sync position to Mesa space (frontend needs this)
        if self.current_location:
            self.pos = self.model._normalize_coords(self.current_location[0], self.current_location[1])
            self.model.space.move_agent(self, self.pos)
    
    def _assess_threats(self):
        """Assess threat level in patrol area."""
        if not self.current_location:
            return
        
        threat_score = 0.0
        
        # Check for active alerts
        alert = self.model.get_active_alert(self.hotel_id)
        if alert:
            alert_loc = alert.get("location")
            if alert_loc:
                distance = self._distance(self.current_location, alert_loc)
                proximity_factor = max(0, 1 - (distance / self.coverage_radius))
                threat_score += 0.6 * proximity_factor
        
        # Check for nearby incidents
        for incident in self.model.active_incidents:
            incident_loc = incident.get("location")
            if incident_loc:
                distance = self._distance(self.current_location, incident_loc)
                if distance < self.coverage_radius:
                    threat_score += 0.3
        
        # Check crowd density (predictive positioning)
        nearby_athletes = self.model.get_agents_near(
            self.current_location, self.coverage_radius, agent_type=Athlete
        )
        crowd_density = len(nearby_athletes)
        if crowd_density > 10:  # High density threshold
            threat_score += 0.2 * min(1.0, crowd_density / 20)
        
        self.threat_level = min(1.0, threat_score)
        self.last_threat_check = self.model.current_time
    
    def _should_respond_to_threat(self) -> bool:
        """Determine if threat requires immediate response."""
        alert = self.model.get_active_alert(self.hotel_id)
        return alert is not None or self.threat_level > self.alert_threshold
    
    def _switch_to_response_mode(self):
        """Switch from patrolling to response mode."""
        alert = self.model.get_active_alert(self.hotel_id)
        if alert:
            self.status = "responding"
            # Alert nearby volunteers
            self._alert_nearby_volunteers(alert.get("location"))
    
    def _dynamic_patrol(self):
        """Dynamic patrol with predictive positioning."""
        # If high threat detected, adjust route to cover threat area
        if self.threat_level > 0.3 and self.patrol_route:
            # Add threat area to patrol route temporarily
            threat_location = self._get_threat_location()
            if threat_location and threat_location not in self.patrol_route:
                # Insert threat location into route
                insert_index = min(self.route_index + 1, len(self.patrol_route))
                self.patrol_route.insert(insert_index, threat_location)
        
        # Follow patrol route
        if not self.patrol_route:
            # Generate default patrol if none exists
            self._generate_default_patrol()
            return
        
        if self.route_index >= len(self.patrol_route):
            self.route_index = 0
            # Reset to base route periodically
            if random.random() < 0.1:  # 10% chance to reset
                self.patrol_route = list(self.base_patrol_route)
        
        target = self.patrol_route[self.route_index]
        if self.current_location:
            distance = self._distance(self.current_location, target)
            if distance < 0.001:  # Reached waypoint
                self.route_index += 1
            else:
                self.current_location = self._move_towards(
                    self.current_location, target, 1.2
                )
        else:
            self.current_location = target
    
    def _get_threat_location(self) -> Optional[Tuple[float, float]]:
        """Get location of highest threat."""
        alert = self.model.get_active_alert(self.hotel_id)
        if alert:
            return alert.get("location")
        
        # Find nearest incident
        if self.model.active_incidents:
            nearest = min(
                self.model.active_incidents,
                key=lambda i: self._distance(
                    self.current_location or (0.5, 0.5),
                    i.get("location", (0.5, 0.5))
                )
            )
            return nearest.get("location")
        
        return None
    
    def _generate_default_patrol(self):
        """Generate default patrol route around hotel."""
        hotel_key = f"{self.hotel_id}_hotel"
        if hotel_key in self.model.venues:
            hotel = self.model.venues[hotel_key]
            center = (hotel["lat"], hotel["lon"])
            # Create circular patrol around hotel
            import math
            radius = 0.01
            num_points = 8
            self.patrol_route = [
                (
                    center[0] + radius * math.cos(2 * math.pi * i / num_points),
                    center[1] + radius * math.sin(2 * math.pi * i / num_points)
                )
                for i in range(num_points)
            ]
            self.base_patrol_route = list(self.patrol_route)
    
    def _respond_to_alert(self):
        """Enhanced response with coordination."""
        alert = self.model.get_active_alert(self.hotel_id)
        if not alert:
            self.status = "patrolling"
            return
        
        alert_loc = alert.get("location")
        if not alert_loc or not self.current_location:
            return
        
        distance = self._distance(self.current_location, alert_loc)
        
        # Track response time
        if not hasattr(self, 'response_start_time'):
            self.response_start_time = self.model.current_time
        
        if distance < 0.001:  # Arrived
            # Record response time
            if hasattr(self, 'response_start_time'):
                response_time = (self.model.current_time - self.response_start_time).total_seconds()
                self.response_times.append(response_time)
                delattr(self, 'response_start_time')
            
            # Resolve alert
            self.model.resolve_alert(self.hotel_id, alert["id"])
            
            # Check if crowd management needed
            nearby_athletes = self.model.get_agents_near(
                alert_loc, 0.01, agent_type=Athlete
            )
            if len(nearby_athletes) > 5:
                self.status = "crowd_management"
            else:
                self.status = "patrolling"
        else:
            # Clear pathway for medical units if needed
            self._clear_pathway_for_medical(alert_loc)
            
            # Move towards alert
            self.current_location = self._move_towards(
                self.current_location, alert_loc, 2.0
            )
    
    def _alert_nearby_volunteers(self, location: Tuple[float, float]):
        """Alert nearby volunteers to assist."""
        if not hasattr(self.model, 'volunteers'):
            return
        
        nearby_volunteers = self.model.get_agents_near(
            location, 0.02, agent_type=Volunteer
        )
        
        for volunteer in nearby_volunteers:
            if volunteer.status == "patrolling":
                volunteer.status = "responding"
                volunteer.current_assignment = {
                    "type": "security_alert",
                    "location": location,
                    "security_id": self.unique_id,
                }
    
    def _clear_pathway_for_medical(self, target_location: Tuple[float, float]):
        """Clear pathway for medical units."""
        # Check if AMR units are en route
        for amr in self.model.amr_units:
            if amr.status == "dispatched" and amr.current_patient:
                patient_loc = amr.current_patient.current_location
                if patient_loc:
                    # Check if pathway intersects with our route
                    pathway_distance = self._distance(target_location, patient_loc)
                    if pathway_distance < 0.02:  # Near medical route
                        # Coordinate with medical unit
                        if self.unique_id not in self.coordinating_with:
                            self.coordinating_with.append(amr.unique_id)
                            self.status = "coordinating"
    
    def _coordinate_with_units(self):
        """Coordinate with other security/medical units."""
        # Ensure pathway is clear
        if self.coordinating_with:
            # Check if coordination is still needed
            still_needed = False
            for unit_id in self.coordinating_with[:]:
                # Find unit (simplified - in real implementation would track better)
                still_needed = True  # Simplified check
                if not still_needed:
                    self.coordinating_with.remove(unit_id)
            
            if not self.coordinating_with:
                self.status = "patrolling"
        else:
            self.status = "patrolling"
    
    def _manage_crowd_flow(self):
        """Manage crowd flow at high-traffic areas."""
        # Position at strategic points to guide flow
        if self.current_location:
            nearby_athletes = self.model.get_agents_near(
                self.current_location, 0.015, agent_type=Athlete
            )
            
            # If crowd thins, return to patrol
            if len(nearby_athletes) < 3:
                self.status = "patrolling"
            # Otherwise maintain position to guide flow
            # (In full implementation, would redirect athletes)
    
    def _move_towards(self, start: Tuple[float, float], end: Tuple[float, float], speed: float) -> Tuple[float, float]:
        """Move towards target."""
        distance = self._distance(start, end)
        step_seconds = self.model.step_duration.total_seconds() if hasattr(self.model.step_duration, 'total_seconds') else self.model.step_duration
        step_distance = speed * step_seconds
        if distance <= step_distance:
            return end
        ratio = step_distance / distance
        return (
            start[0] + (end[0] - start[0]) * ratio,
            start[1] + (end[1] - start[1]) * ratio,
        )
    
    def _distance(self, p1: Tuple[float, float], p2: Tuple[float, float]) -> float:
        """Calculate distance."""
        return np.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)
    
    def get_security_metrics(self) -> Dict:
        """Get security-specific metrics."""
        avg_response_time = (
            sum(self.response_times) / len(self.response_times)
            if self.response_times else 0.0
        )
        access_success_rate = (
            self.access_control_checks["success"] / 
            (self.access_control_checks["success"] + self.access_control_checks["failed"])
            if (self.access_control_checks["success"] + self.access_control_checks["failed"]) > 0
            else 1.0
        )
        
        return {
            "threat_level": self.threat_level,
            "avg_response_time": avg_response_time,
            "access_success_rate": access_success_rate,
            "coverage_radius": self.coverage_radius,
        }


class LVMPDUnit(Agent):
    """Enhanced LVMPD security unit with incident prioritization and coordination."""
    
    def __init__(
        self,
        unique_id: int,
        model,
        response_radius: float = 0.05,  # degrees
        dispatch_time: float = 120.0,  # seconds
    ):
        # Mesa 3.4.0 workaround
        self.model = model
        self.unique_id = unique_id
        self.response_radius = response_radius
        self.dispatch_time = dispatch_time
        self.current_location = None
        self.status = "available"  # available, dispatched, on_scene, coordinating, crowd_management
        self.current_incident = None
        self.dispatch_start_time = None
        
        # Enhanced capabilities
        self.incident_priority = 0.0  # Current incident priority (0-1)
        self.response_times = []  # Track response times by location
        self.coordinating_with = []  # Other units coordinating with
        self.pathway_cleared_for = []  # Medical units we're clearing path for
        
    def step(self):
        """Enhanced LVMPD unit behavior with prioritization."""
        if self.status == "available":
            # Check for high-priority incidents
            priority_incident = self._get_highest_priority_incident()
            if priority_incident:
                self._dispatch_to_incident(priority_incident)
        elif self.status == "dispatched":
            self._respond()
        elif self.status == "on_scene":
            self._handle_incident()
        elif self.status == "coordinating":
            self._coordinate_with_units()
        elif self.status == "crowd_management":
            self._manage_crowd_flow()
        
        # ✅ CRITICAL: Sync position to Mesa space (frontend needs this)
        if self.current_location:
            self.pos = self.model._normalize_coords(self.current_location[0], self.current_location[1])
            self.model.space.move_agent(self, self.pos)
    
    def _get_highest_priority_incident(self) -> Optional[Dict]:
        """Get highest priority incident using threat assessment."""
        if not self.model.active_incidents:
            return None
        
        # Score incidents by priority
        scored_incidents = []
        for incident in self.model.active_incidents:
            priority_score = self._assess_incident_priority(incident)
            scored_incidents.append((priority_score, incident))
        
        # Sort by priority (highest first)
        scored_incidents.sort(reverse=True, key=lambda x: x[0])
        
        # Check if another unit is already handling it
        for priority, incident in scored_incidents:
            incident_id = incident.get("id")
            # Check if other LVMPD units are handling this
            other_units_handling = [
                u for u in self.model.lvmpd_units
                if u != self and u.current_incident and u.current_incident.get("id") == incident_id
            ]
            if not other_units_handling:
                return incident
        
        return None
    
    def _assess_incident_priority(self, incident: Dict) -> float:
        """Assess priority of incident (0-1 scale)."""
        priority = 0.5  # Base priority
        
        incident_type = incident.get("type", "")
        incident_loc = incident.get("location")
        
        # Type-based priority
        type_priorities = {
            "suspicious_person": 0.8,
            "access_denied": 0.7,
            "crowd_surge": 0.6,
            "medical_event": 0.5,  # Medical handled by AMR, but we may assist
        }
        priority = type_priorities.get(incident_type, 0.5)
        
        # Proximity factor (closer = higher priority for this unit)
        if incident_loc and self.current_location:
            distance = self._distance(self.current_location, incident_loc)
            proximity_factor = max(0, 1 - (distance / self.response_radius))
            priority += 0.2 * proximity_factor
        
        # Crowd density at location
        if incident_loc:
            nearby_athletes = self.model.get_agents_near(
                incident_loc, 0.02, agent_type=Athlete
            )
            crowd_factor = min(1.0, len(nearby_athletes) / 20)
            priority += 0.1 * crowd_factor
        
        # VIP presence (if available in model)
        # priority += 0.1 if vip_present else 0
        
        return min(1.0, priority)
    
    def _dispatch_to_incident(self, incident: Dict):
        """Dispatch to incident with coordination."""
        self.current_incident = incident
        self.status = "dispatched"
        self.dispatch_start_time = self.model.current_time
        self.incident_priority = self._assess_incident_priority(incident)
        
        # Alert nearby volunteers
        incident_loc = incident.get("location")
        if incident_loc:
            self._alert_nearby_volunteers(incident_loc)
            
            # Check if medical units need pathway clearing
            self._check_medical_pathway_clearing(incident_loc)
    
    def _respond(self):
        """Enhanced response with pathway clearing."""
        if not self.current_incident:
            self.status = "available"
            return
        
        incident_loc = self.current_incident.get("location")
        if not incident_loc:
            return
        
        # Check if dispatch time elapsed
        if self.dispatch_start_time:
            elapsed = (self.model.current_time - self.dispatch_start_time).total_seconds()
            if elapsed < self.dispatch_time:
                return  # Still preparing
        
        # Move towards incident
        if self.current_location:
            distance = self._distance(self.current_location, incident_loc)
            if distance < 0.005:  # Arrived
                self.status = "on_scene"
                
                # Record response time
                response_time = (self.model.current_time - self.dispatch_start_time).total_seconds()
                self.response_times.append({
                    "time": response_time,
                    "location": incident_loc,
                    "incident_type": self.current_incident.get("type"),
                })
            else:
                # Clear pathway while moving
                self._clear_pathway_while_moving(incident_loc)
                
                # Move towards incident
                self.current_location = self._move_towards(
                    self.current_location, incident_loc, 15.0  # Fast response
                )
    
    def _clear_pathway_while_moving(self, target: Tuple[float, float]):
        """Clear pathway for medical units while responding."""
        # Check for AMR units that might need pathway
        for amr in self.model.amr_units:
            if amr.status in ["dispatched", "transporting"] and amr.current_patient:
                patient_loc = amr.current_patient.current_location
                if patient_loc:
                    # Check if our route intersects with medical route
                    route_distance = self._distance(self.current_location, target)
                    medical_route_distance = self._distance(patient_loc, target)
                    
                    # If we're near medical route, coordinate
                    if medical_route_distance < 0.02 and route_distance < 0.03:
                        if amr.unique_id not in self.pathway_cleared_for:
                            self.pathway_cleared_for.append(amr.unique_id)
                            self.status = "coordinating"
    
    def _check_medical_pathway_clearing(self, incident_loc: Tuple[float, float]):
        """Check if medical units need pathway cleared."""
        for amr in self.model.amr_units:
            if amr.status == "dispatched" and amr.current_patient:
                patient_loc = amr.current_patient.current_location
                if patient_loc:
                    # Check if incident is near medical route
                    distance_to_medical = self._distance(incident_loc, patient_loc)
                    if distance_to_medical < 0.02:
                        # Coordinate to clear pathway
                        if amr.unique_id not in self.pathway_cleared_for:
                            self.pathway_cleared_for.append(amr.unique_id)
    
    def _alert_nearby_volunteers(self, location: Tuple[float, float]):
        """Alert nearby volunteers to assist with incident."""
        nearby_volunteers = self.model.get_agents_near(
            location, 0.03, agent_type=Volunteer
        )
        
        for volunteer in nearby_volunteers:
            if volunteer.status == "patrolling":
                volunteer.status = "responding"
                volunteer.current_assignment = {
                    "type": "lvmpd_incident",
                    "location": location,
                    "incident": self.current_incident,
                    "lvmpd_id": self.unique_id,
                }
    
    def _handle_incident(self):
        """Handle incident on scene with crowd management."""
        if not self.current_incident:
            self.status = "available"
            return
        
        incident_loc = self.current_incident.get("location")
        
        # Check for crowd management needs
        if incident_loc:
            nearby_athletes = self.model.get_agents_near(
                incident_loc, 0.015, agent_type=Athlete
            )
            
            if len(nearby_athletes) > 10:
                # Need crowd management
                self.status = "crowd_management"
                return
        
        # Resolve incident after handling time
        incident_id = self.current_incident.get("id")
        if incident_id:
            self.model.resolve_incident(incident_id)
            self.status = "available"
            self.current_incident = None
            self.pathway_cleared_for = []
            self.incident_priority = 0.0
    
    def _coordinate_with_units(self):
        """Coordinate with other units (medical, security)."""
        # Ensure pathways are clear
        if self.pathway_cleared_for:
            # Check if coordination still needed
            still_needed = []
            for unit_id in self.pathway_cleared_for:
                # Find medical unit (simplified)
                # In real implementation, would track units better
                still_needed.append(unit_id)
            
            if not still_needed:
                self.pathway_cleared_for = []
                if self.current_incident:
                    self.status = "on_scene"
                else:
                    self.status = "available"
        else:
            if self.current_incident:
                self.status = "on_scene"
            else:
                self.status = "available"
    
    def _manage_crowd_flow(self):
        """Manage crowd flow at incident scene."""
        if not self.current_incident:
            self.status = "available"
            return
        
        incident_loc = self.current_incident.get("location")
        if incident_loc:
            nearby_athletes = self.model.get_agents_near(
                incident_loc, 0.015, agent_type=Athlete
            )
            
            # If crowd thins, return to handling incident
            if len(nearby_athletes) < 5:
                self.status = "on_scene"
            # Otherwise maintain position to manage flow
            # (In full implementation, would redirect athletes)
    
    def _move_towards(self, start: Tuple[float, float], end: Tuple[float, float], speed: float) -> Tuple[float, float]:
        """Move towards target."""
        distance = self._distance(start, end)
        step_seconds = self.model.step_duration.total_seconds() if hasattr(self.model.step_duration, 'total_seconds') else self.model.step_duration
        step_distance = speed * step_seconds
        if distance <= step_distance:
            return end
        ratio = step_distance / distance
        return (
            start[0] + (end[0] - start[0]) * ratio,
            start[1] + (end[1] - start[1]) * ratio,
        )
    
    def _distance(self, p1: Tuple[float, float], p2: Tuple[float, float]) -> float:
        """Calculate distance."""
        return np.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)
    
    def get_lvmpd_metrics(self) -> Dict:
        """Get LVMPD-specific metrics."""
        avg_response_time = (
            sum(r["time"] for r in self.response_times) / len(self.response_times)
            if self.response_times else 0.0
        )
        
        return {
            "avg_response_time": avg_response_time,
            "incidents_handled": len(self.response_times),
            "current_priority": self.incident_priority,
        }


class AMRUnit(Agent):
    """Represents an AMR (American Medical Response) unit."""
    
    def __init__(
        self,
        unique_id: int,
        model,
        transport_capacity: int = 1,
        eta_base: float = 300.0,  # seconds
    ):
        # Mesa 3.4.0 workaround
        self.model = model
        self.unique_id = unique_id
        self.transport_capacity = transport_capacity
        self.eta_base = eta_base
        self.current_location = None
        self.status = "available"  # available, dispatched, transporting
        self.current_patient = None
        self.destination = None
        
    def step(self):
        """AMR unit behavior."""
        if self.status == "dispatched":
            self._respond_to_medical()
        elif self.status == "transporting":
            self._transport_patient()
        
        # ✅ CRITICAL: Sync position to Mesa space (frontend needs this)
        if self.current_location:
            self.pos = self.model._normalize_coords(self.current_location[0], self.current_location[1])
            self.model.space.move_agent(self, self.pos)
    
    def _respond_to_medical(self):
        """Respond to medical emergency."""
        if not self.current_patient:
            return
        
        patient_loc = self.current_patient.current_location
        if not patient_loc:
            return
        
        # Move to patient
        if self.current_location:
            distance = self._distance(self.current_location, patient_loc)
            if distance < 0.005:  # Arrived
                self.status = "transporting"
                # Determine destination (hospital)
                self.destination = self.model.get_nearest_hospital(patient_loc)
            else:
                self.current_location = self._move_towards(
                    self.current_location, patient_loc, 12.0
                )
    
    def _transport_patient(self):
        """Transport patient to hospital."""
        if not self.destination:
            return
        
        if self.current_location:
            distance = self._distance(self.current_location, self.destination)
            if distance < 0.005:  # Arrived at hospital
                # Patient delivered
                self.model.complete_medical_transport(self.current_patient.unique_id)
                self.status = "available"
                self.current_patient = None
                self.destination = None
            else:
                self.current_location = self._move_towards(
                    self.current_location, self.destination, 12.0
                )
    
    def _move_towards(self, start: Tuple[float, float], end: Tuple[float, float], speed: float) -> Tuple[float, float]:
        """Move towards target."""
        distance = self._distance(start, end)
        step_seconds = self.model.step_duration.total_seconds() if hasattr(self.model.step_duration, 'total_seconds') else self.model.step_duration
        step_distance = speed * step_seconds
        if distance <= step_distance:
            return end
        ratio = step_distance / distance
        return (
            start[0] + (end[0] - start[0]) * ratio,
            start[1] + (end[1] - start[1]) * ratio,
        )
    
    def _distance(self, p1: Tuple[float, float], p2: Tuple[float, float]) -> float:
        """Calculate distance."""
        return np.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)


class Bus(Agent):
    """Represents a transit bus."""
    
    def __init__(
        self,
        unique_id: int,
        model,
        route: List[Tuple[float, float]],
        capacity: int = 40,
    ):
        # Mesa 3.4.0 workaround
        self.model = model
        self.unique_id = unique_id
        self.route = route
        self.capacity = capacity
        self.current_passengers = []
        self.current_location = None
        self.route_index = 0
        self.status = "in_service"
        self.door_access_points = []  # Locations where athletes can board
        
    def step(self):
        """Bus behavior."""
        if self.status == "in_service":
            self._follow_route()
            self._handle_boarding()
        
        # ✅ CRITICAL: Sync position to Mesa space (frontend needs this)
        if self.current_location:
            self.pos = self.model._normalize_coords(self.current_location[0], self.current_location[1])
            self.model.space.move_agent(self, self.pos)
    
    def _follow_route(self):
        """Follow assigned route."""
        if not self.route:
            return
        
        if self.route_index >= len(self.route):
            self.route_index = 0  # Loop route
        
        target = self.route[self.route_index]
        if self.current_location:
            distance = self._distance(self.current_location, target)
            if distance < 0.001:
                self.route_index += 1
            else:
                self.current_location = self._move_towards(
                    self.current_location, target, 8.0  # Bus speed
                )
        else:
            self.current_location = target
    
    def _handle_boarding(self):
        """Handle athlete boarding at stops."""
        # Simplified: check if athletes are waiting at current stop
        if self.current_location and len(self.current_passengers) < self.capacity:
            nearby_athletes = self.model.get_agents_near(
                self.current_location, 0.002, agent_type=Athlete
            )
            for athlete in nearby_athletes:
                if athlete.status == "waiting" and len(self.current_passengers) < self.capacity:
                    self.current_passengers.append(athlete)
                    athlete.status = "traveling"
                    athlete.current_location = self.current_location
    
    def _move_towards(self, start: Tuple[float, float], end: Tuple[float, float], speed: float) -> Tuple[float, float]:
        """Move towards target."""
        distance = self._distance(start, end)
        step_seconds = self.model.step_duration.total_seconds() if hasattr(self.model.step_duration, 'total_seconds') else self.model.step_duration
        step_distance = speed * step_seconds
        if distance <= step_distance:
            return end
        ratio = step_distance / distance
        return (
            start[0] + (end[0] - start[0]) * ratio,
            start[1] + (end[1] - start[1]) * ratio,
        )
    
    def _distance(self, p1: Tuple[float, float], p2: Tuple[float, float]) -> float:
        """Calculate distance."""
        return np.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)


class SecurityCommandCenter(Agent):
    """Centralized security command center for coordination and threat assessment."""
    
    def __init__(
        self,
        unique_id: int,
        model,
        location: Optional[Tuple[float, float]] = None,
    ):
        # Mesa 3.4.0 workaround
        self.model = model
        self.unique_id = unique_id
        self.location = location or (0.5, 0.5)  # Central command location
        self.current_location = self.location
        
        # Command center capabilities
        self.threat_map = {}  # Location -> threat level
        self.unit_assignments = {}  # Unit ID -> assignment
        self.coordination_queue = []  # Pending coordination tasks
        self.incident_priorities = {}  # Incident ID -> priority score
        self.hotspots = []  # High-risk areas
        
    def step(self):
        """Command center coordination and threat assessment."""
        # Update threat map
        self._update_threat_map()
        
        # Assess incident priorities
        self._assess_all_incidents()
        
        # Coordinate unit assignments
        self._coordinate_units()
        
        # Identify hotspots
        self._identify_hotspots()
        
        # Dispatch units to hotspots if needed
        self._dispatch_to_hotspots()
    
    def _update_threat_map(self):
        """Update threat map based on current situation."""
        # Clear old threat data
        self.threat_map = {}
        
        # Assess threats from incidents
        for incident in self.model.active_incidents:
            incident_loc = incident.get("location")
            if incident_loc:
                threat_level = self._calculate_threat_level(incident)
                self.threat_map[tuple(incident_loc)] = threat_level
        
        # Assess threats from alerts
        for hotel_id, alerts in self.model.active_alerts.items():
            for alert in alerts:
                alert_loc = alert.get("location")
                if alert_loc:
                    threat_level = 0.7  # Base threat for alerts
                    self.threat_map[tuple(alert_loc)] = threat_level
        
        # Assess crowd density threats
        for venue_key, venue_data in self.model.venues.items():
            venue_loc = (venue_data.get("lat"), venue_data.get("lon"))
            nearby_athletes = self.model.get_agents_near(
                venue_loc, 0.02, agent_type=Athlete
            )
            if len(nearby_athletes) > 15:
                threat_level = min(0.5, len(nearby_athletes) / 30)
                if tuple(venue_loc) in self.threat_map:
                    self.threat_map[tuple(venue_loc)] += threat_level
                else:
                    self.threat_map[tuple(venue_loc)] = threat_level
    
    def _calculate_threat_level(self, incident: Dict) -> float:
        """Calculate threat level for an incident."""
        base_threats = {
            "suspicious_person": 0.8,
            "access_denied": 0.7,
            "crowd_surge": 0.6,
            "medical_event": 0.4,
        }
        return base_threats.get(incident.get("type", ""), 0.5)
    
    def _assess_all_incidents(self):
        """Assess priority of all active incidents."""
        self.incident_priorities = {}
        
        for incident in self.model.active_incidents:
            incident_id = incident.get("id")
            priority = self._calculate_incident_priority(incident)
            self.incident_priorities[incident_id] = priority
    
    def _calculate_incident_priority(self, incident: Dict) -> float:
        """Calculate priority score for incident."""
        priority = 0.5  # Base priority
        
        # Type-based priority
        type_priorities = {
            "suspicious_person": 0.9,
            "access_denied": 0.8,
            "crowd_surge": 0.7,
            "medical_event": 0.5,
        }
        priority = type_priorities.get(incident.get("type", ""), 0.5)
        
        # Crowd density factor
        incident_loc = incident.get("location")
        if incident_loc:
            nearby_athletes = self.model.get_agents_near(
                incident_loc, 0.02, agent_type=Athlete
            )
            crowd_factor = min(1.0, len(nearby_athletes) / 20)
            priority += 0.2 * crowd_factor
        
        return min(1.0, priority)
    
    def _coordinate_units(self):
        """Coordinate assignments across all security units."""
        # Prioritize incidents and assign units
        sorted_incidents = sorted(
            self.model.active_incidents,
            key=lambda i: self.incident_priorities.get(i.get("id"), 0.5),
            reverse=True
        )
        
        # Assign LVMPD units to highest priority incidents
        available_lvmpd = [u for u in self.model.lvmpd_units if u.status == "available"]
        for incident, unit in zip(sorted_incidents, available_lvmpd):
            if unit.status == "available":
                unit._dispatch_to_incident(incident)
    
    def _identify_hotspots(self):
        """Identify high-risk hotspots for predictive positioning."""
        self.hotspots = []
        
        # Find locations with high threat levels
        for location, threat_level in self.threat_map.items():
            if threat_level > 0.6:
                self.hotspots.append({
                    "location": location,
                    "threat_level": threat_level,
                    "type": "high_threat",
                })
        
        # Find high-traffic areas
        for venue_key, venue_data in self.model.venues.items():
            venue_loc = (venue_data.get("lat"), venue_data.get("lon"))
            nearby_athletes = self.model.get_agents_near(
                venue_loc, 0.02, agent_type=Athlete
            )
            if len(nearby_athletes) > 20:
                self.hotspots.append({
                    "location": venue_loc,
                    "threat_level": 0.5,
                    "type": "high_traffic",
                    "crowd_size": len(nearby_athletes),
                })
    
    def _dispatch_to_hotspots(self):
        """Dispatch units to hotspots for preventive positioning."""
        # Assign available security to hotspots
        available_security = [
            s for s in self.model.hotel_security
            if s.status == "patrolling"
        ]
        
        # Sort hotspots by threat level
        sorted_hotspots = sorted(
            self.hotspots,
            key=lambda h: h["threat_level"],
            reverse=True
        )
        
        # Assign security to top hotspots
        for hotspot, security in zip(sorted_hotspots[:len(available_security)], available_security):
            # Adjust patrol route to include hotspot
            hotspot_loc = hotspot["location"]
            if hotspot_loc not in security.patrol_route:
                # Insert hotspot into patrol route
                security.patrol_route.insert(0, hotspot_loc)
    
    def get_command_center_metrics(self) -> Dict:
        """Get command center metrics."""
        return {
            "active_threats": len(self.threat_map),
            "hotspots_identified": len(self.hotspots),
            "incidents_prioritized": len(self.incident_priorities),
            "coordination_tasks": len(self.coordination_queue),
        }
