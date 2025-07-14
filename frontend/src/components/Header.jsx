import React from 'react';
import { Menu, Bell, User, Activity } from 'lucide-react';

const Header = ({ sidebarOpen, setSidebarOpen }) => {
  return (
    <header className="bg-white shadow-sm border-b border-gray-200">
      <div className="flex items-center justify-between px-6 py-4">
        <div className="flex items-center">
          <button
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="text-gray-500 hover:text-gray-700 focus:outline-none focus:text-gray-700 lg:hidden"
          >
            <Menu className="h-6 w-6" />
          </button>
          
          <div className="flex items-center ml-4 lg:ml-0">
            <Activity className="h-8 w-8 text-primary-600" />
            <div className="ml-3">
              <h1 className="text-xl font-semibold text-gray-900">
                Healthcare Operations Assistant
              </h1>
              <p className="text-sm text-gray-500">
                Your AI-powered healthcare operations management solution
              </p>
            </div>
          </div>
        </div>
        
        <div className="flex items-center space-x-4">
          {/* Status Indicator */}
          <div className="flex items-center space-x-2">
            <div className="h-2 w-2 bg-green-400 rounded-full animate-pulse"></div>
            <span className="text-sm text-gray-600 hidden sm:block">Online</span>
          </div>
          
          {/* Notifications */}
          <button className="relative p-2 text-gray-400 hover:text-gray-500 focus:outline-none focus:text-gray-500">
            <Bell className="h-6 w-6" />
            <span className="absolute top-0 right-0 block h-2 w-2 rounded-full bg-red-400 ring-2 ring-white"></span>
          </button>
          
          {/* User Menu */}
          <div className="relative">
            <button className="flex items-center space-x-2 text-gray-700 hover:text-gray-900 focus:outline-none">
              <div className="h-8 w-8 bg-primary-100 rounded-full flex items-center justify-center">
                <User className="h-5 w-5 text-primary-600" />
              </div>
              <span className="hidden md:block text-sm font-medium">Dr. Admin</span>
            </button>
          </div>
        </div>
      </div>
    </header>
  );
};

export default Header;
