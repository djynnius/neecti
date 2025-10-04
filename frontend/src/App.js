import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import { SocketProvider } from './contexts/SocketContext';
import { ThemeProvider } from './contexts/ThemeContext';
import { LanguageProvider } from './contexts/LanguageContext';

// Components
import Navbar from './components/Layout/Navbar';
import Sidebar from './components/Layout/Sidebar';
import RightSidebar from './components/Layout/RightSidebar';
import LoadingSpinner from './components/Common/LoadingSpinner';

// Pages
import Home from './pages/Home';
import Login from './pages/Login';
import Register from './pages/Register';
import Profile from './pages/Profile';
import Messages from './pages/Messages';
import Notifications from './pages/Notifications';
import Search from './pages/Search';
import Post from './pages/Post';
import LLMTest from './components/Admin/LLMTest';

function AppContent() {
  const { user, loading } = useAuth();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <LoadingSpinner size="large" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <Navbar onMenuClick={() => setSidebarOpen(!sidebarOpen)} />
      
      <div className="flex">
        {/* Sidebar */}
        {user && (
          <div className={`w-64 ${sidebarOpen ? 'block' : 'hidden'} lg:block`}>
            <Sidebar />
          </div>
        )}
        
        {/* Main Content */}
        <main className="flex-1 min-h-screen">
          <div className="max-w-4xl mx-auto px-4 py-6">
            <Routes>
              <Route 
                path="/" 
                element={user ? <Home /> : <Navigate to="/login" />} 
              />
              <Route 
                path="/login" 
                element={!user ? <Login /> : <Navigate to="/" />} 
              />
              <Route 
                path="/register" 
                element={!user ? <Register /> : <Navigate to="/" />} 
              />
              <Route 
                path="/profile/:handle" 
                element={user ? <Profile /> : <Navigate to="/login" />} 
              />
              <Route 
                path="/messages" 
                element={user ? <Messages /> : <Navigate to="/login" />} 
              />
              <Route 
                path="/notifications" 
                element={user ? <Notifications /> : <Navigate to="/login" />} 
              />
              <Route 
                path="/search" 
                element={<Search />} 
              />
              <Route
                path="/post/:id"
                element={<Post />}
              />
              <Route
                path="/admin/llm-test"
                element={user ? <LLMTest /> : <Navigate to="/login" />}
              />
            </Routes>
          </div>
        </main>
        
        {/* Right Sidebar */}
        {user && (
          <div className="w-80 hidden xl:block">
            <RightSidebar />
          </div>
        )}
      </div>
    </div>
  );
}

function App() {
  return (
    <ThemeProvider>
      <AuthProvider>
        <LanguageProvider>
          <SocketProvider>
            <Router>
              <AppContent />
            </Router>
          </SocketProvider>
        </LanguageProvider>
      </AuthProvider>
    </ThemeProvider>
  );
}

export default App;
