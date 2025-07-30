import React, { useState, useEffect } from 'react';
import { Users, UserCheck, AlertTriangle, Activity, Clock, Stethoscope } from 'lucide-react';

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

const Badge = ({ children, className = "" }) => (
  <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${className}`}>
    {children}
  </span>
);

const Alert = ({ children, className = "" }) => (
  <div className={`rounded-md border p-4 ${className}`}>{children}</div>
);

const AlertDescription = ({ children, className = "" }) => (
  <div className={`text-sm ${className}`}>{children}</div>
);

const StaffCoordination = () => {
  const [coordinationData, setCoordinationData] = useState(null);
  const [workloadData, setWorkloadData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchCoordinationData = async () => {
    try {
      setLoading(true);
      
      // Fetch coordination status
      const coordResponse = await fetch('http://localhost:8000/api/staff/coordination');
      const coordData = await coordResponse.json();
      
      // Fetch workload analysis
      const workloadResponse = await fetch('http://localhost:8000/api/staff/workload');
      const workloadData = await workloadResponse.json();
      
      if (coordResponse.ok && workloadResponse.ok) {
        setCoordinationData(coordData);
        setWorkloadData(workloadData);
        setError(null);
      } else {
        throw new Error('Failed to fetch staff data');
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCoordinationData();
    
    // Refresh every 30 seconds
    const interval = setInterval(fetchCoordinationData, 30000);
    return () => clearInterval(interval);
  }, []);

  const getWorkloadStatusColor = (status) => {
    switch (status) {
      case 'normal': return 'bg-green-100 text-green-800';
      case 'high': return 'bg-yellow-100 text-yellow-800';
      case 'critical': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getAlertSeverityColor = (severity) => {
    switch (severity) {
      case 'high': return 'bg-red-100 text-red-800 border-red-200';
      case 'medium': return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'low': return 'bg-blue-100 text-blue-800 border-blue-200';
      default: return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  if (loading) {
    return (
      <div className="p-6">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 rounded w-1/4 mb-4"></div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {[1, 2, 3].map(i => (
              <div key={i} className="h-48 bg-gray-200 rounded"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6">
        <Alert className="border-red-200 bg-red-50">
          <AlertTriangle className="h-4 w-4 text-red-600" />
          <AlertDescription className="text-red-800">
            Error loading staff coordination data: {error}
          </AlertDescription>
        </Alert>
      </div>
    );
  }

  const { departments, overall_metrics, alerts } = coordinationData || {};
  const { workload_analysis } = workloadData || {};

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold text-gray-900 flex items-center">
          <Users className="w-8 h-8 mr-3 text-blue-600" />
          Staff Coordination Dashboard
        </h1>
        <button
          onClick={fetchCoordinationData}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
        >
          Refresh Data
        </button>
      </div>

      {/* Overall Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center">
              <Stethoscope className="h-8 w-8 text-blue-600" />
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Total Doctors</p>
                <p className="text-2xl font-bold text-gray-900">{overall_metrics?.total_doctors || 0}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center">
              <UserCheck className="h-8 w-8 text-green-600" />
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Total Nurses</p>
                <p className="text-2xl font-bold text-gray-900">{overall_metrics?.total_nurses || 0}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center">
              <Activity className="h-8 w-8 text-purple-600" />
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Active Staff</p>
                <p className="text-2xl font-bold text-gray-900">{overall_metrics?.active_staff || 0}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center">
              <Users className="h-8 w-8 text-orange-600" />
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Departments</p>
                <p className="text-2xl font-bold text-gray-900">{overall_metrics?.departments_count || 0}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Alerts */}
      {alerts && alerts.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <AlertTriangle className="w-5 h-5 mr-2 text-red-600" />
              Staffing Alerts ({alerts.length})
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {alerts.map((alert, index) => (
                <Alert key={index} className={getAlertSeverityColor(alert.severity)}>
                  <AlertTriangle className="h-4 w-4" />
                  <AlertDescription>
                    <div className="flex justify-between items-start">
                      <div>
                        <strong>{alert.department}</strong>: {alert.message}
                      </div>
                      <Badge variant="outline" className={`ml-2 ${getAlertSeverityColor(alert.severity)}`}>
                        {alert.severity}
                      </Badge>
                    </div>
                  </AlertDescription>
                </Alert>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Department Staff Distribution */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {departments && Object.entries(departments).map(([deptName, deptData]) => {
          const workload = workload_analysis?.[deptName] || {};
          
          return (
            <Card key={deptName}>
              <CardHeader>
                <CardTitle className="flex items-center justify-between">
                  <span>{deptName}</span>
                  <Badge className={getWorkloadStatusColor(workload.workload_status)}>
                    {workload.workload_status || 'unknown'} workload
                  </Badge>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {/* Staff Summary */}
                  <div className="grid grid-cols-3 gap-4 text-center">
                    <div>
                      <p className="text-2xl font-bold text-blue-600">{deptData.doctors?.length || 0}</p>
                      <p className="text-sm text-gray-600">Doctors</p>
                    </div>
                    <div>
                      <p className="text-2xl font-bold text-green-600">{deptData.nurses?.length || 0}</p>
                      <p className="text-sm text-gray-600">Nurses</p>
                    </div>
                    <div>
                      <p className="text-2xl font-bold text-purple-600">{deptData.total_beds || 0}</p>
                      <p className="text-sm text-gray-600">Total Beds</p>
                    </div>
                  </div>

                  {/* Workload Ratios */}
                  {workload.patients_per_doctor !== undefined && (
                    <div className="bg-gray-50 p-3 rounded-lg">
                      <div className="flex justify-between items-center mb-2">
                        <span className="text-sm font-medium">Patients per Doctor:</span>
                        <span className="font-bold">{workload.patients_per_doctor}</span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-sm font-medium">Patients per Nurse:</span>
                        <span className="font-bold">{workload.patients_per_nurse}</span>
                      </div>
                    </div>
                  )}

                  {/* Recommendations */}
                  {workload.recommendations && workload.recommendations.length > 0 && (
                    <div className="bg-yellow-50 p-3 rounded-lg border border-yellow-200">
                      <p className="text-sm font-medium text-yellow-800 mb-1">Recommendations:</p>
                      {workload.recommendations.map((rec, idx) => (
                        <p key={idx} className="text-sm text-yellow-700">• {rec}</p>
                      ))}
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>
    </div>
  );
};

export default StaffCoordination;
