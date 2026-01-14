"""
Unified simulation module integrating AnalyticsEngine and RoutingGraph.
Provides synchronized tracking of agent movement, heatmaps, and optimized routing.
"""

from typing import Dict, List, Optional, Tuple
from datetime import datetime
from .analytics import AnalyticsEngine, SimulationModel
from .graph_routing import RoutingGraph


class IntegratedSimulationSystems:
    """
    Unified system combining analytics and routing.
    Keeps heatmaps, trajectories, and routing synchronized.
    """
    
    def __init__(
        self,
        model: SimulationModel,
        venues: Dict[str, Dict],
        grid_size: int = 20,
        max_density: float = 100.0,
        decay_rate: float = 0.0,
        nearest_node_threshold: float = 0.1,
        connections_per_node: int = 5
    ):
        """
        Initialize integrated systems.
        
        Args:
            model: Simulation model instance
            venues: Venue data for routing graph
            grid_size: Size of heatmap grid
            max_density: Maximum density for normalization
            decay_rate: Decay rate for heatmap (0 = no decay)
            nearest_node_threshold: Distance threshold for nearest node lookup
            connections_per_node: Number of connections per node in graph
        """
        self.model = model
        
        # Initialize analytics engine
        self.analytics = AnalyticsEngine(
            model=model,
            grid_size=grid_size,
            max_density=max_density,
            decay_rate=decay_rate
        )
        
        # Initialize routing graph
        self.routing = RoutingGraph(
            venues=venues,
            nearest_node_threshold=nearest_node_threshold,
            connections_per_node=connections_per_node
        )
        
        # Sync interval (update routing loads every N steps)
        self.sync_interval = 5
        self.step_count = 0
    
    def record_step(self):
        """Record a simulation step in both systems."""
        # Record analytics step
        self.analytics.record_step()
        
        # Sync routing loads from analytics periodically
        self.step_count += 1
        if self.step_count % self.sync_interval == 0:
            self.routing.update_loads_from_analytics(self.analytics)
    
    def find_path(
        self,
        start: Tuple[float, float],
        end: Tuple[float, float],
        accessibility_required: bool = False,
        algorithm: str = "astar",
        avoid_hotspots: bool = True
    ) -> List[Tuple[float, float]]:
        """
        Find optimized path, optionally avoiding hotspots.
        
        Args:
            start: Start location
            end: End location
            accessibility_required: Require accessible path
            algorithm: Pathfinding algorithm ("astar" or "dijkstra")
            avoid_hotspots: Avoid high-density hotspots if possible
        
        Returns:
            List of waypoints forming the path
        """
        # If avoiding hotspots, temporarily increase load on hotspot nodes
        if avoid_hotspots:
            hotspots = self.analytics.get_hotspots(metric="crowd_density", threshold=0.7)
            # ✅ CRITICAL: Force sync routing loads before pathfinding (avoids stale data)
            self.routing.update_loads_from_analytics(self.analytics)
            
            original_loads = {}
            
            try:
                # Increase load on hotspot nodes
                # ✅ OPTIMIZED: Scale load penalty based on hotspot density for more realistic avoidance
                for hotspot in hotspots:
                    location = hotspot["location"]
                    density = hotspot.get("density", 0.7)  # Default to threshold if not provided
                    node_id = self.routing._nearest_node(location)
                    if node_id:
                        node = self.routing.get_node(node_id)
                        if node:
                            original_loads[node_id] = node.current_load
                            # Scale penalty: higher density = higher penalty (configurable multiplier)
                            # Base penalty of 200, scaled by density (0.7-1.0 range)
                            penalty_multiplier = 1.0 + (density - 0.7) * 2.0  # 1.0 to 1.6 multiplier
                            load_penalty = int(200 * penalty_multiplier)
                            self.routing.update_node_load(node_id, node.current_load + load_penalty)
                
                # Find path
                path = self.routing.find_path(
                    start=start,
                    end=end,
                    accessibility_required=accessibility_required,
                    algorithm=algorithm
                )
                
                return path
            finally:
                # ✅ CRITICAL: Always restore original loads, even if pathfinding fails
                for node_id, original_load in original_loads.items():
                    self.routing.update_node_load(node_id, original_load)
        
        # Standard pathfinding
        return self.routing.find_path(
            start=start,
            end=end,
            accessibility_required=accessibility_required,
            algorithm=algorithm
        )
    
    def get_heatmap_data(self, metric: str = "athlete_count") -> List[Dict]:
        """Get heatmap data from analytics."""
        return self.analytics.get_heatmap_data(metric)
    
    def get_hotspots(self, metric: str = "athlete_count", threshold: float = 0.7) -> List[Dict]:
        """Get hotspots from analytics."""
        return self.analytics.get_hotspots(metric, threshold)
    
    def get_agent_trajectory(self, agent_id: int) -> List[Tuple[float, float, datetime]]:
        """Get agent trajectory with timestamps."""
        return self.analytics.get_agent_trajectory(agent_id)
    
    def get_time_series(self, metric: str, start_time: Optional[datetime] = None, end_time: Optional[datetime] = None) -> List[Dict]:
        """Get time series data."""
        return self.analytics.get_time_series(metric, start_time, end_time)
    
    def get_incident_analysis(self) -> Dict:
        """Get incident pattern analysis."""
        return self.analytics.get_incident_analysis()
    
    def get_summary_statistics(self) -> Dict:
        """Get summary statistics."""
        return self.analytics.get_summary_statistics()
    
    def export_data(self, filepath: str):
        """Export all analytics and routing data."""
        self.analytics.export_data(filepath)
    
    def update_node_load(self, node_id: str, load: float):
        """Manually update node load."""
        self.routing.update_node_load(node_id, load)
    
    def get_routing_graph(self) -> RoutingGraph:
        """Get the routing graph instance."""
        return self.routing
    
    def get_analytics_engine(self) -> AnalyticsEngine:
        """Get the analytics engine instance."""
        return self.analytics

