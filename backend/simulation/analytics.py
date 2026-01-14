"""
Centralized analytics and heatmap tracking system.
Tracks time-series data, density maps, and incident patterns.
Type-safe with proper timestamps and configurable normalization.
"""

from typing import Dict, List, Optional, Tuple, Any, Protocol
from datetime import datetime, timedelta
from collections import defaultdict
from dataclasses import dataclass, field
import json


class SimulationModel(Protocol):
    """Protocol for simulation model interface."""
    current_time: datetime
    athletes: List[Any]
    active_incidents: List[Dict[str, Any]]
    medical_events: List[Dict[str, Any]]
    metrics: Dict[str, float]


@dataclass
class HeatmapCell:
    """Represents a cell in a heatmap grid."""
    x: int
    y: int
    center: Tuple[float, float]
    athlete_count: int = 0
    incident_count: int = 0
    medical_events: int = 0
    security_events: int = 0
    crowd_density: float = 0.0
    threat_level: float = 0.0
    response_times: List[float] = field(default_factory=list)
    timestamps: List[datetime] = field(default_factory=list)
    
    # Normalization parameters (configurable)
    max_athlete_count: int = 50
    max_incident_count: int = 10
    max_response_time: float = 600.0  # 10 minutes in seconds
    
    def add_athlete(self, timestamp: datetime):
        """Increment athlete count with timestamp."""
        self.athlete_count += 1
        self.timestamps.append(timestamp)
    
    def add_incident(self, incident_type: str, timestamp: datetime):
        """Add an incident to this cell with timestamp."""
        self.incident_count += 1
        if incident_type in ["medical_event", "medical_emergency"]:
            self.medical_events += 1
        else:
            self.security_events += 1
        self.timestamps.append(timestamp)
    
    def update_density(self, density: float):
        """Update crowd density."""
        self.crowd_density = max(self.crowd_density, density)
    
    def update_threat(self, threat: float):
        """Update threat level."""
        self.threat_level = max(self.threat_level, threat)
    
    def add_response_time(self, response_time: float):
        """Add a response time measurement."""
        self.response_times.append(response_time)
    
    def get_heat_value(self, metric: str = "athlete_count") -> float:
        """Get heat value for visualization (normalized 0-1)."""
        if metric == "athlete_count":
            return min(1.0, self.athlete_count / self.max_athlete_count)
        elif metric == "incident_count":
            return min(1.0, self.incident_count / self.max_incident_count)
        elif metric == "crowd_density":
            return self.crowd_density
        elif metric == "threat_level":
            return self.threat_level
        elif metric == "response_time":
            if self.response_times:
                avg = sum(self.response_times) / len(self.response_times)
                return min(1.0, avg / self.max_response_time)
            return 0.0
        return 0.0
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "x": self.x,
            "y": self.y,
            "center": self.center,
            "athlete_count": self.athlete_count,
            "incident_count": self.incident_count,
            "medical_events": self.medical_events,
            "security_events": self.security_events,
            "crowd_density": self.crowd_density,
            "threat_level": self.threat_level,
            "avg_response_time": (
                sum(self.response_times) / len(self.response_times)
                if self.response_times else 0.0
            ),
        }


