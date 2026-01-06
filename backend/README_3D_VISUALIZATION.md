# 🎨 3D Visualization Guide

## Quick Start

To see the **actual 3D visualization** of the simulation:

### Option 1: Jupyter Notebook (Recommended)

1. **Start Jupyter Notebook:**
   ```bash
   cd backend
   jupyter notebook
   ```

2. **Open the notebook:**
   - Open `run_3d_visualization.ipynb` in your browser
   - Run all cells (Cell → Run All)

3. **Interact with the 3D scene:**
   - **Rotate**: Click and drag
   - **Zoom**: Scroll wheel
   - **Pan**: Right-click and drag

### Option 2: Quick Script

```bash
cd backend
python3 -c "
from pathlib import Path
import json
import sys
sys.path.insert(0, '.')
from simulation.model import SpecialOlympicsModel
from simulation.visualization_3d import Visualization3D

# Load and create
with open('scenarios/baseline.json') as f:
    config = json.load(f)
model = SpecialOlympicsModel(config)
viz = Visualization3D(model, width=1200, height=800)
viz.initialize_venues()
viz.initialize_agents()
viz.set_camera_view('isometric')

# Display (requires Jupyter)
from IPython.display import display
display(viz.scene)
"
```

## Features

### 🎮 Interactive Controls
- **Camera rotation**: Click and drag
- **Zoom**: Mouse wheel
- **Pan**: Right-click drag
- **Smooth transitions**: `viz.set_camera_view('cinematic', smooth=True)`

### 🎨 Visual Elements
- **Athletes**: Gold spheres with trails
- **Volunteers**: Teal boxes
- **Security**: Mint cylinders
- **LVMPD**: Sky blue cylinders
- **AMR**: Coral cylinders
- **Buses**: Purple boxes
- **Venues**: Glowing markers
- **Incidents**: Pulsing spheres

### 🎛️ Toggle Features

```python
# Toggle trails
viz.toggle_trails(show=True)

# Toggle incidents
viz.toggle_incidents(show=True)

# Toggle venues
viz.toggle_venues(show=True)

# Toggle specific agent types
viz.toggle_agent_type('athlete', show=False)
```

### 📷 Camera Views

```python
# Top-down view
viz.set_camera_view('top_down', smooth=True)

# Isometric view
viz.set_camera_view('isometric', smooth=True)

# Cinematic view
viz.set_camera_view('cinematic', smooth=True)
```

## Requirements

- `jupyter` - For notebook interface
- `ipywidgets` - For interactive widgets
- `pythreejs` - For 3D rendering

Install with:
```bash
pip install jupyter ipywidgets pythreejs
```

## Troubleshooting

### "pythreejs not available"
- Install: `pip install pythreejs ipywidgets`
- Restart Jupyter kernel

### Visualization not showing
- Make sure you're in a Jupyter notebook (not terminal)
- Check browser console for errors
- Try: `jupyter nbextension enable --py --sys-prefix pythreejs`

### Scene is empty
- Run `viz.initialize_venues()` and `viz.initialize_agents()`
- Check that model has agents: `len(model.athletes) > 0`

## Next Steps

1. **Run the simulation**: Execute all cells in the notebook
2. **Watch agents move**: The 3D scene updates in real-time
3. **Explore different views**: Try different camera angles
4. **Toggle features**: Hide/show different elements
5. **Analyze metrics**: Check the final metrics after simulation

Enjoy your 3D simulation! 🚀

