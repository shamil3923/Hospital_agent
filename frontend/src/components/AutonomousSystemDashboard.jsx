import React, { useState, useEffect } from 'react';
import {
  Bot,
  Brain,
  Zap,
  TrendingUp,
  AlertTriangle,
  CheckCircle,
  Clock,
  Activity,
  Target,
  BarChart3,
  RefreshCw,
  Play,
  Pause,
  Settings
} from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, AreaChart, Area } from 'recharts';
import axios from 'axios';

const AutonomousSystemDashboard = () => {
  const [autonomousStatus, setAutonomousStatus] = useState(null);
  const [systemHealth, setSystemHealth] = useState(null);
  const [predictions, setPredictions] = useState([]);
  const [actionHistory, setActionHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [lastUpdate, setLastUpdate] = useState(new Date());

  const fetchAutonomousData = async () => {
    try {
      setLoading(true);
      
      // Fetch autonomous system status
      const statusResponse = await axios.get('http://localhost:8000/api/autonomous/status');
      setAutonomousStatus(statusResponse.data);

      // Fetch system health
      const healthResponse = await axios.get('http://localhost:8000/api/autonomous/system-health');
      setSystemHealth(healthResponse.data);

      // Fetch predictions
      const predictionsResponse = await axios.get('http://localhost:8000/api/autonomous/predictions');
      setPredictions(predictionsResponse.data.predictions || []);

      // Fetch action history
      const historyResponse = await axios.get('http://localhost:8000/api/autonomous/actions/history?limit=10');
      setActionHistory(historyResponse.data);

      setLastUpdate(new Date());
    } catch (error) {
      console.error('Error fetching autonomous data:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAutonomousData();
    const interval = setInterval(fetchAutonomousData, 15000); // Update every 15 seconds
    return () => clearInterval(interval);
  }, []);

  const getSystemStatusColor = (running) => {
    return running ? 'text-green-600 bg-green-100' : 'text-red-600 bg-red-100';
  };

  const getSystemStatusIcon = (running) => {
    return running ? <CheckCircle className="h-4 w-4" /> : <AlertTriangle className="h-4 w-4" />;
  };

  const getRiskLevelColor = (riskLevel) => {
    switch (riskLevel) {
      case 'critical': return 'text-red-600 bg-red-100';
      case 'high': return 'text-orange-600 bg-orange-100';
      case 'medium': return 'text-yellow-600 bg-yellow-100';
      case 'low': return 'text-green-600 bg-green-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  // Process predictions for chart
  const predictionChartData = predictions.slice(0, 24).map((pred, index) => ({
    hour: index,
    occupancy_rate: pred.occupancy_rate || 0,
    risk_level: pred.risk_level,
    ward: pred.ward,
    bed_type: pred.bed_type
  }));

  if (loading && !autonomousStatus) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900 flex items-center">
            <Bot className="h-8 w-8 text-primary-600 mr-3" />
            Autonomous Bed Management System
          </h2>
          <p className="text-gray-600 mt-1">
            AI-powered autonomous operations with predictive analytics and proactive actions
          </p>
        </div>
        <button
          onClick={fetchAutonomousData}
          className="flex items-center space-x-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
        >
          <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
          <span>Refresh</span>
        </button>
      </div>

      {/* System Status Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {/* Autonomous Scheduler */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Autonomous Scheduler</p>
              <p className="text-2xl font-bold text-gray-900">
                {autonomousStatus?.autonomous_scheduler?.running ? 'Active' : 'Inactive'}
              </p>
              <div className={`inline-flex items-center space-x-1 mt-2 px-2 py-1 rounded-full text-xs font-medium ${getSystemStatusColor(autonomousStatus?.autonomous_scheduler?.running)}`}>
                {getSystemStatusIcon(autonomousStatus?.autonomous_scheduler?.running)}
                <span>{autonomousStatus?.autonomous_scheduler?.running ? 'Running' : 'Stopped'}</span>
              </div>
            </div>
            <div className="p-3 bg-blue-100 rounded-full">
              <Clock className="h-6 w-6 text-blue-600" />
            </div>
          </div>
        </div>

        {/* Bed Agent */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Bed Agent</p>
              <p className="text-2xl font-bold text-gray-900">
                {autonomousStatus?.autonomous_bed_agent?.running ? 'Active' : 'Inactive'}
              </p>
              <div className={`inline-flex items-center space-x-1 mt-2 px-2 py-1 rounded-full text-xs font-medium ${getSystemStatusColor(autonomousStatus?.autonomous_bed_agent?.running)}`}>
                {getSystemStatusIcon(autonomousStatus?.autonomous_bed_agent?.running)}
                <span>
                  {autonomousStatus?.autonomous_bed_agent?.metrics?.actions_taken || 0} actions
                </span>
              </div>
            </div>
            <div className="p-3 bg-green-100 rounded-full">
              <Bot className="h-6 w-6 text-green-600" />
            </div>
          </div>
        </div>

        {/* Assignment System */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Bed Assignment</p>
              <p className="text-2xl font-bold text-gray-900">
                {autonomousStatus?.intelligent_bed_assignment?.running ? 'Active' : 'Inactive'}
              </p>
              <div className={`inline-flex items-center space-x-1 mt-2 px-2 py-1 rounded-full text-xs font-medium ${getSystemStatusColor(autonomousStatus?.intelligent_bed_assignment?.running)}`}>
                {getSystemStatusIcon(autonomousStatus?.intelligent_bed_assignment?.running)}
                <span>
                  {autonomousStatus?.intelligent_bed_assignment?.metrics?.beds_assigned || 0} assigned
                </span>
              </div>
            </div>
            <div className="p-3 bg-purple-100 rounded-full">
              <Target className="h-6 w-6 text-purple-600" />
            </div>
          </div>
        </div>

        {/* Proactive Actions */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Proactive Actions</p>
              <p className="text-2xl font-bold text-gray-900">
                {autonomousStatus?.proactive_action_system?.running ? 'Active' : 'Inactive'}
              </p>
              <div className={`inline-flex items-center space-x-1 mt-2 px-2 py-1 rounded-full text-xs font-medium ${getSystemStatusColor(autonomousStatus?.proactive_action_system?.running)}`}>
                {getSystemStatusIcon(autonomousStatus?.proactive_action_system?.running)}
                <span>
                  {autonomousStatus?.proactive_action_system?.metrics?.actions_triggered || 0} triggered
                </span>
              </div>
            </div>
            <div className="p-3 bg-orange-100 rounded-full">
              <Zap className="h-6 w-6 text-orange-600" />
            </div>
          </div>
        </div>
      </div>

      {/* System Health Overview */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
          <Activity className="h-5 w-5 text-primary-600 mr-2" />
          System Health Overview
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="text-center">
            <div className="text-3xl font-bold text-gray-900">
              {systemHealth?.health_score?.toFixed(1) || '0.0'}%
            </div>
            <div className="text-sm text-gray-600">Health Score</div>
            <div className={`inline-flex items-center space-x-1 mt-2 px-2 py-1 rounded-full text-xs font-medium ${
              (systemHealth?.health_score || 0) >= 90 ? 'text-green-600 bg-green-100' :
              (systemHealth?.health_score || 0) >= 70 ? 'text-yellow-600 bg-yellow-100' :
              'text-red-600 bg-red-100'
            }`}>
              <span>{systemHealth?.status || 'Unknown'}</span>
            </div>
          </div>
          <div className="text-center">
            <div className="text-3xl font-bold text-gray-900">
              {Math.floor((systemHealth?.uptime_seconds || 0) / 60)}m
            </div>
            <div className="text-sm text-gray-600">Uptime</div>
          </div>
          <div className="text-center">
            <div className="text-3xl font-bold text-gray-900">
              {systemHealth?.tasks_status?.total_tasks || 0}
            </div>
            <div className="text-sm text-gray-600">Active Tasks</div>
          </div>
        </div>
      </div>

      {/* 24-Hour Predictions Chart */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
          <Brain className="h-5 w-5 text-primary-600 mr-2" />
          24-Hour Bed Occupancy Predictions
        </h3>
        <ResponsiveContainer width="100%" height={300}>
          <AreaChart data={predictionChartData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis 
              dataKey="hour" 
              tickFormatter={(hour) => `${hour}:00`}
            />
            <YAxis />
            <Tooltip 
              formatter={(value, name) => [`${value.toFixed(1)}%`, 'Occupancy Rate']}
              labelFormatter={(hour) => `Hour ${hour}:00`}
            />
            <Area
              type="monotone"
              dataKey="occupancy_rate"
              stroke="#3b82f6"
              fill="#3b82f6"
              fillOpacity={0.3}
            />
          </AreaChart>
        </ResponsiveContainer>
        <div className="mt-4 flex flex-wrap gap-2">
          {predictions.slice(0, 6).map((pred, index) => (
            <div key={index} className={`px-3 py-1 rounded-full text-xs font-medium ${getRiskLevelColor(pred.risk_level)}`}>
              {pred.ward} {pred.bed_type}: {pred.occupancy_rate?.toFixed(1)}% ({pred.risk_level})
            </div>
          ))}
        </div>
      </div>

      {/* Recent Autonomous Actions */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
          <BarChart3 className="h-5 w-5 text-primary-600 mr-2" />
          Recent Autonomous Actions
        </h3>
        <div className="space-y-4">
          {/* Bed Agent Actions */}
          {actionHistory?.autonomous_agent_actions?.slice(0, 3).map((action, index) => (
            <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <div className="flex items-center space-x-3">
                <div className="p-2 bg-green-100 rounded-full">
                  <Bot className="h-4 w-4 text-green-600" />
                </div>
                <div>
                  <p className="text-sm font-medium text-gray-900">{action.description}</p>
                  <p className="text-xs text-gray-600">
                    {action.action_type} • Confidence: {(action.confidence_score * 100).toFixed(1)}%
                  </p>
                </div>
              </div>
              <div className="text-xs text-gray-500">
                {new Date(action.executed_time).toLocaleTimeString()}
              </div>
            </div>
          ))}

          {/* Bed Assignment Actions */}
          {actionHistory?.bed_assignments?.slice(0, 2).map((assignment, index) => (
            <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <div className="flex items-center space-x-3">
                <div className="p-2 bg-purple-100 rounded-full">
                  <Target className="h-4 w-4 text-purple-600" />
                </div>
                <div>
                  <p className="text-sm font-medium text-gray-900">
                    Bed {assignment.bed_number} assigned to {assignment.patient_id}
                  </p>
                  <p className="text-xs text-gray-600">
                    Score: {assignment.assignment_score?.toFixed(1)} • {assignment.ward}
                  </p>
                </div>
              </div>
              <div className="text-xs text-gray-500">
                {new Date(assignment.assignment_time).toLocaleTimeString()}
              </div>
            </div>
          ))}

          {/* Proactive Actions */}
          {actionHistory?.proactive_actions?.slice(0, 2).map((action, index) => (
            <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <div className="flex items-center space-x-3">
                <div className="p-2 bg-orange-100 rounded-full">
                  <Zap className="h-4 w-4 text-orange-600" />
                </div>
                <div>
                  <p className="text-sm font-medium text-gray-900">{action.description}</p>
                  <p className="text-xs text-gray-600">
                    {action.action_type} • {action.trigger}
                  </p>
                </div>
              </div>
              <div className="text-xs text-gray-500">
                {new Date(action.executed_time || action.created_time).toLocaleTimeString()}
              </div>
            </div>
          ))}
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
              <div className={`h-2 w-2 rounded-full ${
                systemHealth?.status === 'healthy' ? 'bg-green-400' : 
                systemHealth?.status === 'degraded' ? 'bg-yellow-400' : 'bg-red-400'
              }`}></div>
              <span>Autonomous systems {systemHealth?.status || 'unknown'}</span>
            </div>
          </div>
          <div className="text-right">
            <p>Next update in: 15s</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AutonomousSystemDashboard;
