import React, { useState, useEffect, memo } from 'react';
import { Menu, Bell, User, Activity, AlertTriangle, Clock, X, CheckCircle } from 'lucide-react';
import { useAlerts } from '../contexts/AlertContext';

// Use memo to prevent unnecessary re-renders
const Header = memo(({ sidebarOpen, setSidebarOpen, alertCount = 0 }) => {
  const [showNotification, setShowNotification] = useState(false);
  const [animateNotification, setAnimateNotification] = useState(false);

  // Get alerts from context for detailed display
  const { alerts, refreshAlerts } = useAlerts();

  // Log when alertCount changes
  useEffect(() => {
    console.log('🔔 Header: Received alertCount:', alertCount);

    if (alertCount > 0) {
      // Trigger animation when alert count changes
      setAnimateNotification(true);
      setTimeout(() => setAnimateNotification(false), 2000);

      // Show notification popup
      setShowNotification(true);
      const timer = setTimeout(() => setShowNotification(false), 5000);
      return () => clearTimeout(timer);
    }
  }, [alertCount]);

  return (
    <header className="bg-white shadow-sm border-b border-gray-200 relative">
      <div className="flex items-center justify-between px-6 py-4">
        <div className="flex items-center">
          <button
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="text-gray-500 hover:text-gray-700 focus:outline-none focus:text-gray-700 lg:hidden"
          >
            <Menu className="h-6 w-6" />
          </button>

          <div className="flex items-center ml-4 lg:ml-0">
            <Activity className="h-8 w-8 text-primary-600" />
            <div className="ml-3">
              <h1 className="text-xl font-semibold text-gray-900">
                Healthcare Operations Assistant
              </h1>
              <p className="text-sm text-gray-500">
                Your AI-powered healthcare operations management solution
              </p>
            </div>
          </div>
        </div>

        <div className="flex items-center space-x-4">
          {/* Status Indicator */}
          <div className="flex items-center space-x-2">
            <div className="h-2 w-2 bg-green-400 rounded-full animate-pulse"></div>
            <span className="text-sm text-gray-600 hidden sm:block">Online</span>
          </div>

          {/* Notifications */}
          <div className="relative">
            <button
              className="relative p-2 text-gray-400 hover:text-gray-500 focus:outline-none focus:text-gray-500"
              onClick={() => setShowNotification(!showNotification)}
            >
              <Bell
                className={`h-6 w-6 transition-all duration-300 ${
                  alertCount > 0
                    ? 'text-red-500' + (animateNotification ? ' animate-bounce' : ' animate-pulse')
                    : ''
                }`}
              />

              {alertCount > 0 && (
                <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs rounded-full h-5 w-5 flex items-center justify-center font-bold transition-all duration-300 transform scale-100">
                  {alertCount}
                </span>
              )}
            </button>

            {/* Enhanced Notification Popup with Detailed Alerts */}
            {showNotification && (
              <div className="absolute right-0 mt-2 w-96 bg-white rounded-md shadow-lg overflow-hidden z-20 border border-gray-200">
                <div className="py-3 px-4 bg-gray-100 border-b border-gray-200">
                  <div className="flex justify-between items-center">
                    <h3 className="text-sm font-semibold text-gray-800 flex items-center">
                      <AlertTriangle className="h-4 w-4 text-red-500 mr-2" />
                      Active Alerts ({alerts.length})
                    </h3>
                    <button
                      onClick={() => setShowNotification(false)}
                      className="text-gray-500 hover:text-gray-700 p-1"
                    >
                      <X className="h-4 w-4" />
                    </button>
                  </div>
                </div>

                <div className="max-h-96 overflow-y-auto">
                  {alerts.length === 0 ? (
                    <div className="py-8 px-4 text-center">
                      <CheckCircle className="h-12 w-12 text-green-500 mx-auto mb-3" />
                      <p className="text-sm font-medium text-gray-800">No Active Alerts</p>
                      <p className="text-xs text-gray-500 mt-1">All systems are operating normally</p>
                    </div>
                  ) : (
                    <div className="divide-y divide-gray-100">
                      {alerts.map((alert, index) => (
                        <div key={alert.id || index} className="p-4 hover:bg-gray-50 transition-colors">
                          <div className="flex items-start space-x-3">
                            {/* Priority Indicator */}
                            <div className={`w-2 h-2 rounded-full mt-2 flex-shrink-0 ${
                              alert.priority === 'critical' ? 'bg-red-500' :
                              alert.priority === 'high' ? 'bg-orange-500' :
                              alert.priority === 'medium' ? 'bg-yellow-500' : 'bg-blue-500'
                            }`}></div>

                            <div className="flex-1 min-w-0">
                              {/* Alert Header */}
                              <div className="flex items-center justify-between mb-1">
                                <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                                  alert.priority === 'critical' ? 'bg-red-100 text-red-800' :
                                  alert.priority === 'high' ? 'bg-orange-100 text-orange-800' :
                                  alert.priority === 'medium' ? 'bg-yellow-100 text-yellow-800' : 'bg-blue-100 text-blue-800'
                                }`}>
                                  {alert.priority?.toUpperCase() || 'INFO'}
                                </span>
                                <span className="text-xs text-gray-500 flex items-center">
                                  <Clock className="h-3 w-3 mr-1" />
                                  {alert.created_at ? new Date(alert.created_at).toLocaleTimeString() : 'Now'}
                                </span>
                              </div>

                              {/* Alert Content */}
                              <h4 className="text-sm font-medium text-gray-900 mb-1">
                                {alert.title || 'System Alert'}
                              </h4>
                              <p className="text-xs text-gray-600 mb-2">
                                {alert.message || 'No message available'}
                              </p>

                              {/* Department and Metadata */}
                              <div className="flex items-center justify-between">
                                <span className="text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded">
                                  {alert.department || 'System'}
                                </span>
                                {alert.action_required && (
                                  <span className="text-xs text-red-600 font-medium">
                                    Action Required
                                  </span>
                                )}
                              </div>

                              {/* Metadata */}
                              {alert.metadata && Object.keys(alert.metadata).length > 0 && (
                                <div className="mt-2 pt-2 border-t border-gray-100">
                                  <div className="grid grid-cols-2 gap-1 text-xs text-gray-500">
                                    {Object.entries(alert.metadata).slice(0, 4).map(([key, value]) => (
                                      <div key={key} className="truncate">
                                        <span className="font-medium">{key}:</span> {value}
                                      </div>
                                    ))}
                                  </div>
                                </div>
                              )}
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                {/* Footer Actions */}
                <div className="py-2 px-4 bg-gray-50 border-t border-gray-200">
                  <div className="flex justify-between items-center">
                    <button
                      onClick={refreshAlerts}
                      className="text-xs text-primary-600 hover:text-primary-800 font-medium"
                    >
                      Refresh Alerts
                    </button>
                    <span className="text-xs text-gray-500">
                      Last updated: {new Date().toLocaleTimeString()}
                    </span>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* User Menu */}
          <div className="relative">
            <button className="flex items-center space-x-2 text-gray-700 hover:text-gray-900 focus:outline-none">
              <div className="h-8 w-8 bg-primary-100 rounded-full flex items-center justify-center">
                <User className="h-5 w-5 text-primary-600" />
              </div>
              <span className="hidden md:block text-sm font-medium">Dr. Admin</span>
            </button>
          </div>
        </div>
      </div>
    </header>
  );
});

export default Header;
