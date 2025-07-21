import React, { useState, useRef, useEffect } from 'react';
import { Send, Bot, User, Loader, MessageCircle, Lightbulb, UserPlus, BedDouble } from 'lucide-react';
import axios from 'axios';
import PatientAssignmentModal from './PatientAssignmentModal';

const ChatInterface = () => {
  const [messages, setMessages] = useState([
    {
      id: 1,
      type: 'agent',
      content: "🏥 **Welcome to the Enhanced Hospital Operations Assistant!**\n\nI can help you with:\n\n🛏️ **Bed Management:**\n• Check ICU bed availability\n• View emergency department status\n• Get overall hospital occupancy\n\n👨‍⚕️ **Patient Operations:**\n• Assign patients to beds with automated workflows\n• Find available doctors by specialty\n• Coordinate medical team assignments\n\n📊 **Smart Queries:**\n• \"Show me ICU beds\" - Get ICU-specific information\n• \"Assign patient to ICU\" - Start automated assignment workflow\n• \"Hospital bed status\" - Overall capacity overview\n\nTry asking me something specific!",
      timestamp: new Date(),
      enhanced: true
    }
  ]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef(null);
  const [assignmentModal, setAssignmentModal] = useState({
    isOpen: false,
    bedInfo: null,
    fromChat: false
  });
  const [availableBeds, setAvailableBeds] = useState([]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Fetch available beds when component mounts
  useEffect(() => {
    fetchAvailableBeds();
  }, []);

  const fetchAvailableBeds = async () => {
    try {
      const response = await axios.get('http://localhost:8000/api/beds');
      const beds = response.data.filter(bed => bed.status === 'vacant');
      setAvailableBeds(beds);
    } catch (error) {
      console.error('Failed to fetch available beds:', error);
    }
  };

  const detectPatientAssignmentIntent = (message) => {
    const assignmentKeywords = [
      'assign patient', 'assign a patient', 'patient assignment',
      'admit patient', 'admit a patient', 'new patient',
      'find bed', 'available bed', 'bed for patient',
      'place patient', 'allocate bed'
    ];

    return assignmentKeywords.some(keyword =>
      message.toLowerCase().includes(keyword.toLowerCase())
    );
  };

  const handlePatientAssignment = (bedInfo = null) => {
    setAssignmentModal({
      isOpen: true,
      bedInfo: bedInfo,
      fromChat: true
    });
  };

  const handleAssignmentSuccess = (assignmentData) => {
    // Add success message to chat
    const successMessage = {
      id: Date.now(),
      type: 'agent',
      content: `✅ Patient ${assignmentData.patient_name} has been successfully assigned to bed ${assignmentData.bed_id}. The admission workflow has been initiated.`,
      timestamp: new Date(),
      isAssignment: true
    };

    setMessages(prev => [...prev, successMessage]);

    // Close modal
    setAssignmentModal({
      isOpen: false,
      bedInfo: null,
      fromChat: false
    });

    // Refresh available beds
    fetchAvailableBeds();
  };

  const closeAssignmentModal = () => {
    setAssignmentModal({
      isOpen: false,
      bedInfo: null,
      fromChat: false
    });
  };

  const suggestedQuestions = [
    "Show me ICU beds",
    "Show me all patients",
    "Show me all doctors",
    "ICU doctors",
    "Assign patient to ICU",
    "Hospital bed status"
  ];

  const handleSendMessage = async () => {
    if (!inputMessage.trim() || isLoading) return;

    const userMessage = {
      id: Date.now(),
      type: 'user',
      content: inputMessage,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    const currentMessage = inputMessage;
    setInputMessage('');
    setIsLoading(true);

    // Check if this is a patient assignment request
    if (detectPatientAssignmentIntent(currentMessage)) {
      setIsLoading(false);

      // Show available beds and assignment options
      const assignmentResponse = {
        id: Date.now() + 1,
        type: 'agent',
        content: `I can help you assign a patient to an available bed. We currently have ${availableBeds.length} available beds.`,
        timestamp: new Date(),
        isAssignmentResponse: true,
        availableBeds: availableBeds.slice(0, 3) // Show first 3 beds
      };

      setMessages(prev => [...prev, assignmentResponse]);
      return;
    }

    try {
      const response = await axios.post('http://localhost:8000/api/chat', {
        message: currentMessage
      });

      const agentMessage = {
        id: Date.now() + 1,
        type: 'agent',
        content: response.data.response,
        timestamp: new Date(response.data.timestamp),
        agent: response.data.agent
      };

      setMessages(prev => [...prev, agentMessage]);
    } catch (error) {
      console.error('Error sending message:', error);
      const errorMessage = {
        id: Date.now() + 1,
        type: 'agent',
        content: "I apologize, but I encountered an error while processing your request. Please try again.",
        timestamp: new Date(),
        error: true
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const handleSuggestedQuestion = (question) => {
    setInputMessage(question);
  };

  return (
    <div className="flex flex-col h-full max-h-[calc(100vh-200px)]">
      {/* Header */}
      <div className="bg-white rounded-t-lg shadow-sm border border-gray-200 p-4 border-b">
        <div className="flex items-center space-x-3">
          <div className="p-2 bg-primary-100 rounded-full">
            <MessageCircle className="h-6 w-6 text-primary-600" />
          </div>
          <div>
            <h2 className="text-xl font-semibold text-gray-900">Chat Interface</h2>
            <p className="text-sm text-gray-600">
              Interact with the Bed Management Agent using natural language
            </p>
          </div>
          <div className="ml-auto flex items-center space-x-2">
            <div className="h-2 w-2 bg-green-400 rounded-full animate-pulse"></div>
            <span className="text-sm text-gray-600">Agent Online</span>
          </div>
        </div>
      </div>

      {/* Messages Area */}
      <div className="flex-1 bg-gray-50 p-4 overflow-y-auto">
        <div className="space-y-4">
          {messages.map((message) => (
            <div
              key={message.id}
              className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div className={`flex items-start space-x-3 max-w-3xl ${message.type === 'user' ? 'flex-row-reverse space-x-reverse' : ''}`}>
                {/* Avatar */}
                <div className={`flex-shrink-0 p-2 rounded-full ${
                  message.type === 'user' 
                    ? 'bg-primary-500' 
                    : message.error 
                      ? 'bg-red-100' 
                      : 'bg-gray-200'
                }`}>
                  {message.type === 'user' ? (
                    <User className="h-4 w-4 text-white" />
                  ) : (
                    <Bot className={`h-4 w-4 ${message.error ? 'text-red-600' : 'text-gray-600'}`} />
                  )}
                </div>

                {/* Message Content */}
                <div className={`p-4 rounded-lg ${
                  message.type === 'user'
                    ? 'bg-primary-500 text-white'
                    : message.error
                      ? 'bg-red-50 border border-red-200 text-red-800'
                      : message.isAssignment
                        ? 'bg-green-50 border border-green-200 text-green-800'
                        : 'bg-white border border-gray-200 text-gray-800'
                }`}>
                  {/* Enhanced message content rendering */}
                  <div className="text-sm leading-relaxed">
                    {message.enhanced ? (
                      <div
                        className="prose prose-sm max-w-none"
                        dangerouslySetInnerHTML={{
                          __html: message.content
                            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                            .replace(/\n/g, '<br>')
                            .replace(/•/g, '&bull;')
                        }}
                      />
                    ) : (
                      <div className="whitespace-pre-wrap">{message.content}</div>
                    )}
                  </div>

                  {/* Quick action buttons for enhanced responses */}
                  {message.type === 'agent' && message.content.includes('ICU') && (
                    <div className="mt-3 flex flex-wrap gap-2">
                      <button
                        onClick={() => setInputMessage('assign patient to ICU')}
                        className="px-3 py-1 text-xs rounded-full bg-blue-50 text-blue-700 border border-blue-200 hover:bg-blue-100 transition-colors"
                      >
                        🏥 Assign Patient to ICU
                      </button>
                      <button
                        onClick={() => setInputMessage('show available ICU doctors')}
                        className="px-3 py-1 text-xs rounded-full bg-green-50 text-green-700 border border-green-200 hover:bg-green-100 transition-colors"
                      >
                        👨‍⚕️ Find ICU Doctors
                      </button>
                    </div>
                  )}

                  {/* Emergency department actions */}
                  {message.type === 'agent' && message.content.includes('Emergency') && (
                    <div className="mt-3 flex flex-wrap gap-2">
                      <button
                        onClick={() => setInputMessage('assign emergency patient')}
                        className="px-3 py-1 text-xs rounded-full bg-red-50 text-red-700 border border-red-200 hover:bg-red-100 transition-colors"
                      >
                        🚑 Emergency Assignment
                      </button>
                    </div>
                  )}

                  {/* Patient and Doctor management actions */}
                  {message.type === 'agent' && (message.content.includes('Patient') || message.content.includes('patients')) && (
                    <div className="mt-3 flex flex-wrap gap-2">
                      <button
                        onClick={() => setInputMessage('show me all doctors')}
                        className="px-3 py-1 text-xs rounded-full bg-blue-50 text-blue-700 border border-blue-200 hover:bg-blue-100 transition-colors"
                      >
                        👨‍⚕️ View Doctors
                      </button>
                      <button
                        onClick={() => setInputMessage('assign patient to ICU')}
                        className="px-3 py-1 text-xs rounded-full bg-green-50 text-green-700 border border-green-200 hover:bg-green-100 transition-colors"
                      >
                        🏥 Assign to ICU
                      </button>
                    </div>
                  )}

                  {/* Doctor management actions */}
                  {message.type === 'agent' && (message.content.includes('Medical Staff') || message.content.includes('doctors')) && (
                    <div className="mt-3 flex flex-wrap gap-2">
                      <button
                        onClick={() => setInputMessage('show me all patients')}
                        className="px-3 py-1 text-xs rounded-full bg-orange-50 text-orange-700 border border-orange-200 hover:bg-orange-100 transition-colors"
                      >
                        📋 View Patients
                      </button>
                      <button
                        onClick={() => setInputMessage('ICU doctors')}
                        className="px-3 py-1 text-xs rounded-full bg-red-50 text-red-700 border border-red-200 hover:bg-red-100 transition-colors"
                      >
                        🏥 ICU Specialists
                      </button>
                    </div>
                  )}

                  {/* General bed management actions */}
                  {message.type === 'agent' && message.content.includes('bed') && !message.content.includes('ICU') && !message.content.includes('Emergency') && (
                    <div className="mt-3 flex flex-wrap gap-2">
                      <button
                        onClick={() => setInputMessage('hospital bed status')}
                        className="px-3 py-1 text-xs rounded-full bg-gray-50 text-gray-700 border border-gray-200 hover:bg-gray-100 transition-colors"
                      >
                        📊 Bed Status
                      </button>
                      <button
                        onClick={() => setInputMessage('show me ICU beds')}
                        className="px-3 py-1 text-xs rounded-full bg-purple-50 text-purple-700 border border-purple-200 hover:bg-purple-100 transition-colors"
                      >
                        🏥 ICU Beds
                      </button>
                    </div>
                  )}

                  {/* Assignment Response with Available Beds */}
                  {message.isAssignmentResponse && message.availableBeds && (
                    <div className="mt-4 space-y-2">
                      <p className="text-sm font-medium text-gray-700">Available beds:</p>
                      {message.availableBeds.map((bed) => (
                        <div key={bed.bed_id} className="flex items-center justify-between p-3 bg-blue-50 rounded-lg border border-blue-200">
                          <div className="flex items-center space-x-3">
                            <BedDouble className="h-4 w-4 text-blue-600" />
                            <div>
                              <p className="text-sm font-medium text-blue-900">{bed.bed_number}</p>
                              <p className="text-xs text-blue-700">{bed.room_number} • {bed.ward} • Floor {bed.floor_number}</p>
                            </div>
                          </div>
                          <button
                            onClick={() => handlePatientAssignment(bed)}
                            className="px-3 py-1 bg-blue-600 text-white text-xs rounded-md hover:bg-blue-700 transition-colors flex items-center space-x-1"
                          >
                            <UserPlus className="h-3 w-3" />
                            <span>Assign</span>
                          </button>
                        </div>
                      ))}

                      {availableBeds.length > 3 && (
                        <button
                          onClick={() => handlePatientAssignment()}
                          className="w-full mt-2 px-4 py-2 bg-blue-600 text-white text-sm rounded-md hover:bg-blue-700 transition-colors"
                        >
                          View All Available Beds ({availableBeds.length})
                        </button>
                      )}
                    </div>
                  )}

                  <p className={`text-xs mt-2 ${
                    message.type === 'user'
                      ? 'text-primary-100'
                      : 'text-gray-500'
                  }`}>
                    {message.timestamp.toLocaleTimeString()}
                    {message.agent && ` • ${message.agent}`}
                  </p>
                </div>
              </div>
            </div>
          ))}

          {/* Loading indicator */}
          {isLoading && (
            <div className="flex justify-start">
              <div className="flex items-start space-x-3 max-w-3xl">
                <div className="flex-shrink-0 p-2 bg-gray-200 rounded-full">
                  <Bot className="h-4 w-4 text-gray-600" />
                </div>
                <div className="bg-white border border-gray-200 p-4 rounded-lg">
                  <div className="flex items-center space-x-2">
                    <Loader className="h-4 w-4 animate-spin text-gray-600" />
                    <span className="text-sm text-gray-600">Agent is thinking...</span>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
        <div ref={messagesEndRef} />
      </div>

      {/* Suggested Questions */}
      {messages.length === 1 && (
        <div className="bg-white border-t border-gray-200 p-4">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center space-x-2">
              <Lightbulb className="h-4 w-4 text-yellow-500" />
              <span className="text-sm font-medium text-gray-700">Suggested questions:</span>
            </div>
            <button
              onClick={() => handlePatientAssignment()}
              className="px-3 py-1 bg-blue-600 text-white text-xs rounded-md hover:bg-blue-700 transition-colors flex items-center space-x-1"
            >
              <UserPlus className="h-3 w-3" />
              <span>Quick Assign</span>
            </button>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
            {suggestedQuestions.slice(0, 4).map((question, index) => (
              <button
                key={index}
                onClick={() => handleSuggestedQuestion(question)}
                className="text-left p-3 text-sm bg-gray-50 hover:bg-gray-100 rounded-lg border border-gray-200 transition-colors"
              >
                {question}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Input Area */}
      <div className="bg-white rounded-b-lg border border-gray-200 border-t-0 p-4">
        <div className="flex items-end space-x-3">
          <div className="flex-1">
            <textarea
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Ask about bed occupancy, patient flow, or resource management..."
              className="w-full p-3 border border-gray-300 rounded-lg resize-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              rows="3"
              disabled={isLoading}
            />
          </div>
          <button
            onClick={handleSendMessage}
            disabled={!inputMessage.trim() || isLoading}
            className="p-3 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            <Send className="h-5 w-5" />
          </button>
        </div>
        <div className="flex items-center justify-between mt-2 text-xs text-gray-500">
          <span>Press Enter to send, Shift+Enter for new line</span>
          <span>{inputMessage.length}/1000</span>
        </div>
      </div>

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

export default ChatInterface;
