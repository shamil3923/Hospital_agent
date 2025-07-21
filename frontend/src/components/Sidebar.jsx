import React, { useState, useEffect } from 'react';
import {
  BarChart3,
  MessageCircle,
  Settings,
  Bed,
  Users,
  AlertTriangle,
  Activity,
  Clock,
  TrendingUp,
  RefreshCw
} from 'lucide-react';

const Sidebar = ({ isOpen, activeView, setActiveView }) => {
  const [selectedDepartment, setSelectedDepartment] = useState('General Ward');
  const [priorityLevel, setPriorityLevel] = useState(75);
  const [timeInterval, setTimeInterval] = useState('15m');
  const [emergencyMode, setEmergencyMode] = useState(false);
  const [lastUpdate, setLastUpdate] = useState(new Date());
  const [systemStatus, setSystemStatus] = useState('Operational');
  const menuItems = [
    {
      id: 'dashboard',
      label: 'Key Metrics Dashboard',
      icon: BarChart3,
      description: 'Overview of hospital operations'
    },
    {
      id: 'chat',
      label: 'Chat Interface',
      icon: MessageCircle,
      description: 'Talk to the AI agent'
    },
    {
      id: 'alert-test',
      label: 'Alert Test',
      icon: AlertTriangle,
      description: 'Test alert system'
    },
    {
      id: 'settings',
      label: 'Settings',
      icon: Settings,
      description: 'System configuration'
    }
  ];

  // Functional quick actions
  const handleRefresh = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/beds/occupancy');
      if (response.ok) {
        setLastUpdate(new Date());
        setSystemStatus('Updated');
        setTimeout(() => setSystemStatus('Operational'), 2000);
      }
    } catch (error) {
      console.error('Refresh failed:', error);
      setSystemStatus('Error');
    }
  };

  const handleEmergencyAlert = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/alerts/create-test');
      if (response.ok) {
        alert(`🚨 Emergency alert created for ${selectedDepartment}`);
        setSystemStatus('Alert Created');
        setTimeout(() => setSystemStatus('Operational'), 3000);
      }
    } catch (error) {
      console.error('Emergency alert failed:', error);
      setSystemStatus('Error');
    }
  };

  const quickActions = [
    {
      label: 'Emergency Alert',
      icon: Activity,
      color: 'text-red-600 bg-red-100',
      action: handleEmergencyAlert
    },
    {
      label: 'Refresh Data',
      icon: RefreshCw,
      color: 'text-green-600 bg-green-100',
      action: handleRefresh
    }
  ];

  // Initialize last update time once - DISABLED POLLING TO PREVENT REFRESH
  useEffect(() => {
    setLastUpdate(new Date());
  }, []); // Run only once on mount

  return (
    <div className={`bg-white shadow-lg transition-all duration-300 ${isOpen ? 'w-80' : 'w-16'} flex flex-col`}>
      {/* Logo/Brand */}
      <div className="p-6 border-b border-gray-200">
        {isOpen ? (
          <div>
            <h2 className="text-lg font-semibold text-gray-900">Hospital Control</h2>
            <p className="text-sm text-gray-500 mt-1">Quick Actions & Status</p>

            {/* Emergency Mode Toggle */}
            <div className="mt-3">
              <label className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  checked={emergencyMode}
                  onChange={(e) => setEmergencyMode(e.target.checked)}
                  className="rounded border-gray-300 text-red-600 focus:ring-red-500"
                />
                <span className={`text-sm font-medium ${emergencyMode ? 'text-red-600' : 'text-gray-700'}`}>
                  Emergency Mode
                </span>
              </label>
              {emergencyMode && (
                <p className="text-xs text-red-600 mt-1">
                  🚨 Emergency protocols activated
                </p>
              )}
            </div>

            {/* Current Department Focus */}
            <div className="mt-4">
              <label className="text-sm text-gray-600">Focus Department</label>
              <select
                className="mt-1 w-full p-2 border border-gray-300 rounded-md text-sm"
                value={selectedDepartment}
                onChange={(e) => setSelectedDepartment(e.target.value)}
              >
                <option>ICU</option>
                <option>Emergency</option>
                <option>General Ward</option>
                <option>Pediatric</option>
                <option>Maternity</option>
              </select>
            </div>

            {/* System Status Indicator */}
            <div className="mt-4 p-3 bg-gray-50 rounded-lg">
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">System Status</span>
                <div className={`flex items-center space-x-1 ${
                  systemStatus === 'Operational' ? 'text-green-600' :
                  systemStatus === 'Updated' ? 'text-blue-600' :
                  systemStatus === 'Error' ? 'text-red-600' : 'text-gray-600'
                }`}>
                  <div className={`w-2 h-2 rounded-full ${
                    systemStatus === 'Operational' ? 'bg-green-500' :
                    systemStatus === 'Updated' ? 'bg-blue-500' :
                    systemStatus === 'Error' ? 'bg-red-500' : 'bg-gray-500'
                  }`} />
                  <span className="text-xs font-medium">{systemStatus}</span>
                </div>
              </div>
              <div className="text-xs text-gray-500 mt-1">
                Last update: {lastUpdate.toLocaleTimeString()}
              </div>
            </div>
          </div>
        ) : (
          <Settings className="h-6 w-6 text-gray-600" />
        )}
      </div>

      {/* Navigation Menu */}
      <nav className="flex-1 p-4">
        <div className="space-y-2">
          {menuItems.map((item) => {
            const Icon = item.icon;
            return (
              <button
                key={item.id}
                onClick={() => setActiveView(item.id)}
                className={`w-full flex items-center p-3 rounded-lg transition-colors ${
                  activeView === item.id
                    ? 'bg-primary-50 text-primary-700 border border-primary-200'
                    : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                }`}
              >
                <Icon className="h-5 w-5 flex-shrink-0" />
                {isOpen && (
                  <div className="ml-3 text-left">
                    <div className="text-sm font-medium">{item.label}</div>
                    <div className="text-xs text-gray-500">{item.description}</div>
                  </div>
                )}
              </button>
            );
          })}
        </div>

        {/* Quick Actions */}
        {isOpen && (
          <div className="mt-8">
            <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">
              Quick Actions
            </h3>
            <div className="space-y-2">
              {quickActions.map((action, index) => {
                const Icon = action.icon;
                return (
                  <button
                    key={index}
                    onClick={action.action}
                    className="w-full flex items-center p-2 rounded-lg hover:bg-gray-50 transition-colors"
                  >
                    <div className={`p-2 rounded-lg ${action.color}`}>
                      <Icon className="h-4 w-4" />
                    </div>
                    <span className="ml-3 text-sm text-gray-700">{action.label}</span>
                  </button>
                );
              })}
            </div>
          </div>
        )}

        {/* Emergency Mode */}
        {isOpen && (
          <div className="mt-8">
            <div className={`p-4 rounded-lg border-2 transition-colors ${
              emergencyMode
                ? 'border-red-300 bg-red-50'
                : 'border-gray-200 bg-gray-50'
            }`}>
              <div className="flex items-center">
                <AlertTriangle className={`h-5 w-5 ${
                  emergencyMode ? 'text-red-600' : 'text-gray-400'
                }`} />
                <span className="ml-2 text-sm font-medium text-gray-700">
                  Emergency Mode
                </span>
              </div>
              <div className="mt-2">
                <label className="flex items-center cursor-pointer">
                  <input
                    type="checkbox"
                    checked={emergencyMode}
                    onChange={(e) => {
                      setEmergencyMode(e.target.checked);
                      if (e.target.checked) {
                        alert('Emergency Protocol Activated! All non-critical operations will be suspended.');
                      } else {
                        alert('Emergency Protocol Deactivated. Normal operations resumed.');
                      }
                    }}
                    className="rounded border-gray-300 text-red-600 focus:ring-red-500"
                  />
                  <span className="ml-2 text-xs text-gray-600">
                    Activate Emergency Protocol
                  </span>
                </label>
              </div>
              {emergencyMode && (
                <div className="mt-2 p-2 bg-red-100 rounded text-xs text-red-700">
                  ⚠️ Emergency mode active - Priority alerts only
                </div>
              )}
            </div>
          </div>
        )}
      </nav>

      {/* Footer */}
      {isOpen && (
        <div className="p-4 border-t border-gray-200">
          <div className="text-xs text-gray-500">
            <div className="flex items-center justify-between">
              <span>Last Update</span>
              <span>{lastUpdate.toLocaleTimeString()}</span>
            </div>
            <div className="flex items-center justify-between mt-1">
              <span>Status</span>
              <span className={`${
                systemStatus === 'Operational' ? 'text-green-600' :
                systemStatus === 'Updated' ? 'text-blue-600' :
                systemStatus === 'Error' ? 'text-red-600' : 'text-gray-600'
              }`}>
                {systemStatus}
              </span>
            </div>
            <div className="flex items-center justify-between mt-1">
              <span>Focus Ward</span>
              <span className="text-blue-600">{selectedDepartment}</span>
            </div>
            <div className="flex items-center justify-between mt-1">
              <span>AI Systems</span>
              <span className="text-green-600">Active</span>
            </div>
            {emergencyMode && (
              <div className="flex items-center justify-between mt-1">
                <span>Emergency</span>
                <span className="text-red-600 font-medium animate-pulse">🚨 ACTIVE</span>
              </div>
            )}
            <div className="mt-2 pt-2 border-t border-gray-100">
              <div className="text-center text-gray-400 text-xs">
                Hospital Agent v1.0.0
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Sidebar;
