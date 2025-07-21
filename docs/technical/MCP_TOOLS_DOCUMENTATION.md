# 🔧 **MCP TOOLS DOCUMENTATION & USAGE GUIDE**

## 📊 **OVERVIEW**

Your Hospital Agent has **5 core MCP tools** integrated for comprehensive hospital management. These tools provide real-time data access, predictive analytics, and operational control through the Model Context Protocol.

## 🛠️ **INTEGRATED MCP TOOLS**

### **1. 🏥 `get_bed_occupancy_status`**
**Purpose**: Get comprehensive real-time bed occupancy across all hospital wards

**Usage**: 
```python
result = await manager.execute_tool('get_bed_occupancy_status')
```

**Returns**:
```json
{
  "total_beds": 18,
  "occupied_beds": 10,
  "vacant_beds": 7,
  "cleaning_beds": 1,
  "maintenance_beds": 0,
  "occupancy_rate": 55.6,
  "ward_breakdown": {
    "ICU": {"total": 5, "occupied": 5, "vacant": 0},
    "Emergency": {"total": 4, "occupied": 1, "vacant": 3},
    "General": {"total": 4, "occupied": 2, "vacant": 2},
    "Pediatric": {"total": 3, "occupied": 1, "vacant": 2},
    "Maternity": {"total": 2, "occupied": 1, "vacant": 1}
  },
  "timestamp": "2025-07-21T17:30:00"
}
```

**Chat Usage**: 
- "What is the current bed occupancy status?"
- "Show me hospital capacity"
- "How many beds are available?"

---

### **2. 🛏️ `get_available_beds`**
**Purpose**: Find available beds with optional filtering by ward or bed type

**Usage**:
```python
# All available beds
result = await manager.execute_tool('get_available_beds')

# ICU beds only
result = await manager.execute_tool('get_available_beds', ward='ICU')

# Emergency beds only
result = await manager.execute_tool('get_available_beds', ward='Emergency')
```

**Returns**:
```json
[
  {
    "bed_id": 2,
    "bed_number": "ER-02",
    "ward": "Emergency",
    "bed_type": "Standard",
    "status": "vacant",
    "equipment": "Standard equipment",
    "last_cleaned": null
  },
  {
    "bed_id": 4,
    "bed_number": "ER-04", 
    "ward": "Emergency",
    "bed_type": "Standard",
    "status": "vacant",
    "equipment": "Standard equipment",
    "last_cleaned": null
  }
]
```

**Chat Usage**:
- "Show me available beds"
- "Find available ICU beds"
- "What emergency beds are free?"

---

### **3. 🚨 `get_critical_bed_alerts`**
**Purpose**: Get critical alerts requiring immediate attention with recommendations

**Usage**:
```python
result = await manager.execute_tool('get_critical_bed_alerts')
```

**Returns**:
```json
[
  {
    "type": "capacity_critical",
    "priority": "critical",
    "title": "ICU Capacity Critical",
    "message": "ICU at 100.0% capacity (5/5 beds)",
    "department": "ICU",
    "action_required": true,
    "timestamp": "2025-07-21T17:30:00"
  }
]
```

**Alert Types**:
- **`capacity_critical`**: Ward at 90%+ capacity
- **`capacity_warning`**: Ward at 85%+ capacity  
- **`maintenance_alert`**: Multiple beds under maintenance

**Chat Usage**:
- "Are there any critical alerts?"
- "Show me urgent issues"
- "What problems need attention?"

---

### **4. 📊 `get_patient_discharge_predictions`**
**Purpose**: Get AI-powered predictions for upcoming patient discharges

**Usage**:
```python
result = await manager.execute_tool('get_patient_discharge_predictions')
```

**Returns**:
```json
[
  {
    "patient_id": "PAT001",
    "patient_name": "John Smith",
    "admission_date": "2025-07-16T12:00:00",
    "days_admitted": 5,
    "discharge_probability": 0.5,
    "predicted_discharge_date": "2025-07-22T12:00:00",
    "confidence": "medium"
  }
]
```

