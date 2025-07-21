import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from './ui/card';
import { Button } from './ui/button';
import { Alert, AlertDescription } from './ui/alert';
import { 
  User, 
  Calendar, 
  Clock, 
  MapPin, 
  Activity,
  CheckCircle,
  AlertTriangle,
  X
} from 'lucide-react';

const DischargeModal = ({ bedNumber, isOpen, onClose, onDischargeComplete }) => {
  const [dischargeInfo, setDischargeInfo] = useState(null);
  const [loading, setLoading] = useState(false);
  const [discharging, setDischarging] = useState(false);
  const [error, setError] = useState(null);

  // Fetch discharge information when modal opens
  useEffect(() => {
    if (isOpen && bedNumber) {
      fetchDischargeInfo();
    }
  }, [isOpen, bedNumber]);

  const fetchDischargeInfo = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await fetch(`/api/beds/${bedNumber}/discharge-info`);
      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.detail || 'Failed to fetch discharge information');
      }
      
      setDischargeInfo(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleDischarge = async () => {
    try {
      setDischarging(true);
      setError(null);
      
      const response = await fetch(`/api/beds/${bedNumber}/discharge`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        }
      });
      
      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.detail || 'Failed to discharge patient');
      }
      
      // Call the completion callback
      if (onDischargeComplete) {
        onDischargeComplete(data);
      }
      
      // Close modal
      onClose();
      
    } catch (err) {
      setError(err.message);
    } finally {
      setDischarging(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-md w-full mx-4">
        <Card>
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <CardTitle className="flex items-center">
                <User className="w-5 h-5 mr-2" />
                Discharge Patient - Bed {bedNumber}
              </CardTitle>
              <Button 
                variant="ghost" 
                size="sm" 
                onClick={onClose}
                className="h-6 w-6 p-0"
              >
                <X className="h-4 w-4" />
              </Button>
            </div>
          </CardHeader>
          
          <CardContent>
            {loading && (
              <div className="flex items-center justify-center py-8">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                <span className="ml-2">Loading patient information...</span>
              </div>
            )}

            {error && (
              <Alert className="mb-4 border-red-200 bg-red-50">
                <AlertTriangle className="h-4 w-4 text-red-600" />
                <AlertDescription className="text-red-800">
                  {error}
                </AlertDescription>
              </Alert>
            )}

            {dischargeInfo && !dischargeInfo.can_discharge && (
              <Alert className="mb-4 border-yellow-200 bg-yellow-50">
                <AlertTriangle className="h-4 w-4 text-yellow-600" />
                <AlertDescription className="text-yellow-800">
                  {dischargeInfo.message}
                </AlertDescription>
              </Alert>
            )}

            {dischargeInfo && dischargeInfo.can_discharge && (
              <div className="space-y-4">
                {/* Patient Information */}
                <div className="bg-gray-50 rounded-lg p-4">
                  <h3 className="font-semibold text-gray-900 mb-3 flex items-center">
                    <User className="w-4 h-4 mr-2" />
                    Patient Information
                  </h3>
                  
                  <div className="grid grid-cols-2 gap-3 text-sm">
                    <div>
                      <span className="text-gray-600">Name:</span>
                      <p className="font-medium">{dischargeInfo.patient.name}</p>
                    </div>
                    <div>
                      <span className="text-gray-600">Age:</span>
                      <p className="font-medium">{dischargeInfo.patient.age} years</p>
                    </div>
                    <div className="col-span-2">
                      <span className="text-gray-600">Condition:</span>
                      <p className="font-medium">{dischargeInfo.patient.condition}</p>
                    </div>
                  </div>
                </div>

                {/* Admission Details */}
                <div className="bg-blue-50 rounded-lg p-4">
                  <h3 className="font-semibold text-gray-900 mb-3 flex items-center">
                    <Calendar className="w-4 h-4 mr-2" />
                    Admission Details
                  </h3>
                  
                  <div className="grid grid-cols-2 gap-3 text-sm">
                    <div>
                      <span className="text-gray-600">Admitted:</span>
                      <p className="font-medium">
                        {new Date(dischargeInfo.patient.admission_time).toLocaleDateString()}
                      </p>
                      <p className="text-xs text-gray-500">
                        {new Date(dischargeInfo.patient.admission_time).toLocaleTimeString()}
                      </p>
                    </div>
                    <div>
                      <span className="text-gray-600">Length of Stay:</span>
                      <p className="font-medium flex items-center">
                        <Clock className="w-3 h-3 mr-1" />
                        {dischargeInfo.patient.length_of_stay_hours}h
                      </p>
                    </div>
                  </div>
                </div>

                {/* Bed Information */}
                <div className="bg-green-50 rounded-lg p-4">
                  <h3 className="font-semibold text-gray-900 mb-3 flex items-center">
                    <MapPin className="w-4 h-4 mr-2" />
                    Bed Information
                  </h3>
                  
                  <div className="grid grid-cols-2 gap-3 text-sm">
                    <div>
                      <span className="text-gray-600">Ward:</span>
                      <p className="font-medium">{dischargeInfo.bed.ward}</p>
                    </div>
                    <div>
                      <span className="text-gray-600">Room:</span>
                      <p className="font-medium">{dischargeInfo.bed.room_number}</p>
                    </div>
                    <div className="col-span-2">
                      <span className="text-gray-600">Bed Type:</span>
                      <p className="font-medium">{dischargeInfo.bed.bed_type}</p>
                    </div>
                  </div>
                </div>

                {/* Discharge Warning */}
                <Alert className="border-orange-200 bg-orange-50">
                  <Activity className="h-4 w-4 text-orange-600" />
                  <AlertDescription className="text-orange-800">
                    <strong>Discharge Process:</strong>
                    <ul className="mt-2 text-sm list-disc list-inside space-y-1">
                      <li>Patient will be discharged from bed {bedNumber}</li>
                      <li>Bed status will change to "Cleaning Required"</li>
                      <li>Bed will be available after housekeeping completion</li>
                    </ul>
                  </AlertDescription>
                </Alert>

                {/* Action Buttons */}
                <div className="flex space-x-3 pt-4">
                  <Button
                    onClick={handleDischarge}
                    disabled={discharging}
                    className="flex-1 bg-red-600 hover:bg-red-700 text-white"
                  >
                    {discharging ? (
                      <>
                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                        Discharging...
                      </>
                    ) : (
                      <>
                        <CheckCircle className="w-4 h-4 mr-2" />
                        Confirm Discharge
                      </>
                    )}
                  </Button>
                  
                  <Button
                    onClick={onClose}
                    variant="outline"
                    disabled={discharging}
                    className="flex-1"
                  >
                    Cancel
                  </Button>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default DischargeModal;
