import React, { useState } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from './ui/card';
import { Button } from './ui/button';
import { Alert, AlertDescription } from './ui/alert';
import { 
  Sparkles, 
  CheckCircle, 
  AlertTriangle,
  Clock,
  X
} from 'lucide-react';

const CleaningModal = ({ bedNumber, isOpen, onClose, onCleaningComplete }) => {
  const [completing, setCompleting] = useState(false);
  const [error, setError] = useState(null);

  const handleCompletecleaning = async () => {
    try {
      setCompleting(true);
      setError(null);
      
      const response = await fetch(`/api/beds/${bedNumber}/complete-cleaning`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        }
      });
      
      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.detail || 'Failed to complete cleaning');
      }
      
      // Call the completion callback
      if (onCleaningComplete) {
        onCleaningComplete(data);
      }
      
      // Close modal
      onClose();
      
    } catch (err) {
      setError(err.message);
    } finally {
      setCompleting(false);
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
                <Sparkles className="w-5 h-5 mr-2 text-blue-500" />
                Complete Cleaning - Bed {bedNumber}
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
            {error && (
              <Alert className="mb-4 border-red-200 bg-red-50">
                <AlertTriangle className="h-4 w-4 text-red-600" />
                <AlertDescription className="text-red-800">
                  {error}
                </AlertDescription>
              </Alert>
            )}

            <div className="space-y-4">
              {/* Cleaning Status */}
              <div className="bg-yellow-50 rounded-lg p-4 border border-yellow-200">
                <div className="flex items-center mb-3">
                  <Clock className="w-5 h-5 text-yellow-600 mr-2" />
                  <h3 className="font-semibold text-yellow-800">Cleaning in Progress</h3>
                </div>
                <p className="text-yellow-700 text-sm">
                  Bed {bedNumber} is currently being cleaned and sanitized.
                </p>
              </div>

              {/* Cleaning Checklist */}
              <div className="bg-gray-50 rounded-lg p-4">
                <h3 className="font-semibold text-gray-900 mb-3 flex items-center">
                  <CheckCircle className="w-4 h-4 mr-2 text-green-500" />
                  Cleaning Checklist
                </h3>
                
                <div className="space-y-2 text-sm">
                  <div className="flex items-center">
                    <CheckCircle className="w-4 h-4 text-green-500 mr-2" />
                    <span>Bed linens changed</span>
                  </div>
                  <div className="flex items-center">
                    <CheckCircle className="w-4 h-4 text-green-500 mr-2" />
                    <span>Surfaces disinfected</span>
                  </div>
                  <div className="flex items-center">
                    <CheckCircle className="w-4 h-4 text-green-500 mr-2" />
                    <span>Equipment sanitized</span>
                  </div>
                  <div className="flex items-center">
                    <CheckCircle className="w-4 h-4 text-green-500 mr-2" />
                    <span>Room inspected</span>
                  </div>
                  <div className="flex items-center">
                    <CheckCircle className="w-4 h-4 text-green-500 mr-2" />
                    <span>Ready for next patient</span>
                  </div>
                </div>
              </div>

              {/* Completion Notice */}
              <Alert className="border-green-200 bg-green-50">
                <Sparkles className="h-4 w-4 text-green-600" />
                <AlertDescription className="text-green-800">
                  <strong>Mark as Complete:</strong> Once all cleaning tasks are finished, 
                  click "Complete Cleaning" to make this bed available for new patients.
                </AlertDescription>
              </Alert>

              {/* Action Buttons */}
              <div className="flex space-x-3 pt-4">
                <Button
                  onClick={handleCompletecleaning}
                  disabled={completing}
                  className="flex-1 bg-green-600 hover:bg-green-700 text-white"
                >
                  {completing ? (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                      Completing...
                    </>
                  ) : (
                    <>
                      <CheckCircle className="w-4 h-4 mr-2" />
                      Complete Cleaning
                    </>
                  )}
                </Button>
                
                <Button
                  onClick={onClose}
                  variant="outline"
                  disabled={completing}
                  className="flex-1"
                >
                  Cancel
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default CleaningModal;
