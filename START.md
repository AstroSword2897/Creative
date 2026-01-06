# 🚀 Quick Start Guide

## Start the Web Application

### Option 1: Automated (Easiest)

```bash
./start_web_app.sh
```

### Option 2: Manual Start

**Terminal 1 - Backend:**
```bash
cd backend
python3 -m uvicorn api.main:app --reload --port 8000
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

## Access the Application

Open your browser to: **http://localhost:5173**

## What You'll See

1. **Left Panel**: Scenario selection
2. **Center**: Interactive 3D visualization
3. **Right Panel**: Real-time metrics

## To Start a Simulation

1. Click on a scenario in the left panel
2. Watch the 3D scene come to life
3. Agents will move in real-time
4. Metrics update automatically

## Features

- ✅ Diff-based updates (smooth performance)
- ✅ Shared geometry cache (efficient rendering)
- ✅ Working trails for athletes
- ✅ WebSocket lifecycle management
- ✅ Production-ready architecture

Enjoy! 🎉

