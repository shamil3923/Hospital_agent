import React, { useState, useEffect } from 'react';
import {
  Bed,
  Users,
  TrendingUp,
  AlertTriangle,
  Activity,
  Clock,
  CheckCircle,
  XCircle,
  RefreshCw,
  Bot,
  Brain,
  Target
} from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, ReferenceDot } from 'recharts';
import axios from 'axios';
import RealTimeBedMonitor from './RealTimeBedMonitor';
import BedManagement from './BedManagement';
import AutonomousSystemDashboard from './AutonomousSystemDashboard';
import BedRecommendations from './BedRecommendations';

const Dashboard = () => {
  const [metrics, setMetrics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [lastUpdate, setLastUpdate] = useState(new Date());
  const [activeTab, setActiveTab] = useState('overview');
  const [predictedCurve, setPredictedCurve] = useState([]);
  const [riskHours, setRiskHours] = useState([]);
  const [autonomousStatus, setAutonomousStatus] = useState(null);
  const [alerts, setAlerts] = useState([]);

  // Mock time series data for charts
  const occupancyTrend = [
    { time: '00:00', occupancy: 72 },
    { time: '04:00', occupancy: 68 },
    { time: '08:00', occupancy: 75 },
    { time: '12:00', occupancy: 82 },
    { time: '16:00', occupancy: 85 },
    { time: '20:00', occupancy: 78 },
    { time: '24:00', occupancy: 75 }
  ];

  const fetchMetrics = async () => {
    try {
      setLoading(true);
      const response = await axios.get('http://localhost:8000/api/dashboard/metrics');
      setMetrics(response.data);
      setLastUpdate(new Date());
    } catch (error) {
      console.error('Error fetching metrics:', error);
      // Set default values if API fails
      setMetrics({
        bed_occupancy: 0,
        patient_satisfaction: 0,
        available_staff: 0,
        resource_utilization: 0,
        total_beds: 0,
        occupied_beds: 0,
        vacant_beds: 0,
        cleaning_beds: 0
      });
    } finally {
      setLoading(false);
    }
  };

  const fetchPredictedOccupancy = async () => {
    try {
      const response = await axios.get('http://localhost:8000/api/beds/predicted-occupancy');
      if (response.data && response.data.predicted_occupancy_curve) {
        setPredictedCurve(response.data.predicted_occupancy_curve);
        setRiskHours(response.data.risk_days || []);
      }
    } catch (error) {
      console.error('Error fetching predicted occupancy:', error);
      setPredictedCurve([]);
      setRiskHours([]);
    }
  };

  const fetchAutonomousStatus = async () => {
    try {
      const response = await axios.get('http://localhost:8000/api/autonomous/status');
      setAutonomousStatus(response.data);
    } catch (error) {
      console.error('Error fetching autonomous status:', error);
      setAutonomousStatus(null);
    }
  };

  const fetchAlerts = async () => {
    try {
      console.log('🚨 Dashboard: Fetching alerts from API...');

      const response = await axios.get('http://localhost:8000/api/alerts/active', {
        headers: {
          'Cache-Control': 'no-cache',
          'Pragma': 'no-cache'
        },
        timeout: 10000
      });

      console.log('🚨 Dashboard: Alert API Response:', response.data);
      console.log('🚨 Dashboard: Alerts array:', response.data.alerts);
      console.log('🚨 Dashboard: Alerts length:', response.data.alerts?.length || 0);

      const alertsArray = response.data.alerts || [];
      console.log('🚨 Dashboard: Setting alerts:', alertsArray);
      setAlerts(alertsArray);

    } catch (error) {
      console.error('❌ Dashboard: Error fetching alerts:', error);
      setAlerts([]);
    }
  };

  useEffect(() => {
    fetchMetrics();
    fetchPredictedOccupancy();
    fetchAutonomousStatus();
    fetchAlerts();
    const interval = setInterval(() => {
      fetchMetrics();
      fetchPredictedOccupancy();
      fetchAutonomousStatus();
      fetchAlerts();
    }, 30000); // Update every 30 seconds
    return () => clearInterval(interval);
  }, []);

  if (loading && !metrics) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  const getStatusColor = (rate) => {
    if (rate >= 90) return 'text-red-600 bg-red-100';
    if (rate >= 85) return 'text-yellow-600 bg-yellow-100';
    return 'text-green-600 bg-green-100';
  };

  const getStatusIcon = (rate) => {
    if (rate >= 90) return <XCircle className="h-4 w-4" />;
    if (rate >= 85) return <AlertTriangle className="h-4 w-4" />;
    return <CheckCircle className="h-4 w-4" />;
  };

  const bedDistributionData = metrics ? [
    { name: 'Occupied', value: metrics.occupied_beds, color: '#ef4444' },
    { name: 'Vacant', value: metrics.vacant_beds, color: '#22c55e' },
    { name: 'Cleaning', value: metrics.cleaning_beds, color: '#f59e0b' }
  ] : [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Hospital Operations Dashboard</h1>
            <p className="text-gray-600 mt-1">
              AI-powered healthcare operations management with real-time monitoring
            </p>
          </div>

          {/* Notification Bell */}
          {alerts.length > 0 && (
            <div className="relative">
              <AlertTriangle className="h-8 w-8 text-red-500 animate-pulse" />
              <div className="absolute -top-2 -right-2 bg-red-500 text-white text-xs rounded-full h-6 w-6 flex items-center justify-center font-bold">
                {alerts.length}
              </div>
            </div>
          )}
        </div>
        <button
          onClick={() => {
            fetchMetrics();
            fetchPredictedOccupancy();
            fetchAutonomousStatus();
            fetchAlerts();
          }}
          className="flex items-center space-x-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
        >
          <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
          <span>Refresh</span>
        </button>
      </div>

      {/* Tab Navigation */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          <button
            onClick={() => setActiveTab('overview')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'overview'
                ? 'border-primary-500 text-primary-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            <Activity className="w-4 h-4 inline mr-2" />
            Overview
          </button>
          <button
            onClick={() => setActiveTab('realtime')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'realtime'
                ? 'border-primary-500 text-primary-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            <Bed className="w-4 h-4 inline mr-2" />
            Real-Time Bed Monitor
          </button>
          <button
            onClick={() => setActiveTab('management')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'management'
                ? 'border-primary-500 text-primary-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            <Users className="w-4 h-4 inline mr-2" />
            Bed Management
          </button>
          <button
            onClick={() => setActiveTab('autonomous')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'autonomous'
                ? 'border-primary-500 text-primary-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            <Bot className="w-4 h-4 inline mr-2" />
            Autonomous Systems
          </button>
          <button
            onClick={() => setActiveTab('recommendations')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'recommendations'
                ? 'border-primary-500 text-primary-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            <Brain className="w-4 h-4 inline mr-2" />
            AI Recommendations
          </button>
        </nav>
      </div>

      {/* Tab Content */}
      {activeTab === 'overview' && (
        <>
          {/* Key Metrics Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-6">
        {/* Bed Occupancy */}
        <div className="metric-card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Bed Occupancy</p>
              <p className="text-3xl font-bold text-gray-900">
                {metrics?.bed_occupancy?.toFixed(1) || '0.0'}%
              </p>
              <div className={`inline-flex items-center space-x-1 mt-2 px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(metrics?.bed_occupancy || 0)}`}>
                {getStatusIcon(metrics?.bed_occupancy || 0)}
                <span>Normal</span>
              </div>
            </div>
            <div className="p-3 bg-primary-100 rounded-full">
              <Bed className="h-6 w-6 text-primary-600" />
            </div>
          </div>
        </div>

        {/* Patient Satisfaction */}
        <div className="metric-card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Patient Satisfaction</p>
              <p className="text-3xl font-bold text-gray-900">
                {metrics?.patient_satisfaction || '0.0'}/10
              </p>
              <div className="inline-flex items-center space-x-1 mt-2 px-2 py-1 rounded-full text-xs font-medium text-green-600 bg-green-100">
                <TrendingUp className="h-4 w-4" />
                <span>+10.5</span>
              </div>
            </div>
            <div className="p-3 bg-green-100 rounded-full">
              <Users className="h-6 w-6 text-green-600" />
            </div>
          </div>
        </div>

        {/* Available Staff */}
        <div className="metric-card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Available Staff</p>
              <p className="text-3xl font-bold text-gray-900">
                {metrics?.available_staff || '0'}
              </p>
              <div className="inline-flex items-center space-x-1 mt-2 px-2 py-1 rounded-full text-xs font-medium text-blue-600 bg-blue-100">
                <Activity className="h-4 w-4" />
                <span>Low</span>
              </div>
            </div>
            <div className="p-3 bg-blue-100 rounded-full">
              <Users className="h-6 w-6 text-blue-600" />
            </div>
          </div>
        </div>

        {/* Resource Utilization */}
        <div className="metric-card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Resource Utilization</p>
              <p className="text-3xl font-bold text-gray-900">
                {metrics?.resource_utilization?.toFixed(1) || '0.0'}%
              </p>
              <div className="inline-flex items-center space-x-1 mt-2 px-2 py-1 rounded-full text-xs font-medium text-yellow-600 bg-yellow-100">
                <TrendingUp className="h-4 w-4" />
                <span>+2%</span>
              </div>
            </div>
            <div className="p-3 bg-yellow-100 rounded-full">
              <Activity className="h-6 w-6 text-yellow-600" />
            </div>
          </div>
        </div>

        {/* Autonomous Systems Status */}
        <div className="metric-card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Autonomous Systems</p>
              <p className="text-3xl font-bold text-gray-900">
                {autonomousStatus ?
                  Object.values(autonomousStatus).filter(system => system?.running).length : 0
                }/4
              </p>
              <div className={`inline-flex items-center space-x-1 mt-2 px-2 py-1 rounded-full text-xs font-medium ${
                autonomousStatus && Object.values(autonomousStatus).filter(system => system?.running).length >= 3
                  ? 'text-green-600 bg-green-100'
                  : 'text-yellow-600 bg-yellow-100'
              }`}>
                <Bot className="h-4 w-4" />
                <span>
                  {autonomousStatus && Object.values(autonomousStatus).filter(system => system?.running).length >= 3
                    ? 'Active' : 'Partial'
                  }
                </span>
              </div>
            </div>
            <div className="p-3 bg-purple-100 rounded-full">
              <Bot className="h-6 w-6 text-purple-600" />
            </div>
          </div>
        </div>
      </div>

      {/* Active Alerts Section */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900 flex items-center">
            <AlertTriangle className="h-5 w-5 text-orange-600 mr-2" />
            Active Alerts
          </h3>
          <div className="text-2xl font-bold text-orange-600">
            {alerts.length}
          </div>
        </div>

        {alerts.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            <CheckCircle className="h-12 w-12 mx-auto mb-4 text-green-400" />
            <p className="text-lg font-medium">No Active Alerts</p>
            <p className="text-gray-400">All systems are operating normally</p>
          </div>
        ) : (
          <div className="space-y-3">
            {alerts.slice(0, 5).map((alert) => (
              <div
                key={alert.id}
                className={`p-3 rounded-lg border-l-4 ${
                  alert.priority === 'critical' ? 'border-l-red-500 bg-red-50' :
                  alert.priority === 'high' ? 'border-l-orange-500 bg-orange-50' :
                  alert.priority === 'medium' ? 'border-l-yellow-500 bg-yellow-50' :
                  'border-l-blue-500 bg-blue-50'
                }`}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center space-x-2 mb-1">
                      <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                        alert.priority === 'critical' ? 'bg-red-100 text-red-800' :
                        alert.priority === 'high' ? 'bg-orange-100 text-orange-800' :
                        alert.priority === 'medium' ? 'bg-yellow-100 text-yellow-800' :
                        'bg-blue-100 text-blue-800'
                      }`}>
                        {alert.priority?.toUpperCase()}
                      </span>
                      <span className="text-sm text-gray-600">{alert.department}</span>
                    </div>
                    <h4 className="font-medium text-gray-900">{alert.title}</h4>
                    <p className="text-sm text-gray-600 mt-1">{alert.message}</p>
                  </div>
                  <div className="text-xs text-gray-500">
                    {new Date(alert.created_at).toLocaleTimeString()}
                  </div>
                </div>
              </div>
            ))}
            {alerts.length > 5 && (
              <div className="text-center pt-2">
                <button className="text-sm text-primary-600 hover:text-primary-700">
                  View all {alerts.length} alerts →
                </button>
              </div>
            )}
          </div>
        )}

        {/* Alert Summary */}
        {alerts.length > 0 && (
          <div className="mt-4 pt-4 border-t border-gray-200">
            <div className="flex space-x-4 text-sm">
              {alerts.filter(a => a.priority === 'critical').length > 0 && (
                <span className="text-red-600">
                  {alerts.filter(a => a.priority === 'critical').length} Critical
                </span>
              )}
              {alerts.filter(a => a.priority === 'high').length > 0 && (
                <span className="text-orange-600">
                  {alerts.filter(a => a.priority === 'high').length} High
                </span>
              )}
              {alerts.filter(a => a.priority === 'medium').length > 0 && (
                <span className="text-yellow-600">
                  {alerts.filter(a => a.priority === 'medium').length} Medium
                </span>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Charts Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Occupancy Trend Chart */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Bed Occupancy Trend</h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={occupancyTrend}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="time" />
              <YAxis />
              <Tooltip />
              <Line 
                type="monotone" 
                dataKey="occupancy" 
                stroke="#3b82f6" 
                strokeWidth={2}
                dot={{ fill: '#3b82f6', strokeWidth: 2, r: 4 }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Predicted Occupancy Curve */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Predicted Occupancy (Next 24h)</h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={predictedCurve}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="time" tickFormatter={t => t ? t.slice(11, 16) : ''} />
              <YAxis />
              <Tooltip formatter={(value, name) => [value, name === 'predicted_occupied' ? 'Occupied' : 'Available']} />
              <Line 
                type="monotone" 
                dataKey="predicted_occupied" 
                stroke="#ef4444" 
                strokeWidth={2}
                dot={false}
                name="Predicted Occupied"
              />
              <Line 
                type="monotone" 
                dataKey="predicted_available" 
                stroke="#22c55e" 
                strokeWidth={2}
                dot={false}
                name="Predicted Available"
              />
              {/* Highlight risk hours */}
              {predictedCurve.map((point, idx) => riskHours.includes(point.time) && (
                <ReferenceDot key={idx} x={point.time} y={point.predicted_available} r={6} fill="#dc2626" stroke="#b91c1c" label={{ value: 'Risk', position: 'top', fill: '#dc2626', fontSize: 10 }} />
              ))}
            </LineChart>
          </ResponsiveContainer>
          {riskHours.length > 0 && (
            <div className="mt-2 text-sm text-red-600">
              <b>Risk hours:</b> {riskHours.map(t => new Date(t).toLocaleString()).join(', ')}
            </div>
          )}
        </div>

        {/* Bed Distribution Chart */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Bed Distribution</h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={bedDistributionData}
                cx="50%"
                cy="50%"
                innerRadius={60}
                outerRadius={100}
                paddingAngle={5}
                dataKey="value"
              >
                {bedDistributionData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
          <div className="flex justify-center space-x-4 mt-4">
            {bedDistributionData.map((entry, index) => (
              <div key={index} className="flex items-center space-x-2">
                <div 
                  className="w-3 h-3 rounded-full" 
                  style={{ backgroundColor: entry.color }}
                ></div>
                <span className="text-sm text-gray-600">{entry.name}: {entry.value}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

          {/* Status Footer */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
            <div className="flex items-center justify-between text-sm text-gray-600">
              <div className="flex items-center space-x-4">
                <div className="flex items-center space-x-2">
                  <Clock className="h-4 w-4" />
                  <span>Last updated: {lastUpdate.toLocaleTimeString()}</span>
                </div>
                <div className="flex items-center space-x-2">
                  <div className="h-2 w-2 bg-green-400 rounded-full"></div>
                  <span>System operational</span>
                </div>
              </div>
              <div className="text-right">
                <p>Next update in: 30s</p>
              </div>
            </div>
          </div>
        </>
      )}

      {/* Real-Time Bed Monitor Tab */}
      {activeTab === 'realtime' && (
        <RealTimeBedMonitor />
      )}

      {/* Bed Management Tab */}
      {activeTab === 'management' && (
        <BedManagement />
      )}

      {/* Autonomous Systems Tab */}
      {activeTab === 'autonomous' && (
        <AutonomousSystemDashboard />
      )}

      {/* AI Recommendations Tab */}
      {activeTab === 'recommendations' && (
        <BedRecommendations />
      )}
    </div>
  );
};

export default Dashboard;
