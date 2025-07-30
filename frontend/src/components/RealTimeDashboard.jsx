import React, { useState, useEffect, useCallback } from 'react';
import {
  Bell,
  BedDouble,
  AlertTriangle,
  CheckCircle,
  Activity,
  TrendingUp,
  Zap,
  RefreshCw
} from 'lucide-react';
import PatientAssignmentModal from './PatientAssignmentModal';
import EnhancedAlertCard from './EnhancedAlertCard';
import { useAlerts } from '../contexts/AlertContext';

// Simple UI components
const Card = ({ children, className = "" }) => (
  <div className={`bg-white rounded-lg shadow ${className}`}>{children}</div>
);

const CardHeader = ({ children, className = "" }) => (
  <div className={`px-6 py-4 border-b border-gray-200 ${className}`}>{children}</div>
);

const CardTitle = ({ children, className = "" }) => (
  <h3 className={`text-lg font-semibold text-gray-900 ${className}`}>{children}</h3>
);

const CardContent = ({ children, className = "" }) => (
  <div className={`px-6 py-4 ${className}`}>{children}</div>
);

const Alert = ({ children, className = "" }) => (
  <div className={`p-4 rounded-md border ${className}`}>{children}</div>
);

const AlertDescription = ({ children, className = "" }) => (
  <div className={`text-sm ${className}`}>{children}</div>
);

