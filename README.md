# 🏥 Hospital Agent - Bed Management System

A comprehensive hospital bed management system with AI-powered agents, real-time monitoring, and intelligent workflow automation using MCP (Model Context Protocol) integration.

## ✨ Features

- **🔄 Real-time Bed Monitoring**: Live tracking of bed occupancy across all hospital wards
- **🤖 AI-Powered Chat Agent**: Intelligent assistant with MCP tools for bed management
- **👥 Patient Assignment Workflow**: Streamlined patient admission and bed assignment
- **🚨 Enhanced Alert System**: Real-time notifications for all ward capacity issues
- **📊 Interactive Dashboard**: Comprehensive web-based dashboard for hospital staff
- **📈 Predictive Analytics**: AI-driven discharge predictions and capacity management
- **🔧 MCP Tools Integration**: 7 specialized hospital management tools
- **👨‍⚕️ Doctor Integration**: Complete doctor database with specialization tracking

## 🛠 Technology Stack

- **Backend**: FastAPI, SQLAlchemy, Python, MCP Protocol
- **Frontend**: React, Vite, Tailwind CSS
- **AI/ML**: Gemini 2.5 Flash, LangChain, RAG System, LangGraph
- **Database**: SQLite (development), PostgreSQL (production)
- **Real-time**: WebSocket connections, Live alerts, MCP tools

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Node.js 16+
- npm or yarn

### Backend Setup
```bash
cd backend
pip install -r requirements.txt
python main.py
```

### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

### Access the Application
- **Frontend Dashboard**: http://localhost:3001
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

## 📁 Project Structure

```
hospital_agent/
├── 🔧 backend/              # FastAPI backend application
├── 🖥️ frontend/             # React frontend application  
├── 🤖 agents/               # AI agent implementations (MCP + LangGraph)
├── 🏥 hospital_mcp/         # MCP server and tools
├── 📊 data/                 # Database and data files
├── 🔧 scripts/              # Utility and management scripts
├── 🧪 tests/                # All testing files
└── 📚 docs/                 # Documentation and guides
    ├── 📖 guides/           # User guides and tutorials
    ├── 🔧 technical/        # Technical documentation
    └── 📋 api/              # API documentation
```

## 🎯 Key Components

### 1. 🤖 MCP-Powered Bed Management Agent
- 7 specialized MCP tools for hospital operations
- Intelligent bed assignment with real-time data
- Predictive discharge planning (70%+ accuracy)
- Multi-ward capacity monitoring

### 2. 📊 Real-time Dashboard
- Live bed status visualization across all wards
- Interactive patient assignment interface
- Enhanced notification system with detailed alerts
- Ward-wise occupancy tracking with critical alerts

### 3. 💬 Enhanced Chat Interface
- Natural language patient assignment ("assign John to bed ICU-01")
- MCP-powered intelligent responses
- Automated workflow execution
- Real-time hospital data integration

### 4. 🚨 Advanced Alert System
- Real-time monitoring of ALL wards (not just ICU)
- Critical capacity alerts (≥90% occupancy)
- Enhanced notification bell with detailed popup
- Proactive workflow triggers

## 🔧 MCP Tools Available

1. **`get_bed_occupancy_status`** - Real-time bed status across all wards
2. **`get_available_beds`** - Available beds with filtering options
3. **`get_critical_bed_alerts`** - Critical alerts and recommendations
4. **`get_patient_discharge_predictions`** - AI-powered discharge forecasting
5. **`update_bed_status`** - Bed status management with validation
6. **`assign_patient_to_bed`** - Assign existing patients to beds
7. **`create_patient_and_assign`** - Create new patient and assign bed

## 📋 API Endpoints

### 🛏️ Bed Management
- `GET /api/beds` - Get all beds with current status
- `GET /api/beds/occupancy` - Get detailed occupancy statistics
- `POST /api/beds/{bed_number}/assign-new-patient` - Assign patient to bed

### 👥 Patient Management
- `GET /api/patients` - Get all patients
- `POST /api/patients` - Create new patient record
- `PUT /api/patients/{patient_id}` - Update patient information

### 🚨 Enhanced Alerts
- `GET /api/alerts/active` - Get real-time MCP-powered alerts
- `GET /api/mcp/status` - Check MCP system status

### 🤖 AI Chat Agent
- `POST /api/chat` - Chat with MCP-enabled agent
- `POST /api/chat/mcp` - Direct MCP agent access

### 👨‍⚕️ Doctor Management
- `GET /api/doctors` - Get all available doctors with specializations

## 🧪 Testing

All test files are organized in the `tests/` folder:

```bash
# Run all tests
cd tests
python test_all_functionality.py

# Test specific components
python test_mcp_tools.py           # Test MCP tools
python test_patient_assignment.py  # Test patient assignment
python test_backend_health.py      # Test backend health
```

## 📚 Documentation

Comprehensive documentation is available in the `docs/` folder:

- **📖 `docs/guides/`** - User guides and tutorials
- **🔧 `docs/technical/`** - Technical implementation details
- **📋 `docs/api/`** - API documentation

## 🎊 Recent Achievements (July 2025)

- ✅ **MCP Integration**: 7 specialized hospital tools
- ✅ **Enhanced Alerts**: Real-time monitoring of ALL wards
- ✅ **Patient Assignment**: Complete chat + dashboard workflow
- ✅ **Doctor Integration**: Full database integration with specializations
- ✅ **Predictive Analytics**: AI-powered discharge predictions
- ✅ **File Organization**: Proper project structure with tests and docs

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests for new functionality
5. Run tests: `cd tests && python test_all_functionality.py`
6. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- 📧 Open an issue in the GitHub repository
- 📚 Check the documentation in `docs/guides/`
- 🧪 Run tests in `tests/` folder to verify functionality

---

**🏥 Hospital Agent - Transforming hospital operations with AI-powered bed management and real-time intelligence!** ✨
