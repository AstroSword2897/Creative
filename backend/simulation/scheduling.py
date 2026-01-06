"""
Dynamic scheduling system for athletes with delay tracking and adjustment.
Handles bus delays, traffic, crowding, weather, and medical events.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
import heapq
import random


class DelayType(Enum):
    """Types of delays that can affect athlete schedules."""
    BUS_DELAY = "bus_delay"
    TRAFFIC = "traffic"
    CROWDING = "crowding"
    WEATHER = "weather"
    MEDICAL_EVENT = "medical_event"
    SECURITY_INCIDENT = "security_incident"
    ACCESS_CONTROL = "access_control"


class ScheduleEvent:
    """Represents a scheduled event for an athlete."""
    
    def __init__(
        self,
        event_time: datetime,
        location: Tuple[float, float],
        event_type: str,
        priority: int = 5,  # 1-10, higher = more important
        flexible: bool = True,  # Can be rescheduled
    ):
        self.original_time = event_time
        self.current_time = event_time
        self.location = location
        self.event_type = event_type
        self.priority = priority
        self.flexible = flexible
        self.delays = []  # List of (delay_type, duration, timestamp)
        self.total_delay = timedelta(0)
        self.completed = False
    
    def add_delay(self, delay_type: DelayType, duration: timedelta, reason: str = ""):
        """Add a delay to this event."""
        if not self.flexible:
            return False
        
        self.delays.append({
            "type": delay_type,
            "duration": duration,
            "timestamp": datetime.now(),
            "reason": reason,
        })
        self.total_delay += duration
        self.current_time += duration
        return True
    
    def get_adjusted_time(self) -> datetime:
        """Get the adjusted time accounting for all delays."""
        return self.current_time
    
    def is_overdue(self, current_time: datetime) -> bool:
        """Check if event is overdue."""
        return current_time > self.current_time and not self.completed
    
    def get_delay_summary(self) -> Dict:
        """Get summary of delays."""
        return {
            "total_delay_minutes": self.total_delay.total_seconds() / 60,
            "delay_count": len(self.delays),
            "delays_by_type": {
                delay_type.value: sum(
                    1 for d in self.delays if d["type"] == delay_type
                )
                for delay_type in DelayType
            },
        }


class DynamicScheduler:
    """Manages dynamic scheduling with delay tracking and adjustment."""
    
    def __init__(self, model):
        self.model = model
        self.athlete_schedules: Dict[int, List[ScheduleEvent]] = {}
        self.delay_factors = {
            DelayType.BUS_DELAY: 0.1,  # 10% chance per bus interaction
            DelayType.TRAFFIC: 0.05,  # 5% chance per step in high-traffic area
            DelayType.CROWDING: 0.15,  # 15% chance in crowded areas
            DelayType.WEATHER: 0.0,  # Weather-based (calculated dynamically)
            DelayType.MEDICAL_EVENT: 0.02,  # 2% chance per step
            DelayType.SECURITY_INCIDENT: 0.03,  # 3% chance near incidents
            DelayType.ACCESS_CONTROL: 0.05,  # 5% chance at access points
        }
    
    def create_schedule(
        self,
        athlete_id: int,
        events: List[Dict[str, Any]]
    ) -> List[ScheduleEvent]:
        """Create a schedule for an athlete from event list."""
        schedule = []
        for event in events:
            event_time = datetime.strptime(
                event.get("time", "08:00"),
                "%H:%M"
            ).replace(
                year=self.model.start_time.year,
                month=self.model.start_time.month,
                day=self.model.start_time.day,
            )
            
            location = event.get("location")
            if isinstance(location, str):
                # Look up venue location
                venue = self.model.venues.get(location)
                if venue:
                    location = (venue["lat"], venue["lon"])
            
            schedule_event = ScheduleEvent(
                event_time=event_time,
                location=location,
                event_type=event.get("type", "general"),
                priority=event.get("priority", 5),
                flexible=event.get("flexible", True),
            )
            schedule.append(schedule_event)
        
        self.athlete_schedules[athlete_id] = schedule
        return schedule
    
    def check_delays(self, athlete_id: int, athlete_location: Tuple[float, float]) -> List[Dict]:
        """Check for delays affecting athlete and return list of new delays."""
        if athlete_id not in self.athlete_schedules:
            return []
        
        schedule = self.athlete_schedules[athlete_id]
        active_events = [e for e in schedule if not e.completed and e.current_time <= self.model.current_time + timedelta(hours=1)]
        
        if not active_events:
            return []
        
        new_delays = []
        
        # Check bus delays
        nearby_buses = self.model.get_agents_near(athlete_location, 0.01, agent_type=None)
        for bus in nearby_buses:
            if hasattr(bus, 'status') and bus.status != "in_service":
                if self._should_delay(DelayType.BUS_DELAY):
                    delay = timedelta(minutes=random.randint(5, 15))
                    new_delays.append({
                        "type": DelayType.BUS_DELAY,
                        "duration": delay,
                        "reason": f"Bus {bus.unique_id} delayed",
                    })
        
        # Check traffic (high athlete density)
        nearby_athletes = self.model.get_agents_near(athlete_location, 0.02, agent_type=None)
        if len(nearby_athletes) > 20:
            if self._should_delay(DelayType.TRAFFIC):
                delay = timedelta(minutes=random.randint(2, 10))
                new_delays.append({
                    "type": DelayType.TRAFFIC,
                    "duration": delay,
                    "reason": "High traffic congestion",
                })
        
        # Check crowding (very high density)
        if len(nearby_athletes) > 30:
            if self._should_delay(DelayType.CROWDING):
                delay = timedelta(minutes=random.randint(5, 20))
                new_delays.append({
                    "type": DelayType.CROWDING,
                    "duration": delay,
                    "reason": "Crowd surge at location",
                })
        
        # Check weather delays
        weather = self.model.weather
        if weather.get("heat_alert", False) or weather.get("temp_C", 20) > 35:
            if self._should_delay(DelayType.WEATHER, base_probability=0.1):
                delay = timedelta(minutes=random.randint(3, 8))
                new_delays.append({
                    "type": DelayType.WEATHER,
                    "duration": delay,
                    "reason": "Heat alert - reduced mobility",
                })
        
        # Check security incidents
        for incident in self.model.active_incidents:
            incident_loc = incident.get("location")
            if incident_loc:
                distance = self._distance(athlete_location, incident_loc)
                if distance < 0.01:  # Near incident
                    if self._should_delay(DelayType.SECURITY_INCIDENT):
                        delay = timedelta(minutes=random.randint(5, 15))
                        new_delays.append({
                            "type": DelayType.SECURITY_INCIDENT,
                            "duration": delay,
                            "reason": f"Security incident at location",
                        })
        
        return new_delays
    
    def apply_delays(self, athlete_id: int, delays: List[Dict]):
        """Apply delays to athlete's schedule."""
        if athlete_id not in self.athlete_schedules:
            return
        
        schedule = self.athlete_schedules[athlete_id]
        active_events = [e for e in schedule if not e.completed]
        
        for delay_info in delays:
            delay_type = delay_info["type"]
            duration = delay_info["duration"]
            reason = delay_info.get("reason", "")
            
            # Apply to next flexible event
            for event in active_events:
                if event.flexible:
                    event.add_delay(delay_type, duration, reason)
                    break
    
    def get_next_event(self, athlete_id: int) -> Optional[ScheduleEvent]:
        """Get the next scheduled event for an athlete."""
        if athlete_id not in self.athlete_schedules:
            return None
        
        schedule = self.athlete_schedules[athlete_id]
        upcoming = [e for e in schedule if not e.completed and e.current_time > self.model.current_time]
        
        if not upcoming:
            return None
        
        return min(upcoming, key=lambda e: e.current_time)
    
    def get_current_event(self, athlete_id: int) -> Optional[ScheduleEvent]:
        """Get the current event (if any) for an athlete."""
        if athlete_id not in self.athlete_schedules:
            return None
        
        schedule = self.athlete_schedules[athlete_id]
        current = [
            e for e in schedule
            if not e.completed
            and e.current_time <= self.model.current_time
            and (e.current_time + timedelta(minutes=30)) >= self.model.current_time
        ]
        
        if not current:
            return None
        
        return max(current, key=lambda e: e.current_time)
    
    def complete_event(self, athlete_id: int, event_type: str = None):
        """Mark an event as completed."""
        if athlete_id not in self.athlete_schedules:
            return
        
        schedule = self.athlete_schedules[athlete_id]
        for event in schedule:
            if not event.completed:
                if event_type is None or event.event_type == event_type:
                    event.completed = True
                    break
    
    def _should_delay(self, delay_type: DelayType, base_probability: float = None) -> bool:
        """Check if a delay should occur based on probability."""
        prob = base_probability or self.delay_factors.get(delay_type, 0.0)
        return random.random() < prob * (self.model.step_duration.total_seconds() / 3600)  # Per hour
    
    def _distance(self, p1: Tuple[float, float], p2: Tuple[float, float]) -> float:
        """Calculate distance between two points."""
        return ((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)**0.5
    
    def get_schedule_metrics(self, athlete_id: int) -> Dict:
        """Get scheduling metrics for an athlete."""
        if athlete_id not in self.athlete_schedules:
            return {}
        
        schedule = self.athlete_schedules[athlete_id]
        total_delays = sum(len(e.delays) for e in schedule)
        total_delay_time = sum(e.total_delay for e in schedule)
        
        return {
            "total_events": len(schedule),
            "completed_events": sum(1 for e in schedule if e.completed),
            "total_delays": total_delays,
            "total_delay_minutes": total_delay_time.total_seconds() / 60,
            "events": [
                {
                    "type": e.event_type,
                    "original_time": e.original_time.isoformat(),
                    "adjusted_time": e.current_time.isoformat(),
                    "delays": len(e.delays),
                    "completed": e.completed,
                }
                for e in schedule
            ],
        }

