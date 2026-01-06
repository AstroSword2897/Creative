# Simulation Enhancements Documentation

This document describes all the major enhancements made to the Special Olympics Las Vegas Security Simulation.

## Overview

The simulation has been enhanced with four major systems plus a 3D visualization:

1. **Dynamic Scheduling System** - Handles delays and schedule adjustments
2. **Global Alert Prioritization** - Centralized threat assessment and coordination
3. **Analytics & Heatmaps** - Time-series tracking and visualization
4. **Graph-Based Routing** - Realistic pathfinding with A* and Dijkstra
5. **3D Visualization** - Interactive pythreejs-based 3D display

---

## 1. Dynamic Scheduling System

**File:** `backend/simulation/scheduling.py`

### Features

- **Delay Tracking**: Tracks multiple types of delays (bus, traffic, crowding, weather, medical, security)
- **Schedule Adjustment**: Automatically adjusts event times based on delays
- **Flexible Events**: Supports both flexible and fixed-time events
- **Delay Analytics**: Provides detailed delay summaries and metrics

### Usage

```python
from simulation.scheduling import DynamicScheduler

# Scheduler is automatically initialized in the model
scheduler = model.scheduler

# Create schedule for athlete
events = [
    {"time": "08:00", "location": "harry_reid_airport", "type": "arrival"},
    {"time": "10:00", "location": "mgm_grand", "type": "checkin"},
    {"time": "12:45", "location": "unlv_cox", "type": "competition"},
]
schedule = scheduler.create_schedule(athlete_id=1, events=events)

# Check for delays
delays = scheduler.check_delays(athlete_id=1, athlete_location=(0.5, 0.5))
scheduler.apply_delays(athlete_id=1, delays=delays)

# Get schedule metrics
metrics = scheduler.get_schedule_metrics(athlete_id=1)
```

### Delay Types

- `BUS_DELAY`: Delays from bus service interruptions
- `TRAFFIC`: High-density traffic congestion
- `CROWDING`: Crowd surge delays
- `WEATHER`: Heat alerts and weather conditions
- `MEDICAL_EVENT`: Medical emergency delays
- `SECURITY_INCIDENT`: Security-related delays
- `ACCESS_CONTROL`: Access control checkpoint delays

---

## 2. Global Alert Prioritization

**File:** `backend/simulation/alert_prioritization.py`

### Features

- **Threat Hierarchy**: 5-level threat system (CRITICAL, HIGH, MEDIUM, LOW, INFO)
- **Dynamic Prioritization**: Factors in crowd density, proximity, weather, VIP presence
- **Priority Queue**: Efficient alert management using heapq
- **Category Classification**: Alerts organized by type (security, medical, crowd, etc.)
- **Unit Assignment**: Tracks which units are assigned to which alerts

### Usage

```python
from simulation.alert_prioritization import GlobalAlertManager, ThreatLevel

# Alert manager is automatically initialized in the model
alert_manager = model.alert_manager

# Register an alert
alert = alert_manager.register_alert(
    alert_id="incident_001",
    alert_type="suspicious_person",
    location=(0.5, 0.5),
    metadata={"reported_by": "volunteer"}
)

# Get highest priority alert
priority_alert = alert_manager.get_highest_priority_alert()

# Get alerts by category
security_alerts = alert_manager.get_alerts_by_category(AlertCategory.SECURITY_THREAT)

# Get statistics
stats = alert_manager.get_alert_statistics()
```

### Threat Levels

1. **CRITICAL**: Immediate response required (suspicious person, medical emergency)
2. **HIGH**: Urgent response (access denied, crowd surge)
3. **MEDIUM**: Standard response (traffic incident, weather alert)
4. **LOW**: Routine response
5. **INFO**: Informational only

### Priority Factors

- **Base Priority**: Set by alert type
- **Crowd Density**: Higher density increases priority
- **Proximity to VIP**: Critical if near VIP
- **Weather Factor**: Heat alerts increase priority
- **Time Factor**: Older incidents may escalate

---

## 3. Analytics & Heatmaps

**File:** `backend/simulation/analytics.py`

### Features

- **Heatmap Grid**: 20x20 grid tracking agent density, incidents, threats
- **Time-Series Data**: Records metrics at each simulation step
- **Incident Patterns**: Tracks incident locations and patterns
- **Agent Trajectories**: Records movement paths for analysis
- **Hotspot Detection**: Identifies high-risk areas automatically

### Usage

```python
from simulation.analytics import AnalyticsEngine

# Analytics engine is automatically initialized in the model
analytics = model.analytics

# Get heatmap data
heatmap_data = analytics.get_heatmap_data(metric="athlete_count")

# Get hotspots
hotspots = analytics.get_hotspots(metric="incident_count", threshold=0.7)

# Get time series
time_series = analytics.get_time_series(
    metric="safety_score",
    start_time=datetime(2024, 6, 1, 8, 0),
    end_time=datetime(2024, 6, 1, 16, 0)
)

# Get incident analysis
incident_analysis = analytics.get_incident_analysis()

# Export data
analytics.export_data("analytics_export.json")
```

### Metrics Tracked

- **Athlete Count**: Density of athletes per cell
- **Incident Count**: Number of incidents per cell
- **Crowd Density**: Normalized crowd density (0-1)
- **Threat Level**: Threat assessment per cell
- **Response Time**: Average response times per location

---

## 4. Graph-Based Routing

**File:** `backend/simulation/graph_routing.py`

### Features

- **Graph Network**: Creates realistic road network from venues
- **Pathfinding Algorithms**: A* and Dijkstra algorithms
- **Accessibility Support**: Considers wheelchair accessibility
- **Traffic Load**: Accounts for node capacity and current load
- **Nearest Neighbor**: Connects each node to 3-5 nearest neighbors

