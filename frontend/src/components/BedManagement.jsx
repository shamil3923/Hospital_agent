import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Alert, AlertDescription } from './ui/alert';
import DischargeModal from './DischargeModal';
import CleaningModal from './CleaningModal';
import { 
  Bed, 
  Users, 
  UserMinus,
  Sparkles,
  Clock,
  CheckCircle,
  AlertTriangle,
  RefreshCw
} from 'lucide-react';

const BedManagement = () => {
  const [beds, setBeds] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedBed, setSelectedBed] = useState(null);
  const [dischargeModalOpen, setDischargeModalOpen] = useState(false);
  const [cleaningModalOpen, setCleaningModalOpen] = useState(false);

  // Fetch beds data
  const fetchBeds = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/beds');
      const data = await response.json();
      
      if (!response.ok) {
        throw new Error('Failed to fetch beds');
      }
      
      setBeds(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchBeds();
    
    // Refresh beds every 30 seconds
    const interval = setInterval(fetchBeds, 30000);
    return () => clearInterval(interval);
  }, []);

  // Handle discharge button click
  const handleDischargeClick = (bed) => {
    setSelectedBed(bed);
    setDischargeModalOpen(true);
  };

  // Handle cleaning button click
  const handleCleaningClick = (bed) => {
    setSelectedBed(bed);
    setCleaningModalOpen(true);
  };

  // Handle discharge completion
  const handleDischargeComplete = (result) => {
    console.log('Discharge completed:', result);
    fetchBeds(); // Refresh beds list
    
    // Show success message (you can implement toast notifications)
    alert(`Patient successfully discharged from bed ${result.bed_number}`);
  };

  // Handle cleaning completion
  const handleCleaningComplete = (result) => {
    console.log('Cleaning completed:', result);
    fetchBeds(); // Refresh beds list
    
    // Show success message
    alert(`Cleaning completed for bed ${result.bed_number} - now available`);
  };

  // Get status badge
  const getStatusBadge = (status) => {
    const statusConfig = {
      occupied: { color: 'bg-red-500', icon: Users, text: 'Occupied' },
      vacant: { color: 'bg-green-500', icon: CheckCircle, text: 'Vacant' },
      cleaning: { color: 'bg-yellow-500', icon: Clock, text: 'Cleaning' },
      maintenance: { color: 'bg-gray-500', icon: AlertTriangle, text: 'Maintenance' }
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

  // Get action buttons for each bed
  const getActionButtons = (bed) => {
    switch (bed.status) {
      case 'occupied':
        return (
          <Button
            onClick={() => handleDischargeClick(bed)}
            size="sm"
            className="bg-red-600 hover:bg-red-700 text-white"
          >
            <UserMinus className="w-4 h-4 mr-1" />
            Discharge
          </Button>
        );
      
      case 'cleaning':
        return (
          <Button
            onClick={() => handleCleaningClick(bed)}
            size="sm"
            className="bg-blue-600 hover:bg-blue-700 text-white"
          >
            <Sparkles className="w-4 h-4 mr-1" />
            Complete Cleaning
          </Button>
        );
      
      case 'vacant':
        return (
          <Button
            size="sm"
            variant="outline"
            className="text-green-600 border-green-600 hover:bg-green-50"
          >
            <Users className="w-4 h-4 mr-1" />
            Assign Patient
          </Button>
        );
      
      default:
        return null;
    }
  };

  if (loading) {
    return (
      <Card className="w-full">
        <CardContent className="flex items-center justify-center p-8">
          <RefreshCw className="w-6 h-6 animate-spin mr-2" />
          <span>Loading bed management...</span>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <Card>
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center">
              <Bed className="w-5 h-5 mr-2" />
              Bed Management & Discharge System
            </CardTitle>
            <Button 
              onClick={fetchBeds} 
              size="sm" 
              variant="outline"
              className="ml-2"
            >
              <RefreshCw className="w-4 h-4 mr-1" />
              Refresh
            </Button>
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

      {/* Beds Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {beds.map((bed) => (
          <Card key={bed.id} className="hover:shadow-md transition-shadow">
            <CardContent className="p-4">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center">
                  <Bed className="w-4 h-4 mr-2 text-gray-600" />
                  <span className="font-semibold">Bed {bed.bed_number}</span>
                </div>
                {getStatusBadge(bed.status)}
              </div>
              
              <div className="space-y-2 text-sm text-gray-600 mb-4">
                <div className="flex justify-between">
                  <span>Ward:</span>
                  <span className="font-medium">{bed.ward}</span>
                </div>
                <div className="flex justify-between">
                  <span>Room:</span>
                  <span className="font-medium">{bed.room_number}</span>
                </div>
                <div className="flex justify-between">
                  <span>Type:</span>
                  <span className="font-medium">{bed.bed_type}</span>
                </div>
                {bed.patient_id && (
                  <div className="flex justify-between">
                    <span>Patient ID:</span>
                    <span className="font-medium">#{bed.patient_id}</span>
                  </div>
                )}
                {bed.last_updated && (
                  <div className="flex justify-between">
                    <span>Updated:</span>
                    <span className="font-medium">
                      {new Date(bed.last_updated).toLocaleTimeString()}
                    </span>
                  </div>
                )}
              </div>
              
              <div className="flex justify-center">
                {getActionButtons(bed)}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Discharge Modal */}
      <DischargeModal
        bedNumber={selectedBed?.bed_number}
        isOpen={dischargeModalOpen}
        onClose={() => {
          setDischargeModalOpen(false);
          setSelectedBed(null);
        }}
        onDischargeComplete={handleDischargeComplete}
      />

      {/* Cleaning Modal */}
      <CleaningModal
        bedNumber={selectedBed?.bed_number}
        isOpen={cleaningModalOpen}
        onClose={() => {
          setCleaningModalOpen(false);
          setSelectedBed(null);
        }}
        onCleaningComplete={handleCleaningComplete}
      />
    </div>
  );
};

export default BedManagement;
