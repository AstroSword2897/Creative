# Debug Report - Simulation Issues

## Issues Found

### 1. Frontend Validation Error
**Problem:** Frontend rejects "completed" messages because validation expects `data.agents` structure
**Location:** `frontend/src/App.tsx:205`
**Error:** "Invalid message shape, skipping: [object Object]"
**Fix Needed:** Update validation to handle "completed" message type differently

### 2. Simulation Completing Too Quickly
**Problem:** Simulation completes after only 1 step
**Backend Log:** "Simulation completed for run ... after 1 steps"
**Possible Causes:**
- End time calculation issue
- Time comparison logic
- Step duration vs end time mismatch

### 3. Console Warnings
- "View3D: No scene or state" - Expected when no simulation running
- Agent location out of bounds warnings - Some agents have locations outside normalized bounds

## Screenshots Captured
1. `frontend-home.png` - Initial page load with scenario buttons
2. `simulation-running.png` - Simulation started but showing "Connection lost" warning

## Network Activity
✅ Scenarios API: Working (200 OK)
✅ Start Simulation API: Working (200 OK)  
✅ WebSocket Connection: Working (101 Switching Protocols)
✅ State Updates: Received initial state and 1 update
❌ Completed Message: Rejected by frontend validation

## Next Steps
1. Fix frontend validation to handle "completed" messages
2. Investigate why simulation ends after 1 step
3. Check time calculation logic in model.step()

