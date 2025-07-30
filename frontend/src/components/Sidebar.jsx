import React, { useState } from 'react';
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
      id: 'staff-coordination',
      label: 'Staff Coordination',
      icon: Users,
      description: 'Manage staff assignments and workload'
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
        console.log('Data refreshed successfully');
      }
    } catch (error) {
      console.error('Refresh failed:', error);
    }
  };

  const handleEmergencyAlert = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/alerts/create-test');
      if (response.ok) {
        alert(`🚨 Emergency alert created for ${selectedDepartment}`);
      }
    } catch (error) {
      console.error('Emergency alert failed:', error);
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



  return (
    <div className={`bg-white shadow-lg transition-all duration-300 ${isOpen ? 'w-80' : 'w-16'} flex flex-col`}>
      {/* Logo/Brand */}
      <div className="p-6 border-b border-gray-200">
        {isOpen ? (
          <div>
            <h2 className="text-lg font-semibold text-gray-900">Hospital Control</h2>
            <p className="text-sm text-gray-500 mt-1">Quick Actions & Status</p>

            {/* Current Department Focus */}
            <div className="mt-3">
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


      </nav>


    </div>
  );
};

export default Sidebar;
