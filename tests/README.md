# 🧪 Hospital Agent Testing Suite

This folder contains all testing files for the Hospital Agent platform. Tests are organized by functionality and component.

## 📁 Test Files Overview

### 🔧 Core System Tests
- **`test_all_functionality.py`** - Comprehensive system test suite
- **`test_backend_health.py`** - Backend API health checks
- **`debug_issues.py`** - System debugging and issue identification

### 🤖 MCP & Agent Tests
- **`test_mcp_tools.py`** - Test all 7 MCP tools functionality
- **`test_enhanced_chatbot.py`** - Chat agent and conversation testing
- **`test_enhanced_predictions.py`** - Discharge prediction accuracy tests

### 👥 Patient Management Tests
- **`test_patient_assignment.py`** - Patient assignment workflow testing
- **`test_dashboard_assignment.py`** - Dashboard patient assignment interface

### 🚨 Alert System Tests
- **`test_alert_system.py`** - Alert generation and notification testing

### 🌐 API & Integration Tests
- **`test_doctors_api.py`** - Doctor database API testing
- **`test_cors_doctors.py`** - CORS configuration testing
- **`test_preflight.py`** - HTTP preflight request testing

### 🖥️ Frontend Tests
- **`test_frontend_alerts.html`** - Frontend alert system testing

## 🚀 Running Tests

### Run All Tests
```bash
cd tests
python test_all_functionality.py
```

### Run Specific Test Categories

#### MCP Tools Testing
```bash
python test_mcp_tools.py
```

#### Patient Assignment Testing
```bash
python test_patient_assignment.py
```

#### Backend Health Check
```bash
python test_backend_health.py
```

#### Enhanced Chatbot Testing
```bash
python test_enhanced_chatbot.py
```

#### Alert System Testing
```bash
python test_alert_system.py
```

### Debug System Issues
```bash
python debug_issues.py
```

## 📊 Test Coverage

| Component | Test File | Status | Coverage |
|-----------|-----------|--------|----------|
| MCP Tools | `test_mcp_tools.py` | ✅ Complete | 7/7 tools |
| Patient Assignment | `test_patient_assignment.py` | ✅ Complete | Full workflow |
| Backend APIs | `test_backend_health.py` | ✅ Complete | All endpoints |
| Chat Agent | `test_enhanced_chatbot.py` | ✅ Complete | Enhanced features |
| Alert System | `test_alert_system.py` | ✅ Complete | Real-time alerts |
| Doctor Integration | `test_doctors_api.py` | ✅ Complete | Full database |
| Predictions | `test_enhanced_predictions.py` | ✅ Complete | AI accuracy |

## 🎯 Test Scenarios Covered

### 🤖 MCP Tools Testing
- ✅ Bed occupancy status retrieval
- ✅ Available beds filtering
- ✅ Critical alerts generation
- ✅ Discharge predictions accuracy
- ✅ Bed status updates
- ✅ Patient assignment workflows
- ✅ New patient creation and assignment

### 👥 Patient Management Testing
- ✅ Patient assignment through chat
- ✅ Patient assignment through dashboard
- ✅ Doctor selection integration
- ✅ Ward assignment logic
- ✅ Validation and error handling

### 🚨 Alert System Testing
- ✅ Real-time ward capacity monitoring
- ✅ Critical alert generation (≥90% occupancy)
- ✅ Multi-ward alert detection
- ✅ Notification bell functionality
- ✅ Alert popup interface

### 🌐 API Integration Testing
- ✅ CORS configuration
- ✅ HTTP preflight requests
- ✅ Doctor database integration
- ✅ Real-time data synchronization

## 🔧 Test Environment Setup

### Prerequisites
```bash
# Ensure backend is running
cd ../backend
python main.py

# Ensure frontend is running (for integration tests)
cd ../frontend
npm run dev
```

### Environment Variables
- Backend URL: `http://localhost:8000`
- Frontend URL: `http://localhost:3001`
- Database: SQLite (test database)

## 📈 Test Results Interpretation

### Success Indicators
- ✅ All API endpoints return 200 status
- ✅ MCP tools execute without errors
- ✅ Patient assignment workflows complete
- ✅ Alerts generate for critical conditions
- ✅ Real-time data synchronization works

### Common Issues & Solutions
- **Database Connection**: Ensure backend is running
- **CORS Errors**: Check frontend/backend URL configuration
- **MCP Tool Failures**: Verify database has test data
- **Alert Generation**: Confirm bed occupancy data exists

## 🤝 Adding New Tests

1. Create test file following naming convention: `test_[component].py`
2. Include comprehensive test scenarios
3. Add error handling and edge cases
4. Update this README with new test information
5. Ensure tests can run independently

## 📞 Troubleshooting

If tests fail:
1. Check backend is running on port 8000
2. Verify database has test data
3. Ensure all dependencies are installed
4. Check logs for specific error messages
5. Run `debug_issues.py` for system diagnostics

---

**🧪 Comprehensive testing suite ensuring Hospital Agent reliability and performance!** ✨
