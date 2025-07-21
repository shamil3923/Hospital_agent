"""
Real-Time Bed Status Monitoring System
Automatically tracks and updates bed occupancy status with live dashboard updates
"""
import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from sqlalchemy import event, and_
import threading
import time

try:
    from .database import SessionLocal, Bed, Patient, BedOccupancyHistory
    from .websocket_manager import WebSocketManager
except ImportError:
    from database import SessionLocal, Bed, Patient, BedOccupancyHistory
    from websocket_manager import WebSocketManager

logger = logging.getLogger(__name__)

class RealTimeBedMonitor:
    """Real-time bed status monitoring and broadcasting system"""
    
    def __init__(self, websocket_manager: WebSocketManager):
        self.websocket_manager = websocket_manager
        self.is_monitoring = False
        self.monitoring_task = None
        self.bed_status_cache: Dict[str, Dict] = {}
        self.last_update = datetime.now()
        self.update_interval = 2  # Update every 2 seconds
        self.change_detection_enabled = True
        
        # Status change tracking
        self.status_change_history: List[Dict] = []
        self.max_history_size = 100
        
        # Performance metrics
        self.metrics = {
            'total_updates': 0,
            'status_changes': 0,
            'broadcast_count': 0,
            'last_broadcast': None,
            'average_response_time': 0
        }

        self.predicted_occupancy_curve = []  # Store predicted occupancy for dashboard
        self.risk_days = []  # Store risk days/times
        self.forecasting_task = None
    
    async def start_monitoring(self):
        """Start real-time bed monitoring"""
        if self.is_monitoring:
            logger.warning("Bed monitoring is already running")
            return
        
        self.is_monitoring = True
        logger.info("🛏️ Starting real-time bed status monitoring...")
        
        # Initialize bed status cache
        await self.initialize_bed_cache()
        
        # Start monitoring loop
        self.monitoring_task = asyncio.create_task(self.monitoring_loop())
        
        # Start forecasting loop
        self.forecasting_task = asyncio.create_task(self.forecasting_loop())
        
        logger.info("✅ Real-time bed monitoring started")
    
    async def stop_monitoring(self):
        """Stop real-time bed monitoring"""
        self.is_monitoring = False
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
        if self.forecasting_task:
            self.forecasting_task.cancel()
            try:
                await self.forecasting_task
            except asyncio.CancelledError:
                pass
        logger.info("🛑 Real-time bed monitoring stopped")
    
    async def initialize_bed_cache(self):
        """Initialize the bed status cache with current data"""
        try:
            with SessionLocal() as db:
                beds = db.query(Bed).all()
                
                for bed in beds:
                    bed_data = {
                        'id': bed.id,
                        'bed_number': bed.bed_number,
                        'room_number': bed.room_number,
                        'ward': bed.ward,
                        'bed_type': bed.bed_type,
                        'status': bed.status,
                        'patient_id': bed.patient_id,
                        'last_updated': bed.last_updated.isoformat() if bed.last_updated else None,
                        'created_at': bed.created_at.isoformat() if bed.created_at else None
                    }
                    
                    self.bed_status_cache[bed.bed_number] = bed_data
                
                logger.info(f"📊 Initialized bed cache with {len(beds)} beds")
                
        except Exception as e:
            logger.error(f"❌ Error initializing bed cache: {e}")
    
    async def monitoring_loop(self):
        """Main monitoring loop that checks for bed status changes"""
        while self.is_monitoring:
            try:
                start_time = time.time()
                
                # Check for bed status changes
                changes = await self.detect_bed_changes()
                
                if changes:
                    # Broadcast changes to connected clients
                    await self.broadcast_bed_updates(changes)
                    
                    # Update metrics
                    self.metrics['status_changes'] += len(changes)
                    self.metrics['broadcast_count'] += 1
                    self.metrics['last_broadcast'] = datetime.now().isoformat()
                
                # Update performance metrics
                response_time = time.time() - start_time
                self.metrics['total_updates'] += 1
                self.metrics['average_response_time'] = (
                    (self.metrics['average_response_time'] * (self.metrics['total_updates'] - 1) + response_time) 
                    / self.metrics['total_updates']
                )
                
                # Wait for next update cycle
                await asyncio.sleep(self.update_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"❌ Error in monitoring loop: {e}")
                await asyncio.sleep(self.update_interval)
    
    async def forecasting_loop(self):
        """Periodically forecast bed occupancy and alert if shortage is predicted"""
        while self.is_monitoring:
            try:
                await self.run_predictive_forecasting()
            except Exception as e:
                logger.error(f"❌ Error in forecasting loop: {e}")
            await asyncio.sleep(600)  # Run every 10 minutes

    async def run_predictive_forecasting(self):
        """Forecast bed occupancy and generate alerts if needed"""
        from alert_system import alert_system, Alert, AlertType, AlertPriority
        with SessionLocal() as db:
            # 1. Get all current patients with expected discharge dates
            now = datetime.now()
            future_window = now + timedelta(hours=24)
            patients = db.query(Patient).filter(
                Patient.status == "admitted",
                Patient.expected_discharge_date.isnot(None),
                Patient.expected_discharge_date >= now,
                Patient.expected_discharge_date <= future_window
            ).all()
            # 2. Build a timeline of predicted discharges
            discharge_events = []
            for p in patients:
                discharge_events.append((p.expected_discharge_date, -1))  # -1 bed when discharged
            # 3. Get all beds and current occupancy
            total_beds = db.query(Bed).count()
            occupied_beds = db.query(Bed).filter(Bed.status == "occupied").count()
            # 4. Estimate expected admissions for each hour (use historical inflow)
            # For simplicity, use last 7 days admissions per hour as average
            admissions_per_hour = [0]*25
            for h in range(1,25):
                start = now - timedelta(days=7)
                end = now + timedelta(hours=h)
                count = db.query(Patient).filter(
                    Patient.admission_date >= start,
                    Patient.admission_date < end
                ).count()
                admissions_per_hour[h] = count // 7  # crude average
            # 5. Build predicted occupancy curve
            curve = []
            risk_hours = []
            current_occupied = occupied_beds
            events = sorted(discharge_events)
            event_idx = 0
            for h in range(1,25):
                t = now + timedelta(hours=h)
                # Apply discharges up to this hour
                while event_idx < len(events) and events[event_idx][0] <= t:
                    current_occupied += events[event_idx][1]
                    event_idx += 1
                # Add expected admissions
                current_occupied += admissions_per_hour[h]
                available = total_beds - current_occupied
                curve.append({
                    'time': t.isoformat(),
                    'predicted_occupied': current_occupied,
                    'predicted_available': available
                })
                # If predicted available beds < expected admissions for this hour, mark as risk
                if available < admissions_per_hour[h]:
                    risk_hours.append(t)
                    # Generate alert if not already sent for this window
                    if alert_system:
                        alert = Alert(
                            type=AlertType.CAPACITY_CRITICAL,
                            priority=AlertPriority.HIGH,
                            title="Forecasted Capacity Constraint",
                            message=f"Predicted bed shortage at {t.strftime('%Y-%m-%d %H:%M')}. Available: {available}, Expected admissions: {admissions_per_hour[h]}",
                            department="Administration",
                            action_required=True,
                            metadata={
                                'predicted_available': available,
                                'expected_admissions': admissions_per_hour[h],
                                'forecast_time': t.isoformat()
                            }
                        )
                        await alert_system.create_alert(alert)
            self.predicted_occupancy_curve = curve
            self.risk_days = [t.isoformat() for t in risk_hours]

    async def detect_bed_changes(self) -> List[Dict]:
        """Detect changes in bed status since last check"""
        changes = []
        
        try:
            with SessionLocal() as db:
                beds = db.query(Bed).all()
                
                for bed in beds:
                    bed_number = bed.bed_number
                    current_status = {
                        'id': bed.id,
                        'bed_number': bed.bed_number,
                        'room_number': bed.room_number,
                        'ward': bed.ward,
                        'bed_type': bed.bed_type,
                        'status': bed.status,
                        'patient_id': bed.patient_id,
                        'last_updated': bed.last_updated.isoformat() if bed.last_updated else None,
                        'created_at': bed.created_at.isoformat() if bed.created_at else None
                    }
                    
                    # Check if bed status has changed
                    if bed_number in self.bed_status_cache:
                        cached_status = self.bed_status_cache[bed_number]
                        
                        # Compare key fields for changes
                        if (cached_status['status'] != current_status['status'] or
                            cached_status['patient_id'] != current_status['patient_id'] or
                            cached_status['last_updated'] != current_status['last_updated']):
                            
                            change = {
                                'bed_number': bed_number,
                                'previous_status': cached_status['status'],
                                'new_status': current_status['status'],
                                'previous_patient_id': cached_status['patient_id'],
                                'new_patient_id': current_status['patient_id'],
                                'timestamp': datetime.now().isoformat(),
                                'change_type': self.determine_change_type(cached_status, current_status),
                                'bed_data': current_status
                            }
                            
                            changes.append(change)
                            
                            # Update cache
                            self.bed_status_cache[bed_number] = current_status
                            
                            # Add to change history
                            self.add_to_change_history(change)
                    
                    else:
                        # New bed detected
                        self.bed_status_cache[bed_number] = current_status
                        changes.append({
                            'bed_number': bed_number,
                            'previous_status': None,
                            'new_status': current_status['status'],
                            'previous_patient_id': None,
                            'new_patient_id': current_status['patient_id'],
                            'timestamp': datetime.now().isoformat(),
                            'change_type': 'new_bed',
                            'bed_data': current_status
                        })
                
        except Exception as e:
            logger.error(f"❌ Error detecting bed changes: {e}")
        
        return changes
    
    def determine_change_type(self, previous: Dict, current: Dict) -> str:
        """Determine the type of change that occurred"""
        prev_status = previous['status']
        curr_status = current['status']
        prev_patient = previous['patient_id']
        curr_patient = current['patient_id']
        
        if prev_status != curr_status:
            if curr_status == 'occupied' and prev_status == 'vacant':
                return 'admission'
            elif curr_status == 'vacant' and prev_status == 'occupied':
                return 'discharge'
            elif curr_status == 'cleaning':
                return 'cleaning_started'
            elif prev_status == 'cleaning':
                return 'cleaning_completed'
            else:
                return 'status_change'
        
        elif prev_patient != curr_patient:
            return 'patient_change'
        
        return 'update'
    
    def add_to_change_history(self, change: Dict):
        """Add change to history with size limit"""
        self.status_change_history.append(change)
        
        # Maintain history size limit
        if len(self.status_change_history) > self.max_history_size:
            self.status_change_history = self.status_change_history[-self.max_history_size:]
    
    async def broadcast_bed_updates(self, changes: List[Dict]):
        """Broadcast bed status updates to all connected clients"""
        if not changes:
            return
        
        # Prepare broadcast message
        message = {
            'type': 'bed_status_update',
            'timestamp': datetime.now().isoformat(),
            'changes': changes,
            'total_changes': len(changes),
            'summary': self.generate_change_summary(changes)
        }
        
        # Broadcast to bed status connections
        await self.websocket_manager.broadcast_to_bed_status(message)
        
        # Also broadcast to dashboard connections
        dashboard_message = {
            'type': 'dashboard_bed_update',
            'timestamp': datetime.now().isoformat(),
            'bed_summary': await self.get_bed_summary(),
            'recent_changes': changes[-5:],  # Last 5 changes
            'metrics': self.get_monitoring_metrics()
        }
        
        await self.websocket_manager.send_to_dashboard(dashboard_message)
        
        logger.info(f"📡 Broadcasted {len(changes)} bed status changes")
    
    def generate_change_summary(self, changes: List[Dict]) -> Dict:
        """Generate a summary of changes for quick overview"""
        summary = {
            'total_changes': len(changes),
            'admissions': 0,
            'discharges': 0,
            'cleaning_started': 0,
            'cleaning_completed': 0,
            'status_changes': 0,
            'affected_wards': set()
        }
        
        for change in changes:
            change_type = change['change_type']
            if change_type in summary:
                summary[change_type] += 1
            else:
                summary['status_changes'] += 1
            
            # Track affected wards
            if 'bed_data' in change:
                summary['affected_wards'].add(change['bed_data']['ward'])
        
        summary['affected_wards'] = list(summary['affected_wards'])
        return summary
    
    async def get_bed_summary(self) -> Dict:
        """Get current bed summary for dashboard"""
        try:
            with SessionLocal() as db:
                total_beds = db.query(Bed).count()
                occupied_beds = db.query(Bed).filter(Bed.status == "occupied").count()
                vacant_beds = db.query(Bed).filter(Bed.status == "vacant").count()
                cleaning_beds = db.query(Bed).filter(Bed.status == "cleaning").count()
                
                occupancy_rate = (occupied_beds / total_beds * 100) if total_beds > 0 else 0
                
                return {
                    'total_beds': total_beds,
                    'occupied_beds': occupied_beds,
                    'vacant_beds': vacant_beds,
                    'cleaning_beds': cleaning_beds,
                    'occupancy_rate': round(occupancy_rate, 1),
                    'last_updated': datetime.now().isoformat()
                }
        except Exception as e:
            logger.error(f"❌ Error getting bed summary: {e}")
            return {}
    
    def get_monitoring_metrics(self) -> Dict:
        """Get monitoring performance metrics"""
        return {
            **self.metrics,
            'cache_size': len(self.bed_status_cache),
            'history_size': len(self.status_change_history),
            'is_monitoring': self.is_monitoring,
            'update_interval': self.update_interval
        }

    def get_predicted_occupancy_curve(self):
        return self.predicted_occupancy_curve

    def get_risk_days(self):
        return self.risk_days
    
    async def force_update(self):
        """Force an immediate update check"""
        if self.is_monitoring:
            changes = await self.detect_bed_changes()
            if changes:
                await self.broadcast_bed_updates(changes)
            return changes
        return []
    
    def get_change_history(self, limit: int = 50) -> List[Dict]:
        """Get recent change history"""
        return self.status_change_history[-limit:] if self.status_change_history else []

# Singleton pattern for global bed monitor
class BedMonitorSingleton:
    _instance = None
    _bed_monitor = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(BedMonitorSingleton, cls).__new__(cls)
        return cls._instance

    def initialize(self, websocket_manager: WebSocketManager):
        """Initialize the bed monitor"""
        if self._bed_monitor is None:
            self._bed_monitor = RealTimeBedMonitor(websocket_manager)
            logger.info("🛏️ Bed monitor singleton initialized")
        return self._bed_monitor

    def get_monitor(self) -> Optional[RealTimeBedMonitor]:
        """Get the bed monitor instance"""
        return self._bed_monitor

    def reset(self):
        """Reset the singleton (for testing)"""
        self._bed_monitor = None

# Global singleton instance
_bed_monitor_singleton = BedMonitorSingleton()

def get_bed_monitor() -> Optional[RealTimeBedMonitor]:
    """Get the global bed monitor instance"""
    return _bed_monitor_singleton.get_monitor()

def initialize_bed_monitor(websocket_manager: WebSocketManager) -> RealTimeBedMonitor:
    """Initialize the global bed monitor"""
    return _bed_monitor_singleton.initialize(websocket_manager)
