import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { AuthProvider } from './AuthContext';
import Home from './pages/Home';
import TripPlanner from './pages/TripPlanner';
import Results from './pages/Results';
import DestinationDetails from './pages/DestinationDetails';
import AuthPage from './pages/AuthPage';
import Dashboard from './pages/Dashboard';
import TripDetails from './pages/TripDetails';
import Community from './pages/Community';
import AIChatbot from './components/AIChatbot';
import './index.css';

function App() {
  return (
    <AuthProvider>
      <Router>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/plan" element={<TripPlanner />} />
          <Route path="/results" element={<Results />} />
          <Route path="/destination/:id" element={<DestinationDetails />} />
          <Route path="/auth" element={<AuthPage />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/trips/:tripId" element={<TripDetails />} />
          <Route path="/community" element={<Community />} />
        </Routes>
        <AIChatbot />
      </Router>
    </AuthProvider>
  );
}

export default App;
