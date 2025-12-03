"""
Route planner for agents using simplified road network.
In production, this would use PostGIS for real routing.
"""

from typing import List, Tuple, Dict, Optional
import math


class RoutePlanner:
    """Simplified route planner for simulation."""
    
    def __init__(self, venues: Dict[str, Dict]):
        self.venues = venues
        # Simplified: create direct paths between major venues
        self.road_network = self._build_simple_network()
    
    def _build_simple_network(self) -> Dict[Tuple[float, float], List[Tuple[float, float]]]:
        """Build simplified road network connecting venues."""
        network = {}
        venue_points = []
        
        for venue_name, venue_data in self.venues.items():
            point = (venue_data.get("lon", 0.5), venue_data.get("lat", 0.5))
            venue_points.append(point)
            network[point] = []
        
        # Connect all venues in a simple network
        for i, point1 in enumerate(venue_points):
            for j, point2 in enumerate(venue_points):
                if i != j:
                    network[point1].append(point2)
        
        return network
    
    def find_path(self, start: Tuple[float, float], end: Tuple[float, float]) -> List[Tuple[float, float]]:
        """Find path from start to end using simplified A*."""
        # For now, return direct path with waypoints
        # In production, use PostGIS routing
        
        # Find nearest network nodes
        start_node = self._nearest_node(start)
        end_node = self._nearest_node(end)
        
        if start_node == end_node:
            return [end]
        
        # Simple path: start -> start_node -> end_node -> end
        path = [start]
        if start_node and start_node != start:
            path.append(start_node)
        if end_node and end_node != start_node:
            path.append(end_node)
        if end != end_node:
            path.append(end)
        
        return path
    
    def _nearest_node(self, point: Tuple[float, float]) -> Optional[Tuple[float, float]]:
        """Find nearest node in road network."""
        if not self.road_network:
            return point
        
        min_dist = float('inf')
        nearest = None
        
        for node in self.road_network.keys():
            dist = self._distance(point, node)
            if dist < min_dist:
                min_dist = dist
                nearest = node
        
        return nearest if min_dist < 0.1 else point  # Threshold
    
    def _distance(self, p1: Tuple[float, float], p2: Tuple[float, float]) -> float:
        """Calculate Euclidean distance."""
        return math.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)

