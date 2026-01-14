"""
Async Global Alert Manager with WebSocket integration.
Provides real-time alert streaming and dynamic priority updates.
"""

import asyncio
from typing import Dict, List, Optional, Tuple, Set, Callable
from datetime import datetime, timedelta
from enum import Enum
import heapq
import json
from collections import defaultdict

from .alert_prioritization import (
    PrioritizedAlert, ThreatLevel, AlertCategory, GlobalAlertManager
)


class AsyncGlobalAlertManager(GlobalAlertManager):
    """
    Async version of GlobalAlertManager with WebSocket support.
    Thread-safe and optimized for real-time updates.
    """
    
    def __init__(self, model, max_density: int = 30, vip_locations: List[Tuple[float, float]] = None):
        super().__init__(model)
        self.max_density = max_density
        self.vip_locations = vip_locations or []
        self._lock = asyncio.Lock()
        self._dirty_alerts: Set[str] = set()  # Alerts that need priority recalculation
        self._alert_ttl: Dict[str, datetime] = {}  # Time-to-live for alerts
        self._subscribers: Set[Callable] = set()  # WebSocket subscribers
        
        # Configurable TTL by threat level (in minutes)
        self.ttl_by_threat = {
            ThreatLevel.INFO: 30,  # Info alerts expire after 30 min
            ThreatLevel.LOW: 60,   # Low priority: 1 hour
            ThreatLevel.MEDIUM: 120,  # Medium: 2 hours
            ThreatLevel.HIGH: None,   # High: no expiration
            ThreatLevel.CRITICAL: None,  # Critical: no expiration
        }
    
    async def register_alert(
        self,
        alert_id: str,
        alert_type: str,
        location: Tuple[float, float],
        timestamp: datetime = None,
        metadata: Dict = None,
    ) -> PrioritizedAlert:
        """Register a new alert asynchronously."""
        async with self._lock:
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
            await self._update_alert_factors_async(alert)
            
            self.active_alerts[alert_id] = alert
            heapq.heappush(self.alert_queue, alert)
            self.alert_history.append(alert)
            
            # Set TTL if applicable
            ttl_minutes = self.ttl_by_threat.get(base_priority)
            if ttl_minutes:
                self._alert_ttl[alert_id] = timestamp + timedelta(minutes=ttl_minutes)
            
            # Notify subscribers
            await self._notify_subscribers('alert_registered', alert)
            
            # Log in development mode
            import os
            if os.getenv('DEBUG', '').lower() == 'true':
                print(f"🔔 Registered alert {alert_id} with priority {alert.priority_score:.2f}")
            
            return alert
    
    async def _update_alert_factors_async(self, alert: PrioritizedAlert):
        """Update dynamic priority factors asynchronously."""
        # Crowd density with configurable max
        nearby_athletes = self.model.get_agents_near(
            alert.location, 0.02, agent_type=None
        )
        alert.crowd_density = min(1.0, len(nearby_athletes) / self.max_density)
        
        # VIP proximity check
        alert.proximity_to_vip = await self._check_vip_proximity(alert.location)
        
        # Weather factor
        weather = self.model.weather
        if weather.get("heat_alert", False) or weather.get("temp_C", 20) > 35:
            alert.weather_factor = 1.3
        else:
            alert.weather_factor = 1.0
    
    async def _check_vip_proximity(self, location: Tuple[float, float], radius: float = 0.01) -> bool:
        """Check if location is near any VIP."""
        for vip_loc in self.vip_locations:
            distance = ((location[0] - vip_loc[0])**2 + (location[1] - vip_loc[1])**2)**0.5
            if distance <= radius:
                return True
        return False
    
    async def update_all_alerts(self):
        """Update all active alerts with current factors (optimized)."""
        async with self._lock:
            # Only update dirty alerts or all if queue is small
            alerts_to_update = (
                [self.active_alerts[aid] for aid in self._dirty_alerts if aid in self.active_alerts]
                if self._dirty_alerts and len(self.active_alerts) > 10
                else list(self.active_alerts.values())
            )
            
            for alert in alerts_to_update:
                await self._update_alert_factors_async(alert)
                alert.priority_score = alert._calculate_priority_score()
            
            self._dirty_alerts.clear()
            
            # Lazy heap rebuild (only if needed)
            if alerts_to_update:
                self.alert_queue = list(self.active_alerts.values())
                heapq.heapify(self.alert_queue)
    
    async def mark_alert_dirty(self, alert_id: str):
        """Mark an alert as needing priority recalculation."""
        async with self._lock:
            self._dirty_alerts.add(alert_id)
    
    async def expire_alerts(self):
        """Remove expired alerts based on TTL."""
        async with self._lock:
            now = self.model.current_time
            expired = [
                alert_id for alert_id, expiry_time in self._alert_ttl.items()
                if expiry_time and now > expiry_time
            ]
            
            for alert_id in expired:
                if alert_id in self.active_alerts:
                    alert = self.active_alerts[alert_id]
                    await self._notify_subscribers('alert_expired', alert)
                    del self.active_alerts[alert_id]
                    del self._alert_ttl[alert_id]
            
            if expired:
                # Rebuild queue
                self.alert_queue = list(self.active_alerts.values())
                heapq.heapify(self.alert_queue)
    
    async def escalate_alert(self, alert_id: str):
        """Escalate an alert asynchronously."""
        async with self._lock:
            if alert_id in self.active_alerts:
                alert = self.active_alerts[alert_id]
                alert.update_factors(escalation=True)
                await self.mark_alert_dirty(alert_id)
                await self._notify_subscribers('alert_escalated', alert)
    
    async def assign_unit(self, alert_id: str, unit_id: str):
        """Assign a unit to an alert asynchronously."""
        async with self._lock:
            self.unit_assignments[alert_id] = unit_id
            if alert_id in self.active_alerts:
                alert = self.active_alerts[alert_id]
                await self._notify_subscribers('alert_assigned', alert, unit_id=unit_id)
    
    async def resolve_alert(self, alert_id: str):
        """Resolve an alert asynchronously."""
        async with self._lock:
            if alert_id in self.active_alerts:
                alert = self.active_alerts[alert_id]
                await self._notify_subscribers('alert_resolved', alert)
            
            if alert_id in self.active_alerts:
                del self.active_alerts[alert_id]
            if alert_id in self.unit_assignments:
                del self.unit_assignments[alert_id]
            if alert_id in self._alert_ttl:
                del self._alert_ttl[alert_id]
            
            # Rebuild queue
            self.alert_queue = [
                alert for alert in self.alert_queue
                if alert.alert_id != alert_id
            ]
            heapq.heapify(self.alert_queue)
    
    async def register_batch(self, alerts: List[Dict]) -> List[PrioritizedAlert]:
        """Register multiple alerts in batch."""
        results = []
        for alert_data in alerts:
            alert = await self.register_alert(
                alert_id=alert_data['alert_id'],
                alert_type=alert_data['alert_type'],
                location=alert_data['location'],
                timestamp=alert_data.get('timestamp'),
                metadata=alert_data.get('metadata'),
            )
            results.append(alert)
        return results
    
    async def _notify_subscribers(self, event_type: str, alert: PrioritizedAlert, **kwargs):
        """Notify all WebSocket subscribers of alert events."""
        if not self._subscribers:
            return
        
        message = {
            "type": "alert_update",
            "event": event_type,
            "alert": alert.to_dict(),
            **kwargs
        }
        
        # Notify all subscribers
        disconnected = set()
        for subscriber in self._subscribers:
            try:
                await subscriber(message)
            except Exception as e:
                print(f"Error notifying subscriber: {e}")
                disconnected.add(subscriber)
        
        # Remove disconnected subscribers
        self._subscribers -= disconnected
    
    def subscribe(self, callback: Callable):
        """Subscribe to alert updates."""
        self._subscribers.add(callback)
    
    def unsubscribe(self, callback: Callable):
        """Unsubscribe from alert updates."""
        self._subscribers.discard(callback)
    
    async def get_top_alerts(self, limit: int = 5) -> List[Dict]:
        """Get top N alerts for dashboard display."""
        alerts = self.get_alerts_by_priority(limit)
        return [alert.to_dict() for alert in alerts]
    
    async def get_alert_metrics(self) -> Dict:
        """Get real-time alert metrics for analytics."""
        stats = self.get_alert_statistics()
        
        # Add average priority score per category
        category_scores = defaultdict(list)
        for alert in self.active_alerts.values():
            category_scores[alert.category.value].append(alert.priority_score)
        
        avg_scores = {
            cat: sum(scores) / len(scores) if scores else 0
            for cat, scores in category_scores.items()
        }
        
        return {
            **stats,
            "average_priority_by_category": avg_scores,
            "expired_count": len(self._alert_ttl),
        }
    
    def to_dict(self) -> Dict:
        """Convert to dictionary with unit assignments."""
        result = super().to_dict() if hasattr(super(), 'to_dict') else {}
        return {
            **result,
            "unit_assignments": {
                alert_id: unit_id
                for alert_id, unit_id in self.unit_assignments.items()
                if alert_id in self.active_alerts
            }
        }