### Usage

```python
from simulation.graph_routing import RoutingGraph

# Graph router is automatically initialized in the model
router = model.graph_router

# Find path
path = router.find_path(
    start=(0.3, 0.3),
    end=(0.7, 0.7),
    accessibility_required=True,  # For wheelchair users
    algorithm="astar"  # or "dijkstra"
)

# Update node load (for traffic simulation)
router.update_node_load("venue_1", load=0.7)  # 70% capacity
```

### Algorithms

- **A***: Optimal pathfinding with heuristic (faster for long paths)
- **Dijkstra**: Guaranteed shortest path (better for dense graphs)

### Network Structure

- Each venue becomes a node
- Nodes connected to 3-5 nearest neighbors
- Bidirectional edges with distance weights
- Supports custom nodes (intersections, bus stops)

---

## 5. 3D Visualization

**File:** `backend/simulation/visualization_3d.py`

### Features

- **3D Scene**: Full 3D environment with camera, lights, controls
- **Agent Representation**: Different shapes/colors for each agent type
- **Smooth Animation**: Interpolated movement between steps
- **Trails**: Visual trails showing agent movement paths
- **Incident Markers**: Pulsing markers for active incidents
- **Venue Markers**: 3D markers for hotels, venues, hospitals
- **Interactive Controls**: Orbit, zoom, pan with mouse

### Usage

```python
from simulation.visualization_3d import Visualization3D

# Create visualization
viz = Visualization3D(model, width=1000, height=700)

# Initialize
viz.initialize_venues()
viz.initialize_agents()

# Set camera view
viz.set_camera_view("top_down")  # or "isometric", "cinematic"

# Update each step
model.step()
viz.update()

# Display (in Jupyter notebook)
viz.display()
```

### Agent Types & Colors

- **Athletes**: Gold spheres (`#F4C430`)
- **Volunteers**: Green boxes (`#2ECC71`)
- **Hotel Security**: Teal cylinders (`#00F5D4`)
- **LVMPD**: Blue cylinders (`#0077FF`)
- **AMR**: Red cylinders (`#E74C3C`)
- **Buses**: Indigo boxes (`#6366F1`)

### Camera Views

- **top_down**: Strategic overview from above
- **isometric**: 45-degree angled view
- **cinematic**: Dynamic action view

### Requirements

```bash
pip install pythreejs ipywidgets
```

**Note**: 3D visualization works best in Jupyter notebooks. For web deployment, consider using Three.js directly in the frontend.

---

## Integration with Model

All systems are automatically initialized in `SpecialOlympicsModel`:

```python
# In model.__init__()
self.graph_router = RoutingGraph(self.venues)
self.scheduler = DynamicScheduler(self)
self.alert_manager = GlobalAlertManager(self)
self.analytics = AnalyticsEngine(self, grid_size=20)
```

### Step Function Updates

The model's `step()` function now includes:

```python
def step(self):
    # ... existing code ...
    
    # Update enhanced systems
    self.alert_manager.update_all_alerts()
    self.analytics.record_step()
    
    # Update metrics
    self._update_metrics()
```

---

## API Integration

### Enhanced State Response

The `get_state()` method now includes:

```python
{
    "time": "...",
    "agents": {...},
    "incidents": [...],
    "metrics": {...},
    "command_center": {
        "location": [...],
        "threat_map": [...],
        "hotspots": [...]
    },
    "security_metrics": {
        "hotel_security": [...],
        "lvmpd": [...]
    }
}
```

### New Endpoints (Recommended)

```python
GET /api/runs/{run_id}/analytics/heatmap
GET /api/runs/{run_id}/analytics/timeseries
GET /api/runs/{run_id}/alerts/prioritized
GET /api/runs/{run_id}/schedules/{athlete_id}
```

---

## Performance Considerations

1. **Heatmap Grid**: 20x20 grid = 400 cells (adjustable)
2. **Graph Nodes**: One per venue (typically 10-20 nodes)
3. **Alert Queue**: Heap-based for O(log n) operations
4. **Time-Series**: Grows with simulation steps (consider pruning old data)

### Optimization Tips

- Reduce heatmap grid size for large simulations
- Limit time-series data retention
- Use A* for long paths, Dijkstra for short paths
- Batch analytics updates (every N steps instead of every step)

---

## Future Enhancements

1. **PostGIS Integration**: Replace graph routing with real road network
2. **Machine Learning**: Predictive positioning using historical data
3. **Real-Time Dashboard**: WebSocket streaming of analytics
4. **Export Formats**: CSV, GeoJSON, KML for external analysis
5. **Replay System**: Record and replay simulation runs

---

## Testing

Example test script:

```python
from simulation.model import SpecialOlympicsModel
import json

# Load scenario
with open("scenarios/baseline.json") as f:
    config = json.load(f)

# Create model
model = SpecialOlympicsModel(config)

# Run simulation
for i in range(100):
    model.step()
    
    # Check analytics
    if i % 10 == 0:
        hotspots = model.analytics.get_hotspots()
        print(f"Step {i}: {len(hotspots)} hotspots identified")
        
        alerts = model.alert_manager.get_alerts_by_priority(limit=5)
        print(f"  Top alerts: {len(alerts)}")

# Export analytics
model.analytics.export_data("test_run_analytics.json")
```

---

## Summary

These enhancements transform the simulation from a basic prototype into a production-ready system with:

✅ **Realistic scheduling** with delay handling  
✅ **Intelligent alert prioritization** with global coordination  
✅ **Comprehensive analytics** with heatmaps and time-series  
✅ **Graph-based routing** with pathfinding algorithms  
✅ **3D visualization** for interactive exploration  

All systems are modular, well-documented, and ready for integration with the existing API and frontend.

