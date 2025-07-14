# 🏥 Hospital Bed Management Agent - Run Steps

## Prerequisites
- Python 3.8+ installed
- Node.js 16+ installed
- PostgreSQL running (or use SQLite for testing)

## Step-by-Step Instructions

### 1. Install Python Dependencies
```bash
pip install -r requirements.txt
```

### 2. Install Frontend Dependencies
```bash
cd frontend
npm install
cd ..
```

### 3. Setup Environment (Optional)
```bash
# Copy and edit .env if needed
cp .env.example .env
```

### 4. Initialize Database with Sample Data
```bash
python scripts/init_data.py
```

### 5. Start the Platform
```bash
python start_platform.py
```

## What Happens Next

1. **Backend starts** on http://localhost:8000
2. **Frontend starts** on http://localhost:3000
3. **Browser opens** automatically to the dashboard
4. **Sample data** is loaded (16 beds, 8 patients)

## Using the Platform

### Dashboard
- View real-time bed occupancy metrics
- See interactive charts and trends
- Monitor system status and alerts

### Chat Interface
- Click "Chat Interface" in the sidebar
- Ask questions about bed management
- Get AI-powered responses with real data

### Sample Questions
- "What's the current bed occupancy?"
- "Show available ICU beds"
- "Any critical alerts?"
- "Expected discharges today?"

## Troubleshooting

### Port Issues
```bash
# If ports are in use, kill processes
npx kill-port 3000 8000
```

### Database Issues
```bash
# Reinitialize database
python scripts/init_data.py
```

### Dependency Issues
```bash
# Reinstall Python packages
pip install --upgrade -r requirements.txt

# Reinstall Node packages
cd frontend
rm -rf node_modules package-lock.json
npm install
cd ..
```

## Project Structure
```
Hospital_Agent/
├── backend/           # FastAPI backend
├── frontend/          # React frontend
├── agents/            # LangGraph agents
├── scripts/           # Utility scripts
├── requirements.txt   # Python dependencies
└── start_platform.py  # Main startup script
```

## Key URLs
- **Dashboard**: http://localhost:3000
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/api/health

---
**🎉 That's it! Your Hospital Bed Management Agent is ready to use.**
