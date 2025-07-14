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
  RefreshCw
} from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import axios from 'axios';

const Dashboard = () => {
  const [metrics, setMetrics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [lastUpdate, setLastUpdate] = useState(new Date());

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
      const response = await axios.get('/api/dashboard/metrics');
      setMetrics(response.data);
      setLastUpdate(new Date());
    } catch (error) {
      console.error('Error fetching metrics:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMetrics();
    const interval = setInterval(fetchMetrics, 30000); // Update every 30 seconds
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
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Key Metrics Dashboard</h1>
          <p className="text-gray-600 mt-1">
            Your AI-powered healthcare operations management solution is
          </p>
        </div>
        <button
          onClick={fetchMetrics}
          className="flex items-center space-x-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
        >
          <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
          <span>Refresh</span>
        </button>
      </div>

      {/* Key Metrics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
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
    </div>
  );
};

export default Dashboard;
