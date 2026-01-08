import { Link } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';
import { LogOut, Building2, FolderOpen, Users, ClipboardCheck, Bot, Layers, Wand2, Sparkles, TrendingUp } from 'lucide-react';
import NotificationBell from '../../components/NotificationBell';
import AnalyticsDashboard from '../../components/AnalyticsDashboard';

const Dashboard = () => {
  const { user, logout } = useAuth();

  const handleLogout = async () => {
    await logout();
  };

  // Check user roles
  const isAdmin = user?.roles?.some((role) => role.name === 'Admin');
  const isProjectOwner = user?.roles?.some((role) => role.name === 'ProjectOwner');
  const isArchitect = user?.roles?.some((role) => role.name === 'Architect');
  const isEngineer = user?.roles?.some((role) => role.name === 'Engineer');
  const isRegulator = user?.roles?.some((role) => role.name === 'Regulator');

  // Can create projects: Admin, ProjectOwner, or Architect
  const canCreateProject = isAdmin || isProjectOwner || isArchitect;

  // Can review/approve: Admin, Architect, Engineer, or Regulator
  const canReviewProjects = isAdmin || isArchitect || isEngineer || isRegulator;

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 via-blue-50/30 to-purple-50/30">
      {/* Modern Header */}
      <header className="bg-white/80 backdrop-blur-lg shadow-sm sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex justify-between items-center">
          <div className="flex items-center space-x-3">
            <div className="bg-gradient-to-br from-primary-500 to-purple-600 p-2 rounded-xl shadow-lg">
              <Building2 className="h-7 w-7 text-white" />
            </div>
            <h1 className="text-2xl font-bold text-gray-900">
              Smart City Planning
            </h1>
          </div>
          <div className="flex items-center space-x-4">
            <NotificationBell />
            <div className="flex items-center space-x-3 border-l border-gray-300 pl-4">
              <div className="text-right">
                <p className="text-sm font-semibold text-gray-900">{user?.full_name}</p>
                <p className="text-xs text-gray-500">{user?.roles?.map((r) => r.display_name).join(', ')}</p>
              </div>
              <button
                onClick={handleLogout}
                className="btn-icon text-gray-600 hover:text-error"
                title="Logout"
              >
                <LogOut className="h-5 w-5" />
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 animate-fade-in">
        {/* Welcome Section */}
        <div className="mb-10 animate-slide-up">
          <div className="flex items-center gap-2 mb-3">
            <Sparkles className="h-6 w-6 text-primary-500" />
            <h2 className="text-4xl font-extrabold bg-gradient-to-r from-gray-900 to-gray-700 bg-clip-text text-transparent">
              Welcome back, {user?.full_name}!
            </h2>
          </div>
          <p className="text-lg text-gray-600 flex items-center gap-2">
            <TrendingUp className="h-5 w-5 text-success" />
            Ready to build something amazing today?
          </p>
        </div>

        {/* Quick Actions Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 animate-slide-up">
          {/* My Projects */}
          <Link to="/projects" className="card-hover group">
            <div className="flex items-start space-x-4">
              <div className="bg-gradient-to-br from-primary-100 to-primary-200 p-4 rounded-2xl group-hover:scale-110 transition-transform duration-300 shadow-md">
                <FolderOpen className="h-8 w-8 text-primary-700" />
              </div>
              <div className="flex-1">
                <h3 className="text-xl font-bold text-gray-900 mb-1 group-hover:text-primary-600 transition-colors">
                  My Projects
                </h3>
                <p className="text-gray-600 text-sm leading-relaxed">
                  View and manage your urban planning projects
                </p>
              </div>
            </div>
          </Link>

          {/* AI Assistant */}
          <Link to="/ai-assistant" className="card-hover group">
            <div className="flex items-start space-x-4">
              <div className="bg-gradient-to-br from-blue-100 to-indigo-200 p-4 rounded-2xl group-hover:scale-110 transition-transform duration-300 shadow-md">
                <Bot className="h-8 w-8 text-blue-700" />
              </div>
              <div className="flex-1">
                <h3 className="text-xl font-bold text-gray-900 mb-1 group-hover:text-blue-600 transition-colors">
                  AI Assistant
                </h3>
                <p className="text-gray-600 text-sm leading-relaxed">
                  Get AI-powered planning guidance and insights
                </p>
              </div>
            </div>
          </Link>

          {/* Floor Plan AI */}
          <Link to="/floor-plan-generator" className="card-hover group">
            <div className="flex items-start space-x-4">
              <div className="bg-gradient-to-br from-cyan-100 to-blue-200 p-4 rounded-2xl group-hover:scale-110 transition-transform duration-300 shadow-md">
                <Layers className="h-8 w-8 text-cyan-700" />
              </div>
              <div className="flex-1">
                <h3 className="text-xl font-bold text-gray-900 mb-1 group-hover:text-cyan-600 transition-colors">
                  3D Interior Design AI
                </h3>
                <p className="text-gray-600 text-sm leading-relaxed">
                  Convert floor plans to photorealistic 3D interiors
                </p>
              </div>
            </div>
          </Link>

          {/* Text-to-City Generator */}
          <Link to="/text-to-city" className="card-hover group">
            <div className="flex items-start space-x-4">
              <div className="bg-gradient-to-br from-purple-100 to-pink-200 p-4 rounded-2xl group-hover:scale-110 transition-transform duration-300 shadow-md">
                <Wand2 className="h-8 w-8 text-purple-700" />
              </div>
              <div className="flex-1">
                <h3 className="text-xl font-bold text-gray-900 mb-1 group-hover:text-purple-600 transition-colors">
                  Text-to-City AI
                </h3>
                <p className="text-gray-600 text-sm leading-relaxed">
                  Generate complete cities from descriptions
                </p>
              </div>
            </div>
          </Link>

          {/* New Project - Role-based */}
          {canCreateProject && (
            <Link to="/projects/create" className="card-hover group bg-gradient-to-br from-green-50 to-emerald-50 border-2 border-green-200">
              <div className="flex items-start space-x-4">
                <div className="bg-gradient-to-br from-green-100 to-green-200 p-4 rounded-2xl group-hover:scale-110 transition-transform duration-300 shadow-md">
                  <Building2 className="h-8 w-8 text-green-700" />
                </div>
                <div className="flex-1">
                  <h3 className="text-xl font-bold text-gray-900 mb-1 group-hover:text-green-600 transition-colors">
                    New Project
                  </h3>
                  <p className="text-gray-600 text-sm leading-relaxed">
                    Start a new urban planning project
                  </p>
                </div>
              </div>
            </Link>
          )}

          {/* Approvals - Role-based */}
          {canReviewProjects && (
            <Link to="/approvals" className="card-hover group">
              <div className="flex items-start space-x-4">
                <div className="bg-gradient-to-br from-orange-100 to-orange-200 p-4 rounded-2xl group-hover:scale-110 transition-transform duration-300 shadow-md">
                  <ClipboardCheck className="h-8 w-8 text-orange-700" />
                </div>
                <div className="flex-1">
                  <h3 className="text-xl font-bold text-gray-900 mb-1 group-hover:text-orange-600 transition-colors">
                    Approvals
                  </h3>
                  <p className="text-gray-600 text-sm leading-relaxed">
                    Review and approve pending projects
                  </p>
                </div>
              </div>
            </Link>
          )}

          {/* Admin Panel - Admin only */}
          {isAdmin && (
            <Link to="/admin" className="card-hover group bg-gradient-to-br from-purple-50 to-pink-50 border-2 border-purple-200">
              <div className="flex items-start space-x-4">
                <div className="bg-gradient-to-br from-purple-100 to-purple-200 p-4 rounded-2xl group-hover:scale-110 transition-transform duration-300 shadow-md">
                  <Users className="h-8 w-8 text-purple-700" />
                </div>
                <div className="flex-1">
                  <h3 className="text-xl font-bold text-gray-900 mb-1 group-hover:text-purple-600 transition-colors">
                    Admin Panel
                  </h3>
                  <p className="text-gray-600 text-sm leading-relaxed">
                    Manage users and system settings
                  </p>
                </div>
              </div>
            </Link>
          )}
        </div>

        {/* Analytics Section */}
        <div className="mt-16 animate-slide-up">
          <div className="flex items-center gap-3 mb-6">
            <TrendingUp className="h-6 w-6 text-primary-600" />
            <h3 className="text-3xl font-bold text-gray-900">Analytics Overview</h3>
          </div>
          <div className="bg-white/60 backdrop-blur-lg rounded-2xl shadow-lg p-8 border border-gray-100">
            <AnalyticsDashboard />
          </div>
        </div>
      </main>
    </div>
  );
};

export default Dashboard;
