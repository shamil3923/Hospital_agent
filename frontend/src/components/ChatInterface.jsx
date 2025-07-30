import { useRef, useEffect, useState } from 'react';
import { Send, Bot, User, Loader, MessageCircle, Lightbulb, UserPlus, BedDouble } from 'lucide-react';
import axios from 'axios';
import PatientAssignmentModal from './PatientAssignmentModal';
import { useChat } from '../contexts/ChatContext';

const ChatInterface = () => {
  const {
    messages,
    setMessages,
    inputMessage,
    setInputMessage,
    isLoading,
    setIsLoading,
    addMessage
  } = useChat();
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
      'place patient', 'allocate bed', 'need bed for',
      'icu bed', 'emergency bed', 'general bed'
    ];

    return assignmentKeywords.some(keyword =>
      message.toLowerCase().includes(keyword.toLowerCase())
    );
  };

  const extractWardFromMessage = (message) => {
    const wardKeywords = {
      'ICU': ['icu', 'intensive care', 'critical care'],
      'Emergency': ['emergency', 'er', 'trauma', 'urgent'],
      'General': ['general', 'medical', 'internal medicine'],
      'Cardiology': ['cardiology', 'cardiac', 'heart'],
      'Pediatrics': ['pediatric', 'children', 'kids', 'peds'],
      'Maternity': ['maternity', 'obstetrics', 'labor', 'delivery'],
      'Surgery': ['surgery', 'surgical', 'operating', 'post-op'],
      'Orthopedics': ['orthopedic', 'ortho', 'bone', 'joint'],
      'Neurology': ['neurology', 'neuro', 'brain', 'neurological'],
      'Oncology': ['oncology', 'cancer', 'chemotherapy'],
      'Psychiatry': ['psychiatry', 'mental health', 'psychiatric'],
      'Rehabilitation': ['rehabilitation', 'rehab', 'recovery']
    };

    const lowerMessage = message.toLowerCase();
    for (const [ward, keywords] of Object.entries(wardKeywords)) {
      if (keywords.some(keyword => lowerMessage.includes(keyword))) {
        return ward;
      }
    }
    return null;
  };

  const detectEmergencyContext = (message) => {
    const emergencyKeywords = [
      'emergency', 'critical', 'urgent', 'trauma', 'code red',
      'immediate', 'crisis', 'severe', 'life threatening', 'stat'
    ];

    return emergencyKeywords.some(keyword =>
      message.toLowerCase().includes(keyword.toLowerCase())
    );
  };

  const detectPredictiveQuery = (message) => {
    const predictiveKeywords = [
      'predict', 'forecast', 'trend', 'next', 'future', 'expect',
      'bottleneck', 'capacity', 'surge', 'analytics', 'pattern'
    ];

    return predictiveKeywords.some(keyword =>
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

    addMessage(successMessage);

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
    "🚨 Show critical alerts and required actions",
    "🏥 ICU capacity status with discharge predictions",
    "⚡ Emergency bed availability for trauma patient",
    "📊 Analyze current bottlenecks and solutions",
    "📈 Predict bed availability for next 4 hours",
    "🎯 Optimize patient flow for maximum efficiency",
    "👨‍⚕️ Find optimal bed for cardiac patient",
    "🔄 Show pending discharges and bed turnover",
    "📋 Assign patient with automated doctor matching",
    "🛠️ Equipment status and maintenance alerts",
    "👥 Staff workload analysis and optimization",
    "📍 Ward-specific capacity and utilization"
  ];

  const handleSendMessage = async () => {
    if (!inputMessage.trim() || isLoading) return;

    const userMessage = {
      id: Date.now(),
      type: 'user',
      content: inputMessage,
      timestamp: new Date()
    };

    addMessage(userMessage);
    const currentMessage = inputMessage;
    setInputMessage('');
    setIsLoading(true);

    // Check for different types of queries and add context
    const isEmergency = detectEmergencyContext(currentMessage);
    const isPredictive = detectPredictiveQuery(currentMessage);
    const isAssignment = detectPatientAssignmentIntent(currentMessage);

    // Handle patient assignment requests with ward filtering
    if (isAssignment) {
      const wardContext = extractWardFromMessage(currentMessage);
      let filteredBeds = availableBeds;

      // Filter beds by ward if ward context is detected
      if (wardContext) {
        filteredBeds = availableBeds.filter(bed =>
          bed.ward && bed.ward.toLowerCase() === wardContext.toLowerCase()
        );
      }

      setIsLoading(false);

      const wardText = wardContext ? ` in ${wardContext} ward` : '';
      const assignmentResponse = {
        id: Date.now() + 1,
        type: 'agent',
        content: `🏥 **Patient Assignment${wardText}**\n\nI found ${filteredBeds.length} available beds${wardText}.\n\n${isEmergency ? '🚨 **EMERGENCY MODE** - Prioritizing immediate availability.' : 'Select a bed below to proceed with patient assignment.'}`,
        timestamp: new Date(),
        isAssignmentResponse: true,
        availableBeds: filteredBeds.slice(0, 5), // Show up to 5 ward-specific beds
        wardContext: wardContext,
        isEmergency: isEmergency
      };

      addMessage(assignmentResponse);
      return;
    }

    try {
      const startTime = Date.now();
      const wardContext = extractWardFromMessage(currentMessage);

      // Use MCP agent for enhanced capabilities
      const response = await axios.post('http://localhost:8000/api/chat/mcp', {
        message: currentMessage,
        context: {
          isEmergency: isEmergency,
          isPredictive: isPredictive,
          wardContext: wardContext,
          timestamp: new Date().toISOString()
        }
      });
      const endTime = Date.now();
      const responseTime = ((endTime - startTime) / 1000).toFixed(1);

      const agentMessage = {
        id: Date.now() + 1,
        type: 'agent',
        content: response.data.response,
        timestamp: new Date(response.data.timestamp),
        agent: response.data.agent,
        responseTime: responseTime,
        enhanced: true // Mark as enhanced AI response
      };

      addMessage(agentMessage);
    } catch (error) {
      console.error('Error sending message:', error);
      const errorMessage = {
        id: Date.now() + 1,
        type: 'agent',
        content: "I apologize, but I encountered an error while processing your request. Please try again.",
        timestamp: new Date(),
        error: true
      };
      addMessage(errorMessage);
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
    <div className="h-screen flex flex-col bg-white overflow-hidden">
      {/* Header - Enhanced */}
      <div className="bg-gradient-to-r from-blue-600 to-purple-600 shadow-lg border-b border-gray-200 p-4 flex-shrink-0">
        <div className="flex items-center space-x-3">
          <div className="p-2 bg-white/20 rounded-full backdrop-blur-sm">
            <MessageCircle className="h-6 w-6 text-white" />
          </div>
          <div>
            <h2 className="text-xl font-bold text-white">ARIA - Advanced Resource Intelligence</h2>
            <p className="text-sm text-blue-100">
              🧠 LLM + RAG + MCP • 🚨 Emergency Response • 📊 Predictive Analytics
            </p>
          </div>
          <div className="ml-auto flex items-center space-x-3">
            <div className="flex items-center space-x-2 bg-white/20 rounded-full px-3 py-1 backdrop-blur-sm">
              <div className="h-2 w-2 bg-green-400 rounded-full animate-pulse"></div>
              <span className="text-sm text-white font-medium">Enhanced AI Online</span>
            </div>
          </div>
        </div>
      </div>

      {/* Messages Area - Flex 1 to take remaining space */}
      <div className="flex-1 bg-gray-50 overflow-y-auto">
        <div className="p-4 space-y-4">
          {messages.map((message) => (
            <div
              key={message.id}
              className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div className={`flex items-start space-x-2 max-w-4xl ${message.type === 'user' ? 'flex-row-reverse space-x-reverse' : ''}`}>
                {/* Avatar - Smaller */}
                <div className={`flex-shrink-0 p-1.5 rounded-full ${
                  message.type === 'user'
                    ? 'bg-primary-500'
                    : message.error
                      ? 'bg-red-100'
                      : 'bg-gray-200'
                }`}>
                  {message.type === 'user' ? (
                    <User className="h-3.5 w-3.5 text-white" />
                  ) : (
                    <Bot className={`h-3.5 w-3.5 ${message.error ? 'text-red-600' : 'text-gray-600'}`} />
                  )}
                </div>

                {/* Message Content - Optimized */}
                <div className={`p-3 rounded-lg ${
                  message.type === 'user'
                    ? 'bg-primary-500 text-white'
                    : message.error
                      ? 'bg-red-50 border border-red-200 text-red-800'
                      : message.isAssignment
                        ? 'bg-green-50 border border-green-200 text-green-800'
                        : 'bg-white border border-gray-200 text-gray-800'
                }`}>
                  {/* Agent Badge for AI responses */}
                  {message.type === 'agent' && message.agent && (
                    <div className="mb-2 flex items-center space-x-2">
                      <div className="flex items-center space-x-1 px-2 py-1 bg-blue-50 border border-blue-200 rounded-full text-xs">
                        <div className="h-1.5 w-1.5 bg-blue-500 rounded-full animate-pulse"></div>
                        <span className="text-blue-700 font-medium">
                          {message.agent === 'mcp_bed_management_agent' ? '🧠 Enhanced AI (LLM+RAG+MCP)' :
                           message.agent === 'aria_quick_response' ? '⚡ Quick Response' :
                           message.agent === 'aria_icu_intelligence' ? '🏥 ICU Intelligence' :
                           message.agent === 'aria_emergency_protocol' ? '🚨 Emergency Protocol' :
                           message.agent === 'aria_department_analyzer' ? '📊 Department Analyzer' :
                           `🤖 ${message.agent}`}
                        </span>
                      </div>
                      {message.responseTime && (
                        <span className="text-xs text-gray-500">
                          ⏱️ {message.responseTime}s
                        </span>
                      )}
                    </div>
                  )}

                  {/* Enhanced message content rendering - Optimized */}
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
                      <div className="whitespace-pre-wrap break-words">{message.content}</div>
                    )}
                  </div>

                  {/* Context-aware quick action buttons */}
                  {message.type === 'agent' && (
                    <div className="mt-2 flex flex-wrap gap-1.5">
                      {/* ICU-specific actions */}
                      {message.content.includes('ICU') && (
                        <>
                          <button
                            onClick={() => setInputMessage('🚨 Show critical ICU alerts and capacity')}
                            className="px-2.5 py-1 text-xs rounded-full bg-red-50 text-red-700 border border-red-200 hover:bg-red-100 transition-colors"
                          >
                            🚨 Critical ICU Status
                          </button>
                          <button
                            onClick={() => setInputMessage('📈 Predict ICU availability next 4 hours')}
                            className="px-2.5 py-1 text-xs rounded-full bg-blue-50 text-blue-700 border border-blue-200 hover:bg-blue-100 transition-colors"
                          >
                            📈 ICU Predictions
                          </button>
                        </>
                      )}

                      {/* Emergency-specific actions */}
                      {(message.content.includes('emergency') || message.content.includes('critical')) && (
                        <>
                          <button
                            onClick={() => setInputMessage('⚡ Emergency surge capacity assessment')}
                            className="px-2.5 py-1 text-xs rounded-full bg-orange-50 text-orange-700 border border-orange-200 hover:bg-orange-100 transition-colors"
                          >
                            ⚡ Surge Capacity
                          </button>
                          <button
                            onClick={() => setInputMessage('🚨 Activate emergency response protocol')}
                            className="px-2.5 py-1 text-xs rounded-full bg-red-50 text-red-700 border border-red-200 hover:bg-red-100 transition-colors"
                          >
                            🚨 Emergency Protocol
                          </button>
                        </>
                      )}

                      {/* General predictive actions */}
                      {!message.content.includes('prediction') && !message.content.includes('forecast') && (
                        <button
                          onClick={() => setInputMessage('📊 Analyze bottlenecks and predict capacity issues')}
                          className="px-2.5 py-1 text-xs rounded-full bg-purple-50 text-purple-700 border border-purple-200 hover:bg-purple-100 transition-colors"
                        >
                          📊 Predictive Analysis
                        </button>
                      )}
                    </div>
                  )}

                  {/* Emergency department actions - Compact */}
                  {message.type === 'agent' && message.content.includes('Emergency') && (
                    <div className="mt-2 flex flex-wrap gap-1.5">
                      <button
                        onClick={() => setInputMessage('assign emergency patient')}
                        className="px-2.5 py-1 text-xs rounded-full bg-red-50 text-red-700 border border-red-200 hover:bg-red-100 transition-colors"
                      >
                        🚑 Emergency
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

                  <p className={`text-xs mt-1.5 ${
                    message.type === 'user'
                      ? 'text-primary-100'
                      : 'text-gray-500'
                  }`}>
                    {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    {message.agent && ` • ${message.agent}`}
                  </p>
                </div>
              </div>
            </div>
          ))}

          {/* Loading indicator - Compact */}
          {isLoading && (
            <div className="flex justify-start">
              <div className="flex items-start space-x-2 max-w-4xl">
                <div className="flex-shrink-0 p-1.5 bg-gray-200 rounded-full">
                  <Bot className="h-3.5 w-3.5 text-gray-600" />
                </div>
                <div className="bg-white border border-gray-200 p-3 rounded-lg">
                  <div className="flex items-center space-x-2">
                    <Loader className="h-3.5 w-3.5 animate-spin text-gray-600" />
                    <span className="text-sm text-gray-600">Agent is thinking...</span>
                  </div>
                </div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Input Section */}
      <div className="bg-white border-t border-gray-200 flex-shrink-0">
        {/* Suggested Questions - Only show when first message */}
        {messages.length === 1 && (
          <div className="border-b border-gray-200 p-4">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center space-x-2">
                <Lightbulb className="h-3.5 w-3.5 text-yellow-500" />
                <span className="text-xs font-medium text-gray-700">Suggested questions:</span>
              </div>
              <button
                onClick={() => handlePatientAssignment()}
                className="px-2 py-1 bg-blue-600 text-white text-xs rounded-md hover:bg-blue-700 transition-colors flex items-center space-x-1"
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
                  className="text-left p-2 text-xs bg-gray-50 hover:bg-gray-100 rounded-md border border-gray-200 transition-colors"
                >
                  {question}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Input Area - Fixed at Bottom */}
        <div className="bg-white border-t border-gray-200 p-4 flex-shrink-0 shadow-lg">
          <div className="flex items-end space-x-3">
            <div className="flex-1">
              <textarea
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                onKeyDown={handleKeyPress}
                placeholder="🧠 Ask ARIA about critical bed status, patient flow optimization, emergency capacity, predictive analytics, or any medical query..."
                className="w-full p-4 border-2 border-gray-300 rounded-xl resize-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm transition-all duration-200 shadow-sm"
                rows="2"
                disabled={isLoading}
                style={{ maxHeight: '120px' }}
              />
            </div>
            <button
              onClick={handleSendMessage}
              disabled={!inputMessage.trim() || isLoading}
              className="p-4 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-xl hover:from-blue-700 hover:to-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 shadow-lg transform hover:scale-105"
            >
              {isLoading ? (
                <Loader className="h-5 w-5 animate-spin" />
              ) : (
                <Send className="h-5 w-5" />
              )}
            </button>
          </div>
          <div className="flex items-center justify-between mt-2 text-xs text-gray-500">
            <span className="flex items-center space-x-2">
              <span>🚀 Enhanced AI with LLM + RAG + MCP</span>
              <span>•</span>
              <span>Press Enter to send, Shift+Enter for new line</span>
            </span>
            <span className={`${inputMessage.length > 800 ? 'text-orange-500' : ''}`}>
              {inputMessage.length}/1000
            </span>
          </div>
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
