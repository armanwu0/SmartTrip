import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Home from './pages/Home';
import TripPlanner from './pages/TripPlanner';
import Results from './pages/Results';
import DestinationDetails from './pages/DestinationDetails';
import './index.css';

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/plan" element={<TripPlanner />} />
        <Route path="/results" element={<Results />} />
        <Route path="/destination/:id" element={<DestinationDetails />} />
      </Routes>
    </Router>
  );
}

export default App;
