# 🚀 Quick Start - See the 3D Simulation

## Option 1: Jupyter Notebook (Recommended)

1. **Start Jupyter:**
   ```bash
   cd backend
   jupyter notebook
   ```

2. **Open the notebook:**
   - Click on `run_3d_visualization.ipynb`
   - Click "Run All" or run cells one by one (Shift+Enter)

3. **Watch the magic!** 🎨
   - The 3D scene will appear
   - Agents will move in real-time
   - Incidents will trigger responses
   - Metrics will update live

## Option 2: Direct Script

```bash
cd backend
jupyter notebook view_3d_simulation.py
```

Or in a Jupyter cell:
```python
%run view_3d_simulation.py
```

## What You'll See

- **🟡 Gold Spheres**: Athletes moving with trails
- **🔵 Teal Boxes**: Volunteers assisting
- **🟢 Mint Cylinders**: Hotel security patrolling
- **🔵 Blue Cylinders**: LVMPD units responding
- **🔴 Coral Cylinders**: AMR medical units
- **🟣 Purple Boxes**: Buses transporting
- **⚠️ Pulsing Spheres**: Active incidents
- **✨ Glowing Markers**: Venue locations

## Interactive Controls

- **Rotate**: Click and drag
- **Zoom**: Scroll wheel
- **Pan**: Right-click and drag

## Troubleshooting

**"pythreejs not available"**
```bash
pip install pythreejs ipywidgets
jupyter nbextension enable --py --sys-prefix pythreejs
```

**Visualization not showing**
- Make sure you're in Jupyter (not terminal)
- Restart kernel after installing pythreejs
- Check browser console for errors

**Scene is empty**
- Run all cells in order
- Check that agents were initialized
- Verify venues are loaded

## Next Steps

After seeing the visualization:
1. Try different camera views
2. Toggle features (trails, incidents, venues)
3. Modify the scenario for different events
4. Analyze the metrics and performance

Enjoy! 🎉

