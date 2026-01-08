import { Link } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';
import { Users, FolderOpen, CheckCircle, Settings, ArrowLeft } from 'lucide-react';

const AdminDashboard = () => {
  const { user } = useAuth();

  // Get user info for display
  const userName = user?.full_name || 'Admin';

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center space-x-4">
            <Link to="/dashboard" className="text-gray-600 hover:text-primary-600">
              <ArrowLeft className="h-6 w-6" />
            </Link>
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Admin Panel</h1>
              <p className="text-sm text-gray-600">Welcome, {userName}</p>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-8">
          <h2 className="text-3xl font-bold text-gray-900 mb-2">System Administration</h2>
          <p className="text-gray-600">Manage users, roles, projects, and system settings</p>
        </div>

        {/* Admin Actions */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <Link to="/admin/users" className="card-hover group">
            <div className="text-center">
              <div className="bg-gradient-to-br from-primary-100 to-primary-200 w-20 h-20 rounded-2xl flex items-center justify-center mx-auto mb-6 group-hover:scale-110 transition-transform duration-300 shadow-md">
                <Users className="h-10 w-10 text-primary-700" />
              </div>
              <h3 className="text-xl font-bold mb-3 text-gray-900 group-hover:text-primary-600 transition-colors">User Management</h3>
              <p className="text-gray-600 text-sm leading-relaxed">Create, edit, and manage user accounts</p>
            </div>
          </Link>

          <Link to="/admin/projects" className="card-hover group">
            <div className="text-center">
              <div className="bg-gradient-to-br from-green-100 to-emerald-200 w-20 h-20 rounded-2xl flex items-center justify-center mx-auto mb-6 group-hover:scale-110 transition-transform duration-300 shadow-md">
                <FolderOpen className="h-10 w-10 text-green-700" />
              </div>
              <h3 className="text-xl font-bold mb-3 text-gray-900 group-hover:text-green-600 transition-colors">Project Overview</h3>
              <p className="text-gray-600 text-sm leading-relaxed">View all projects across the system</p>
            </div>
          </Link>

          <Link to="/admin/approvals" className="card-hover group">
            <div className="text-center">
              <div className="bg-gradient-to-br from-orange-100 to-orange-200 w-20 h-20 rounded-2xl flex items-center justify-center mx-auto mb-6 group-hover:scale-110 transition-transform duration-300 shadow-md">
                <CheckCircle className="h-10 w-10 text-orange-700" />
              </div>
              <h3 className="text-xl font-bold mb-3 text-gray-900 group-hover:text-orange-600 transition-colors">Approval Dashboard</h3>
              <p className="text-gray-600 text-sm leading-relaxed">Monitor and manage approval workflow</p>
            </div>
          </Link>

          <Link to="/admin/settings" className="card-hover group">
            <div className="text-center">
              <div className="bg-gradient-to-br from-purple-100 to-purple-200 w-20 h-20 rounded-2xl flex items-center justify-center mx-auto mb-6 group-hover:scale-110 transition-transform duration-300 shadow-md">
                <Settings className="h-10 w-10 text-purple-700" />
              </div>
              <h3 className="text-xl font-bold mb-3 text-gray-900 group-hover:text-purple-600 transition-colors">System Settings</h3>
              <p className="text-gray-600 text-sm leading-relaxed">Configure system-wide settings</p>
            </div>
          </Link>
        </div>

        {/* Statistics */}
        <div className="mt-16">
          <h3 className="text-3xl font-bold text-gray-900 mb-8">System Statistics</h3>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            <div className="card-gradient text-center">
              <p className="text-5xl font-extrabold bg-gradient-to-r from-primary-600 to-accent-purple bg-clip-text text-transparent mb-3">0</p>
              <p className="text-gray-600 font-semibold">Total Users</p>
            </div>
            <div className="card-gradient text-center">
              <p className="text-5xl font-extrabold bg-gradient-to-r from-green-600 to-emerald-600 bg-clip-text text-transparent mb-3">0</p>
              <p className="text-gray-600 font-semibold">Active Projects</p>
            </div>
            <div className="card-gradient text-center">
              <p className="text-5xl font-extrabold bg-gradient-to-r from-orange-600 to-red-600 bg-clip-text text-transparent mb-3">0</p>
              <p className="text-gray-600 font-semibold">Pending Approvals</p>
            </div>
            <div className="card-gradient text-center">
              <p className="text-5xl font-extrabold bg-gradient-to-r from-blue-600 to-cyan-600 bg-clip-text text-transparent mb-3">0</p>
              <p className="text-gray-600 font-semibold">Approved Projects</p>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
};

export default AdminDashboard;
