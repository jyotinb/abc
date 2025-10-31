import React, { useState, useEffect } from 'react';

const ZoneTopicsManager = () => {
  const [zones, setZones] = useState([]);
  const [selectedZone, setSelectedZone] = useState(null);
  const [topics, setTopics] = useState([]);
  const [loading, setLoading] = useState(false);
  const [showAddModal, setShowAddModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [editingTopic, setEditingTopic] = useState(null);
  const [activeOnly, setActiveOnly] = useState(false);
  const [error, setError] = useState('');

  const [formData, setFormData] = useState({
    topic_path: '',
    direction: 'publish',
    description: '',
    qos: 1,
    is_active: true
  });

  const API_BASE = 'http://167.86.89.98:8000/api';
  const token = localStorage.getItem('token');

  useEffect(() => {
    if (token) fetchZones();
  }, []);

  useEffect(() => {
    if (selectedZone) fetchTopics();
  }, [selectedZone, activeOnly]);

  const fetchZones = async () => {
    try {
      const response = await fetch(`${API_BASE}/zones/`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (!response.ok) throw new Error('Failed to fetch zones');
      const data = await response.json();
      setZones(data);
      if (data.length > 0) setSelectedZone(data[0].id);
    } catch (err) {
      setError('Error fetching zones: ' + err.message);
    }
  };

  const fetchTopics = async () => {
    if (!selectedZone) return;
    setLoading(true);
    setError('');
    try {
      const url = `${API_BASE}/zones/${selectedZone}/topics${activeOnly ? '?active_only=true' : ''}`;
      const response = await fetch(url, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (!response.ok) throw new Error('Failed to fetch topics');
      const data = await response.json();
      setTopics(data);
    } catch (err) {
      setError('Error fetching topics: ' + err.message);
    }
    setLoading(false);
  };

  const handleCreateTopic = async (e) => {
    e.preventDefault();
    setError('');
    try {
      const response = await fetch(`${API_BASE}/zones/${selectedZone}/topics`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(formData)
      });
      if (!response.ok) {
        const errData = await response.json();
        throw new Error(errData.detail || 'Failed to create topic');
      }
      setShowAddModal(false);
      resetForm();
      fetchTopics();
    } catch (err) {
      setError(err.message);
    }
  };

  const handleUpdateTopic = async (e) => {
    e.preventDefault();
    setError('');
    try {
      const response = await fetch(`${API_BASE}/zones/${selectedZone}/topics/${editingTopic.id}`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(formData)
      });
      if (!response.ok) throw new Error('Failed to update topic');
      setShowEditModal(false);
      setEditingTopic(null);
      resetForm();
      fetchTopics();
    } catch (err) {
      setError(err.message);
    }
  };

  const handleToggleTopic = async (topicId) => {
    try {
      const response = await fetch(`${API_BASE}/zones/${selectedZone}/topics/${topicId}/toggle`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (!response.ok) throw new Error('Failed to toggle topic');
      fetchTopics();
    } catch (err) {
      setError(err.message);
    }
  };

  const handleDeleteTopic = async (topicId) => {
    if (!window.confirm('Are you sure you want to delete this topic?')) return;
    try {
      const response = await fetch(`${API_BASE}/zones/${selectedZone}/topics/${topicId}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (!response.ok) throw new Error('Failed to delete topic');
      fetchTopics();
    } catch (err) {
      setError(err.message);
    }
  };

  const openEditModal = (topic) => {
    setEditingTopic(topic);
    setFormData({
      topic_path: topic.topic_path,
      direction: topic.direction,
      description: topic.description || '',
      qos: topic.qos,
      is_active: topic.is_active
    });
    setShowEditModal(true);
  };

  const resetForm = () => {
    setFormData({
      topic_path: '',
      direction: 'publish',
      description: '',
      qos: 1,
      is_active: true
    });
    setError('');
  };

  const getDirectionColor = (direction) => {
    const colors = {
      'publish': 'bg-blue-100 text-blue-700 border-blue-300',
      'subscribe': 'bg-green-100 text-green-700 border-green-300',
      'both': 'bg-purple-100 text-purple-700 border-purple-300'
    };
    return colors[direction] || colors['publish'];
  };

  const getQosBadge = (qos) => {
    const colors = ['bg-gray-100 text-gray-700', 'bg-yellow-100 text-yellow-700', 'bg-red-100 text-red-700'];
    return colors[qos] || colors[0];
  };

  return (
    <div className="container mx-auto p-4 max-w-6xl">
      <div className="bg-white rounded-lg shadow-lg">
        {/* Header */}
        <div className="border-b p-6">
          <h1 className="text-3xl font-bold text-gray-800">Zone Topics Manager</h1>
          <p className="text-gray-600 mt-2">Manage MQTT topics for your greenhouse zones</p>
        </div>

        {/* Error Display */}
        {error && (
          <div className="mx-6 mt-4 p-4 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-red-700 text-sm">{error}</p>
          </div>
        )}

        {/* Zone Selection */}
        <div className="p-6 border-b bg-gray-50">
          <div className="flex flex-wrap items-end gap-4">
            <div className="flex-1 min-w-64">
              <label className="block text-sm font-medium mb-2 text-gray-700">Select Zone</label>
              <select
                value={selectedZone || ''}
                onChange={(e) => setSelectedZone(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="">Choose a zone...</option>
                {zones.map(zone => (
                  <option key={zone.id} value={zone.id}>
                    {zone.name} ({zone.topic_name})
                  </option>
                ))}
              </select>
            </div>

            <label className="flex items-center space-x-2 px-4 py-2 bg-white border border-gray-300 rounded-lg cursor-pointer hover:bg-gray-50">
              <input
                type="checkbox"
                checked={activeOnly}
                onChange={(e) => setActiveOnly(e.target.checked)}
                className="w-4 h-4 text-blue-600 rounded focus:ring-2 focus:ring-blue-500"
              />
              <span className="text-sm font-medium text-gray-700">Active only</span>
            </label>

            <button
              onClick={() => setShowAddModal(true)}
              disabled={!selectedZone}
              className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition disabled:bg-gray-300 disabled:cursor-not-allowed font-medium"
            >
              + Add Topic
            </button>
          </div>
        </div>

        {/* Topics List */}
        <div className="p-6">
          {loading ? (
            <div className="text-center py-12">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
              <p className="text-gray-600 mt-4">Loading topics...</p>
            </div>
          ) : topics.length === 0 ? (
            <div className="text-center py-12">
              <svg className="w-16 h-16 text-gray-300 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.111 16.404a5.5 5.5 0 017.778 0M12 20h.01m-7.08-7.071c3.904-3.905 10.236-3.905 14.141 0M1.394 9.393c5.857-5.857 15.355-5.857 21.213 0" />
              </svg>
              <p className="text-gray-600 text-lg font-medium">No topics found</p>
              <p className="text-gray-400 text-sm mt-2">
                {selectedZone ? 'Click "Add Topic" to create your first topic' : 'Select a zone to view topics'}
              </p>
            </div>
          ) : (
            <div className="space-y-4">
              {topics.map(topic => (
                <div
                  key={topic.id}
                  className={`border-2 rounded-lg p-5 transition-all ${
                    topic.is_active 
                      ? 'bg-white border-gray-200 hover:border-blue-300 hover:shadow-md' 
                      : 'bg-gray-50 border-gray-300 opacity-70'
                  }`}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex flex-wrap items-center gap-2 mb-3">
                        <code className="text-sm font-mono bg-gray-800 text-white px-3 py-1.5 rounded">
                          {topic.topic_path}
                        </code>
                        <span className={`px-3 py-1 rounded-full text-xs font-semibold border ${getDirectionColor(topic.direction)}`}>
                          {topic.direction.toUpperCase()}
                        </span>
                        <span className={`px-3 py-1 rounded-full text-xs font-semibold ${getQosBadge(topic.qos)}`}>
                          QoS {topic.qos}
                        </span>
                        {topic.is_active ? (
                          <span className="flex items-center gap-1 px-3 py-1 bg-green-50 text-green-700 border border-green-300 rounded-full text-xs font-semibold">
                            <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></span>
                            Active
                          </span>
                        ) : (
                          <span className="px-3 py-1 bg-gray-100 text-gray-500 border border-gray-300 rounded-full text-xs font-semibold">
                            Inactive
                          </span>
                        )}
                      </div>
                      {topic.description && (
                        <p className="text-sm text-gray-700 mb-2 leading-relaxed">{topic.description}</p>
                      )}
                      <p className="text-xs text-gray-400">
                        Last updated: {new Date(topic.updated_at).toLocaleString()}
                      </p>
                    </div>

                    <div className="flex items-center gap-2 ml-4">
                      <button
                        onClick={() => handleToggleTopic(topic.id)}
                        className="p-2 text-gray-600 hover:bg-gray-100 rounded-lg transition"
                        title="Toggle active status"
                      >
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4" />
                        </svg>
                      </button>
                      <button
                        onClick={() => openEditModal(topic)}
                        className="p-2 text-blue-600 hover:bg-blue-50 rounded-lg transition"
                        title="Edit topic"
                      >
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                        </svg>
                      </button>
                      <button
                        onClick={() => handleDeleteTopic(topic.id)}
                        className="p-2 text-red-600 hover:bg-red-50 rounded-lg transition"
                        title="Delete topic"
                      >
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                        </svg>
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Modals would go here - implementing separately for clarity */}
    </div>
  );
};

export default ZoneTopicsManager;
