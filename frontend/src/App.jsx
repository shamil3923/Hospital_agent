import { useState } from 'react';
import RealTimeDashboard from './components/RealTimeDashboard';
import ChatInterface from './components/ChatInterface';
import StaffCoordination from './components/StaffCoordination';
import Sidebar from './components/Sidebar';
import Header from './components/Header';
import AlertTest from './components/AlertTest';
import { AlertProvider, useAlerts } from './contexts/AlertContext';
import { ChatProvider } from './contexts/ChatContext';

// Main App component that uses alerts
const AppContent = () => {
  const [activeView, setActiveView] = useState('dashboard');
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const { alertCount } = useAlerts();

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
          alertCount={alertCount}
        />

        {/* Main Content Area */}
        <main className="flex-1 overflow-hidden bg-gray-50">
          {/* Chat Interface - Full Screen */}
          {activeView === 'chat' && (
            <div className="h-full w-full relative">
              <ChatInterface />
            </div>
          )}

          {/* Other Views - With Container */}
          {activeView !== 'chat' && (
            <div className="container mx-auto px-6 py-8 h-full overflow-y-auto">
              {activeView === 'dashboard' && <RealTimeDashboard />}
              {activeView === 'staff-coordination' && <StaffCoordination />}
              {activeView === 'alert-test' && <AlertTest />}
              {activeView === 'settings' && (
                <div className="bg-white rounded-lg shadow p-6">
                  <h2 className="text-2xl font-bold text-gray-900 mb-4">Settings</h2>
                  <p className="text-gray-600">Settings panel coming soon...</p>
                </div>
              )}
            </div>
          )}
        </main>
      </div>
    </div>
  );
};

// Main App component with AlertProvider and ChatProvider
function App() {
  return (
    <AlertProvider>
      <ChatProvider>
        <AppContent />
      </ChatProvider>
    </AlertProvider>
  );
}

export default App;
