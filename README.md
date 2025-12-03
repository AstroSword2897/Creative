# Special Olympics Las Vegas Security Simulation

An interactive simulation demonstrating how Las Vegas secures and supports Special Olympics athletes through coordinated efforts of real-world Las Vegas services, hotels, venues, public safety agencies, medical providers, and transportation systems.

## Real-World Las Vegas Services Integrated

This simulation uses **publicly available information** about real Las Vegas services:

### Hotels
- **MGM Grand Hotel & Casino**
- **Westgate Las Vegas Resort & Casino**
- **South Point Hotel, Casino & Spa**
- **The Venetian Resort Las Vegas**
- **Mandalay Bay Resort and Casino**
- **Luxor Hotel & Casino**
- **Resorts World Las Vegas**

### Competition Venues
- **UNLV Cox Pavilion**
- **Thomas & Mack Center**
- **Las Vegas Convention Center**
- **T-Mobile Arena**
- **Dollar Loan Center Arena**
- **Las Vegas Ballpark**

### Transportation
- **Las Vegas Monorail** (7 stations along the Strip)
- **RTC of Southern Nevada** (Regional Transportation Commission buses)
- **Designated Ride-Share Zones** (Uber/Lyft)

### Public Safety Agencies
- **LVMPD** (Las Vegas Metropolitan Police Department) - Community policing, traffic management, event coordination
- **Las Vegas Fire & Rescue** - Emergency medical services, fire suppression
- **Clark County Fire Department** - County-wide emergency services
- **AMR Las Vegas** (American Medical Response) - Emergency medical transportation

### Medical Facilities
- **University Medical Center (UMC)** - Trauma center
- **Sunrise Hospital & Medical Center** - Full-service hospital

### Airport
- **Harry Reid International Airport (LAS)** - Primary arrival point

**Note:** All information used is publicly available and non-sensitive. The simulation presents high-level, public-facing workflows and does not reveal any operational security details or tactical procedures.

## Project Structure

```
.
├── backend/              # Python simulation engine & API
│   ├── simulation/      # Mesa agent-based models
│   ├── api/             # FastAPI endpoints
│   ├── models/          # Data models
│   └── scenarios/       # Scenario JSON files
├── frontend/            # React + TypeScript + Mapbox
├── database/            # PostGIS setup scripts
├── docker-compose.yml   # Local development environment
└── docs/                # Documentation
```

## Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+
- Docker & Docker Compose
- PostgreSQL 14+ with PostGIS extension

### Local Development Setup

1. **Clone and setup backend:**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

2. **Setup database:**
```bash
docker-compose up -d postgres redis
cd database
psql -U postgres -f init.sql
python seed_spatial_data.py
```

3. **Start backend API:**
```bash
cd backend
uvicorn api.main:app --reload --port 8000
```

4. **Setup and start frontend:**
```bash
cd frontend
npm install
npm run dev
```

5. **Run a simulation:**
```bash
cd backend
python -m simulation.run_scenario scenarios/baseline.json
```

## Architecture

- **Simulation Engine**: Python Mesa for agent-based modeling
- **Backend API**: FastAPI with WebSocket support for real-time updates
- **Frontend**: React + TypeScript + Mapbox GL for interactive map visualization
- **Database**: PostgreSQL + PostGIS for spatial queries
- **State Management**: Redis for pub/sub and state caching

## Scenarios

1. **Baseline** - Standard operations
2. **Heat Surge** - High temperature medical events
3. **Medical Emergency** - Critical incident response
4. **Suspicious Person Detection** - Security threat response
5. **Crowd Surge** - Post-event congestion management
6. **VIP Delegation** - Privacy and media management
7. **Hotel Intrusion Attempt** - Access control validation

## API Endpoints

- `POST /api/scenarios` - Create new scenario
- `POST /api/scenarios/{id}/run` - Start simulation run
- `GET /api/runs/{run_id}/state` - Get current state snapshot
- `WS /ws/runs/{run_id}` - WebSocket stream for real-time updates
- `GET /api/runs/{run_id}/metrics` - Get computed KPIs

## Development Roadmap

See the detailed plan document for phased implementation milestones.

## License

[To be determined]

