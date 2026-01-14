# Deployment & Showcase Guide

## Overview
This guide explains how to deploy and showcase the Special Olympics Simulation System on third-party platforms.

## Fixed Metrics
- **Containment Rate**: Fixed at 10% (0.1) - consistent across all simulations
- **Response Time**: Fixed at 5 minutes (300 seconds) - consistent across all simulations

## Local Development Setup

### Prerequisites
- Python 3.9+
- Node.js 18+
- npm or yarn

### Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn api.main:app --host 0.0.0.0 --port 3333
```

### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

The frontend will be available at `http://localhost:5173` (or the port shown in terminal).

## Deployment Options

### Option 1: Vercel (Frontend) + Railway/Render (Backend)

#### Frontend Deployment (Vercel)
1. **Install Vercel CLI**:
   ```bash
   npm i -g vercel
   ```

2. **Deploy**:
   ```bash
   cd frontend
   vercel
   ```

3. **Configure Environment Variables** in Vercel Dashboard:
   - `VITE_API_URL`: Your backend URL (e.g., `https://your-backend.railway.app`)

4. **Update API Configuration**:
   Edit `frontend/src/App.tsx`:
   ```typescript
   const getApiBaseUrl = () => {
     return import.meta.env.VITE_API_URL || 'http://localhost:3333'
   }
   ```

#### Backend Deployment (Railway)
1. **Create Railway Account**: https://railway.app
2. **Create New Project** → "Deploy from GitHub"
3. **Select Repository** → Set root directory to `backend`
4. **Configure Build Command**:
   ```bash
   pip install -r requirements.txt
   ```
5. **Configure Start Command**:
   ```bash
   uvicorn api.main:app --host 0.0.0.0 --port $PORT
   ```
6. **Set Environment Variables**:
   - `PORT`: Auto-set by Railway
   - `PYTHON_VERSION`: `3.11`

#### Backend Deployment (Render)
1. **Create Render Account**: https://render.com
2. **Create New Web Service**
3. **Connect GitHub Repository**
4. **Configure**:
   - **Root Directory**: `backend`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn api.main:app --host 0.0.0.0 --port $PORT`
   - **Environment**: Python 3

### Option 2: Docker Deployment

#### Create Dockerfile (Backend)
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 3333

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "3333"]
```

#### Create Dockerfile (Frontend)
```dockerfile
FROM node:18-alpine AS builder

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

#### Deploy to Docker Hub / AWS ECS / Google Cloud Run
```bash
# Build
docker build -t special-olympics-backend ./backend
docker build -t special-olympics-frontend ./frontend

# Run
docker run -p 3333:3333 special-olympics-backend
docker run -p 80:80 special-olympics-frontend
```

### Option 3: AWS Deployment

#### Backend (AWS Elastic Beanstalk)
1. Install EB CLI: `pip install awsebcli`
2. Initialize: `eb init -p python-3.11`
3. Create environment: `eb create special-olympics-backend`
4. Deploy: `eb deploy`

#### Frontend (AWS Amplify)
1. Connect GitHub repository
2. Set build settings:
   ```yaml
   version: 1
   frontend:
     phases:
       preBuild:
         commands:
           - npm install
       build:
         commands:
           - npm run build
     artifacts:
       baseDirectory: dist
       files:
         - '**/*'
   ```

### Option 4: Google Cloud Platform

#### Backend (Cloud Run)
```bash
# Build and deploy
gcloud builds submit --tag gcr.io/PROJECT_ID/special-olympics-backend ./backend
gcloud run deploy special-olympics-backend \
  --image gcr.io/PROJECT_ID/special-olympics-backend \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

#### Frontend (Firebase Hosting)
```bash
cd frontend
npm install -g firebase-tools
firebase login
firebase init hosting
npm run build
firebase deploy
```

## WebSocket Configuration

### Important Notes
- WebSocket connections require **persistent connections**
- Some platforms (like Vercel) have WebSocket limitations
- Consider using **Railway**, **Render**, or **AWS** for WebSocket support

### WebSocket URL Configuration
Update `frontend/src/App.tsx`:
```typescript
const getWsBaseUrl = () => {
  const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:3333'
  // Convert http:// to ws:// and https:// to wss://
  return apiUrl.replace(/^http/, 'ws')
}
```

## Environment Variables

### Backend
```bash
PORT=3333
PYTHON_VERSION=3.11
DEBUG=false
```

### Frontend
```bash
VITE_API_URL=https://your-backend-url.com
```

## Showcase Features

### Key Metrics (Fixed)
- **Containment Rate**: Always 10% (0.1)
- **Response Time**: Always 5 minutes (300 seconds)

### Live Features
- Real-time 3D visualization
- WebSocket streaming
- Multiple scenario support
- Interactive controls

## Testing Deployment

### Health Check Endpoint
```bash
curl https://your-backend-url.com/api/scenarios
```

### WebSocket Test
```javascript
const ws = new WebSocket('wss://your-backend-url.com/ws/runs/RUN_ID')
ws.onopen = () => console.log('Connected')
ws.onmessage = (event) => console.log('Message:', JSON.parse(event.data))
```

## Troubleshooting

### WebSocket Connection Issues
1. **Check CORS settings** in `backend/api/main.py`
2. **Verify WebSocket URL** uses `wss://` for HTTPS
3. **Check firewall/security groups** allow WebSocket connections
4. **Verify backend is running** and accessible

### Frontend Not Connecting
1. **Check `VITE_API_URL`** environment variable
2. **Verify CORS** allows frontend origin
3. **Check browser console** for errors
4. **Verify WebSocket URL** is correct

### Metrics Not Updating
1. **Check backend logs** for errors
2. **Verify WebSocket connection** is active
3. **Check browser network tab** for WebSocket messages
4. **Verify metrics are being sent** from backend

## Support

For issues or questions:
1. Check backend logs: `uvicorn api.main:app --log-level debug`
2. Check browser console for frontend errors
3. Verify all environment variables are set correctly
4. Ensure WebSocket connections are supported by your hosting platform

