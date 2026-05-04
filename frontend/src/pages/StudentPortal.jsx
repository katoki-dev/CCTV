import React, { useState, useEffect } from 'react';
import api from '../api';
import socket from '../socket';
import { Calendar, BookOpen, Bell, Send, CheckCircle, Clock } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

function StudentPortal({ user }) {
  const [events, setEvents] = useState([]);
  const [magazines, setMagazines] = useState([]);
  const [notifications, setNotifications] = useState([]);
  const [showNotificationPanel, setShowNotificationPanel] = useState(false);
  const [magTitle, setMagTitle] = useState('');
  const [magContent, setMagContent] = useState('');

  useEffect(() => {
    fetchData();
    socket.on('new_event', (event) => {
      setEvents(prev => [event, ...prev]);
      setNotifications(prev => [{ id: Date.now(), message: `New Event: ${event.title}`, type: 'event' }, ...prev]);
    });
    return () => socket.off('new_event');
  }, []);

  const fetchData = async () => {
    try {
      const [eventsRes, magsRes] = await Promise.all([
        api.get('/api/events'),
        api.get('/api/magazines')
      ]);
      setEvents(eventsRes.data);
      setMagazines(magsRes.data);
    } catch (err) {
      console.error('Error fetching data:', err);
    }
  };

  const submitMagazine = async (e) => {
    e.preventDefault();
    try {
      await api.post('/api/magazines', { title: magTitle, content: magContent });
      setMagTitle('');
      setMagContent('');
      fetchData();
    } catch (err) {
      console.error('Error submitting magazine:', err);
    }
  };

  return (
    <div className="portal-content">
      <div className="portal-header">
        <motion.h1 initial={{ opacity: 0 }} animate={{ opacity: 1 }}>Student Hub</motion.h1>
        <p style={{ color: 'var(--text-muted)' }}>Welcome, {user.username}</p>
      </div>

      <div className="grid" style={{ gridTemplateColumns: '2fr 1fr' }}>
        {/* Events Section */}
        <section>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem' }}>
            <Calendar className="text-primary" />
            <h2 style={{ fontSize: '1.5rem' }}>Upcoming Events</h2>
          </div>
          <div className="grid">
            {events.map(event => (
              <motion.div 
                key={event.id} 
                layoutId={event.id}
                className="card glass"
                whileHover={{ scale: 1.02 }}
              >
                <h3 style={{ marginBottom: '0.5rem' }}>{event.title}</h3>
                <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', marginBottom: '1rem' }}>{event.description}</p>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.8rem' }}>
                  <span>📍 {event.location}</span>
                  <span>📅 {new Date(event.date).toLocaleDateString()}</span>
                </div>
              </motion.div>
            ))}
          </div>
        </section>

        {/* Magazine & Notifications Column */}
        <aside className="grid">
          {/* Notifications */}
          <div className="card glass">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <Bell className="text-accent" />
                <h3>Notifications</h3>
              </div>
              {notifications.length > 0 && <span className="badge" style={{ background: 'var(--danger)', padding: '2px 6px', borderRadius: '10px', fontSize: '0.7rem' }}>{notifications.length}</span>}
            </div>
            <div style={{ maxHeight: '200px', overflowY: 'auto' }}>
              {notifications.length === 0 ? (
                <p style={{ color: 'var(--text-muted)', textAlign: 'center', fontSize: '0.8rem' }}>No new alerts</p>
              ) : (
                notifications.map(n => (
                  <div key={n.id} style={{ padding: '0.5rem', borderBottom: '1px solid var(--glass-border)', fontSize: '0.85rem' }}>
                    {n.message}
                  </div>
                ))
              )}
            </div>
          </div>

          {/* Magazine Management */}
          <div className="card glass">
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem' }}>
              <BookOpen className="text-primary" />
              <h3>Campus Magazine</h3>
            </div>
            
            <form onSubmit={submitMagazine} style={{ marginBottom: '1.5rem' }}>
              <input 
                type="text" 
                placeholder="Article Title" 
                className="glass" 
                style={{ width: '100%', padding: '0.5rem', marginBottom: '0.5rem', color: 'white' }}
                value={magTitle}
                onChange={e => setMagTitle(e.target.value)}
                required
              />
              <textarea 
                placeholder="Write your article content..." 
                className="glass" 
                style={{ width: '100%', padding: '0.5rem', marginBottom: '0.5rem', color: 'white', minHeight: '80px' }}
                value={magContent}
                onChange={e => setMagContent(e.target.value)}
                required
              />
              <button type="submit" className="btn btn-primary" style={{ width: '100%', padding: '0.5rem', fontSize: '0.9rem' }}>
                Submit Proposal
              </button>
            </form>

            <div>
              <h4 style={{ fontSize: '0.9rem', marginBottom: '0.5rem', borderBottom: '1px solid var(--glass-border)' }}>My Submissions</h4>
              {magazines.filter(m => m.author_id === user.id).map(m => (
                <div key={m.id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.8rem', padding: '0.4rem 0' }}>
                  <span style={{ maxWidth: '120px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{m.title}</span>
                  <span style={{ 
                    color: m.status === 'approved' ? 'var(--success)' : m.status === 'rejected' ? 'var(--danger)' : 'var(--warning)',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '4px'
                  }}>
                    {m.status === 'approved' ? <CheckCircle size={12} /> : <Clock size={12} />}
                    {m.status}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </aside>
      </div>
    </div>
  );
}

export default StudentPortal;
