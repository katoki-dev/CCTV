import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Login from './pages/Login';
import StudentPortal from './pages/StudentPortal';
import FacultyPortal from './pages/FacultyPortal';
import Navbar from './components/Navbar';
import socket from './socket';

function App() {
  const [user, setUser] = useState(JSON.parse(localStorage.getItem('user')));

  useEffect(() => {
    if (user) {
      localStorage.setItem('user', JSON.stringify(user));
    } else {
      localStorage.removeItem('user');
    }
  }, [user]);

  return (
    <Router>
      <div className="app-container">
        {user && <Navbar user={user} onLogout={() => setUser(null)} />}
        <Routes>
          <Route 
            path="/login" 
            element={user ? <Navigate to={user.role === 'faculty' || user.role === 'admin' ? '/faculty' : '/student'} /> : <Login onLogin={setUser} />} 
          />
          <Route 
            path="/student/*" 
            element={user?.role === 'student' || user?.role === 'admin' ? <StudentPortal user={user} /> : <Navigate to="/login" />} 
          />
          <Route 
            path="/faculty/*" 
            element={user?.role === 'faculty' || user?.role === 'admin' ? <FacultyPortal user={user} /> : <Navigate to="/login" />} 
          />
          <Route path="/" element={<Navigate to="/login" />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;
