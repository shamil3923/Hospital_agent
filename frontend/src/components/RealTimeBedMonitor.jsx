import React, { useState, useEffect, useRef } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from './ui/card';
import { Badge } from './ui/badge';
import { Button } from './ui/button';
import { Alert, AlertDescription } from './ui/alert';
import { 
  Activity, 
  Bed, 
  Users, 
  Clock, 
  TrendingUp, 
  RefreshCw,
  Wifi,
  WifiOff,
  AlertTriangle,
  CheckCircle,
  XCircle
} from 'lucide-react';

const RealTimeBedMonitor = () => {
  const [bedStatus, setBedStatus] = useState({
    summary: {},
    metrics: {},
    last_update: null,
    status: 'inactive'
  });
  const [recentChanges, setRecentChanges] = useState([]);
  const [connectionStatus, setConnectionStatus] = useState('disconnected');
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  
  const wsRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);
  const reconnectAttempts = useRef(0);
  const maxReconnectAttempts = 5;

  // WebSocket connection management
  const connectWebSocket = () => {
    try {
      const wsUrl = `ws://localhost:8000/ws/bed-status`;
      wsRef.current = new WebSocket(wsUrl);

      wsRef.current.onopen = () => {
        console.log('🔗 Real-time bed monitoring WebSocket connected');
        setConnectionStatus('connected');
        setError(null);
        reconnectAttempts.current = 0;
        
        // Send ping to keep connection alive
        const pingInterval = setInterval(() => {
          if (wsRef.current?.readyState === WebSocket.OPEN) {
            wsRef.current.send(JSON.stringify({ type: 'ping' }));
          } else {
            clearInterval(pingInterval);
          }
        }, 30000);
      };

      wsRef.current.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          handleWebSocketMessage(data);
        } catch (err) {
          console.error('Error parsing WebSocket message:', err);
        }
      };

      wsRef.current.onclose = (event) => {
        console.log('🔌 Bed monitoring WebSocket disconnected:', event.code);
        setConnectionStatus('disconnected');
        
        // Attempt to reconnect if not intentionally closed
        if (event.code !== 1000 && reconnectAttempts.current < maxReconnectAttempts) {
          reconnectAttempts.current++;
          const delay = Math.min(1000 * Math.pow(2, reconnectAttempts.current), 30000);
          
          reconnectTimeoutRef.current = setTimeout(() => {
            console.log(`🔄 Attempting to reconnect (${reconnectAttempts.current}/${maxReconnectAttempts})...`);
            connectWebSocket();
          }, delay);
        }
      };

      wsRef.current.onerror = (error) => {
        console.error('❌ Bed monitoring WebSocket error:', error);
        setConnectionStatus('error');
        setError('WebSocket connection failed');
      };

    } catch (err) {
      console.error('Failed to create WebSocket connection:', err);
      setConnectionStatus('error');
      setError('Failed to establish real-time connection');
    }
  };

  const handleWebSocketMessage = (data) => {
    switch (data.type) {
      case 'bed_status_update':
        console.log('📡 Received bed status update:', data);
        handleBedStatusUpdate(data);
        break;
      
      case 'dashboard_bed_update':
        console.log('📊 Received dashboard bed update:', data);
        handleDashboardUpdate(data);
        break;
      
      case 'pong':
        // Keep-alive response
        break;
      
      default:
        console.log('📨 Unknown message type:', data.type);
    }
  };

  const handleBedStatusUpdate = (data) => {
    if (data.changes && data.changes.length > 0) {
      setRecentChanges(prev => {
        const newChanges = [...data.changes, ...prev].slice(0, 20); // Keep last 20 changes
        return newChanges;
      });
    }
  };

  const handleDashboardUpdate = (data) => {
    if (data.bed_summary) {
      setBedStatus(prev => ({
        ...prev,
        summary: data.bed_summary,
        last_update: data.timestamp
      }));
    }
    
    if (data.recent_changes) {
      setRecentChanges(prev => {
        const combined = [...data.recent_changes, ...prev];
        const unique = combined.filter((change, index, self) => 
          index === self.findIndex(c => c.bed_number === change.bed_number && c.timestamp === change.timestamp)
        );
        return unique.slice(0, 20);
      });
    }
    
    if (data.metrics) {
      setBedStatus(prev => ({
        ...prev,
        metrics: data.metrics
      }));
    }
  };

  // Fetch initial data
  const fetchInitialData = async () => {
    try {
      setIsLoading(true);
      
      // Fetch current bed status
      const statusResponse = await fetch('/api/beds/real-time/status');
      const statusData = await statusResponse.json();
      
      if (statusData.summary) {
        setBedStatus({
          summary: statusData.summary,
          metrics: statusData.metrics || {},
          last_update: statusData.last_update,
          status: statusData.status
        });
      }
      
      // Fetch recent changes
      const changesResponse = await fetch('/api/beds/real-time/changes?limit=10');
      const changesData = await changesResponse.json();
      
      if (changesData.changes) {
        setRecentChanges(changesData.changes);
      }
      
    } catch (err) {
      console.error('Error fetching initial data:', err);
      setError('Failed to load initial bed data');
    } finally {
      setIsLoading(false);
    }
  };

  // Force update
  const handleForceUpdate = async () => {
    try {
      const response = await fetch('/api/beds/real-time/force-update', {
        method: 'POST'
      });
      const data = await response.json();
      
      if (data.changes && data.changes.length > 0) {
        setRecentChanges(prev => [...data.changes, ...prev].slice(0, 20));
      }
      
      // Refresh summary data
      await fetchInitialData();
      
    } catch (err) {
      console.error('Error forcing update:', err);
      setError('Failed to force update');
    }
  };

  // Component lifecycle
  useEffect(() => {
    fetchInitialData();
    connectWebSocket();

    return () => {
      if (wsRef.current) {
        wsRef.current.close(1000);
      }
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
    };
  }, []);

  // Status badge component
  const StatusBadge = ({ status }) => {
    const statusConfig = {
      occupied: { color: 'bg-red-500', icon: Users, text: 'Occupied' },
      vacant: { color: 'bg-green-500', icon: CheckCircle, text: 'Vacant' },
      cleaning: { color: 'bg-yellow-500', icon: Clock, text: 'Cleaning' },
      maintenance: { color: 'bg-gray-500', icon: XCircle, text: 'Maintenance' }
    };
    
    const config = statusConfig[status] || statusConfig.vacant;
    const Icon = config.icon;
    
    return (
      <Badge className={`${config.color} text-white`}>
        <Icon className="w-3 h-3 mr-1" />
        {config.text}
      </Badge>
    );
  };

  // Change type badge
  const ChangeTypeBadge = ({ changeType }) => {
    const typeConfig = {
      admission: { color: 'bg-blue-500', text: 'Admission' },
      discharge: { color: 'bg-green-500', text: 'Discharge' },
      cleaning_started: { color: 'bg-yellow-500', text: 'Cleaning Started' },
      cleaning_completed: { color: 'bg-green-500', text: 'Cleaning Done' },
      status_change: { color: 'bg-purple-500', text: 'Status Change' },
      patient_change: { color: 'bg-orange-500', text: 'Patient Change' }
    };
    
    const config = typeConfig[changeType] || { color: 'bg-gray-500', text: changeType };
    
    return (
      <Badge className={`${config.color} text-white text-xs`}>
        {config.text}
      </Badge>
    );
  };

  if (isLoading) {
    return (
      <Card className="w-full">
        <CardContent className="flex items-center justify-center p-8">
          <RefreshCw className="w-6 h-6 animate-spin mr-2" />
          <span>Loading real-time bed monitoring...</span>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header with Connection Status */}
      <Card>
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center">
              <Activity className="w-5 h-5 mr-2" />
              Real-Time Bed Status Monitor
            </CardTitle>
            <div className="flex items-center space-x-2">
              <div className="flex items-center">
                {connectionStatus === 'connected' ? (
                  <Wifi className="w-4 h-4 text-green-500 mr-1" />
                ) : (
                  <WifiOff className="w-4 h-4 text-red-500 mr-1" />
                )}
                <span className={`text-sm ${connectionStatus === 'connected' ? 'text-green-600' : 'text-red-600'}`}>
                  {connectionStatus === 'connected' ? 'Live' : 'Disconnected'}
                </span>
              </div>
              <Button 
                onClick={handleForceUpdate} 
                size="sm" 
                variant="outline"
                className="ml-2"
              >
                <RefreshCw className="w-4 h-4 mr-1" />
                Refresh
              </Button>
            </div>
          </div>
        </CardHeader>
      </Card>

      {/* Error Alert */}
      {error && (
        <Alert className="border-red-200 bg-red-50">
          <AlertTriangle className="h-4 w-4 text-red-600" />
          <AlertDescription className="text-red-800">
            {error}
          </AlertDescription>
        </Alert>
      )}

      {/* Bed Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Total Beds</p>
                <p className="text-2xl font-bold">{bedStatus.summary.total_beds || 0}</p>
              </div>
              <Bed className="w-8 h-8 text-blue-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Occupied</p>
                <p className="text-2xl font-bold text-red-600">{bedStatus.summary.occupied_beds || 0}</p>
              </div>
              <Users className="w-8 h-8 text-red-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Available</p>
                <p className="text-2xl font-bold text-green-600">{bedStatus.summary.vacant_beds || 0}</p>
              </div>
              <CheckCircle className="w-8 h-8 text-green-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Occupancy Rate</p>
                <p className="text-2xl font-bold text-blue-600">{bedStatus.summary.occupancy_rate || 0}%</p>
              </div>
              <TrendingUp className="w-8 h-8 text-blue-500" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Recent Changes */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <Clock className="w-5 h-5 mr-2" />
            Recent Bed Status Changes
          </CardTitle>
        </CardHeader>
        <CardContent>
          {recentChanges.length === 0 ? (
            <p className="text-gray-500 text-center py-4">No recent changes</p>
          ) : (
            <div className="space-y-3">
              {recentChanges.slice(0, 10).map((change, index) => (
                <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div className="flex items-center space-x-3">
                    <Badge variant="outline">Bed {change.bed_number}</Badge>
                    <ChangeTypeBadge changeType={change.change_type} />
                    <div className="text-sm">
                      <span className="text-gray-600">
                        {change.previous_status && (
                          <>
                            <StatusBadge status={change.previous_status} />
                            <span className="mx-2">→</span>
                          </>
                        )}
                        <StatusBadge status={change.new_status} />
                      </span>
                    </div>
                  </div>
                  <div className="text-xs text-gray-500">
                    {new Date(change.timestamp).toLocaleTimeString()}
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Monitoring Metrics */}
      {bedStatus.metrics && Object.keys(bedStatus.metrics).length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Monitoring Performance</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
              <div>
                <p className="text-gray-600">Total Updates</p>
                <p className="font-semibold">{bedStatus.metrics.total_updates || 0}</p>
              </div>
              <div>
                <p className="text-gray-600">Status Changes</p>
                <p className="font-semibold">{bedStatus.metrics.status_changes || 0}</p>
              </div>
              <div>
                <p className="text-gray-600">Avg Response Time</p>
                <p className="font-semibold">{(bedStatus.metrics.average_response_time || 0).toFixed(3)}s</p>
              </div>
              <div>
                <p className="text-gray-600">Last Broadcast</p>
                <p className="font-semibold">
                  {bedStatus.metrics.last_broadcast 
                    ? new Date(bedStatus.metrics.last_broadcast).toLocaleTimeString()
                    : 'Never'
                  }
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default RealTimeBedMonitor;
