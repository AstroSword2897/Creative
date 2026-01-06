# 🌐 Web Application - 3D Visualization

## Quick Start

### Option 1: Automated Script (Easiest)

```bash
./start_web_app.sh
```

This will:
- Start the backend API (port 8000)
- Start the frontend dev server (port 5173)
- Open the 3D visualization in your browser

### Option 2: Manual Start

**Terminal 1 - Backend:**
```bash
cd backend
python3 -m uvicorn api.main:app --reload --port 8000
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm install  # First time only
npm run dev
```

Then open: **http://localhost:5173**

## Features

### 🎨 Interactive 3D Visualization
- **Real-time agent movement** in 3D space
- **Interactive camera controls**:
  - Click & drag to rotate
  - Scroll to zoom
  - Right-click & drag to pan
- **Beautiful visuals**:
  - Gold spheres = Athletes
  - Teal boxes = Volunteers
  - Mint cylinders = Security
  - Blue cylinders = LVMPD
  - Red cylinders = AMR
  - Purple boxes = Buses
  - Pulsing spheres = Incidents
  - Glowing markers = Venues

### 📊 Real-Time Metrics
- Safety score
- Response times
- Incident tracking
- Agent activity

### 🎮 Controls
- Select scenario from sidebar
- Start/stop simulation
- View metrics in real-time
- Interactive 3D scene

## Technology Stack

- **Frontend**: React + TypeScript + Three.js
- **Backend**: FastAPI + Python
- **3D Engine**: Three.js (WebGL)
- **Real-time**: WebSocket updates

## Requirements

- Node.js 18+
- Python 3.8+
- npm or yarn

## Installation

```bash
# Backend dependencies
cd backend
pip install -r requirements.txt

# Frontend dependencies
cd ../frontend
npm install
```

## Troubleshooting

**3D scene not showing:**
- Check browser console for errors
- Ensure Three.js is installed: `npm install three`
- Try hard refresh (Cmd+Shift+R / Ctrl+Shift+R)

**Backend not connecting:**
- Check backend is running on port 8000
- Check CORS settings in `backend/api/main.py`

**Agents not moving:**
- Ensure simulation is started
- Check WebSocket connection
- Verify scenario has agents configured

## Next Steps

1. Open the web app
2. Select a scenario
3. Click "Start Simulation"
4. Watch the 3D visualization come to life!

Enjoy your interactive 3D simulation! 🎉

