#!/bin/bash
# Start Jupyter notebook for 3D visualization

echo "🚀 Starting Jupyter Notebook for 3D Visualization..."
echo ""
echo "📝 Instructions:"
echo "   1. The notebook will open in your browser"
echo "   2. Open 'run_3d_visualization.ipynb'"
echo "   3. Run all cells to see the 3D simulation"
echo ""
echo "💡 Make sure you have:"
echo "   - jupyter installed: pip install jupyter ipywidgets"
echo "   - pythreejs installed: pip install pythreejs"
echo ""

cd "$(dirname "$0")"
jupyter notebook

