import React, { useState, useEffect } from 'react';
import api from '../api';
import { Calendar, CheckCircle, Video, Plus, X, Eye } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

function FacultyPortal({ user }) {
  const [events, setEvents] = useState([]);
  const [magazines, setMagazines] = useState([]);
  const [cameras, setCameras] = useState([]);
  const [showAddEvent, setShowAddEvent] = useState(false);
  const [activeFeed, setActiveFeed] = useState(null);

  // New Event Form State
  const [newEv, setNewEv] = useState({ title: '', description: '', location: '', date: '', camera_id: '' });

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [eventsRes, magsRes, camsRes] = await Promise.all([
        api.get('/api/events'),
        api.get('/api/magazines'),
        api.get('/api/cameras')
      ]);
      setEvents(eventsRes.data);
      setMagazines(magsRes.data.filter(m => m.status === 'pending'));
      setCameras(camsRes.data);
    } catch (err) {
      console.error('Error fetching data:', err);
    }
  };

  const createEvent = async (e) => {
    e.preventDefault();
    try {
      await api.post('/api/events', newEv);
      setShowAddEvent(false);
      setNewEv({ title: '', description: '', location: '', date: '', camera_id: '' });
      fetchData();
    } catch (err) {
      console.error('Error creating event:', err);
    }
  };

  const approveMagazine = async (id) => {
    try {
      await api.post(`/api/magazines/${id}/approve`);
      fetchData();
    } catch (err) {
      console.error('Error approving magazine:', err);
    }
  };

  return (
    <div className="portal-content">
      <div className="portal-header">
        <h1>Faculty Command Center</h1>
        <p style={{ color: 'var(--text-muted)' }}>Security and Campus Management</p>
      </div>

      <div className="grid" style={{ gridTemplateColumns: '1fr 1fr' }}>
        {/* Left: Event & Camera Management */}
        <div className="grid">
          {/* Event Creation */}
          <section className="card glass">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <Calendar className="text-primary" />
                <h2>Event Management</h2>
              </div>
              <button className="btn btn-primary" onClick={() => setShowAddEvent(true)}>
                <Plus size={18} /> Add Event
              </button>
            </div>

            <div style={{ maxHeight: '300px', overflowY: 'auto' }}>
              {events.map(ev => (
                <div key={ev.id} className="glass" style={{ padding: '0.75rem', marginBottom: '0.5rem', borderRadius: '0.5rem' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <strong>{ev.title}</strong>
                    <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>{new Date(ev.date).toLocaleDateString()}</span>
                  </div>
                  <div style={{ fontSize: '0.8rem', marginTop: '0.4rem', color: 'var(--text-muted)' }}>
                    📍 {ev.location} {ev.camera_id && <span style={{ marginLeft: '10px' }}>📹 Linked to Cam: {ev.camera_name}</span>}
                  </div>
                </div>
              ))}
            </div>
          </section>

          {/* Live Camera Feeds */}
          <section className="card glass">
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem' }}>
              <Video className="text-accent" />
              <h2>Security Feeds</h2>
            </div>
            <div className="grid" style={{ gridTemplateColumns: 'repeat(auto-fill, minmax(120px, 1fr))' }}>
              {cameras.map(cam => (
                <div 
                  key={cam.id} 
                  className="glass" 
                  style={{ padding: '0.5rem', textAlign: 'center', cursor: 'pointer' }}
                  onClick={() => setActiveFeed(cam)}
                >
                  <Eye size={20} style={{ marginBottom: '5px' }} />
                  <div style={{ fontSize: '0.75rem' }}>{cam.name}</div>
                </div>
              ))}
            </div>
          </section>
        </div>

        {/* Right: Magazine Approvals & Active Feed */}
        <div className="grid">
          {/* Live Feed Viewer */}
          <section className="card glass" style={{ minHeight: '300px', display: 'flex', flexDirection: 'column' }}>
            <h3>{activeFeed ? `Live: ${activeFeed.name}` : 'Select a camera to view feed'}</h3>
            <div style={{ flex: 1, background: '#000', borderRadius: '0.5rem', marginTop: '1rem', overflow: 'hidden', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              {activeFeed ? (
                <img 
                  src={`http://localhost:5000/video_stream/${activeFeed.id}`} 
                  alt="Live Feed" 
                  style={{ width: '100%', height: '100%', objectFit: 'contain' }}
                  onError={(e) => { e.target.src = 'https://via.placeholder.com/640x360?text=Camera+Offline'; }}
                />
              ) : (
                <p style={{ color: '#444' }}>No Active Feed</p>
              )}
            </div>
          </section>

          {/* Magazine Approvals */}
          <section className="card glass">
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem' }}>
              <CheckCircle className="text-success" />
              <h2>Pending Approvals</h2>
            </div>
            {magazines.length === 0 ? (
              <p style={{ textAlign: 'center', color: 'var(--text-muted)' }}>No pending submissions</p>
            ) : (
              magazines.map(mag => (
                <div key={mag.id} className="glass" style={{ padding: '1rem', marginBottom: '0.5rem' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div>
                      <strong>{mag.title}</strong>
                      <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>By: {mag.author_name}</div>
                    </div>
                    <button className="btn btn-primary" style={{ padding: '0.4rem 0.8rem', fontSize: '0.8rem' }} onClick={() => approveMagazine(mag.id)}>
                      Approve
                    </button>
                  </div>
                </div>
              ))
            )}
          </section>
        </div>
      </div>

      {/* Add Event Modal */}
      <AnimatePresence>
        {showAddEvent && (
          <motion.div 
            initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
            className="modal-overlay"
            style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.8)', zIndex: 1000, display: 'flex', alignItems: 'center', justifyContent: 'center' }}
          >
            <motion.div 
              initial={{ scale: 0.9 }} animate={{ scale: 1 }} exit={{ scale: 0.9 }}
              className="card glass" style={{ width: '450px' }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '1.5rem' }}>
                <h3>Add New Event</h3>
                <X style={{ cursor: 'pointer' }} onClick={() => setShowAddEvent(false)} />
              </div>
              <form onSubmit={createEvent}>
                <div className="form-group" style={{ marginBottom: '1rem' }}>
                  <label>Title</label>
                  <input type="text" className="glass" style={{ width: '100%', padding: '0.6rem', color: 'white' }} value={newEv.title} onChange={e => setNewEv({...newEv, title: e.target.value})} required />
                </div>
                <div className="form-group" style={{ marginBottom: '1rem' }}>
                  <label>Description</label>
                  <textarea className="glass" style={{ width: '100%', padding: '0.6rem', color: 'white' }} value={newEv.description} onChange={e => setNewEv({...newEv, description: e.target.value})} required />
                </div>
                <div style={{ display: 'flex', gap: '1rem', marginBottom: '1rem' }}>
                  <div style={{ flex: 1 }}>
                    <label>Location</label>
                    <input type="text" className="glass" style={{ width: '100%', padding: '0.6rem', color: 'white' }} value={newEv.location} onChange={e => setNewEv({...newEv, location: e.target.value})} required />
                  </div>
                  <div style={{ flex: 1 }}>
                    <label>Date</label>
                    <input type="datetime-local" className="glass" style={{ width: '100%', padding: '0.6rem', color: 'white' }} value={newEv.date} onChange={e => setNewEv({...newEv, date: e.target.value})} required />
                  </div>
                </div>
                <div className="form-group" style={{ marginBottom: '1.5rem' }}>
                  <label>Link to Camera (Optional)</label>
                  <select className="glass" style={{ width: '100%', padding: '0.6rem', color: 'white' }} value={newEv.camera_id} onChange={e => setNewEv({...newEv, camera_id: e.target.value})}>
                    <option value="">None</option>
                    {cameras.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
                  </select>
                </div>
                <button type="submit" className="btn btn-primary" style={{ width: '100%' }}>Create Event & Notify Students</button>
              </form>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

export default FacultyPortal;
