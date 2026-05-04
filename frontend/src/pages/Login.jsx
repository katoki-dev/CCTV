import React, { useState } from 'react';
import api from '../api';
import { useNavigate } from 'react-router-dom';
import { UserCircle, ShieldCheck, ArrowRight } from 'lucide-react';
import { motion } from 'framer-motion';

function Login({ onLogin }) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [isFaculty, setIsFaculty] = useState(false);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const handleLogin = async (e) => {
    e.preventDefault();
    try {
      const response = await api.post('/login', { username, password });
      if (response.data.success) {
        // Fetch user info to get role
        const userResponse = await api.get('/api/cameras'); // Simple check to see if we can access APIs
        // Actually, let's assume the login response should return user data or we fetch it
        // Since my app.py /login doesn't return user info currently, I should update it or fetch it.
        // I'll update app.py /login to return user info.
        
        // For now, let's assume it returns {success: true, user: {...}}
        // I'll update app.py in the next step.
        const userData = response.data.user;
        onLogin(userData);
        if (userData.role === 'faculty' || userData.role === 'admin') {
          navigate('/faculty');
        } else {
          navigate('/student');
        }
      }
    } catch (err) {
      setError(err.response?.data?.error || 'Invalid credentials');
    }
  };

  return (
    <div className="login-page" style={{ 
      display: 'flex', 
      alignItems: 'center', 
      justifyContent: 'center', 
      height: '100vh',
      background: 'radial-gradient(circle at top right, #1e293b, #0f172a)'
    }}>
      <motion.div 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="glass card" 
        style={{ width: '400px', padding: '2.5rem' }}
      >
        <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
          <h2 style={{ fontSize: '2rem', fontWeight: '800', marginBottom: '0.5rem' }}>CASS Portal</h2>
          <p style={{ color: 'var(--text-muted)' }}>Welcome back, please login</p>
        </div>

        <div style={{ display: 'flex', gap: '1rem', marginBottom: '2rem' }}>
          <button 
            className={`btn ${!isFaculty ? 'btn-primary' : ''}`} 
            style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.5rem', background: !isFaculty ? '' : 'var(--glass)' }}
            onClick={() => setIsFaculty(false)}
          >
            <UserCircle size={18} /> Student
          </button>
          <button 
            className={`btn ${isFaculty ? 'btn-primary' : ''}`} 
            style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.5rem', background: isFaculty ? '' : 'var(--glass)' }}
            onClick={() => setIsFaculty(true)}
          >
            <ShieldCheck size={18} /> Faculty
          </button>
        </div>

        <form onSubmit={handleLogin}>
          <div style={{ marginBottom: '1.5rem' }}>
            <label style={{ display: 'block', marginBottom: '0.5rem', color: 'var(--text-muted)' }}>Username</label>
            <input 
              type="text" 
              className="glass" 
              style={{ width: '100%', padding: '0.75rem', color: 'white', outline: 'none' }}
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
            />
          </div>
          <div style={{ marginBottom: '2rem' }}>
            <label style={{ display: 'block', marginBottom: '0.5rem', color: 'var(--text-muted)' }}>Password</label>
            <input 
              type="password" 
              className="glass" 
              style={{ width: '100%', padding: '0.75rem', color: 'white', outline: 'none' }}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>

          {error && <p style={{ color: 'var(--danger)', marginBottom: '1rem', textAlign: 'center' }}>{error}</p>}

          <button type="submit" className="btn btn-primary" style={{ width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.5rem' }}>
            Login <ArrowRight size={18} />
          </button>
        </form>
      </motion.div>
    </div>
  );
}

export default Login;
