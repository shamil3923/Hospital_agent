import React, { useState } from 'react';
import RealTimeDashboard from './components/RealTimeDashboard';
import ChatInterface from './components/ChatInterface';
import Sidebar from './components/Sidebar';
import Header from './components/Header';

function App() {
  const [activeView, setActiveView] = useState('dashboard');
  const [sidebarOpen, setSidebarOpen] = useState(true);

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Sidebar */}
      <Sidebar 
        isOpen={sidebarOpen}
        activeView={activeView}
        setActiveView={setActiveView}
      />
      
      {/* Main Content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Header */}
        <Header 
          sidebarOpen={sidebarOpen}
          setSidebarOpen={setSidebarOpen}
        />
        
        {/* Main Content Area */}
        <main className="flex-1 overflow-x-hidden overflow-y-auto bg-gray-50">
          <div className="container mx-auto px-6 py-8">
            {activeView === 'dashboard' && <RealTimeDashboard />}
            {activeView === 'chat' && <ChatInterface />}
            {activeView === 'settings' && (
              <div className="bg-white rounded-lg shadow p-6">
                <h2 className="text-2xl font-bold text-gray-900 mb-4">Settings</h2>
                <p className="text-gray-600">Settings panel coming soon...</p>
              </div>
            )}
          </div>
        </main>
      </div>
    </div>
  );
}

export default App;
