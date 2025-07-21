import React, { useState, useEffect } from 'react';
import {
  Target,
  User,
  Bed,
  Star,
  TrendingUp,
  AlertTriangle,
  CheckCircle,
  Clock,
  Brain,
  Zap,
  RefreshCw
} from 'lucide-react';
import axios from 'axios';

const BedRecommendations = () => {
  const [patients, setPatients] = useState([]);
  const [selectedPatient, setSelectedPatient] = useState(null);
  const [recommendations, setRecommendations] = useState([]);
  const [loading, setLoading] = useState(false);
  const [assignmentLoading, setAssignmentLoading] = useState(false);

  const fetchPatients = async () => {
    try {
      const response = await axios.get('http://localhost:8000/api/patients');
      setPatients(response.data);
    } catch (error) {
      console.error('Error fetching patients:', error);
    }
  };

  const fetchRecommendations = async (patientId) => {
    try {
      setLoading(true);
      const response = await axios.get(`http://localhost:8000/api/autonomous/bed-recommendations/${patientId}`);
      setRecommendations(response.data.recommendations || []);
    } catch (error) {
      console.error('Error fetching recommendations:', error);
      setRecommendations([]);
    } finally {
      setLoading(false);
    }
  };

  const requestBedAssignment = async (patientId, priority = 'medium') => {
    try {
      setAssignmentLoading(true);
      const response = await axios.post('http://localhost:8000/api/autonomous/bed-assignment/request', null, {
        params: {
          patient_id: patientId,
          priority: priority,
          medical_requirements: JSON.stringify({
            isolation_required: false,
            monitoring_level: 'medium'
          }),
          preferences: JSON.stringify({
            private_room: false
          })
        }
      });
      
      alert(`Bed assignment request submitted successfully! Request ID: ${response.data.request_id}`);
      
      // Refresh data
      await fetchPatients();
      if (selectedPatient) {
        await fetchRecommendations(selectedPatient.patient_id);
      }
    } catch (error) {
      console.error('Error requesting bed assignment:', error);
      alert('Failed to request bed assignment. Please try again.');
    } finally {
      setAssignmentLoading(false);
    }
  };

  useEffect(() => {
    fetchPatients();
  }, []);

  useEffect(() => {
    if (selectedPatient) {
      fetchRecommendations(selectedPatient.patient_id);
    }
  }, [selectedPatient]);

  const getScoreColor = (score) => {
    if (score >= 80) return 'text-green-600 bg-green-100';
    if (score >= 60) return 'text-yellow-600 bg-yellow-100';
    return 'text-red-600 bg-red-100';
  };

  const getScoreIcon = (score) => {
    if (score >= 80) return <CheckCircle className="h-4 w-4" />;
    if (score >= 60) return <AlertTriangle className="h-4 w-4" />;
    return <AlertTriangle className="h-4 w-4" />;
  };

  const getPriorityColor = (condition) => {
    const conditionLower = condition?.toLowerCase() || '';
    if (conditionLower.includes('critical') || conditionLower.includes('emergency')) {
      return 'text-red-600 bg-red-100';
    }
    if (conditionLower.includes('urgent') || conditionLower.includes('icu')) {
      return 'text-orange-600 bg-orange-100';
    }
    return 'text-blue-600 bg-blue-100';
  };

  // Filter patients without beds
  const unassignedPatients = patients.filter(patient => !patient.current_bed_id);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900 flex items-center">
            <Brain className="h-8 w-8 text-primary-600 mr-3" />
            Intelligent Bed Recommendations
          </h2>
          <p className="text-gray-600 mt-1">
            AI-powered bed assignment recommendations with smart scoring
          </p>
        </div>
        <button
          onClick={fetchPatients}
          className="flex items-center space-x-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
        >
          <RefreshCw className="h-4 w-4" />
          <span>Refresh</span>
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Patient Selection */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
            <User className="h-5 w-5 text-primary-600 mr-2" />
            Patients Needing Beds ({unassignedPatients.length})
          </h3>
          
          {unassignedPatients.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              <Bed className="h-12 w-12 mx-auto mb-4 text-gray-300" />
              <p>All patients have been assigned beds!</p>
            </div>
          ) : (
            <div className="space-y-3">
              {unassignedPatients.map((patient) => (
                <div
                  key={patient.patient_id}
                  className={`p-4 border rounded-lg cursor-pointer transition-colors ${
                    selectedPatient?.patient_id === patient.patient_id
                      ? 'border-primary-500 bg-primary-50'
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                  onClick={() => setSelectedPatient(patient)}
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <h4 className="font-medium text-gray-900">{patient.name}</h4>
                      <p className="text-sm text-gray-600">ID: {patient.patient_id}</p>
                      <p className="text-sm text-gray-600">Age: {patient.age} • {patient.gender}</p>
                    </div>
                    <div className="text-right">
                      <div className={`inline-flex items-center space-x-1 px-2 py-1 rounded-full text-xs font-medium ${getPriorityColor(patient.condition)}`}>
                        <span>{patient.condition}</span>
                      </div>
                      <p className="text-xs text-gray-500 mt-1">
                        Dr. {patient.attending_doctor}
                      </p>
                    </div>
                  </div>
                  
                  {selectedPatient?.patient_id === patient.patient_id && (
                    <div className="mt-3 pt-3 border-t border-gray-200">
                      <div className="flex space-x-2">
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            requestBedAssignment(patient.patient_id, 'high');
                          }}
                          disabled={assignmentLoading}
                          className="flex items-center space-x-1 px-3 py-1 bg-primary-600 text-white text-xs rounded hover:bg-primary-700 disabled:opacity-50"
                        >
                          <Zap className="h-3 w-3" />
                          <span>Auto-Assign</span>
                        </button>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            requestBedAssignment(patient.patient_id, 'emergency');
                          }}
                          disabled={assignmentLoading}
                          className="flex items-center space-x-1 px-3 py-1 bg-red-600 text-white text-xs rounded hover:bg-red-700 disabled:opacity-50"
                        >
                          <AlertTriangle className="h-3 w-3" />
                          <span>Emergency</span>
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Bed Recommendations */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
            <Target className="h-5 w-5 text-primary-600 mr-2" />
            Bed Recommendations
            {selectedPatient && (
              <span className="ml-2 text-sm font-normal text-gray-600">
                for {selectedPatient.name}
              </span>
            )}
          </h3>

          {!selectedPatient ? (
            <div className="text-center py-8 text-gray-500">
              <Target className="h-12 w-12 mx-auto mb-4 text-gray-300" />
              <p>Select a patient to see bed recommendations</p>
            </div>
          ) : loading ? (
            <div className="flex items-center justify-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
            </div>
          ) : recommendations.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              <AlertTriangle className="h-12 w-12 mx-auto mb-4 text-gray-300" />
              <p>No suitable beds found for this patient</p>
            </div>
          ) : (
            <div className="space-y-4">
              {recommendations.map((rec, index) => (
                <div
                  key={rec.bed_id}
                  className={`p-4 border rounded-lg ${
                    index === 0 ? 'border-green-200 bg-green-50' : 'border-gray-200'
                  }`}
                >
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center space-x-3">
                      <div className={`p-2 rounded-full ${
                        index === 0 ? 'bg-green-100' : 'bg-gray-100'
                      }`}>
                        <Bed className={`h-4 w-4 ${
                          index === 0 ? 'text-green-600' : 'text-gray-600'
                        }`} />
                      </div>
                      <div>
                        <h4 className="font-medium text-gray-900">
                          Bed {rec.bed_number}
                          {index === 0 && (
                            <span className="ml-2 inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
                              <Star className="h-3 w-3 mr-1" />
                              Best Match
                            </span>
                          )}
                        </h4>
                        <p className="text-sm text-gray-600">{rec.ward} • {rec.bed_type}</p>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className={`inline-flex items-center space-x-1 px-2 py-1 rounded-full text-xs font-medium ${getScoreColor(rec.total_score)}`}>
                        {getScoreIcon(rec.total_score)}
                        <span>{rec.total_score.toFixed(1)}</span>
                      </div>
                      <p className="text-xs text-gray-500 mt-1">
                        {(rec.confidence * 100).toFixed(1)}% confidence
                      </p>
                    </div>
                  </div>

                  {/* Assignment Reasons */}
                  {rec.assignment_reasons && rec.assignment_reasons.length > 0 && (
                    <div className="mb-3">
                      <p className="text-xs font-medium text-gray-700 mb-1">Why this bed:</p>
                      <div className="flex flex-wrap gap-1">
                        {rec.assignment_reasons.map((reason, idx) => (
                          <span
                            key={idx}
                            className="inline-flex items-center px-2 py-1 rounded-full text-xs bg-blue-100 text-blue-800"
                          >
                            <CheckCircle className="h-3 w-3 mr-1" />
                            {reason}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Criteria Scores */}
                  {rec.criteria_scores && (
                    <div className="grid grid-cols-2 gap-2 text-xs">
                      {Object.entries(rec.criteria_scores).map(([criteria, score]) => (
                        <div key={criteria} className="flex justify-between">
                          <span className="text-gray-600 capitalize">
                            {criteria.replace('_', ' ')}:
                          </span>
                          <span className="font-medium">{score.toFixed(1)}</span>
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Potential Issues */}
                  {rec.potential_issues && rec.potential_issues.length > 0 && (
                    <div className="mt-3 pt-3 border-t border-gray-200">
                      <p className="text-xs font-medium text-gray-700 mb-1">Considerations:</p>
                      <div className="flex flex-wrap gap-1">
                        {rec.potential_issues.map((issue, idx) => (
                          <span
                            key={idx}
                            className="inline-flex items-center px-2 py-1 rounded-full text-xs bg-yellow-100 text-yellow-800"
                          >
                            <AlertTriangle className="h-3 w-3 mr-1" />
                            {issue}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Quick Stats */}
      {selectedPatient && recommendations.length > 0 && (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Recommendation Summary</h3>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="text-center">
              <div className="text-2xl font-bold text-gray-900">
                {recommendations.length}
              </div>
              <div className="text-sm text-gray-600">Available Options</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-gray-900">
                {recommendations[0]?.total_score.toFixed(1) || '0.0'}
              </div>
              <div className="text-sm text-gray-600">Best Score</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-gray-900">
                {((recommendations[0]?.confidence || 0) * 100).toFixed(1)}%
              </div>
              <div className="text-sm text-gray-600">Confidence</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-gray-900">
                {new Set(recommendations.map(r => r.ward)).size}
              </div>
              <div className="text-sm text-gray-600">Wards Available</div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default BedRecommendations;
