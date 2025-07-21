import { useState, useEffect } from 'react';
import { X, User, AlertCircle, CheckCircle, Clock } from 'lucide-react';

const PatientAssignmentModal = ({ isOpen, onClose, bedInfo, onAssignSuccess }) => {
  const [step, setStep] = useState(1); // 1: Patient Info, 2: Medical Details, 3: Confirmation
  const [loading, setLoading] = useState(false);
  const [doctors, setDoctors] = useState([]);
  const [doctorsLoading, setDoctorsLoading] = useState(true);
  const [patientData, setPatientData] = useState({
    // Basic Info
    patient_id: '',
    patient_name: '',
    age: '',
    gender: 'male',
    phone: '',
    emergency_contact: '',

    // Medical Info
    primary_condition: '',
    severity: 'stable',
    attending_physician: ''
  });

  const [errors, setErrors] = useState({});
  const [assignmentResult, setAssignmentResult] = useState(null);

  // Fetch doctors function
  const fetchDoctors = async () => {
    try {
      setDoctorsLoading(true);
      console.log('Fetching doctors from API...'); // Debug log

      const response = await fetch('http://localhost:8000/api/doctors');
      console.log('Response status:', response.status); // Debug log
      console.log('Response headers:', response.headers); // Debug log

      if (response.ok) {
        const doctorsData = await response.json();
        console.log('API Response:', doctorsData); // Debug log
        // The API returns {doctors: [...], count: 3}, so we need to extract the doctors array
        const doctorsList = doctorsData.doctors || [];
        console.log('Doctors extracted:', doctorsList); // Debug log
        console.log('Number of doctors:', doctorsList.length); // Debug log
        setDoctors(doctorsList);
      } else {
        console.error('API request failed with status:', response.status);
        const errorText = await response.text();
        console.error('Error response:', errorText);
      }
    } catch (error) {
      console.error('Error fetching doctors:', error);
      setDoctors([]); // Set empty array on error
    } finally {
      setDoctorsLoading(false);
    }
  };

  // Fetch doctors on component mount
  useEffect(() => {
    fetchDoctors();
  }, []);

  // Reset form when modal opens
  useEffect(() => {
    if (isOpen) {
      setStep(1);
      setPatientData({
        patient_id: `PAT${Date.now()}`,
        patient_name: '',
        age: '',
        gender: 'male',
        phone: '',
        emergency_contact: '',
        primary_condition: '',
        severity: 'stable',
        attending_physician: ''
      });
      setErrors({});
      setAssignmentResult(null);
      setLoading(false);
    }
  }, [isOpen]);

  const handleInputChange = (field, value) => {
    setPatientData(prev => ({
      ...prev,
      [field]: value
    }));

    // Clear error when user starts typing
    if (errors[field]) {
      setErrors(prev => {
        const newErrors = { ...prev };
        delete newErrors[field];
        return newErrors;
      });
    }
  };



  const validateStep = (stepNumber) => {
    const newErrors = {};

    if (stepNumber === 1) {
      if (!patientData.patient_name.trim()) newErrors.patient_name = 'Patient name is required';
      if (!patientData.age || patientData.age < 0 || patientData.age > 150) newErrors.age = 'Valid age is required';
      if (!patientData.phone.trim()) newErrors.phone = 'Phone number is required';
    }

    if (stepNumber === 2) {
      if (!patientData.primary_condition.trim()) newErrors.primary_condition = 'Primary condition is required';
      if (!patientData.attending_physician.trim()) newErrors.attending_physician = 'Attending physician is required';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleNext = (e) => {
    if (e) {
      e.preventDefault();
      e.stopPropagation();
    }
    if (validateStep(step)) {
      setStep(step + 1);
    }
  };

  const handlePrevious = (e) => {
    if (e) {
      e.preventDefault();
      e.stopPropagation();
    }
    setStep(step - 1);
  };

  const handleSubmit = async (e) => {
    if (e) {
      e.preventDefault();
      e.stopPropagation();
    }
    if (!validateStep(2)) return;

    setLoading(true);
    try {
      // Use the combined endpoint to create patient and assign bed in one call
      const response = await fetch(`http://localhost:8000/api/beds/${bedInfo.bed_number}/assign-new-patient`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(patientData)
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to assign patient to bed');
      }

      const result = await response.json();

      setAssignmentResult({
        success: true,
        admission_id: result.patient_id,
        workflow_id: result.workflow_id,
        bed_number: result.bed_number,
        patient_name: result.patient_name
      });

      setStep(4); // Success step

      // Notify parent component
      if (onAssignSuccess) {
        onAssignSuccess({
          bed_id: bedInfo.bed_id,
          patient_id: result.patient_id,
          patient_name: result.patient_name
        });
      }

    } catch (error) {
      console.error('Assignment error:', error);
      setAssignmentResult({
        success: false,
        error: error.message
      });
      setStep(4); // Error step
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  const handleFormSubmit = (e) => {
    e.preventDefault();
    e.stopPropagation();
    return false;
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && e.target.tagName !== 'TEXTAREA') {
      e.preventDefault();
      if (step < 3) {
        handleNext(e);
      } else if (step === 3) {
        handleSubmit(e);
      }
    }
  };

  const handleBackdropClick = (e) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  };

  const handleModalClick = (e) => {
    e.stopPropagation();
  };

  return (
    <div
      className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
      onClick={handleBackdropClick}
    >
      <div
        className="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto"
        onClick={handleModalClick}
      >
        <form onSubmit={handleFormSubmit} onKeyDown={handleKeyDown}>
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <div>
            <h2 className="text-xl font-semibold text-gray-900">
              Assign Patient to {bedInfo?.bed_number}
            </h2>
            <p className="text-sm text-gray-500 mt-1">
              {bedInfo?.room_number} • {bedInfo?.ward} • Floor {bedInfo?.floor_number}
            </p>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <X className="h-6 w-6" />
          </button>
        </div>

        {/* Progress Indicator */}
        <div className="px-6 py-4 border-b border-gray-200">
          <div className="flex items-center space-x-4">
            {[1, 2, 3].map((stepNumber) => (
              <div key={stepNumber} className="flex items-center">
                <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
                  step >= stepNumber 
                    ? 'bg-blue-600 text-white' 
                    : 'bg-gray-200 text-gray-600'
                }`}>
                  {stepNumber}
                </div>
                {stepNumber < 3 && (
                  <div className={`w-12 h-1 mx-2 ${
                    step > stepNumber ? 'bg-blue-600' : 'bg-gray-200'
                  }`} />
                )}
              </div>
            ))}
          </div>
          <div className="flex justify-between mt-2 text-xs text-gray-500">
            <span>Patient Info</span>
            <span>Medical Details</span>
            <span>Confirmation</span>
          </div>
        </div>

        {/* Content */}
        <div className="p-6">
          {step === 1 && (
            <div className="space-y-4">
              <h3 className="text-lg font-medium text-gray-900 flex items-center">
                <User className="h-5 w-5 mr-2" />
                Patient Information
              </h3>
              
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Patient Name *
                  </label>
                  <input
                    type="text"
                    value={patientData.patient_name}
                    onChange={(e) => handleInputChange('patient_name', e.target.value)}
                    className={`w-full p-2 border rounded-md ${errors.patient_name ? 'border-red-500' : 'border-gray-300'}`}
                    placeholder="Enter patient name"
                  />
                  {errors.patient_name && <p className="text-red-500 text-xs mt-1">{errors.patient_name}</p>}
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Age *
                  </label>
                  <input
                    type="number"
                    value={patientData.age}
                    onChange={(e) => handleInputChange('age', e.target.value)}
                    className={`w-full p-2 border rounded-md ${errors.age ? 'border-red-500' : 'border-gray-300'}`}
                    placeholder="Age"
                    min="0"
                    max="150"
                  />
                  {errors.age && <p className="text-red-500 text-xs mt-1">{errors.age}</p>}
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Gender
                  </label>
                  <select
                    value={patientData.gender}
                    onChange={(e) => handleInputChange('gender', e.target.value)}
                    className="w-full p-2 border border-gray-300 rounded-md"
                  >
                    <option value="male">Male</option>
                    <option value="female">Female</option>
                    <option value="other">Other</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Phone Number *
                  </label>
                  <input
                    type="tel"
                    value={patientData.phone}
                    onChange={(e) => handleInputChange('phone', e.target.value)}
                    className={`w-full p-2 border rounded-md ${errors.phone ? 'border-red-500' : 'border-gray-300'}`}
                    placeholder="Phone number"
                  />
                  {errors.phone && <p className="text-red-500 text-xs mt-1">{errors.phone}</p>}
                </div>

                <div className="col-span-2">
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Emergency Contact
                  </label>
                  <input
                    type="text"
                    value={patientData.emergency_contact}
                    onChange={(e) => handleInputChange('emergency_contact', e.target.value)}
                    className="w-full p-2 border border-gray-300 rounded-md"
                    placeholder="Emergency contact name and phone"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Patient ID
                  </label>
                  <input
                    type="text"
                    value={patientData.patient_id}
                    onChange={(e) => handleInputChange('patient_id', e.target.value)}
                    className="w-full p-2 border border-gray-300 rounded-md bg-gray-50"
                    placeholder="Auto-generated"
                  />
                </div>
              </div>
            </div>
          )}

          {step === 2 && (
            <div className="space-y-4">
              <h3 className="text-lg font-medium text-gray-900 flex items-center">
                <AlertCircle className="h-5 w-5 mr-2" />
                Medical Information
              </h3>
              
              <div className="grid grid-cols-2 gap-4">
                <div className="col-span-2">
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Primary Condition *
                  </label>
                  <input
                    type="text"
                    value={patientData.primary_condition}
                    onChange={(e) => handleInputChange('primary_condition', e.target.value)}
                    className={`w-full p-2 border rounded-md ${errors.primary_condition ? 'border-red-500' : 'border-gray-300'}`}
                    placeholder="Primary medical condition"
                  />
                  {errors.primary_condition && <p className="text-red-500 text-xs mt-1">{errors.primary_condition}</p>}
                </div>

                <div>
                  <div className="flex justify-between items-center mb-1">
                    <label className="block text-sm font-medium text-gray-700">
                      Attending Physician *
                    </label>
                    <button
                      type="button"
                      onClick={fetchDoctors}
                      className="text-xs text-blue-600 hover:text-blue-800"
                    >
                      Refresh Doctors ({doctors.length})
                    </button>
                  </div>
                  <select
                    value={patientData.attending_physician}
                    onChange={(e) => handleInputChange('attending_physician', e.target.value)}
                    className={`w-full p-2 border rounded-md ${errors.attending_physician ? 'border-red-500' : 'border-gray-300'}`}
                    disabled={doctorsLoading}
                  >
                    {doctorsLoading ? (
                      <option value="">Loading doctors...</option>
                    ) : doctors.length === 0 ? (
                      <option value="">No doctors available</option>
                    ) : (
                      <>
                        <option value="">Select a doctor</option>
                        {doctors.map((doctor) => (
                          <option key={doctor.id} value={doctor.name}>
                            {doctor.name} - {doctor.specialization}
                          </option>
                        ))}
                      </>
                    )}
                  </select>
                  {errors.attending_physician && <p className="text-red-500 text-xs mt-1">{errors.attending_physician}</p>}
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Severity Level
                  </label>
                  <select
                    value={patientData.severity}
                    onChange={(e) => handleInputChange('severity', e.target.value)}
                    className="w-full p-2 border border-gray-300 rounded-md"
                  >
                    <option value="stable">Stable</option>
                    <option value="serious">Serious</option>
                    <option value="critical">Critical</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Admission Type
                  </label>
                  <select
                    value={patientData.admission_type}
                    onChange={(e) => handleInputChange('admission_type', e.target.value)}
                    className="w-full p-2 border border-gray-300 rounded-md"
                  >
                    <option value="scheduled">Scheduled</option>
                    <option value="emergency">Emergency</option>
                    <option value="transfer">Transfer</option>
                    <option value="observation">Observation</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Priority
                  </label>
                  <select
                    value={patientData.priority}
                    onChange={(e) => handleInputChange('priority', e.target.value)}
                    className="w-full p-2 border border-gray-300 rounded-md"
                  >
                    <option value="routine">Routine</option>
                    <option value="semi_urgent">Semi-Urgent</option>
                    <option value="urgent">Urgent</option>
                    <option value="critical">Critical</option>
                  </select>
                </div>


              </div>
            </div>
          )}

          {step === 3 && (
            <div className="space-y-4">
              <h3 className="text-lg font-medium text-gray-900 flex items-center">
                <CheckCircle className="h-5 w-5 mr-2" />
                Confirmation
              </h3>
              
              <div className="bg-gray-50 p-4 rounded-lg">
                <h4 className="font-medium text-gray-900 mb-2">Assignment Summary</h4>
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="text-gray-600">Patient:</span>
                    <span className="ml-2 font-medium">{patientData.patient_name}</span>
                  </div>
                  <div>
                    <span className="text-gray-600">Age:</span>
                    <span className="ml-2">{patientData.age} years</span>
                  </div>
                  <div>
                    <span className="text-gray-600">Condition:</span>
                    <span className="ml-2">{patientData.primary_condition}</span>
                  </div>
                  <div>
                    <span className="text-gray-600">Physician:</span>
                    <span className="ml-2">{patientData.attending_physician}</span>
                  </div>
                  <div>
                    <span className="text-gray-600">Bed:</span>
                    <span className="ml-2 font-medium">{bedInfo?.bed_number}</span>
                  </div>
                  <div>
                    <span className="text-gray-600">Ward:</span>
                    <span className="ml-2">{bedInfo?.ward}</span>
                  </div>
                  <div>
                    <span className="text-gray-600">Severity:</span>
                    <span className={`ml-2 px-2 py-1 rounded text-xs ${
                      patientData.severity === 'critical' ? 'bg-red-100 text-red-800' :
                      patientData.severity === 'serious' ? 'bg-orange-100 text-orange-800' :
                      patientData.severity === 'stable' ? 'bg-green-100 text-green-800' :
                      'bg-blue-100 text-blue-800'
                    }`}>
                      {patientData.severity.toUpperCase()}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          )}

          {step === 4 && assignmentResult && (
            <div className="space-y-4 text-center">
              {assignmentResult.success ? (
                <div>
                  <CheckCircle className="h-16 w-16 text-green-500 mx-auto mb-4" />
                  <h3 className="text-lg font-medium text-gray-900 mb-2">
                    Patient Successfully Assigned!
                  </h3>
                  <p className="text-gray-600 mb-4">
                    {assignmentResult.patient_name} has been assigned to bed {assignmentResult.bed_number}
                  </p>
                  <div className="bg-green-50 p-4 rounded-lg text-left">
                    <h4 className="font-medium text-green-900 mb-2">Assignment Details:</h4>
                    <div className="text-sm text-green-800 space-y-1">
                      <div>Admission ID: {assignmentResult.admission_id}</div>
                      <div>Workflow ID: {assignmentResult.workflow_id}</div>
                      <div>Status: Processing bed assignment workflow</div>
                    </div>
                  </div>
                </div>
              ) : (
                <div>
                  <AlertCircle className="h-16 w-16 text-red-500 mx-auto mb-4" />
                  <h3 className="text-lg font-medium text-gray-900 mb-2">
                    Assignment Failed
                  </h3>
                  <p className="text-gray-600 mb-4">
                    {assignmentResult.error}
                  </p>
                  <div className="bg-red-50 p-4 rounded-lg">
                    <p className="text-sm text-red-800">
                      Please try again or contact system administrator.
                    </p>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between p-6 border-t border-gray-200">
          <div className="flex space-x-3">
            {step > 1 && step < 4 && (
              <button
                type="button"
                onClick={handlePrevious}
                className="px-4 py-2 text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200 transition-colors"
              >
                Previous
              </button>
            )}
          </div>
          
          <div className="flex space-x-3">
            {step < 3 && (
              <button
                type="button"
                onClick={handleNext}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
              >
                Next
              </button>
            )}

            {step === 3 && (
              <button
                type="button"
                onClick={handleSubmit}
                disabled={loading}
                className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 transition-colors disabled:opacity-50 flex items-center"
              >
                {loading && <Clock className="h-4 w-4 mr-2 animate-spin" />}
                {loading ? 'Assigning...' : 'Assign Patient'}
              </button>
            )}

            {step === 4 && (
              <button
                type="button"
                onClick={onClose}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
              >
                Close
              </button>
            )}
          </div>
        </div>
        </form>
      </div>
    </div>
  );
};

export default PatientAssignmentModal;
