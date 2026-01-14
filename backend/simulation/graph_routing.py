"""
Graph-based routing system with pathfinding algorithms.
Supports road networks, accessibility constraints, and obstacle avoidance.
Enhanced with configurable thresholds, better accessibility handling, and optimizations.
"""

from typing import Dict, List, Optional, Tuple, Set
from collections import defaultdict
from dataclasses import dataclass
import heapq
import math


@dataclass
class GraphNode:
    """Represents a node in the routing graph."""
    node_id: str
    location: Tuple[float, float]
    node_type: str = "venue"
    neighbors: List[Tuple[str, float]] = None  # (node_id, distance)
    accessible: bool = True  # Wheelchair accessible
    capacity: float = float('inf')  # Max capacity (for traffic)
    current_load: float = 0  # Current traffic load
    
    def __post_init__(self):
        if self.neighbors is None:
            self.neighbors = []
    
    def add_neighbor(self, neighbor_id: str, distance: float):
        """Add a neighbor node."""
        self.neighbors.append((neighbor_id, distance))
    
    def get_cost(self, base_distance: float) -> float:
        """Get cost to traverse this node (considering load)."""
        load_factor = 1.0 + (self.current_load / max(1, self.capacity)) * 0.5
        return base_distance * load_factor


class RoutingGraph:
    """Graph-based routing system with enhanced features."""
    
    def __init__(
        self, 
        venues: Dict[str, Dict],
        nearest_node_threshold: float = 0.1,
        connections_per_node: int = 5
    ):
        self.nodes: Dict[str, GraphNode] = {}
        self.venues = venues
        self.nearest_node_threshold = nearest_node_threshold
        self.connections_per_node = connections_per_node
        self._build_graph()
    
    def _build_graph(self):
        """Build routing graph from venues."""
        # Create nodes for all venues
        for venue_id, venue_data in self.venues.items():
            location = (venue_data.get("lat"), venue_data.get("lon"))
            node_type = venue_data.get("type", "venue")
            
            node = GraphNode(
                node_id=venue_id,
                location=location,
                node_type=node_type,
            )
            
            # Set accessibility based on venue type
            node.accessible = venue_data.get("accessible", True)
            
            self.nodes[venue_id] = node
        
        # Connect nodes (create edges)
        self._connect_nodes()
    
    def _connect_nodes(self):
        """Connect nodes to create a road network."""
        node_list = list(self.nodes.values())
        
        # Strategy: Connect each node to its N nearest neighbors
        # This creates a more realistic network than fully connected
        for i, node1 in enumerate(node_list):
            # Find nearest neighbors
            distances = [
                (self._distance(node1.location, node2.location), node2.node_id)
                for j, node2 in enumerate(node_list) if i != j
            ]
            distances.sort()
            
            # Connect to configured number of nearest neighbors
            num_connections = min(self.connections_per_node, len(distances))
            for dist, neighbor_id in distances[:num_connections]:
                node1.add_neighbor(neighbor_id, dist)
                # Make bidirectional
                if neighbor_id in self.nodes:
                    self.nodes[neighbor_id].add_neighbor(node1.node_id, dist)
    
    def add_node(
        self, 
        node_id: str, 
        location: Tuple[float, float], 
        node_type: str = "intersection",
        accessible: bool = True
    ) -> GraphNode:
        """Add a custom node to the graph."""
        node = GraphNode(
            node_id=node_id,
            location=location,
            node_type=node_type,
            accessible=accessible
        )
        self.nodes[node_id] = node
        return node
    
    def find_path(
        self,
        start: Tuple[float, float],
        end: Tuple[float, float],
        accessibility_required: bool = False,
        algorithm: str = "astar"
    ) -> List[Tuple[float, float]]:
        """Find path from start to end using specified algorithm."""
        # Find nearest nodes (with fallback to nearest accessible)
        start_node_id = self._nearest_node(start, accessibility_required)
        end_node_id = self._nearest_node(end, accessibility_required)
        
        if not start_node_id or not end_node_id:
            # Fallback to direct path
            return [start, end]
        
        if start_node_id == end_node_id:
            return [start, end]
        
        # Use pathfinding algorithm
        if algorithm == "astar":
            path_nodes = self._astar_path(start_node_id, end_node_id, accessibility_required)
        elif algorithm == "dijkstra":
            path_nodes = self._dijkstra_path(start_node_id, end_node_id, accessibility_required)
        else:
            path_nodes = self._dijkstra_path(start_node_id, end_node_id, accessibility_required)
        
        if not path_nodes:
            # Fallback to direct path
            return [start, end]
        
        # Convert node IDs to locations
        path = [start]
        for node_id in path_nodes:
            if node_id in self.nodes:
                path.append(self.nodes[node_id].location)
        path.append(end)
        
        return path
    
    def _astar_path(
        self,
        start_id: str,
        end_id: str,
        accessibility_required: bool = False
    ) -> List[str]:
        """A* pathfinding algorithm with enhanced heuristic."""
        if start_id not in self.nodes or end_id not in self.nodes:
            return []
        
        start_node = self.nodes[start_id]
        end_node = self.nodes[end_id]
        end_location = end_node.location
        
        # Priority queue: (f_score, node_id, path)
        open_set = [(0, start_id, [start_id])]
        visited = set()
        g_scores = {start_id: 0}
        
        while open_set:
            f_score, current_id, path = heapq.heappop(open_set)
            
            if current_id in visited:
                continue
            
            visited.add(current_id)
            
            if current_id == end_id:
                return path[1:]  # Exclude start node
            
            current_node = self.nodes[current_id]
            
            # Check accessibility
            if accessibility_required and not current_node.accessible:
                continue
            
            for neighbor_id, distance in current_node.neighbors:
                if neighbor_id in visited:
                    continue
                
                neighbor_node = self.nodes[neighbor_id]
                
                # Check accessibility
                if accessibility_required and not neighbor_node.accessible:
                    continue
                
                # Calculate g_score (cost from start)
                base_cost = distance * current_node.get_cost(distance)
                tentative_g = g_scores[current_id] + base_cost
                
                # Enhanced heuristic: weighted Euclidean + load consideration
                h_score = self._distance(neighbor_node.location, end_location)
                # Incorporate load into heuristic for better pathfinding
                if neighbor_node.current_load > 0:
                    load_penalty = neighbor_node.current_load / max(1, neighbor_node.capacity)
                    h_score *= (1 + load_penalty * 0.2)
                
                # Calculate f_score
                f_score = tentative_g + h_score
                
                if neighbor_id not in g_scores or tentative_g < g_scores[neighbor_id]:
                    g_scores[neighbor_id] = tentative_g
                    heapq.heappush(open_set, (f_score, neighbor_id, path + [neighbor_id]))
        
        return []  # No path found
    
    def _dijkstra_path(
        self,
        start_id: str,
        end_id: str,
        accessibility_required: bool = False
    ) -> List[str]:
        """Dijkstra's pathfinding algorithm."""
        if start_id not in self.nodes or end_id not in self.nodes:
            return []
        
        # Priority queue: (distance, node_id, path)
        open_set = [(0, start_id, [start_id])]
        visited = set()
        distances = {start_id: 0}
        
        while open_set:
            dist, current_id, path = heapq.heappop(open_set)
            
            if current_id in visited:
                continue
            
            visited.add(current_id)
            
            if current_id == end_id:
                return path[1:]  # Exclude start node
            
            current_node = self.nodes[current_id]
            
            # Check accessibility
            if accessibility_required and not current_node.accessible:
                continue
            
            for neighbor_id, edge_distance in current_node.neighbors:
                if neighbor_id in visited:
                    continue
                
                neighbor_node = self.nodes[neighbor_id]
                
                # Check accessibility
                if accessibility_required and not neighbor_node.accessible:
                    continue
                
                # Calculate total distance
                base_cost = edge_distance * current_node.get_cost(edge_distance)
                total_distance = dist + base_cost
                
                if neighbor_id not in distances or total_distance < distances[neighbor_id]:
                    distances[neighbor_id] = total_distance
                    heapq.heappush(open_set, (total_distance, neighbor_id, path + [neighbor_id]))
        
        return []  # No path found
    
    def _nearest_node(
        self, 
        location: Tuple[float, float],
        accessibility_required: bool = False
    ) -> Optional[str]:
        """Find nearest node to a location, with accessibility fallback."""
        if not self.nodes:
            return None
        
        min_dist = float('inf')
        nearest_id = None
        nearest_accessible_id = None
        min_accessible_dist = float('inf')
        
        for node_id, node in self.nodes.items():
            dist = self._distance(location, node.location)
            
            # Track nearest overall
            if dist < min_dist:
                min_dist = dist
                nearest_id = node_id
            
            # Track nearest accessible if required
            if accessibility_required and node.accessible and dist < min_accessible_dist:
                min_accessible_dist = dist
                nearest_accessible_id = node_id
        
        # Return accessible node if required, otherwise nearest
        if accessibility_required:
            if nearest_accessible_id and min_accessible_dist < self.nearest_node_threshold * 2:
                return nearest_accessible_id
            return None
        
        # Only return if within threshold
        if min_dist < self.nearest_node_threshold:
            return nearest_id
        
        # Fallback: return nearest anyway if no node within threshold
        return nearest_id
    
    def update_node_load(self, node_id: str, load: float):
        """Update traffic load on a node."""
        if node_id in self.nodes:
            self.nodes[node_id].current_load = load
    
    def update_loads_from_analytics(self, analytics_engine):
        """Update node loads based on crowd density from analytics."""
        # Get hotspots from analytics
        hotspots = analytics_engine.get_hotspots(metric="crowd_density", threshold=0.5)
        
        # Update node loads based on nearby hotspots
        for hotspot in hotspots:
            location = hotspot["location"]
            density = hotspot["value"]
            
            # Find nearest node
            node_id = self._nearest_node(location)
            if node_id:
                # Scale load based on density (0-1 density -> 0-100 load)
                load = density * 100
                self.update_node_load(node_id, load)
    
    def _distance(self, p1: Tuple[float, float], p2: Tuple[float, float]) -> float:
        """Calculate Euclidean distance."""
        return math.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)
    
    def get_node(self, node_id: str) -> Optional[GraphNode]:
        """Get a node by ID."""
        return self.nodes.get(node_id)
    
    def get_all_nodes(self) -> List[GraphNode]:
        """Get all nodes in the graph."""
        return list(self.nodes.values())