**Prediction Logic**:
- Based on admission duration and patient patterns
- Probability increases with length of stay
- Helps with capacity planning

**Chat Usage**:
- "Predict upcoming discharges"
- "Who might be discharged soon?"
- "Show me discharge predictions"

---

### **5. 🔄 `update_bed_status`**
**Purpose**: Update bed status with validation and logging

**Usage**:
```python
result = await manager.execute_tool('update_bed_status', 
                                  bed_number='ER-02', 
                                  new_status='cleaning',
                                  patient_id='PAT123')  # optional
```

**Parameters**:
- `bed_number` (required): Bed identifier (e.g., "ICU-01", "ER-02")
- `new_status` (required): New status ("occupied", "vacant", "cleaning", "maintenance")
- `patient_id` (optional): Patient ID if assigning to patient

**Returns**:
```json
{
  "success": true,
  "bed_number": "ER-02",
  "old_status": "vacant",
  "new_status": "cleaning",
  "patient_id": null,
  "timestamp": "2025-07-21T17:30:00"
}
```

**Chat Usage**:
- "Mark bed ER-02 as cleaning"
- "Update ICU-01 to occupied"
- "Set bed status to maintenance"

## 🎯 **REAL-TIME TEST RESULTS**

### **Current Hospital Status** (Live Data):
- **📊 Total Beds**: 18
- **🔴 Occupied**: 10 (55.6% occupancy)
- **🟢 Available**: 7 beds
- **🧹 Cleaning**: 1 bed

### **Ward Breakdown**:
- **🏥 ICU**: 100.0% (5/5) - **CRITICAL**
- **🚑 Emergency**: 25.0% (1/4) - Good availability
- **🏨 General**: 50.0% (2/4) - Moderate
- **👶 Pediatric**: 33.3% (1/3) - Good availability
- **🤱 Maternity**: 50.0% (1/2) - Moderate

### **Active Alerts**:
- **🚨 CRITICAL**: ICU Capacity Critical (100% full)

### **Available Beds** (7 total):
1. **ER-02** - Emergency
2. **ER-04** - Emergency  
3. **GEN-02** - General
4. **GEN-03** - General
5. **PED-02** - Pediatric
6. **PED-03** - Pediatric
7. **MAT-02** - Maternity

### **Discharge Predictions** (4 patients):
- **John Smith**: 50% probability (5 days admitted)
- **Mary Johnson**: 50% probability (5 days admitted)
- **John Doe**: 50% probability (5 days admitted)

## 🚀 **HOW TO USE MCP TOOLS**

### **1. Through Chat Interface**:
```
User: "What is the current bed occupancy status?"
Agent: Uses get_bed_occupancy_status tool → Returns detailed ward breakdown

User: "Show me available ICU beds"  
Agent: Uses get_available_beds(ward='ICU') → Returns ICU-specific beds

User: "Are there any critical alerts?"
Agent: Uses get_critical_bed_alerts → Returns urgent issues
```

### **2. Through API Endpoints**:
```bash
# Regular chat (MCP-enabled)
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Show me bed status"}'

# MCP-specific endpoint
curl -X POST http://localhost:8000/api/chat/mcp \
  -H "Content-Type: application/json" \
  -d '{"message": "Get critical alerts"}'

# MCP status check
curl http://localhost:8000/api/mcp/status
```

### **3. Direct Tool Testing**:
```bash
python test_mcp_tools.py
```

## 🎊 **MCP TOOLS ADVANTAGES**

### **🔄 Real-time Data**:
- Live database connections
- Always current information
- No cached or stale data

### **🎯 Specialized Functionality**:
- Hospital-specific operations
- Medical terminology and context
- Healthcare workflow optimization

### **🧠 Intelligent Processing**:
- Predictive analytics
- Pattern recognition
- Automated recommendations

### **🔌 Extensible Architecture**:
- Easy to add new tools
- Modular design
- Plugin-based system

**🏥 Your Hospital Agent now has 5 powerful MCP tools providing comprehensive real-time hospital management capabilities!** ✨
