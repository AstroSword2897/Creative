#!/bin/bash
# Start the web application with 3D visualization

echo "🚀 Starting Special Olympics Las Vegas Simulation Web App"
echo ""

# Check if we're in the right directory
if [ ! -d "frontend" ] || [ ! -d "backend" ]; then
    echo "❌ Error: Please run this from the project root directory"
    exit 1
fi

# Start backend API
echo "🔧 Starting backend API..."
cd backend
python3 -m uvicorn api.main:app --reload --port 8000 > ../backend.log 2>&1 &
BACKEND_PID=$!
cd ..

# Wait for backend to start
sleep 3

# Start frontend
echo "🎨 Starting frontend (3D visualization)..."
cd frontend

# Install dependencies if needed
if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies..."
    npm install
fi

# Start dev server
echo ""
echo "✅ Starting web application..."
echo "   Frontend: http://localhost:5173"
echo "   Backend API: http://localhost:8000"
echo ""
echo "💡 The 3D visualization will open in your browser"
echo "   Press Ctrl+C to stop"
echo ""

npm run dev

# Cleanup on exit
trap "kill $BACKEND_PID 2>/dev/null" EXIT

