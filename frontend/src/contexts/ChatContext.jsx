import React, { createContext, useContext, useState, useCallback, useEffect } from 'react';

const ChatContext = createContext();

export const useChat = () => {
  const context = useContext(ChatContext);
  if (!context) {
    throw new Error('useChat must be used within a ChatProvider');
  }
  return context;
};

const getInitialMessages = () => {
  try {
    const saved = localStorage.getItem('aria_chat_messages');
    if (saved) {
      const parsed = JSON.parse(saved);
      // Convert timestamp strings back to Date objects
      return parsed.map(msg => ({
        ...msg,
        timestamp: new Date(msg.timestamp)
      }));
    }
  } catch (error) {
    console.error('Error loading saved messages:', error);
  }

  // Default welcome message
  return [
    {
      id: 1,
      type: 'agent',
      content: "🏥 **Welcome to ARIA - Advanced Resource Intelligence Assistant**\n\n🧠 **Enhanced AI with LLM + RAG + MCP Integration**\n\nYour intelligent partner for hospital operations management.\n\n🎯 **WHAT I CAN DO:**\n\n**🛏️ Smart Bed Management:**\n• Real-time ICU/ER/Ward availability with predictions\n• Automated patient-bed matching with medical requirements\n• Capacity optimization with discharge planning integration\n\n**👨‍⚕️ Intelligent Patient Operations:**\n• Patient assignment with doctor specialty matching\n• Workflow automation for admissions/transfers/discharges\n• Medical team coordination with availability tracking\n\n**📊 Predictive Analytics:**\n• Occupancy forecasting & bottleneck identification\n• Resource utilization optimization\n• Emergency preparedness & surge capacity planning\n\n**🚨 Real-time Monitoring:**\n• Critical alerts with priority classification\n• Equipment status & maintenance scheduling\n• Staff workload balancing & optimization\n\n**💬 Try These Smart Queries:**\n• \"Show critical ICU status with predictions\"\n• \"Find optimal bed for cardiac patient\"\n• \"Analyze current bottlenecks and solutions\"\n• \"Emergency surge capacity assessment\"\n\n*Ask me anything about hospital operations - I'm here to help optimize patient care with advanced AI!*",
      timestamp: new Date(),
      enhanced: true,
      agent: 'aria_welcome_assistant'
    }
  ];
};

export const ChatProvider = ({ children }) => {
  const [messages, setMessages] = useState(getInitialMessages);
  
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  // Save messages to localStorage whenever messages change
  useEffect(() => {
    try {
      localStorage.setItem('aria_chat_messages', JSON.stringify(messages));
    } catch (error) {
      console.error('Error saving messages:', error);
    }
  }, [messages]);

  const addMessage = useCallback((message) => {
    setMessages(prev => [...prev, message]);
  }, []);

  const clearMessages = useCallback(() => {
    setMessages([{
      id: 1,
      type: 'agent',
      content: "🏥 **Welcome to ARIA - Advanced Resource Intelligence Assistant**\n\nYour intelligent partner for hospital operations management.\n\n🎯 **WHAT I CAN DO:**\n\n**🛏️ Smart Bed Management:**\n• Real-time ICU/ER/Ward availability with predictions\n• Automated patient-bed matching with medical requirements\n• Capacity optimization with discharge planning integration\n\n**👨‍⚕️ Intelligent Patient Operations:**\n• Patient assignment with doctor specialty matching\n• Workflow automation for admissions/transfers/discharges\n• Medical team coordination with availability tracking\n\n**📊 Predictive Analytics:**\n• Occupancy forecasting & bottleneck identification\n• Resource utilization optimization\n• Emergency preparedness & surge capacity planning\n\n**🚨 Real-time Monitoring:**\n• Critical alerts with priority classification\n• Equipment status & maintenance scheduling\n• Staff workload balancing & optimization\n\n**💬 Try These Smart Queries:**\n• \"Show critical ICU status with predictions\"\n• \"Find optimal bed for cardiac patient\"\n• \"Analyze current bottlenecks and solutions\"\n• \"Emergency surge capacity assessment\"\n\n*Ask me anything about hospital operations - I'm here to help optimize patient care!*",
      timestamp: new Date(),
      enhanced: true
    }]);
  }, []);

  const value = {
    messages,
    setMessages,
    inputMessage,
    setInputMessage,
    isLoading,
    setIsLoading,
    addMessage,
    clearMessages
  };

  return (
    <ChatContext.Provider value={value}>
      {children}
    </ChatContext.Provider>
  );
};

export default ChatContext;