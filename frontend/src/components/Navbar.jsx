import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { LogOut, User, Shield, GraduationCap } from 'lucide-react';

function Navbar({ user, onLogout }) {
  const navigate = useNavigate();

  const handleLogout = () => {
    onLogout();
    navigate('/login');
  };

  return (
    <nav className="navbar glass" style={{ margin: '1rem', borderRadius: '1rem' }}>
      <div className="logo" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
        <Shield className="text-primary" />
        CASS Portal
      </div>
      
      <div style={{ display: 'flex', alignItems: 'center', gap: '1.5rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--text-muted)', fontSize: '0.9rem' }}>
          {user.role === 'faculty' || user.role === 'admin' ? <Shield size={16} /> : <GraduationCap size={16} />}
          <span style={{ textTransform: 'capitalize' }}>{user.role}</span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <User size={18} />
          <strong>{user.username}</strong>
        </div>

        <button onClick={handleLogout} className="btn" style={{ background: 'var(--glass)', display: 'flex', alignItems: 'center', gap: '0.5rem', padding: '0.5rem 1rem' }}>
          <LogOut size={18} /> Logout
        </button>
      </div>
    </nav>
  );
}

export default Navbar;
