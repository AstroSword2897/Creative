"""
Centralized analytics and heatmap tracking system.
Tracks time-series data, density maps, and incident patterns.
"""

from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from collections import defaultdict
import json


class HeatmapCell:
    """Represents a cell in a heatmap grid."""
    
    def __init__(self, x: int, y: int, center: Tuple[float, float]):
        self.x = x
        self.y = y
        self.center = center
        self.athlete_count = 0
        self.incident_count = 0
        self.medical_events = 0
        self.security_events = 0
        self.crowd_density = 0.0
        self.threat_level = 0.0
        self.response_times = []
        self.timestamps = []
    
    def add_athlete(self):
        """Increment athlete count."""
        self.athlete_count += 1
        self.timestamps.append(datetime.now())
    
    def add_incident(self, incident_type: str):
        """Add an incident to this cell."""
        self.incident_count += 1
        if incident_type in ["medical_event", "medical_emergency"]:
            self.medical_events += 1
        else:
            self.security_events += 1
        self.timestamps.append(datetime.now())
    
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
        """Get heat value for visualization."""
        if metric == "athlete_count":
            return min(1.0, self.athlete_count / 50)  # Normalize to 0-1
        elif metric == "incident_count":
            return min(1.0, self.incident_count / 10)
        elif metric == "crowd_density":
            return self.crowd_density
        elif metric == "threat_level":
            return self.threat_level
        elif metric == "response_time":
            if self.response_times:
                avg = sum(self.response_times) / len(self.response_times)
                return min(1.0, avg / 600)  # Normalize to 10 minutes
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
    
    def __init__(self, model, grid_size: int = 20):
        self.model = model
        self.grid_size = grid_size
        self.heatmap: Dict[Tuple[int, int], HeatmapCell] = {}
        self.time_series_data: List[Dict] = []
        self.incident_patterns: Dict[str, List[Dict]] = defaultdict(list)
        self.agent_trajectories: Dict[int, List[Tuple[float, float]]] = {}
        
        # Initialize grid
        self._initialize_grid()
    
    def _initialize_grid(self):
        """Initialize heatmap grid."""
        cell_size = 1.0 / self.grid_size
        for x in range(self.grid_size):
            for y in range(self.grid_size):
                center = (
                    (x + 0.5) * cell_size,
                    (y + 0.5) * cell_size,
                )
                self.heatmap[(x, y)] = HeatmapCell(x, y, center)
    
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
        step_data = {
            "timestamp": self.model.current_time.isoformat(),
            "athlete_count": len(self.model.athletes),
            "active_incidents": len(self.model.active_incidents),
            "medical_events": len(self.model.medical_events),
            "metrics": self.model.metrics.copy(),
        }
        
        self.time_series_data.append(step_data)
        
        # Update heatmap
        self._update_heatmap()
    
    def _update_heatmap(self):
        """Update heatmap with current agent positions and incidents."""
        # Clear previous counts (or use decay)
        for cell in self.heatmap.values():
            cell.athlete_count = 0
        
        # Record athlete positions
        for athlete in self.model.athletes:
            if athlete.current_location:
                cell = self._get_cell(athlete.current_location)
                if cell:
                    cell.add_athlete()
                    
                    # Track trajectory
                    if athlete.unique_id not in self.agent_trajectories:
                        self.agent_trajectories[athlete.unique_id] = []
                    self.agent_trajectories[athlete.unique_id].append(athlete.current_location)
        
        # Record incidents
        for incident in self.model.active_incidents:
            incident_loc = incident.get("location")
            if incident_loc:
                cell = self._get_cell(incident_loc)
                if cell:
                    cell.add_incident(incident.get("type", "unknown"))
        
        # Record medical events
        for med_event in self.model.medical_events:
            med_loc = med_event.get("location")
            if med_loc:
                cell = self._get_cell(med_loc)
                if cell:
                    cell.add_incident("medical_event")
        
        # Calculate crowd density
        for cell in self.heatmap.values():
            if cell.athlete_count > 0:
                # Calculate density based on nearby cells
                density = self._calculate_crowd_density(cell)
                cell.update_density(density)
    
    def _calculate_crowd_density(self, cell: HeatmapCell) -> float:
        """Calculate crowd density for a cell."""
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
        
        # Normalize to 0-1
        return min(1.0, total_count / 100)
    
    def record_incident_pattern(self, incident_type: str, location: Tuple[float, float], metadata: Dict = None):
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
    
    def get_hotspots(self, metric: str = "athlete_count", threshold: float = 0.7) -> List[Dict]:
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
    
    def get_time_series(self, metric: str, start_time: datetime = None, end_time: datetime = None) -> List[Dict]:
        """Get time series data for a metric."""
        filtered = self.time_series_data
        
        if start_time:
            filtered = [d for d in filtered if datetime.fromisoformat(d["timestamp"]) >= start_time]
        if end_time:
            filtered = [d for d in filtered if datetime.fromisoformat(d["timestamp"]) <= end_time]
        
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
    
    def get_agent_trajectory(self, agent_id: int) -> List[Tuple[float, float]]:
        """Get trajectory for an agent."""
        return self.agent_trajectories.get(agent_id, [])
    
    def export_data(self, filepath: str):
        """Export analytics data to JSON."""
        data = {
            "time_series": self.time_series_data,
            "heatmap": {
                f"{x}_{y}": cell.to_dict()
                for (x, y), cell in self.heatmap.items()
            },
            "incident_patterns": self.incident_patterns,
            "agent_trajectories": {
                str(agent_id): trajectory
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

