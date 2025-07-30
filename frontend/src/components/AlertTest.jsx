import React, { useState, useEffect } from 'react';
import { Bell, AlertTriangle } from 'lucide-react';

const AlertTest = () => {
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [lastFetch, setLastFetch] = useState(null);

  const fetchAlerts = async () => {
    try {
      console.log('🧪 AlertTest: Starting fetch...');
      setLoading(true);
      setError(null);
      
      const response = await fetch('http://localhost:8000/api/alerts/active');
      console.log('🧪 AlertTest: Response status:', response.status);
      console.log('🧪 AlertTest: Response ok:', response.ok);
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      const data = await response.json();
      console.log('🧪 AlertTest: Raw response data:', data);
      console.log('🧪 AlertTest: data.alerts:', data.alerts);
      console.log('🧪 AlertTest: alerts length:', data.alerts?.length);
      
      setAlerts(data.alerts || []);
      setLastFetch(new Date().toLocaleTimeString());
      
    } catch (err) {
      console.error('🧪 AlertTest: Error:', err);
      setError(err.message);
      setAlerts([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAlerts();
    // Removed automatic polling - use manual refresh button instead
  }, []);

  return (
    <div className="p-6 bg-white rounded-lg shadow-lg max-w-2xl mx-auto">
      <h2 className="text-2xl font-bold mb-4 flex items-center">
        <AlertTriangle className="mr-2 text-orange-500" />
        Alert System Test
      </h2>
      
      <div className="mb-4 p-4 bg-gray-50 rounded">
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <strong>Status:</strong> {loading ? 'Loading...' : error ? 'Error' : 'Success'}
          </div>
          <div>
            <strong>Alert Count:</strong> {alerts.length}
          </div>
          <div>
            <strong>Last Fetch:</strong> {lastFetch || 'Never'}
          </div>
          <div>
            <strong>Error:</strong> {error || 'None'}
          </div>
        </div>
      </div>

      <div className="mb-4">
        <button 
          onClick={fetchAlerts}
          className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
          disabled={loading}
        >
          {loading ? 'Fetching...' : 'Refresh Alerts'}
        </button>
      </div>

      <div className="mb-4">
        <h3 className="text-lg font-semibold mb-2 flex items-center">
          <Bell className={`mr-2 ${alerts.length > 0 ? 'text-red-500 animate-pulse' : 'text-gray-400'}`} />
          Notification Bell Test
          {alerts.length > 0 && (
            <span className="ml-2 bg-red-500 text-white text-xs rounded-full h-6 w-6 flex items-center justify-center font-bold">
              {alerts.length}
            </span>
          )}
        </h3>
      </div>

      <div>
        <h3 className="text-lg font-semibold mb-2">Alerts ({alerts.length})</h3>
        {alerts.length === 0 ? (
          <div className="text-gray-500 text-center py-4">
            No alerts found
          </div>
        ) : (
          <div className="space-y-2">
            {alerts.map((alert, index) => (
              <div 
                key={alert.id || index}
                className={`p-3 rounded border-l-4 ${
                  alert.priority === 'critical' ? 'border-l-red-500 bg-red-50' :
                  alert.priority === 'high' ? 'border-l-orange-500 bg-orange-50' :
                  alert.priority === 'medium' ? 'border-l-yellow-500 bg-yellow-50' :
                  'border-l-blue-500 bg-blue-50'
                }`}
              >
                <div className="flex justify-between items-start">
                  <div>
                    <div className="font-medium">{alert.title}</div>
                    <div className="text-sm text-gray-600">{alert.message}</div>
                    <div className="text-xs text-gray-500 mt-1">
                      {alert.department} • {alert.priority?.toUpperCase()}
                    </div>
                  </div>
                  <div className="text-xs text-gray-400">
                    {new Date(alert.created_at).toLocaleTimeString()}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default AlertTest;
