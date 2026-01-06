"""
Global alert prioritization system with threat hierarchy.
Provides centralized coordination for all security units.
"""

from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
from datetime import datetime
import heapq


class ThreatLevel(Enum):
    """Threat level hierarchy."""
    CRITICAL = 1  # Immediate response required
    HIGH = 2      # Urgent response
    MEDIUM = 3    # Standard response
    LOW = 4       # Routine response
    INFO = 5      # Informational only


class AlertCategory(Enum):
    """Categories of alerts/incidents."""
    SECURITY_THREAT = "security_threat"
    MEDICAL_EMERGENCY = "medical_emergency"
    CROWD_MANAGEMENT = "crowd_management"
    ACCESS_CONTROL = "access_control"
    TRANSPORTATION = "transportation"
    WEATHER = "weather"
    GENERAL = "general"


class PrioritizedAlert:
    """An alert with priority scoring."""
    
    def __init__(
        self,
        alert_id: str,
        alert_type: str,
        location: Tuple[float, float],
        category: AlertCategory,
        base_priority: ThreatLevel,
        timestamp: datetime,
        metadata: Dict = None,
    ):
        self.alert_id = alert_id
        self.alert_type = alert_type
        self.location = location
        self.category = category
        self.base_priority = base_priority
        self.timestamp = timestamp
        self.metadata = metadata or {}
        
        # Dynamic priority factors
        self.crowd_density = 0.0
        self.proximity_to_vip = False
        self.weather_factor = 1.0
        self.time_factor = 1.0
        self.escalation_count = 0
        
        # Calculated priority score (lower = higher priority)
        self.priority_score = self._calculate_priority_score()
    
    def _calculate_priority_score(self) -> float:
        """Calculate overall priority score (lower = higher priority)."""
        base_score = self.base_priority.value
        
        # Crowd density multiplier (higher density = higher priority)
        crowd_multiplier = 1.0 + (self.crowd_density * 0.3)
        
        # VIP proximity (critical if near VIP)
        vip_multiplier = 0.5 if self.proximity_to_vip else 1.0
        
        # Weather factor (heat alerts increase priority)
        weather_multiplier = self.weather_factor
        
        # Time factor (older incidents may escalate)
        time_multiplier = 1.0 + (self.escalation_count * 0.2)
        
        return base_score * crowd_multiplier * vip_multiplier * weather_multiplier * time_multiplier
    
    def update_factors(self, crowd_density: float = None, proximity_to_vip: bool = None,
                      weather_factor: float = None, escalation: bool = False):
        """Update dynamic priority factors."""
        if crowd_density is not None:
            self.crowd_density = crowd_density
        if proximity_to_vip is not None:
            self.proximity_to_vip = proximity_to_vip
        if weather_factor is not None:
            self.weather_factor = weather_factor
        if escalation:
            self.escalation_count += 1
        
        self.priority_score = self._calculate_priority_score()
    
    def __lt__(self, other):
        """For priority queue ordering."""
        return self.priority_score < other.priority_score
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for API."""
        return {
            "alert_id": self.alert_id,
            "alert_type": self.alert_type,
            "location": self.location,
            "category": self.category.value,
            "threat_level": self.base_priority.name,
            "priority_score": self.priority_score,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
            "crowd_density": self.crowd_density,
            "proximity_to_vip": self.proximity_to_vip,
            "escalation_count": self.escalation_count,
        }


class GlobalAlertManager:
    """Manages global alert prioritization and coordination."""
    
    def __init__(self, model):
        self.model = model
        self.active_alerts: Dict[str, PrioritizedAlert] = {}
        self.alert_queue = []  # Priority queue
        self.alert_history: List[PrioritizedAlert] = []
        self.unit_assignments: Dict[str, str] = {}  # alert_id -> unit_id
        
        # Threat level mappings
        self.threat_mappings = {
            "suspicious_person": ThreatLevel.CRITICAL,
            "access_denied": ThreatLevel.HIGH,
            "crowd_surge": ThreatLevel.HIGH,
            "medical_event": ThreatLevel.CRITICAL,
            "fire": ThreatLevel.CRITICAL,
            "security_breach": ThreatLevel.CRITICAL,
            "traffic_incident": ThreatLevel.MEDIUM,
            "weather_alert": ThreatLevel.MEDIUM,
        }
        
        # Category mappings
        self.category_mappings = {
            "suspicious_person": AlertCategory.SECURITY_THREAT,
            "access_denied": AlertCategory.ACCESS_CONTROL,
            "crowd_surge": AlertCategory.CROWD_MANAGEMENT,
            "medical_event": AlertCategory.MEDICAL_EMERGENCY,
            "fire": AlertCategory.SECURITY_THREAT,
            "security_breach": AlertCategory.SECURITY_THREAT,
            "traffic_incident": AlertCategory.TRANSPORTATION,
            "weather_alert": AlertCategory.WEATHER,
        }
    
    def register_alert(
        self,
        alert_id: str,
        alert_type: str,
        location: Tuple[float, float],
        timestamp: datetime = None,
        metadata: Dict = None,
    ) -> PrioritizedAlert:
        """Register a new alert and prioritize it."""
        if timestamp is None:
            timestamp = self.model.current_time
        
        base_priority = self.threat_mappings.get(alert_type, ThreatLevel.MEDIUM)
        category = self.category_mappings.get(alert_type, AlertCategory.GENERAL)
        
        alert = PrioritizedAlert(
            alert_id=alert_id,
            alert_type=alert_type,
            location=location,
            category=category,
            base_priority=base_priority,
            timestamp=timestamp,
            metadata=metadata or {},
        )
        
        # Calculate dynamic factors
        self._update_alert_factors(alert)
        
        self.active_alerts[alert_id] = alert
        heapq.heappush(self.alert_queue, alert)
        self.alert_history.append(alert)
        
        return alert
    
    def _update_alert_factors(self, alert: PrioritizedAlert):
        """Update dynamic priority factors for an alert."""
        # Crowd density
        nearby_athletes = self.model.get_agents_near(
            alert.location, 0.02, agent_type=None
        )
        alert.crowd_density = min(1.0, len(nearby_athletes) / 30)
        
        # Weather factor
        weather = self.model.weather
        if weather.get("heat_alert", False) or weather.get("temp_C", 20) > 35:
            alert.weather_factor = 1.3  # Increase priority in heat
        else:
            alert.weather_factor = 1.0
        
        # VIP proximity (simplified - would check VIP locations in real implementation)
        alert.proximity_to_vip = False  # TODO: Implement VIP tracking
    
    def update_all_alerts(self):
        """Update all active alerts with current factors."""
        for alert in self.active_alerts.values():
            self._update_alert_factors(alert)
            # Recalculate priority
            alert.priority_score = alert._calculate_priority_score()
        
        # Rebuild priority queue
        self.alert_queue = list(self.active_alerts.values())
        heapq.heapify(self.alert_queue)
    
    def get_highest_priority_alert(self) -> Optional[PrioritizedAlert]:
        """Get the highest priority alert."""
        while self.alert_queue:
            alert = heapq.heappop(self.alert_queue)
            if alert.alert_id in self.active_alerts:
                # Still active
                heapq.heappush(self.alert_queue, alert)
                return alert
        return None
    
    def get_alerts_by_priority(self, limit: int = 10) -> List[PrioritizedAlert]:
        """Get top N alerts by priority."""
        alerts = []
        temp_queue = []
        
        while self.alert_queue and len(alerts) < limit:
            alert = heapq.heappop(self.alert_queue)
            if alert.alert_id in self.active_alerts:
                alerts.append(alert)
                temp_queue.append(alert)
        
        # Restore queue
        for alert in temp_queue:
            heapq.heappush(self.alert_queue, alert)
        
        return alerts
    
    def get_alerts_by_category(self, category: AlertCategory) -> List[PrioritizedAlert]:
        """Get all alerts in a specific category."""
        return [
            alert for alert in self.active_alerts.values()
            if alert.category == category
        ]
    
    def get_alerts_by_threat_level(self, threat_level: ThreatLevel) -> List[PrioritizedAlert]:
        """Get all alerts at a specific threat level."""
        return [
            alert for alert in self.active_alerts.values()
            if alert.base_priority == threat_level
        ]
    
    def assign_unit(self, alert_id: str, unit_id: str):
        """Assign a unit to an alert."""
        self.unit_assignments[alert_id] = unit_id
    
    def resolve_alert(self, alert_id: str):
        """Resolve an alert."""
        if alert_id in self.active_alerts:
            del self.active_alerts[alert_id]
        if alert_id in self.unit_assignments:
            del self.unit_assignments[alert_id]
        
        # Rebuild queue without resolved alert
        self.alert_queue = [
            alert for alert in self.alert_queue
            if alert.alert_id != alert_id
        ]
        heapq.heapify(self.alert_queue)
    
    def escalate_alert(self, alert_id: str):
        """Escalate an alert (increase priority)."""
        if alert_id in self.active_alerts:
            alert = self.active_alerts[alert_id]
            alert.update_factors(escalation=True)
            # Rebuild queue
            self.alert_queue = list(self.active_alerts.values())
            heapq.heapify(self.alert_queue)
    
    def get_alert_statistics(self) -> Dict:
        """Get statistics about alerts."""
        total = len(self.active_alerts)
        by_threat = {
            level.name: len(self.get_alerts_by_threat_level(level))
            for level in ThreatLevel
        }
        by_category = {
            cat.value: len(self.get_alerts_by_category(cat))
            for cat in AlertCategory
        }
        
        return {
            "total_active": total,
            "by_threat_level": by_threat,
            "by_category": by_category,
            "assigned": len(self.unit_assignments),
            "unassigned": total - len(self.unit_assignments),
            "historical_total": len(self.alert_history),
        }