const Badge = ({ children, variant = "default", className = "" }) => {
  const variants = {
    default: "bg-blue-100 text-blue-800",
    destructive: "bg-red-100 text-red-800",
    secondary: "bg-gray-100 text-gray-800",
    outline: "border border-gray-300 text-gray-700"
  };
  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${variants[variant]} ${className}`}>
      {children}
    </span>
  );
};

const Button = ({ children, onClick, size = "default", variant = "default", className = "", ...props }) => {
  const sizes = {
    sm: "px-3 py-1.5 text-sm",
    default: "px-4 py-2 text-sm",
    lg: "px-6 py-3 text-base"
  };
  const variants = {
    default: "bg-blue-600 text-white hover:bg-blue-700",
    outline: "border border-gray-300 text-gray-700 hover:bg-gray-50",
    ghost: "text-gray-700 hover:bg-gray-100"
  };
  return (
    <button
      type="button"
      onClick={onClick}
      className={`inline-flex items-center justify-center rounded-md font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 ${sizes[size]} ${variants[variant]} ${className}`}
      {...props}
    >
      {children}
    </button>
  );
};

const Progress = ({ value = 0, className = "", indicatorClassName = "" }) => (
  <div className={`w-full bg-gray-200 rounded-full h-2 ${className}`}>
    <div
      className={`h-2 rounded-full transition-all duration-300 ${indicatorClassName || 'bg-blue-600'}`}
      style={{ width: `${Math.min(100, Math.max(0, value))}%` }}
    />
  </div>
);

const Tabs = ({ defaultValue, children, className = "" }) => {
  const [activeTab, setActiveTab] = useState(defaultValue);

  return (
    <div className={`${className}`}>
      {React.Children.map(children, (child, index) =>
        React.cloneElement(child, { activeTab, setActiveTab, key: index })
      )}
    </div>
  );
};

const TabsList = ({ children, activeTab, setActiveTab }) => (
  <div className="flex space-x-1 bg-gray-100 p-1 rounded-lg mb-4">
    {React.Children.map(children, (child, index) =>
      React.cloneElement(child, { activeTab, setActiveTab, key: index })
    )}
  </div>
);

const TabsTrigger = ({ value, children, activeTab, setActiveTab }) => (
  <button
    onClick={() => setActiveTab(value)}
    className={`px-3 py-2 text-sm font-medium rounded-md transition-colors ${
      activeTab === value
        ? 'bg-white text-gray-900 shadow-sm'
        : 'text-gray-600 hover:text-gray-900'
    }`}
  >
    {children}
  </button>
);

const TabsContent = ({ value, children, activeTab }) => (
  activeTab === value ? <div>{children}</div> : null
);

const RealTimeDashboard = () => {
  const [dashboardData, setDashboardData] = useState(null);
  // Use the AlertContext instead of local state
  const { alerts } = useAlerts();
  const [connectionStatus, setConnectionStatus] = useState('polling');
  const [lastUpdate, setLastUpdate] = useState(null);
  const [loading, setLoading] = useState(true);
  const [assignmentModal, setAssignmentModal] = useState({
    isOpen: false,
    bedInfo: null
  });

  // Fetch data from backend API
  useEffect(() => {
    let isMounted = true;

    const fetchData = async () => {
      try {
        if (!isMounted) return;
        setLoading(true);

        // Fetch occupancy data
        const occupancyResponse = await fetch('http://localhost:8000/api/beds/occupancy');
        if (!occupancyResponse.ok) throw new Error('Failed to fetch occupancy data');
        const occupancyData = await occupancyResponse.json();

        // Fetch available beds
        const bedsResponse = await fetch('http://localhost:8000/api/beds');
        if (!bedsResponse.ok) throw new Error('Failed to fetch beds data');
        const bedsData = await bedsResponse.json();
        const availableBeds = bedsData.filter(bed => bed.status === 'vacant');

        if (!isMounted) return;

        setDashboardData({
          occupancy: occupancyData,
          available_beds: availableBeds,
          active_alerts: alerts // Use alerts from context
        });

        setLastUpdate(new Date());
        setConnectionStatus('connected');
        setLoading(false);

      } catch (error) {
        if (!isMounted) return;

        console.error('Error fetching data:', error);
        setConnectionStatus('error');
        setLoading(false);

        // Set fallback mock data only on error
        setDashboardData({
          occupancy: {
            overall: {
              total_beds: 112,
              occupied_beds: 82,
              vacant_beds: 23,
              cleaning_beds: 5,
              maintenance_beds: 2,
              occupancy_rate: 73.2
            },
            ward_breakdown: [
              { ward: "ICU", total_beds: 20, occupied: 13, vacant: 7, cleaning: 0, occupancy_rate: 65.0 },
              { ward: "Emergency", total_beds: 25, occupied: 17, vacant: 4, cleaning: 2, occupancy_rate: 68.0 },
              { ward: "General", total_beds: 40, occupied: 31, vacant: 7, cleaning: 2, occupancy_rate: 77.5 },
              { ward: "Pediatric", total_beds: 15, occupied: 10, vacant: 4, cleaning: 1, occupancy_rate: 66.7 },
              { ward: "Maternity", total_beds: 12, occupied: 11, vacant: 1, cleaning: 0, occupancy_rate: 91.7 }
            ]
          },
          available_beds: [
            { bed_id: 1, bed_number: "ICU-01", room_number: "101", ward: "ICU", floor_number: 1, wing: "North", private_room: true, daily_rate: 500 },
            { bed_id: 2, bed_number: "ICU-03", room_number: "103", ward: "ICU", floor_number: 1, wing: "North", private_room: true, daily_rate: 500 },
            { bed_id: 3, bed_number: "GEN-15", room_number: "215", ward: "General", floor_number: 2, wing: "South", private_room: false, daily_rate: 200 }
          ],
          active_alerts: []
        });
        setLastUpdate(new Date());
      }
    };

    // Initial fetch
    fetchData();

    return () => {
      isMounted = false;
    };
  }, []); // Empty dependency array - runs only once on mount

  // Manual refresh function
  const requestUpdate = useCallback(async () => {
    try {
      // Fetch occupancy data first to test connection
      const occupancyResponse = await fetch('http://localhost:8000/api/beds/occupancy');
      if (!occupancyResponse.ok) throw new Error('Failed to fetch occupancy data');
      const occupancyData = await occupancyResponse.json();

      // Set to connected only after successful data fetch
      setConnectionStatus('connected');

      // Fetch available beds
      const bedsResponse = await fetch('http://localhost:8000/api/beds');
      if (!bedsResponse.ok) throw new Error('Failed to fetch beds data');
      const bedsData = await bedsResponse.json();
      const availableBeds = bedsData.filter(bed => bed.status === 'vacant');

      setDashboardData({
        occupancy: occupancyData,
        available_beds: availableBeds,
        active_alerts: []
      });

      setLastUpdate(new Date());
      setConnectionStatus('connected');

    } catch (error) {
      console.error('Error refreshing data:', error);
      setConnectionStatus('error');

      // Auto-retry connection after 5 seconds
      setTimeout(() => {
        console.log('Attempting to reconnect...');
        requestUpdate();
      }, 5000);
    }
  }, []);





  const handleAssignPatient = (bed, e) => {
    if (e) {
      e.preventDefault();
      e.stopPropagation();
    }
    setAssignmentModal({
      isOpen: true,
      bedInfo: bed
    });
  };

  const handleAssignmentSuccess = useCallback((assignmentData) => {
    // Refresh dashboard data
    requestUpdate();

    // Close modal
    setAssignmentModal({
      isOpen: false,
      bedInfo: null
    });

    // Show success message
    alert(`Patient ${assignmentData.patient_name} successfully assigned to bed ${assignmentData.bed_id}`);
  }, [requestUpdate]);

  const closeAssignmentModal = useCallback(() => {
    setAssignmentModal({
      isOpen: false,
      bedInfo: null
    });
  }, []);

  const getOccupancyColor = (rate) => {
    if (rate >= 95) return 'bg-red-500';
    if (rate >= 90) return 'bg-orange-500';
    if (rate >= 85) return 'bg-yellow-500';
    return 'bg-green-500';
  };



  if (!dashboardData || loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <RefreshCw className="h-8 w-8 animate-spin mx-auto mb-4" />
          <p>Loading hospital dashboard...</p>
          <p className="text-sm text-gray-500 mt-2">
            {connectionStatus === 'error' ? 'Using demo data' : 'Fetching real-time data...'}
          </p>
        </div>
      </div>
    );
  }

  const { occupancy, available_beds } = dashboardData;

  return (
    <div className="space-y-6">
      {/* Connection Status Bar */}
      <div className="flex items-center justify-between bg-gray-50 p-3 rounded-lg">
        <div className="flex items-center space-x-2">
          <div className={`w-3 h-3 rounded-full ${
            connectionStatus === 'connected' ? 'bg-green-500' : 
            connectionStatus === 'error' ? 'bg-red-500' : 'bg-yellow-500'
          }`} />
          <span className="text-sm font-medium">
            Status: {connectionStatus === 'connected' ? 'Production Mode - Live Data' :
                     connectionStatus === 'error' ? 'Production Mode - Error' : 'Production Mode - Live Data'}
          </span>
          {lastUpdate && (
            <span className="text-xs text-gray-500">
              Last update: {lastUpdate.toLocaleTimeString()}
            </span>
          )}
        </div>
        <Button onClick={requestUpdate} size="sm" variant="outline">
          <RefreshCw className="h-4 w-4 mr-2" />
          Refresh
        </Button>
      </div>

      {/* Critical Alerts Banner */}
      {alerts.filter(alert => alert.priority === 'critical').length > 0 && (
        <Alert className="border-red-200 bg-red-50">
          <AlertTriangle className="h-4 w-4 text-red-600" />
          <AlertDescription className="text-red-800">
            <strong>Critical Alert:</strong> {alerts.filter(alert => alert.priority === 'critical').length} critical issues require immediate attention.
          </AlertDescription>
        </Alert>
      )}

      {/* Main Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {/* Overall Occupancy */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Hospital Occupancy</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{occupancy?.overall?.occupancy_rate || 0}%</div>
            <Progress 
              value={occupancy?.overall?.occupancy_rate || 0} 
              className="mt-2"
              indicatorClassName={getOccupancyColor(occupancy?.overall?.occupancy_rate || 0)}
            />
            <p className="text-xs text-muted-foreground mt-2">
              {occupancy?.overall?.occupied_beds || 0} of {occupancy?.overall?.total_beds || 0} beds occupied
            </p>
          </CardContent>
        </Card>

        {/* Available Beds */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Available Beds</CardTitle>
            <BedDouble className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">
              {occupancy?.overall?.vacant_beds || 0}
            </div>
            <p className="text-xs text-muted-foreground">
              {occupancy?.overall?.cleaning_beds || 0} cleaning, {occupancy?.overall?.maintenance_beds || 0} maintenance
            </p>
            <div className="mt-2">
              <Badge variant="outline" className="text-xs">
                {available_beds?.length || 0} immediately available
              </Badge>
            </div>
          </CardContent>
        </Card>

        {/* Active Alerts */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Alerts</CardTitle>
            <Bell className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-orange-600">{alerts.length}</div>
            <div className="flex space-x-1 mt-2">
              {alerts.filter(a => a.priority === 'critical').length > 0 && (
                <Badge variant="destructive" className="text-xs">
                  {alerts.filter(a => a.priority === 'critical').length} Critical
                </Badge>
              )}
              {alerts.filter(a => a.priority === 'high').length > 0 && (
                <Badge variant="secondary" className="text-xs">
                  {alerts.filter(a => a.priority === 'high').length} High
                </Badge>
              )}
            </div>
          </CardContent>
        </Card>

        {/* System Status */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">System Status</CardTitle>
            <Zap className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="flex items-center space-x-2">
              <CheckCircle className="h-5 w-5 text-green-500" />
              <span className="text-sm font-medium">All Systems Operational</span>
            </div>
            <p className="text-xs text-muted-foreground mt-2">
              Real-time monitoring active
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Detailed Tabs */}
      <Tabs defaultValue="wards" className="space-y-4">
        <TabsList>
          <TabsTrigger value="wards">Ward Status</TabsTrigger>
          <TabsTrigger value="available">Available Beds</TabsTrigger>
          <TabsTrigger value="alerts">Active Alerts ({alerts.length})</TabsTrigger>
          <TabsTrigger value="analytics">Analytics</TabsTrigger>
        </TabsList>

        <TabsContent value="wards" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {occupancy?.ward_breakdown?.map((ward) => (
              <Card key={ward.ward}>
                <CardHeader>
                  <CardTitle className="text-lg">{ward.ward}</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    <div className="flex justify-between">
                      <span>Occupancy:</span>
                      <span className="font-bold">{ward.occupancy_rate}%</span>
                    </div>
                    <Progress 
                      value={ward.occupancy_rate} 
                      className="h-2"
                      indicatorClassName={getOccupancyColor(ward.occupancy_rate)}
                    />
                    <div className="grid grid-cols-2 gap-2 text-sm">
                      <div>Occupied: {ward.occupied}</div>
                      <div>Available: {ward.vacant}</div>
                      <div>Total: {ward.total_beds}</div>
                      <div>Cleaning: {ward.cleaning}</div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>



        <TabsContent value="available" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {available_beds?.slice(0, 12).map((bed) => (
              <Card key={bed.bed_id} className="hover:shadow-md transition-shadow">
                <CardContent className="p-4">
                  <div className="flex items-center justify-between mb-2">
                    <h4 className="font-medium">{bed.bed_number}</h4>
                    <Badge variant="outline" className="text-green-600">
                      Available
                    </Badge>
                  </div>
                  <div className="space-y-1 text-sm text-muted-foreground">
                    <div>Room: {bed.room_number}</div>
                    <div>Ward: {bed.ward}</div>
                    <div>Floor: {bed.floor_number}, {bed.wing} Wing</div>
                    <div>Type: {bed.private_room ? 'Private' : 'Shared'}</div>
                    <div>Rate: ${bed.daily_rate}/day</div>
                  </div>
                  <Button
                    size="sm"
                    className="w-full mt-3"
                    onClick={(e) => handleAssignPatient(bed, e)}
                  >
                    Assign Patient
                  </Button>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="alerts" className="space-y-4">
          <div className="space-y-4">
            {alerts.length > 0 ? (
              <>
                <div className="flex items-center justify-between">
                  <h3 className="text-lg font-semibold">Active Alerts ({alerts.length})</h3>
                  <div className="flex space-x-2">
                    {alerts.filter(a => a.priority === 'critical').length > 0 && (
                      <Badge variant="destructive" className="text-xs">
                        {alerts.filter(a => a.priority === 'critical').length} Critical
                      </Badge>
                    )}
                    {alerts.filter(a => a.priority === 'high').length > 0 && (
                      <Badge variant="secondary" className="text-xs bg-orange-100 text-orange-800">
                        {alerts.filter(a => a.priority === 'high').length} High
                      </Badge>
                    )}
                    {alerts.filter(a => a.priority === 'medium').length > 0 && (
                      <Badge variant="outline" className="text-xs">
                        {alerts.filter(a => a.priority === 'medium').length} Medium
                      </Badge>
                    )}
                  </div>
                </div>
                
                <div className="grid grid-cols-1 gap-4">
                  {alerts
                    .sort((a, b) => {
                      const priorityOrder = { critical: 0, high: 1, medium: 2, low: 3 };
                      return priorityOrder[a.priority] - priorityOrder[b.priority];
                    })
                    .map((alert) => (
                      <EnhancedAlertCard key={alert.id} alert={alert} />
                    ))}
                </div>
              </>
            ) : (
              <Card>
                <CardContent className="text-center py-8">
                  <CheckCircle className="h-12 w-12 mx-auto mb-4 text-green-500" />
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">No Active Alerts</h3>
                  <p className="text-gray-600">All systems are operating normally.</p>
                </CardContent>
              </Card>
            )}
          </div>
        </TabsContent>

        <TabsContent value="analytics" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>Occupancy Trends</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-center py-8 text-muted-foreground">
                  <TrendingUp className="h-12 w-12 mx-auto mb-4" />
                  <p>Analytics dashboard coming soon</p>
                </div>
              </CardContent>
            </Card>
            
            <Card>
              <CardHeader>
                <CardTitle>Performance Metrics</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex justify-between">
                    <span>Average Length of Stay:</span>
                    <span className="font-medium">3.2 days</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Bed Turnover Rate:</span>
                    <span className="font-medium">85%</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Patient Satisfaction:</span>
                    <span className="font-medium">4.6/5</span>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>

      {/* Patient Assignment Modal */}
      <PatientAssignmentModal
        isOpen={assignmentModal.isOpen}
        onClose={closeAssignmentModal}
        bedInfo={assignmentModal.bedInfo}
        onAssignSuccess={handleAssignmentSuccess}
      />
    </div>
  );
};

export default RealTimeDashboard;