class AnalyticsEngine:
    """Centralized analytics and heatmap tracking."""
    
    def __init__(
        self, 
        model: SimulationModel, 
        grid_size: int = 20,
        max_density: float = 100.0,
        decay_rate: float = 0.0,  # 0 = no decay, 0.1 = 10% decay per step
        max_athlete_count: int = 50,
        max_incident_count: int = 10,
        max_response_time: float = 600.0,
        track_agent_types: List[str] = None  # None = track all, or specify types
    ):
        self.model = model
        self.grid_size = grid_size
        self.max_density = max_density
        self.decay_rate = decay_rate
        self.max_athlete_count = max_athlete_count
        self.max_incident_count = max_incident_count
        self.max_response_time = max_response_time
        self.track_agent_types = track_agent_types  # None = all, or ['athlete', 'volunteer', etc.]
        self.heatmap: Dict[Tuple[int, int], HeatmapCell] = {}
        self.time_series_data: List[Dict] = []
        self.incident_patterns: Dict[str, List[Dict]] = defaultdict(list)
        self.agent_trajectories: Dict[int, List[Tuple[float, float, datetime]]] = {}
        self._temp_agent_id_counter = 10000  # For agents without unique_id
        
        # Initialize grid
        self._initialize_grid()
    
    def _initialize_grid(self):
        """Initialize heatmap grid with global normalization parameters."""
        cell_size = 1.0 / self.grid_size
        for x in range(self.grid_size):
            for y in range(self.grid_size):
                center = (
                    (x + 0.5) * cell_size,
                    (y + 0.5) * cell_size,
                )
                cell = HeatmapCell(x, y, center)
                # Set global normalization parameters
                cell.max_athlete_count = self.max_athlete_count
                cell.max_incident_count = self.max_incident_count
                cell.max_response_time = self.max_response_time
                self.heatmap[(x, y)] = cell
    
    def _get_cell(self, location: Tuple[float, float]) -> Optional[HeatmapCell]:
        """Get heatmap cell for a location."""
        cell_size = 1.0 / self.grid_size
        x = int(location[0] / cell_size)
        y = int(location[1] / cell_size)
        
        x = max(0, min(self.grid_size - 1, x))
        y = max(0, min(self.grid_size - 1, y))
        
        return self.heatmap.get((x, y))
    
    def record_step(self):
        """Record data for current simulation step."""
        timestamp = self.model.current_time
        
        step_data = {
            "timestamp": timestamp.isoformat(),
            "athlete_count": len(self.model.athletes),
            "active_incidents": len(self.model.active_incidents),
            "medical_events": len(self.model.medical_events),
            "metrics": self.model.metrics.copy(),
        }
        
        self.time_series_data.append(step_data)
        
        # Update heatmap
        self._update_heatmap(timestamp)
    
    def _update_heatmap(self, timestamp: datetime):
        """Update heatmap with current agent positions and incidents."""
        # Apply decay if enabled (ONLY if decay_rate > 0, otherwise reset)
        if self.decay_rate > 0:
            # Decay mode: reduce counts gradually
            for cell in self.heatmap.values():
                cell.athlete_count = max(0, int(cell.athlete_count * (1 - self.decay_rate)))
                cell.crowd_density *= (1 - self.decay_rate)
                # Also decay incident counts
                cell.incident_count = max(0, int(cell.incident_count * (1 - self.decay_rate)))
        else:
            # Reset mode: clear counts for fresh update
            for cell in self.heatmap.values():
                cell.athlete_count = 0
        
        # Track all agent types (not just athletes)
        all_agents = []
        if self.track_agent_types is None:
            # Track all agent types
            if hasattr(self.model, 'athletes'):
                all_agents.extend([('athlete', a) for a in self.model.athletes])
            if hasattr(self.model, 'volunteers'):
                all_agents.extend([('volunteer', a) for a in self.model.volunteers])
            if hasattr(self.model, 'hotel_security'):
                all_agents.extend([('security', a) for a in self.model.hotel_security])
            if hasattr(self.model, 'lvmpd_units'):
                all_agents.extend([('lvmpd', a) for a in self.model.lvmpd_units])
            if hasattr(self.model, 'amr_units'):
                all_agents.extend([('amr', a) for a in self.model.amr_units])
            if hasattr(self.model, 'buses'):
                all_agents.extend([('bus', a) for a in self.model.buses])
        else:
            # Track only specified types
            for agent_type in self.track_agent_types:
                agents = getattr(self.model, agent_type, [])
                all_agents.extend([(agent_type, a) for a in agents])
        
        # Record agent positions
        for agent_type, agent in all_agents:
            if not hasattr(agent, 'current_location') or not agent.current_location:
                continue
            
            # Validate location is within bounds
            loc = agent.current_location
            if isinstance(loc, (list, tuple)) and len(loc) >= 2:
                # Check if location is normalized [0,1] or needs normalization
                if loc[0] < 0 or loc[0] > 1 or loc[1] < 0 or loc[1] > 1:
                    # Out of bounds - log warning but still process
                    import warnings
                    warnings.warn(f"Agent {getattr(agent, 'unique_id', 'unknown')} location out of bounds: {loc}")
            
            cell = self._get_cell(agent.current_location)
            if cell:
                # Only count athletes in heatmap (or all if configured)
                if agent_type == 'athlete':
                    cell.add_athlete(timestamp)
                
                # Track trajectory with timestamp (for all tracked types)
                agent_id = getattr(agent, 'unique_id', None)
                if agent_id is None:
                    # Assign temporary ID for tracking
                    agent_id = self._temp_agent_id_counter
                    self._temp_agent_id_counter += 1
                    import warnings
                    warnings.warn(f"Agent without unique_id assigned temp ID: {agent_id}")
                
                if agent_id not in self.agent_trajectories:
                    self.agent_trajectories[agent_id] = []
                self.agent_trajectories[agent_id].append(
                    (agent.current_location[0], agent.current_location[1], timestamp)
                )
        
        # Record incidents (avoid double counting with medical events)
        seen_incident_locations = set()
        for incident in self.model.active_incidents:
            incident_id = incident.get("id")
            incident_type = incident.get("type", "unknown")
            incident_loc = incident.get("location")
            
            if not incident_loc:
                continue
            
            # Create location key to avoid double counting
            loc_key = tuple(incident_loc) if isinstance(incident_loc, (list, tuple)) else incident_loc
            
            # Skip if already counted (check by location + type)
            if (loc_key, incident_type) in seen_incident_locations:
                continue
            seen_incident_locations.add((loc_key, incident_type))
            
            cell = self._get_cell(incident_loc)
            if cell:
                cell.add_incident(incident_type, timestamp)
                # Update threat level based on incidents
                threat_increase = 0.2 if incident_type == "security_threat" else 0.1
                cell.update_threat(min(1.0, cell.threat_level + threat_increase))
        
        # Record medical events (only if not already in active_incidents)
        for med_event in self.model.medical_events:
            med_loc = med_event.get("location")
            if not med_loc:
                continue
            
            # Check if this medical event is already counted as an incident
            med_loc_key = tuple(med_loc) if isinstance(med_loc, (list, tuple)) else med_loc
            if (med_loc_key, "medical_event") in seen_incident_locations:
                continue  # Already counted
            
            cell = self._get_cell(med_loc)
            if cell:
                cell.add_incident("medical_event", timestamp)
                # Update threat level for medical events
                cell.update_threat(min(1.0, cell.threat_level + 0.15))
        
        # Calculate crowd density and update threat based on density
        total_athletes = sum(cell.athlete_count for cell in self.heatmap.values())
        dynamic_max_density = max(self.max_density, total_athletes * 1.2)  # Dynamic scaling
        
        for cell in self.heatmap.values():
            if cell.athlete_count > 0:
                density = self._calculate_crowd_density(cell, dynamic_max_density)
                cell.update_density(density)
                # Update threat level based on crowd density
                if density > 0.7:
                    cell.update_threat(min(1.0, cell.threat_level + 0.1))
    
    def _calculate_crowd_density(self, cell: HeatmapCell, max_density: float = None) -> float:
        """Calculate crowd density for a cell with dynamic max scaling."""
        if max_density is None:
            max_density = self.max_density
        
        # Count athletes in this cell and adjacent cells
        total_count = cell.athlete_count
        
        # Check adjacent cells
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue
                adj_x = cell.x + dx
                adj_y = cell.y + dy
                if 0 <= adj_x < self.grid_size and 0 <= adj_y < self.grid_size:
                    adj_cell = self.heatmap.get((adj_x, adj_y))
                    if adj_cell:
                        total_count += adj_cell.athlete_count
        
        # Normalize to 0-1 using dynamic max_density
        return min(1.0, total_count / max_density)
    
    def record_incident_pattern(
        self, 
        incident_type: str, 
        location: Tuple[float, float], 
        metadata: Dict = None
    ):
        """Record an incident pattern for analysis."""
        pattern = {
            "type": incident_type,
            "location": location,
            "timestamp": self.model.current_time.isoformat(),
            "metadata": metadata or {},
        }
        self.incident_patterns[incident_type].append(pattern)
    
    def get_heatmap_data(self, metric: str = "athlete_count") -> List[Dict]:
        """Get heatmap data for visualization."""
        return [
            {
                "x": cell.x,
                "y": cell.y,
                "center": cell.center,
                "value": cell.get_heat_value(metric),
                "details": cell.to_dict(),
            }
            for cell in self.heatmap.values()
        ]
    
    def get_hotspots(
        self, 
        metric: str = "athlete_count", 
        threshold: float = 0.7
    ) -> List[Dict]:
        """Get hotspots (high-value cells) for a metric."""
        hotspots = []
        for cell in self.heatmap.values():
            value = cell.get_heat_value(metric)
            if value >= threshold:
                hotspots.append({
                    "location": cell.center,
                    "value": value,
                    "details": cell.to_dict(),
                })
        return hotspots
    
    def get_time_series(
        self, 
        metric: str, 
        start_time: Optional[datetime] = None, 
        end_time: Optional[datetime] = None
    ) -> List[Dict]:
        """Get time series data for a metric."""
        filtered = self.time_series_data
        
        if start_time:
            filtered = [
                d for d in filtered 
                if datetime.fromisoformat(d["timestamp"]) >= start_time
            ]
        if end_time:
            filtered = [
                d for d in filtered 
                if datetime.fromisoformat(d["timestamp"]) <= end_time
            ]
        
        return [
            {
                "timestamp": d["timestamp"],
                "value": d.get(metric, d.get("metrics", {}).get(metric, 0)),
            }
            for d in filtered
        ]
    
    def get_incident_analysis(self) -> Dict:
        """Get analysis of incident patterns."""
        analysis = {}
        
        for incident_type, patterns in self.incident_patterns.items():
            if not patterns:
                continue
            
            # Calculate statistics
            locations = [p["location"] for p in patterns]
            
            # Find hotspots (locations with multiple incidents)
            location_counts = defaultdict(int)
            for loc in locations:
                location_counts[tuple(loc)] += 1
            
            hotspots = [
                {"location": list(loc), "count": count}
                for loc, count in location_counts.items()
                if count > 1
            ]
            
            analysis[incident_type] = {
                "total_count": len(patterns),
                "hotspots": hotspots,
                "first_occurrence": patterns[0]["timestamp"] if patterns else None,
                "last_occurrence": patterns[-1]["timestamp"] if patterns else None,
            }
        
        return analysis
    
    def get_agent_trajectory(
        self, 
        agent_id: int
    ) -> List[Tuple[float, float, datetime]]:
        """Get trajectory for an agent (with timestamps)."""
        return self.agent_trajectories.get(agent_id, [])
    
    def export_data(self, filepath: str):
        """Export analytics data to JSON with consistent ISO format timestamps."""
        # Convert all timestamps to ISO format
        def convert_timestamps(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            elif isinstance(obj, dict):
                return {k: convert_timestamps(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_timestamps(item) for item in obj]
            return obj
        
        data = {
            "time_series": convert_timestamps(self.time_series_data),
            "heatmap": {
                f"{x}_{y}": cell.to_dict()
                for (x, y), cell in self.heatmap.items()
            },
            "incident_patterns": convert_timestamps(self.incident_patterns),
            "agent_trajectories": {
                str(agent_id): [
                    {"x": x, "y": y, "timestamp": ts.isoformat()}
                    for x, y, ts in trajectory
                ]
                for agent_id, trajectory in self.agent_trajectories.items()
            },
        }
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2, default=str)
    
    def get_summary_statistics(self) -> Dict:
        """Get summary statistics."""
        if not self.time_series_data:
            return {}
        
        latest = self.time_series_data[-1]
        
        return {
            "total_steps": len(self.time_series_data),
            "current_athlete_count": latest.get("athlete_count", 0),
            "current_incidents": latest.get("active_incidents", 0),
            "total_medical_events": latest.get("medical_events", 0),
            "hotspots_identified": len(self.get_hotspots()),
            "incident_types": list(self.incident_patterns.keys()),
        }
