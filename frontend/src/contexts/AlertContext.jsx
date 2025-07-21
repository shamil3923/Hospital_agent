import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';

const AlertContext = createContext();

export const useAlerts = () => {
  const context = useContext(AlertContext);
  if (!context) {
    throw new Error('useAlerts must be used within an AlertProvider');
  }
  return context;
};

export const AlertProvider = ({ children }) => {
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [lastUpdate, setLastUpdate] = useState(null);
  const [isOnline, setIsOnline] = useState(navigator.onLine);

  // Fetch alerts function
  const fetchAlerts = useCallback(async (force = false) => {
    if (loading && !force) return;
    
    try {
      setLoading(true);
      setError(null);
      
      console.log('🔔 AlertContext: Fetching alerts...');
      
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 10000);
      
      const response = await fetch('http://localhost:8000/api/alerts/active', {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'Cache-Control': 'no-cache',
          'Pragma': 'no-cache'
        },
        signal: controller.signal
      });
      
      clearTimeout(timeoutId);
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      const data = await response.json();
      console.log('🔔 AlertContext: Received data:', data);
      
      const alertsArray = data.alerts || [];
      console.log('🔔 AlertContext: Setting alerts:', alertsArray.length, 'alerts');
      
      setAlerts(alertsArray);
      setLastUpdate(new Date());
      setError(null);
      
    } catch (err) {
      if (err.name === 'AbortError') {
        console.log('🔔 AlertContext: Request aborted');
      } else {
        console.error('🔔 AlertContext: Error fetching alerts:', err);
        setError(err.message);
      }
    } finally {
      setLoading(false);
    }
  }, [loading]);

  // Handle online/offline status
  useEffect(() => {
    const handleOnline = () => {
      setIsOnline(true);
      fetchAlerts(true); // Force fetch when coming back online
    };
    
    const handleOffline = () => {
      setIsOnline(false);
    };
    
    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);
    
    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, [fetchAlerts]);

  // Initial fetch and polling
  useEffect(() => {
    let isMounted = true;
    let intervalId;
    
    // Initial fetch
    if (isOnline) {
      fetchAlerts();
    }
    
    // Set up polling interval
    if (isOnline) {
      intervalId = setInterval(() => {
        if (isMounted && isOnline) {
          fetchAlerts();
        }
      }, 15000); // Poll every 15 seconds
    }
    
    return () => {
      isMounted = false;
      if (intervalId) {
        clearInterval(intervalId);
      }
    };
  }, [fetchAlerts, isOnline]);

  // Refresh function for manual updates
  const refreshAlerts = useCallback(() => {
    fetchAlerts(true);
  }, [fetchAlerts]);

  // Get alerts by priority
  const getAlertsByPriority = useCallback((priority) => {
    return alerts.filter(alert => alert.priority === priority);
  }, [alerts]);

  // Get critical alerts count
  const criticalAlertsCount = alerts.filter(alert => alert.priority === 'critical').length;
  const highAlertsCount = alerts.filter(alert => alert.priority === 'high').length;
  const mediumAlertsCount = alerts.filter(alert => alert.priority === 'medium').length;

  const value = {
    alerts,
    alertCount: alerts.length,
    criticalAlertsCount,
    highAlertsCount,
    mediumAlertsCount,
    loading,
    error,
    lastUpdate,
    isOnline,
    fetchAlerts,
    refreshAlerts,
    getAlertsByPriority
  };

  return (
    <AlertContext.Provider value={value}>
      {children}
    </AlertContext.Provider>
  );
};

export default AlertContext;
