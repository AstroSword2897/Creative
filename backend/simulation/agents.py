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
        super().__init__(unique_id, model)
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
        """Agent behavior on each simulation step."""
        # Check for medical event based on risk and weather
        if not self.medical_event:
            self._check_medical_risk()
        
        # Handle movement
        if self.status == "traveling":
            self._move()
        elif self.status == "waiting":
            self._check_schedule()
        
        # Update position in model
        if self.current_location:
            self.model.space.move_agent(self, self.current_location)
    
    def _check_medical_risk(self):
        """Check if athlete experiences medical event based on risk factors."""
        weather = self.model.weather
        temp_factor = 1.0
        if weather.get("temp_C", 20) > 35:
            temp_factor = 1.5 + (weather["temp_C"] - 35) * 0.1
        
        risk = self.medical_risk * temp_factor
        if random.random() < risk * self.model.step_duration / 3600:  # Per hour probability
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
        """Move along planned path."""
        if not self.current_path or self.path_index >= len(self.current_path):
            # Arrived
            self.status = "at_venue"
            self.current_location = self.target_location
            return
        
        # Move towards next waypoint
        next_point = self.current_path[self.path_index]
        distance = self._distance(self.current_location, next_point)
        step_distance = self.walking_speed * self.model.step_duration
        
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
        super().__init__(unique_id, model)
        self.assignment = assignment
        self.patrol_area = patrol_area or []
        self.response_speed = response_speed
        self.current_location = None
        self.status = "patrolling"  # patrolling, responding, assisting
        self.current_assignment = None
        
    def step(self):
        """Volunteer behavior on each step."""
        if self.status == "responding":
            self._respond_to_incident()
        elif self.status == "patrolling":
            self._patrol()
        elif self.status == "assisting":
            self._assist_athlete()
    
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
        step_distance = speed * self.model.step_duration
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
    """Represents hotel security personnel (rovers)."""
    
    def __init__(
        self,
        unique_id: int,
        model,
        hotel_id: str,
        patrol_route: Optional[List[Tuple[float, float]]] = None,
        alert_threshold: float = 0.7,
    ):
        super().__init__(unique_id, model)
        self.hotel_id = hotel_id
        self.patrol_route = patrol_route or []
        self.alert_threshold = alert_threshold
        self.current_location = None
        self.status = "patrolling"
        self.route_index = 0
        
    def step(self):
        """Security rover behavior."""
        if self.status == "patrolling":
            self._patrol_route()
        elif self.status == "responding":
            self._respond_to_alert()
    
    def _patrol_route(self):
        """Follow patrol route."""
        if not self.patrol_route:
            return
        
        if self.route_index >= len(self.patrol_route):
            self.route_index = 0
        
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
    
    def _respond_to_alert(self):
        """Respond to access control alert."""
        # Simplified: move to alert location
        alert = self.model.get_active_alert(self.hotel_id)
        if alert:
            alert_loc = alert.get("location")
            if alert_loc and self.current_location:
                distance = self._distance(self.current_location, alert_loc)
                if distance < 0.001:
                    self.status = "patrolling"
                    self.model.resolve_alert(self.hotel_id, alert["id"])
                else:
                    self.current_location = self._move_towards(
                        self.current_location, alert_loc, 2.0
                    )
    
    def _move_towards(self, start: Tuple[float, float], end: Tuple[float, float], speed: float) -> Tuple[float, float]:
        """Move towards target."""
        distance = self._distance(start, end)
        step_distance = speed * self.model.step_duration
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


class LVMPDUnit(Agent):
    """Represents an LVMPD security unit."""
    
    def __init__(
        self,
        unique_id: int,
        model,
        response_radius: float = 0.05,  # degrees
        dispatch_time: float = 120.0,  # seconds
    ):
        super().__init__(unique_id, model)
        self.response_radius = response_radius
        self.dispatch_time = dispatch_time
        self.current_location = None
        self.status = "available"  # available, dispatched, on_scene
        self.current_incident = None
        self.dispatch_start_time = None
        
    def step(self):
        """LVMPD unit behavior."""
        if self.status == "dispatched":
            self._respond()
        elif self.status == "on_scene":
            self._handle_incident()
    
    def _respond(self):
        """Respond to dispatched incident."""
        if not self.current_incident:
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
            else:
                self.current_location = self._move_towards(
                    self.current_location, incident_loc, 15.0  # Fast response
                )
    
    def _handle_incident(self):
        """Handle incident on scene."""
        if self.current_incident:
            # Resolve incident after handling time
            incident_id = self.current_incident.get("id")
            if incident_id:
                self.model.resolve_incident(incident_id)
                self.status = "available"
                self.current_incident = None
    
    def _move_towards(self, start: Tuple[float, float], end: Tuple[float, float], speed: float) -> Tuple[float, float]:
        """Move towards target."""
        distance = self._distance(start, end)
        step_distance = speed * self.model.step_duration
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


class AMRUnit(Agent):
    """Represents an AMR (American Medical Response) unit."""
    
    def __init__(
        self,
        unique_id: int,
        model,
        transport_capacity: int = 1,
        eta_base: float = 300.0,  # seconds
    ):
        super().__init__(unique_id, model)
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
        step_distance = speed * self.model.step_duration
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
        super().__init__(unique_id, model)
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
        step_distance = speed * self.model.step_duration
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

