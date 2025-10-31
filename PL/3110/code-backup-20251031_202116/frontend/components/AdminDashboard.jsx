import React, { useState, useEffect } from 'react';
import { Users, Building2, Shield, Cpu, Home, Menu, X, Plus, Edit2, Trash2, Save, XCircle, Layers, LogOut, AlertCircle, ArrowRight, ChevronDown, ChevronRight } from 'lucide-react';

const API_BASE_URL = 'http://167.86.89.98:8000/api';

// API Service
const api = {
  token: null,
  currentUser: null,
  
  setToken(token) {
    this.token = token;
    localStorage.setItem('auth_token', token);
  },
  
  getToken() {
    if (!this.token) {
      this.token = localStorage.getItem('auth_token');
    }
    return this.token;
  },
  
  setCurrentUser(user) {
    this.currentUser = user;
    localStorage.setItem('current_user', JSON.stringify(user));
  },
  
  getCurrentUser() {
    if (!this.currentUser) {
      const stored = localStorage.getItem('current_user');
      this.currentUser = stored ? JSON.parse(stored) : null;
    }
    return this.currentUser;
  },
  
  clearToken() {
    this.token = null;
    this.currentUser = null;
    localStorage.removeItem('auth_token');
    localStorage.removeItem('current_user');
  },
  
  isAdmin() {
    const user = this.getCurrentUser();
    return user && (user.role === 'admin' || user.is_superuser);
  },
  
  isManager() {
    const user = this.getCurrentUser();
    return user && (user.role === 'admin' || user.role === 'manager' || user.is_superuser);
  },
  
  async request(endpoint, options = {}) {
    const token = this.getToken();
    const headers = {
      'Content-Type': 'application/json',
      ...options.headers,
    };
    
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
    
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      ...options,
      headers,
    });
    
    if (response.status === 401) {
      this.clearToken();
      window.location.reload();
      throw new Error('Authentication required');
    }
    
    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'An error occurred' }));
      throw new Error(error.detail || 'Request failed');
    }
    
    return response.json();
  },
  
  async login(username, password) {
    const formData = new URLSearchParams();
    formData.append('username', username);
    formData.append('password', password);
    
    const response = await fetch(`${API_BASE_URL}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: formData,
    });
    
    if (!response.ok) throw new Error('Invalid credentials');
    const data = await response.json();
    this.setToken(data.access_token);
    this.setCurrentUser(data.user);
    return data;
  },
  
  async getCompanies() {
    return this.request('/companies/');
  },
  
  async createCompany(data) {
    return this.request('/companies/', { method: 'POST', body: JSON.stringify(data) });
  },
  
  async updateCompany(id, data) {
    return this.request(`/companies/${id}`, { method: 'PUT', body: JSON.stringify(data) });
  },
  
  async deleteCompany(id) {
    return this.request(`/companies/${id}`, { method: 'DELETE' });
  },
  
  // NEW: Company details
  async getCompanyUsers(companyId) {
    return this.request(`/companies/${companyId}/users`);
  },
  
  async getCompanyDevices(companyId) {
    return this.request(`/companies/${companyId}/devices`);
  },
  
  async getUsers() {
    return this.request('/users/');
  },
  
  async createUser(data) {
    return this.request('/users/', { method: 'POST', body: JSON.stringify(data) });
  },
  
  async updateUser(id, data) {
    return this.request(`/users/${id}`, { method: 'PUT', body: JSON.stringify(data) });
  },
  
  async deleteUser(id) {
    return this.request(`/users/${id}`, { method: 'DELETE' });
  },
  
  // NEW: User devices
  async getUserDevices(userId) {
    return this.request(`/users/${userId}/devices`);
  },
  
  async getDevices() {
    return this.request('/devices/');
  },
  
  async createDevice(data) {
    return this.request('/devices/', { method: 'POST', body: JSON.stringify(data) });
  },
  
  async updateDevice(id, data) {
    return this.request(`/devices/${id}`, { method: 'PUT', body: JSON.stringify(data) });
  },
  
  async deleteDevice(id) {
    return this.request(`/devices/${id}`, { method: 'DELETE' });
  },

  async assignDevice(deviceId, userId, accessLevel) {
    return this.request(`/devices/${deviceId}/assign`, {
      method: 'POST',
      body: JSON.stringify({ 
        user_id: userId, 
        device_id: deviceId, 
        access_level: accessLevel 
      })
    });
  },
  
  async unassignDevice(deviceId, userId) {
    return this.request(`/devices/${deviceId}/unassign/${userId}`, {
      method: 'DELETE'
    });
  },
  
  async getDeviceAssignments(deviceId) {
    return this.request(`/devices/${deviceId}/assignments`);
  },
  
  async getZones(deviceId = null) {
    const query = deviceId ? `?device_id=${deviceId}` : '';
    return this.request(`/zones/${query}`);
  },
  
  async createZone(data) {
    return this.request('/zones/', { method: 'POST', body: JSON.stringify(data) });
  },
};

// Alert Component
const Alert = ({ type = 'error', message, onClose }) => {
  const bgColor = type === 'error' ? 'bg-red-50 border-red-200' : 'bg-green-50 border-green-200';
  const textColor = type === 'error' ? 'text-red-800' : 'text-green-800';
  
  return (
    <div className={`${bgColor} border ${textColor} px-4 py-3 rounded-lg mb-4 flex items-center justify-between`}>
      <div className="flex items-center space-x-2">
        <AlertCircle size={18} />
        <span>{message}</span>
      </div>
      {onClose && (
        <button onClick={onClose} className="ml-4">
          <X size={20} />
        </button>
      )}
    </div>
  );
};

// Login Component
const Login = ({ onLogin }) => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  
  const handleSubmit = async () => {
    if (!username || !password) {
      setError('Please enter username and password');
      return;
    }
    
    setLoading(true);
    setError('');
    
    try {
      await api.login(username, password);
      onLogin();
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };
  
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center p-4">
      <div className="bg-white rounded-lg shadow-xl p-8 w-full max-w-md">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900">IoT Dashboard</h1>
          <p className="text-gray-600 mt-2">Greenhouse Management Platform</p>
        </div>
        
        {error && <Alert type="error" message={error} onClose={() => setError('')} />}
        
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleSubmit()}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              placeholder="Enter your email"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleSubmit()}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              placeholder="Enter password"
            />
          </div>
          
          <button
            onClick={handleSubmit}
            disabled={loading}
            className="w-full bg-blue-600 text-white py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50"
          >
            {loading ? 'Logging in...' : 'Login'}
          </button>
        </div>
      </div>
    </div>
  );
};

// Sidebar
const Sidebar = ({ currentPage, setCurrentPage, isMobileOpen, setIsMobileOpen, onLogout }) => {
  const currentUser = api.getCurrentUser();
  
  const menuItems = [
    { id: 'dashboard', label: 'Dashboard', icon: Home },
    { id: 'companies', label: 'Companies', icon: Building2 },
    { id: 'users', label: 'Users & Roles', icon: Users },
    { id: 'devices', label: 'Devices', icon: Cpu },
    { id: 'zones', label: 'Zones', icon: Layers }
  ];

  return (
    <>
      {isMobileOpen && (
        <div className="fixed inset-0 bg-black bg-opacity-50 z-40 lg:hidden" onClick={() => setIsMobileOpen(false)} />
      )}
      
      <div className={`fixed lg:static inset-y-0 left-0 z-50 w-64 bg-gray-900 text-white transform transition-transform duration-300 ${isMobileOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}`}>
        <div className="flex items-center justify-between p-4 border-b border-gray-800">
          <div>
            <h1 className="text-xl font-bold">IoT Admin</h1>
            {currentUser && (
              <span className={`text-xs px-2 py-1 rounded mt-1 inline-block ${
                currentUser.role === 'admin' ? 'bg-purple-600' : 
                currentUser.role === 'manager' ? 'bg-blue-600' : 'bg-gray-600'
              }`}>
                {currentUser.role?.toUpperCase()}
              </span>
            )}
          </div>
          <button onClick={() => setIsMobileOpen(false)} className="lg:hidden">
            <X size={24} />
          </button>
        </div>
        
        <nav className="p-4 space-y-2">
          {menuItems.map(item => {
            const Icon = item.icon;
            return (
              <button
                key={item.id}
                onClick={() => { setCurrentPage(item.id); setIsMobileOpen(false); }}
                className={`w-full flex items-center space-x-3 px-4 py-3 rounded-lg transition-colors ${
                  currentPage === item.id ? 'bg-blue-600 text-white' : 'text-gray-300 hover:bg-gray-800'
                }`}
              >
                <Icon size={20} />
                <span>{item.label}</span>
              </button>
            );
          })}
          
          <button
            onClick={onLogout}
            className="w-full flex items-center space-x-3 px-4 py-3 rounded-lg text-gray-300 hover:bg-red-600 hover:text-white transition-colors mt-4"
          >
            <LogOut size={20} />
            <span>Logout</span>
          </button>
        </nav>
      </div>
    </>
  );
};

// Dashboard Page
const Dashboard = ({ setCurrentPage }) => {
  const [stats, setStats] = useState({ companies: 0, users: 0, devices: 0, zones: 0 });
  const [loading, setLoading] = useState(true);
  const currentUser = api.getCurrentUser();

  useEffect(() => {
    loadStats();
  }, []);

  const loadStats = async () => {
    try {
      const [companies, users, devices, zones] = await Promise.all([
        api.getCompanies(),
        api.getUsers(),
        api.getDevices(),
        api.getZones()
      ]);
      
      setStats({
        companies: companies.length,
        users: users.length,
        devices: devices.length,
        zones: zones.length
      });
    } catch (error) {
      console.error('Failed to load stats:', error);
    } finally {
      setLoading(false);
    }
  };

  const statCards = [
    { label: 'Companies', value: stats.companies, icon: Building2, color: 'bg-blue-500', page: 'companies' },
    { label: 'Users', value: stats.users, icon: Users, color: 'bg-green-500', page: 'users' },
    { label: 'Devices', value: stats.devices, icon: Cpu, color: 'bg-purple-500', page: 'devices' },
    { label: 'Zones', value: stats.zones, icon: Layers, color: 'bg-orange-500', page: 'zones' }
  ];

  if (loading) return <div className="text-center py-12">Loading...</div>;

  return (
    <div>
      <div className="mb-6">
        <h2 className="text-2xl font-bold">Dashboard Overview</h2>
        <p className="text-gray-600 text-sm mt-1">
          Welcome, {currentUser?.name} ({currentUser?.role})
        </p>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {statCards.map((stat, index) => {
          const Icon = stat.icon;
          return (
            <div 
              key={index} 
              onClick={() => setCurrentPage(stat.page)}
              className="bg-white rounded-lg shadow p-6 cursor-pointer hover:shadow-xl transform hover:scale-105 transition-all duration-200"
            >
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-gray-500 text-sm">{stat.label}</p>
                  <p className="text-3xl font-bold mt-2">{stat.value}</p>
                </div>
                <div className={`${stat.color} p-3 rounded-lg`}>
                  <Icon className="text-white" size={24} />
                </div>
              </div>
              <div className="flex items-center justify-end mt-3 text-blue-600">
                <span className="text-xs mr-1 font-medium">View all</span>
                <ArrowRight size={16} />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

// ENHANCED Companies Page
const CompaniesPage = () => {
  const [companies, setCompanies] = useState([]);
  const [expandedCompany, setExpandedCompany] = useState(null);
  const [companyDetails, setCompanyDetails] = useState({});
  const [loadingDetails, setLoadingDetails] = useState({});
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [formData, setFormData] = useState({ name: '', code: '' });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  
  const isAdmin = api.isAdmin();

  useEffect(() => { loadCompanies(); }, []);

  const loadCompanies = async () => {
    try {
      const data = await api.getCompanies();
      setCompanies(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const toggleCompany = async (companyId) => {
    if (expandedCompany === companyId) {
      setExpandedCompany(null);
      return;
    }

    setExpandedCompany(companyId);

    if (!companyDetails[companyId]) {
      setLoadingDetails(prev => ({ ...prev, [companyId]: true }));
      
      try {
        const [users, devices] = await Promise.all([
          api.getCompanyUsers(companyId),
          api.getCompanyDevices(companyId)
        ]);

        setCompanyDetails(prev => ({
          ...prev,
          [companyId]: { users, devices }
        }));
      } catch (error) {
        console.error('Failed to load company details:', error);
        setError('Failed to load company details');
      } finally {
        setLoadingDetails(prev => ({ ...prev, [companyId]: false }));
      }
    }
  };

  const handleSubmit = async () => {
    if (!formData.name || !formData.code) {
      setError('Please fill in all fields');
      return;
    }
    
    try {
      if (editingId) {
        await api.updateCompany(editingId, formData);
        setSuccess('Company updated successfully');
      } else {
        await api.createCompany(formData);
        setSuccess('Company created successfully');
      }
      
      await loadCompanies();
      setShowForm(false);
      setFormData({ name: '', code: '' });
      setEditingId(null);
    } catch (err) {
      setError(err.message);
    }
  };

  const handleEdit = (company) => {
    setEditingId(company.id);
    setFormData({ name: company.name, code: company.code });
    setShowForm(true);
    setError('');
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Delete this company?')) return;
    try {
      await api.deleteCompany(id);
      setSuccess('Company deleted');
      await loadCompanies();
    } catch (err) {
      setError(err.message);
    }
  };

  if (loading) return <div className="text-center py-12">Loading...</div>;

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <div>
          <h2 className="text-2xl font-bold">Companies Management</h2>
          <p className="text-sm text-gray-600 mt-1">Click on a company to view users and devices</p>
        </div>
        {isAdmin && (
          <button
            onClick={() => { setShowForm(true); setEditingId(null); setFormData({ name: '', code: '' }); setError(''); }}
            className="bg-blue-600 text-white px-4 py-2 rounded-lg flex items-center space-x-2 hover:bg-blue-700"
          >
            <Plus size={20} />
            <span>Add Company</span>
          </button>
        )}
      </div>

      {error && <Alert type="error" message={error} onClose={() => setError('')} />}
      {success && <Alert type="success" message={success} onClose={() => setSuccess('')} />}

      {showForm && isAdmin && (
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <h3 className="text-lg font-semibold mb-4">{editingId ? 'Edit Company' : 'Add Company'}</h3>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Company Name *</label>
              <input
                type="text"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                placeholder="e.g., Greenhouse Corp"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Company Code *</label>
              <input
                type="text"
                value={formData.code}
                onChange={(e) => setFormData({ ...formData, code: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                placeholder="e.g., GH001"
              />
            </div>
            <div className="flex space-x-3">
              <button onClick={handleSubmit} className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 flex items-center space-x-2">
                <Save size={18} />
                <span>Save</span>
              </button>
              <button
                onClick={() => { setShowForm(false); setEditingId(null); setError(''); }}
                className="bg-gray-200 text-gray-700 px-4 py-2 rounded-lg hover:bg-gray-300 flex items-center space-x-2"
              >
                <XCircle size={18} />
                <span>Cancel</span>
              </button>
            </div>
          </div>
        </div>
      )}

      <div className="space-y-4">
        {companies.length === 0 ? (
          <div className="bg-white rounded-lg shadow p-8 text-center text-gray-500">No companies found</div>
        ) : (
          companies.map((company) => (
            <div key={company.id} className="bg-white rounded-lg shadow overflow-hidden">
              <div
                onClick={() => toggleCompany(company.id)}
                className="flex items-center justify-between p-6 cursor-pointer hover:bg-gray-50 transition-colors"
              >
                <div className="flex-1">
                  <h3 className="text-lg font-semibold text-gray-900">{company.name}</h3>
                  <p className="text-sm text-gray-500 mt-1">Created {new Date(company.created_at).toLocaleDateString()}</p>
                </div>
                <div className="flex items-center space-x-4">
                  {companyDetails[company.id] && (
                    <div className="flex items-center space-x-3 mr-4">
                      <span className="text-sm bg-blue-100 text-blue-800 px-3 py-1 rounded-full">
                        👥 {companyDetails[company.id].users.length} users
                      </span>
                      <span className="text-sm bg-purple-100 text-purple-800 px-3 py-1 rounded-full">
                        📱 {companyDetails[company.id].devices.length} devices
                      </span>
                    </div>
                  )}
                  {isAdmin && (
                    <div className="flex items-center space-x-2" onClick={(e) => e.stopPropagation()}>
                      <button onClick={() => handleEdit(company)} className="text-blue-600 hover:text-blue-800">
                        <Edit2 size={18} />
                      </button>
                      <button onClick={() => handleDelete(company.id)} className="text-red-600 hover:text-red-800">
                        <Trash2 size={18} />
                      </button>
                    </div>
                  )}
                  {expandedCompany === company.id ? <ChevronDown size={20} /> : <ChevronRight size={20} />}
                </div>
              </div>

              {expandedCompany === company.id && (
                <div className="border-t bg-gray-50 p-6">
                  {loadingDetails[company.id] ? (
                    <div className="text-center py-8 text-gray-500">Loading details...</div>
                  ) : companyDetails[company.id] ? (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      <div className="bg-white rounded-lg p-4">
                        <h4 className="font-semibold text-gray-900 mb-3 flex items-center">
                          <Users size={18} className="mr-2" />
                          Users ({companyDetails[company.id].users.length})
                        </h4>
                        <div className="space-y-2">
                          {companyDetails[company.id].users.map(user => (
                            <div key={user.id} className="flex items-center justify-between p-2 bg-gray-50 rounded">
                              <div>
                                <p className="font-medium text-sm">{user.full_name || user.email}</p>
                                <p className="text-xs text-gray-500">{user.email}</p>
                              </div>
                              <span className={`text-xs px-2 py-1 rounded-full ${
                                user.role === 'admin' ? 'bg-purple-100 text-purple-800' :
                                user.role === 'manager' ? 'bg-blue-100 text-blue-800' :
                                'bg-gray-100 text-gray-800'
                              }`}>
                                {user.role}
                              </span>
                            </div>
                          ))}
                          {companyDetails[company.id].users.length === 0 && (
                            <p className="text-sm text-gray-500 text-center py-4">No users yet</p>
                          )}
                        </div>
                      </div>

                      <div className="bg-white rounded-lg p-4">
                        <h4 className="font-semibold text-gray-900 mb-3 flex items-center">
                          <Cpu size={18} className="mr-2" />
                          Devices ({companyDetails[company.id].devices.length})
                        </h4>
                        <div className="space-y-2">
                          {companyDetails[company.id].devices.map(device => (
                            <div key={device.id} className="flex items-center justify-between p-2 bg-gray-50 rounded">
                              <div>
                                <p className="font-medium text-sm">{device.name}</p>
                                <p className="text-xs text-gray-500">#{device.device_number}</p>
                              </div>
                              <span className={`text-xs px-2 py-1 rounded-full ${
                                device.is_online ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
                              }`}>
                                {device.is_online ? '🟢 Online' : '⚫ Offline'}
                              </span>
                            </div>
                          ))}
                          {companyDetails[company.id].devices.length === 0 && (
                            <p className="text-sm text-gray-500 text-center py-4">No devices yet</p>
                          )}
                        </div>
                      </div>
                    </div>
                  ) : null}
                </div>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  );
};

// ENHANCED Users Page
const UsersPage = () => {
  const [users, setUsers] = useState([]);
  const [companies, setCompanies] = useState([]);
  const [expandedUser, setExpandedUser] = useState(null);
  const [userDevices, setUserDevices] = useState({});
  const [loadingDevices, setLoadingDevices] = useState({});
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [formData, setFormData] = useState({ name: '', email: '', password: '', company_id: '', role: 'user', is_active: true });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  
  const isManager = api.isManager();
  const currentUser = api.getCurrentUser();

  const roles = [
    { value: 'admin', label: 'Admin', description: 'Full system access' },
    { value: 'manager', label: 'Manager', description: 'Company-level management' },
    { value: 'user', label: 'User', description: 'Basic access' }
  ];

  useEffect(() => { loadData(); }, []);

  const loadData = async () => {
    try {
      const [usersData, companiesData] = await Promise.all([api.getUsers(), api.getCompanies()]);
      setUsers(usersData);
      setCompanies(companiesData);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const toggleUser = async (userId) => {
    if (expandedUser === userId) {
      setExpandedUser(null);
      return;
    }

    setExpandedUser(userId);

    if (!userDevices[userId]) {
      setLoadingDevices(prev => ({ ...prev, [userId]: true }));
      
      try {
        const devices = await api.getUserDevices(userId);
        setUserDevices(prev => ({ ...prev, [userId]: devices }));
      } catch (error) {
        console.error('Failed to load user devices:', error);
      } finally {
        setLoadingDevices(prev => ({ ...prev, [userId]: false }));
      }
    }
  };

  const handleSubmit = async () => {
    if (!formData.name || !formData.email || !formData.company_id || (!editingId && !formData.password)) {
      setError('Please fill in all required fields');
      return;
    }
    
    try {
      const payload = { ...formData };
      if (editingId && !payload.password) delete payload.password;
      
      if (editingId) {
        await api.updateUser(editingId, payload);
        setSuccess('User updated');
      } else {
        await api.createUser(payload);
        setSuccess('User created');
      }
      
      await loadData();
      setShowForm(false);
      setFormData({ name: '', email: '', password: '', company_id: '', role: 'user', is_active: true });
      setEditingId(null);
    } catch (err) {
      setError(err.message);
    }
  };

  const handleEdit = (user) => {
    setEditingId(user.id);
    setFormData({ 
      name: user.name, 
      email: user.email, 
      password: '', 
      company_id: user.company_id, 
      role: user.role || 'user',
      is_active: user.is_active 
    });
    setShowForm(true);
    setError('');
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Delete this user?')) return;
    try {
      await api.deleteUser(id);
      setSuccess('User deleted');
      await loadData();
    } catch (err) {
      setError(err.message);
    }
  };

  if (loading) return <div className="text-center py-12">Loading...</div>;

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <div>
          <h2 className="text-2xl font-bold">Users & Roles Management</h2>
          <p className="text-gray-600 text-sm mt-1">Click on a user to view their accessible devices</p>
        </div>
        {isManager && (
          <button
            onClick={() => { setShowForm(true); setEditingId(null); setFormData({ name: '', email: '', password: '', company_id: currentUser?.company_id || '', role: 'user', is_active: true }); setError(''); }}
            className="bg-blue-600 text-white px-4 py-2 rounded-lg flex items-center space-x-2 hover:bg-blue-700"
          >
            <Plus size={20} />
            <span>Add User</span>
          </button>
        )}
      </div>

      {error && <Alert type="error" message={error} onClose={() => setError('')} />}
      {success && <Alert type="success" message={success} onClose={() => setSuccess('')} />}

      {showForm && isManager && (
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <h3 className="text-lg font-semibold mb-4">{editingId ? 'Edit User' : 'Add User'}</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Name *</label>
              <input type="text" value={formData.name} onChange={(e) => setFormData({ ...formData, name: e.target.value })} className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500" placeholder="John Doe" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Email *</label>
              <input type="email" value={formData.email} onChange={(e) => setFormData({ ...formData, email: e.target.value })} className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500" placeholder="john@example.com" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Password {!editingId && '*'}</label>
              <input type="password" value={formData.password} onChange={(e) => setFormData({ ...formData, password: e.target.value })} className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500" placeholder={editingId ? 'Leave blank to keep current' : 'Enter password'} />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Company *</label>
              <select value={formData.company_id} onChange={(e) => setFormData({ ...formData, company_id: e.target.value })} className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500" disabled={currentUser?.role === 'manager'}>
                <option value="">Select Company</option>
                {companies.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Role *</label>
              <select value={formData.role} onChange={(e) => setFormData({ ...formData, role: e.target.value })} className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500">
                {roles.filter(r => currentUser?.role === 'admin' || r.value !== 'admin').map(r => (
                  <option key={r.value} value={r.value}>{r.label} - {r.description}</option>
                ))}
              </select>
            </div>
            <div className="flex items-center">
              <input type="checkbox" id="is_active" checked={formData.is_active} onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })} className="h-4 w-4 text-blue-600 rounded" />
              <label htmlFor="is_active" className="ml-2 text-sm text-gray-700">Active User</label>
            </div>
            <div className="md:col-span-2 flex space-x-3">
              <button onClick={handleSubmit} className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 flex items-center space-x-2">
                <Save size={18} />
                <span>Save User</span>
              </button>
              <button onClick={() => { setShowForm(false); setEditingId(null); setError(''); }} className="bg-gray-200 text-gray-700 px-4 py-2 rounded-lg hover:bg-gray-300 flex items-center space-x-2">
                <XCircle size={18} />
                <span>Cancel</span>
              </button>
            </div>
          </div>
        </div>
      )}

      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
        <div className="flex items-start space-x-3">
          <Shield className="text-blue-600 mt-1" size={20} />
          <div>
            <h4 className="font-semibold text-blue-900">Role-Based Access Control</h4>
            <div className="mt-2 space-y-1 text-sm text-blue-800">
              <p><strong>Admin:</strong> Full access - manage all companies, users, devices, zones</p>
              <p><strong>Manager:</strong> Company access - manage users, devices, zones in their company</p>
              <p><strong>User:</strong> View access - view and control devices/zones in their company</p>
            </div>
          </div>
        </div>
      </div>

      <div className="space-y-4">
        {users.length === 0 ? (
          <div className="bg-white rounded-lg shadow p-8 text-center text-gray-500">No users found</div>
        ) : (
          users.map((user) => (
            <div key={user.id} className="bg-white rounded-lg shadow overflow-hidden">
              <div
                onClick={() => toggleUser(user.id)}
                className="flex items-center justify-between p-6 cursor-pointer hover:bg-gray-50 transition-colors"
              >
                <div className="flex-1">
                  <h3 className="text-lg font-semibold text-gray-900">{user.name}</h3>
                  <p className="text-sm text-gray-500 mt-1">{user.email}</p>
                  <div className="flex items-center space-x-2 mt-2">
                    <span className={`text-xs px-2 py-1 rounded-full ${
                      (user.role || 'user') === 'admin' ? 'bg-purple-100 text-purple-800' : 
                      (user.role || 'user') === 'manager' ? 'bg-blue-100 text-blue-800' : 
                      'bg-gray-100 text-gray-800'
                    }`}>
                      {(user.role || 'user').toUpperCase()}
                    </span>
                    <span className={`text-xs px-2 py-1 rounded-full ${user.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
                      {user.is_active ? 'Active' : 'Inactive'}
                    </span>
                    <span className="text-xs text-gray-500">
                      {companies.find(c => c.id === user.company_id)?.name || 'N/A'}
                    </span>
                  </div>
                </div>
                <div className="flex items-center space-x-4">
                  {userDevices[user.id] && (
                    <span className="text-sm bg-purple-100 text-purple-800 px-3 py-1 rounded-full">
                      📱 {userDevices[user.id].length} devices
                    </span>
                  )}
                  {isManager && (
                    <div className="flex items-center space-x-2" onClick={(e) => e.stopPropagation()}>
                      <button onClick={() => handleEdit(user)} className="text-blue-600 hover:text-blue-800">
                        <Edit2 size={18} />
                      </button>
                      <button onClick={() => handleDelete(user.id)} className="text-red-600 hover:text-red-800">
                        <Trash2 size={18} />
                      </button>
                    </div>
                  )}
                  {expandedUser === user.id ? <ChevronDown size={20} /> : <ChevronRight size={20} />}
                </div>
              </div>

              {expandedUser === user.id && (
                <div className="border-t bg-gray-50 p-6">
                  {loadingDevices[user.id] ? (
                    <div className="text-center py-8 text-gray-500">Loading devices...</div>
                  ) : userDevices[user.id] ? (
                    <div className="bg-white rounded-lg p-4">
                      <h4 className="font-semibold text-gray-900 mb-3 flex items-center">
                        <Cpu size={18} className="mr-2" />
                        Accessible Devices ({userDevices[user.id].length})
                      </h4>
                      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                        {userDevices[user.id].map(device => (
                          <div key={device.id} className="flex items-center justify-between p-3 bg-gray-50 rounded border">
                            <div>
                              <p className="font-medium text-sm">{device.name}</p>
                              <p className="text-xs text-gray-500">#{device.device_number}</p>
                            </div>
                            <span className={`text-xs px-2 py-1 rounded-full ${
                              device.is_online ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
                            }`}>
                              {device.is_online ? '🟢' : '⚫'}
                            </span>
                          </div>
                        ))}
                      </div>
                      {userDevices[user.id].length === 0 && (
                        <p className="text-sm text-gray-500 text-center py-4">No devices accessible</p>
                      )}
                    </div>
                  ) : null}
                </div>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  );
};

// Keep existing ZonesPage and DevicesPage unchanged...
const ZonesPage = () => {
  const [zones, setZones] = useState([]);
  const [devices, setDevices] = useState([]);
  const [showForm, setShowForm] = useState(false);
  const [formData, setFormData] = useState({ name: '', topic_name: '', description: '', device_id: '' });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  
  const isManager = api.isManager();

  useEffect(() => { loadData(); }, []);

  const loadData = async () => {
    try {
      const [zonesData, devicesData] = await Promise.all([api.getZones(), api.getDevices()]);
      setZones(zonesData);
      setDevices(devicesData);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async () => {
    if (!formData.name || !formData.topic_name || !formData.device_id) {
      setError('Please fill in all required fields');
      return;
    }
    
    try {
      await api.createZone(formData);
      setSuccess('Zone created successfully');
      await loadData();
      setShowForm(false);
      setFormData({ name: '', topic_name: '', description: '', device_id: '' });
    } catch (err) {
      setError(err.message);
    }
  };

  if (loading) return <div className="text-center py-12">Loading...</div>;

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <div>
          <h2 className="text-2xl font-bold">Zones Management</h2>
          <p className="text-gray-600 text-sm mt-1">Monitor and control zones in your company's devices</p>
        </div>
        {isManager && (
          <button onClick={() => { setShowForm(true); setFormData({ name: '', topic_name: '', description: '', device_id: '' }); setError(''); }} className="bg-blue-600 text-white px-4 py-2 rounded-lg flex items-center space-x-2 hover:bg-blue-700">
            <Plus size={20} />
            <span>Add Zone</span>
          </button>
        )}
      </div>

      {error && <Alert type="error" message={error} onClose={() => setError('')} />}
      {success && <Alert type="success" message={success} onClose={() => setSuccess('')} />}

      {showForm && isManager && (
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <h3 className="text-lg font-semibold mb-4">Add New Zone</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Zone Name *</label>
              <input type="text" value={formData.name} onChange={(e) => setFormData({ ...formData, name: e.target.value })} className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500" placeholder="e.g., Greenhouse Zone 1" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">MQTT Topic *</label>
              <input type="text" value={formData.topic_name} onChange={(e) => setFormData({ ...formData, topic_name: e.target.value })} className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500" placeholder="e.g., greenhouse/zone1" />
            </div>
            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-gray-700 mb-1">Device *</label>
              <select value={formData.device_id} onChange={(e) => setFormData({ ...formData, device_id: e.target.value })} className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500">
                <option value="">Select Device</option>
                {devices.map(d => <option key={d.id} value={d.id}>{d.name} ({d.device_number})</option>)}
              </select>
            </div>
            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
              <textarea value={formData.description} onChange={(e) => setFormData({ ...formData, description: e.target.value })} className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500" rows="3" placeholder="Optional description" />
            </div>
            <div className="md:col-span-2 flex space-x-3">
              <button onClick={handleSubmit} className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 flex items-center space-x-2">
                <Save size={18} />
                <span>Save Zone</span>
              </button>
              <button onClick={() => { setShowForm(false); setError(''); }} className="bg-gray-200 text-gray-700 px-4 py-2 rounded-lg hover:bg-gray-300 flex items-center space-x-2">
                <XCircle size={18} />
                <span>Cancel</span>
              </button>
            </div>
          </div>
        </div>
      )}

      <div className="bg-white rounded-lg shadow overflow-x-auto">
        <table className="w-full">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Zone Name</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Device</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">MQTT Topic</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Description</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {zones.length === 0 ? (
              <tr><td colSpan="4" className="px-6 py-8 text-center text-gray-500">No zones found</td></tr>
            ) : (
              zones.map((zone) => (
                <tr key={zone.id}>
                  <td className="px-6 py-4 font-medium">{zone.name}</td>
                  <td className="px-6 py-4 text-gray-500">{devices.find(d => d.id === zone.device_id)?.name || 'N/A'}</td>
                  <td className="px-6 py-4 text-gray-500 font-mono text-sm">{zone.topic_name}</td>
                  <td className="px-6 py-4 text-gray-500 text-sm">{zone.description || '-'}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};

const DevicesPage = () => {
  const [devices, setDevices] = useState([]);
  const [users, setUsers] = useState([]);
  const [companies, setCompanies] = useState([]);
  const [showForm, setShowForm] = useState(false);
  const [showAssignModal, setShowAssignModal] = useState(false);
  const [selectedDevice, setSelectedDevice] = useState(null);
  const [assignments, setAssignments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [formData, setFormData] = useState({ device_number: '', name: '', description: '' });
  const isManager = api.isManager();

  useEffect(() => { 
    loadDevices();
    if (isManager) {
      loadUsers();
      loadCompanies();
    }
  }, []);

  const loadDevices = async () => {
    try {
      const data = await api.getDevices();
      setDevices(data);
    } catch (error) {
      console.error('Failed to load devices:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadUsers = async () => {
    try {
      const data = await api.getUsers();
      setUsers(data);
    } catch (error) {
      console.error('Failed to load users:', error);
    }
  };
  
  const loadCompanies = async () => {
    try {
      const data = await api.getCompanies();
      setCompanies(data);
    } catch (error) {
      console.error('Failed to load companies:', error);
    }
  };

  const getCompanyName = (companyId) => {
    const company = companies.find(c => c.id === companyId);
    return company ? company.name : 'Unknown';
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await api.createDevice(formData);
      setShowForm(false);
      setFormData({ device_number: '', name: '', description: '' });
      loadDevices();
    } catch (error) {
      alert('Failed to create device: ' + error.message);
    }
  };

  const openAssignModal = async (device) => {
    setSelectedDevice(device);
    try {
      const data = await api.getDeviceAssignments(device.id);
      setAssignments(data);
      setShowAssignModal(true);
    } catch (error) {
      alert('Failed to load assignments: ' + error.message);
    }
  };

  const handleAssign = async (userId, accessLevel) => {
    try {
      await api.assignDevice(selectedDevice.id, userId, accessLevel);
      const data = await api.getDeviceAssignments(selectedDevice.id);
      setAssignments(data);
    } catch (error) {
      alert('Failed to assign device: ' + error.message);
    }
  };

  const handleUnassign = async (userId) => {
    try {
      await api.unassignDevice(selectedDevice.id, userId);
      const data = await api.getDeviceAssignments(selectedDevice.id);
      setAssignments(data);
    } catch (error) {
      alert('Failed to unassign device: ' + error.message);
    }
  };

  const isUserAssigned = (userId) => {
    return assignments.find(a => a.user_id === userId);
  };

  const getUserAccessLevel = (userId) => {
    const assignment = assignments.find(a => a.user_id === userId);
    return assignment ? assignment.access_level : 'read';
  };

  if (loading) return <div className="text-center py-12">Loading...</div>;

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <div>
          <h2 className="text-2xl font-bold">Devices Management</h2>
          <p className="text-gray-600 text-sm mt-1">View and manage devices in your company</p>
        </div>
        {isManager && (
          <button onClick={() => setShowForm(true)} className="bg-blue-600 text-white px-4 py-2 rounded-lg flex items-center space-x-2 hover:bg-blue-700">
            <Plus size={20} />
            <span>Add Device</span>
          </button>
        )}
      </div>

      {showForm && isManager && (
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-lg font-semibold">Add New Device</h3>
            <button onClick={() => setShowForm(false)} className="text-gray-400 hover:text-gray-600">
              <XCircle size={24} />
            </button>
          </div>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Device Number *</label>
              <input
                type="text"
                required
                value={formData.device_number}
                onChange={(e) => setFormData({ ...formData, device_number: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                placeholder="e.g., DEV001"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Device Name *</label>
              <input
                type="text"
                required
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                placeholder="e.g., Greenhouse Sensor 1"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
              <textarea
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                rows="3"
                placeholder="Optional description"
              />
            </div>
            <div className="flex space-x-3">
              <button type="submit" className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 flex items-center space-x-2">
                <Save size={20} />
                <span>Create Device</span>
              </button>
              <button type="button" onClick={() => setShowForm(false)} className="bg-gray-200 text-gray-700 px-4 py-2 rounded-lg hover:bg-gray-300">
                Cancel
              </button>
            </div>
          </form>
        </div>
      )}

      {showAssignModal && selectedDevice && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[90vh] overflow-hidden">
            <div className="p-6 border-b flex justify-between items-center">
              <div>
                <h3 className="text-xl font-bold">Manage Device Access</h3>
                <p className="text-sm text-gray-600 mt-1">Device: {selectedDevice.name} ({selectedDevice.device_number})</p>
              </div>
              <button onClick={() => setShowAssignModal(false)} className="text-gray-400 hover:text-gray-600">
                <XCircle size={24} />
              </button>
            </div>
            
            <div className="p-6 overflow-y-auto max-h-[calc(90vh-140px)]">
              <div className="mb-4">
                <h4 className="font-semibold text-gray-700 mb-2">
                  Assigned Users ({assignments.length})
                </h4>
              </div>

              <div className="space-y-3">
                {users.filter(u => u.company_id === selectedDevice.company_id).map((user) => {
                  const assigned = isUserAssigned(user.id);
                  const accessLevel = getUserAccessLevel(user.id);
                  
                  return (
                    <div key={user.id} className="flex items-center justify-between p-3 border rounded-lg hover:bg-gray-50">
                      <div className="flex items-center space-x-3">
                        <div className={`w-10 h-10 rounded-full flex items-center justify-center ${assigned ? 'bg-green-100' : 'bg-gray-100'}`}>
                          <Users size={20} className={assigned ? 'text-green-600' : 'text-gray-400'} />
                        </div>
                        <div>
                          <div className="font-medium">{user.name}</div>
                          <div className="text-sm text-gray-500">{user.email}</div>
                          {assigned && (
                            <span className="text-xs bg-green-100 text-green-800 px-2 py-0.5 rounded mt-1 inline-block">
                              {accessLevel.toUpperCase()}
                            </span>
                          )}
                        </div>
                      </div>
                      
                      <div className="flex items-center space-x-2">
                        {!assigned ? (
                          <select
                            onChange={(e) => handleAssign(user.id, e.target.value)}
                            className="px-3 py-1.5 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500"
                            defaultValue=""
                          >
                            <option value="" disabled>Assign Access</option>
                            <option value="read">Read</option>
                            <option value="write">Write</option>
                            <option value="control">Control</option>
                          </select>
                        ) : (
                          <>
                            <select
                              value={accessLevel}
                              onChange={(e) => handleAssign(user.id, e.target.value)}
                              className="px-3 py-1.5 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500"
                            >
                              <option value="read">Read</option>
                              <option value="write">Write</option>
                              <option value="control">Control</option>
                            </select>
                            <button
                              onClick={() => handleUnassign(user.id)}
                              className="p-1.5 text-red-600 hover:bg-red-50 rounded"
                              title="Remove access"
                            >
                              <Trash2 size={18} />
                            </button>
                          </>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>

              {users.length === 0 && (
                <div className="text-center py-8 text-gray-500">
                  No users found in this company
                </div>
              )}
            </div>

            <div className="p-6 border-t bg-gray-50">
              <button
                onClick={() => setShowAssignModal(false)}
                className="w-full bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
              >
                Done
              </button>
            </div>
          </div>
        </div>
      )}

      <div className="bg-white rounded-lg shadow overflow-x-auto">
        <table className="w-full">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Device Number</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Name</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Company</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Last Seen</th>
              {isManager && <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Actions</th>}
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {devices.length === 0 ? (
              <tr><td colSpan={isManager ? "6" : "5"} className="px-6 py-8 text-center text-gray-500">No devices found</td></tr>
            ) : (
              devices.map((device) => (
                <tr key={device.id}>
                  <td className="px-6 py-4 font-mono text-sm">{device.device_number}</td>
                  <td className="px-6 py-4 font-medium">{device.name}</td>
                  <td className="px-6 py-4 text-sm text-gray-600">{getCompanyName(device.company_id)}</td>
                  <td className="px-6 py-4">
                    <span className={`px-2 py-1 text-xs font-semibold rounded-full ${device.is_active ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'}`}>
                      {device.is_active ? 'Active' : 'Inactive'}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-gray-500 text-sm">{device.last_seen ? new Date(device.last_seen).toLocaleString() : 'Never'}</td>
                  {isManager && (
                    <td className="px-6 py-4">
                      <button
                        onClick={() => openAssignModal(device)}
                        className="text-blue-600 hover:text-blue-800 flex items-center space-x-1"
                      >
                        <Users size={16} />
                        <span className="text-sm">Manage Access</span>
                      </button>
                    </td>
                  )}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};

// Main App
export default function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [currentPage, setCurrentPage] = useState('dashboard');
  const [isMobileOpen, setIsMobileOpen] = useState(false);

  useEffect(() => {
    if (api.getToken() && api.getCurrentUser()) setIsAuthenticated(true);
  }, []);

  const handleLogin = () => setIsAuthenticated(true);
  const handleLogout = () => { api.clearToken(); setIsAuthenticated(false); setCurrentPage('dashboard'); };

  if (!isAuthenticated) return <Login onLogin={handleLogin} />;

  const renderPage = () => {
    switch (currentPage) {
      case 'dashboard': return <Dashboard setCurrentPage={setCurrentPage} />;
      case 'companies': return <CompaniesPage />;
      case 'users': return <UsersPage />;
      case 'devices': return <DevicesPage />;
      case 'zones': return <ZonesPage />;
      default: return <Dashboard setCurrentPage={setCurrentPage} />;
    }
  };

  return (
    <div className="flex h-screen bg-gray-100">
      <Sidebar currentPage={currentPage} setCurrentPage={setCurrentPage} isMobileOpen={isMobileOpen} setIsMobileOpen={setIsMobileOpen} onLogout={handleLogout} />
      <div className="flex-1 flex flex-col overflow-hidden">
        <header className="bg-white shadow-sm z-10">
          <div className="flex items-center justify-between px-6 py-4">
            <button onClick={() => setIsMobileOpen(true)} className="lg:hidden"><Menu size={24} /></button>
            <h1 className="text-xl font-semibold hidden lg:block">Greenhouse IoT Platform</h1>
            <div className="flex items-center space-x-4">
              <span className="text-sm text-gray-600 hidden sm:block">{api.getCurrentUser()?.name}</span>
              <div className="w-10 h-10 bg-blue-600 rounded-full flex items-center justify-center text-white font-semibold">
                {api.getCurrentUser()?.name?.charAt(0).toUpperCase()}
              </div>
            </div>
          </div>
        </header>
        <main className="flex-1 overflow-y-auto p-6">{renderPage()}</main>
      </div>
    </div>
  );
}