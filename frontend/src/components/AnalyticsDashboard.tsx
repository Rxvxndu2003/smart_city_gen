import { useState, useEffect } from 'react';
import { BarChart, Bar, LineChart, Line, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { TrendingUp, Building2, CheckCircle, AlertTriangle } from 'lucide-react';
import { projectsApi } from '../services/api';

interface AnalyticsData {
  projectsByDistrict: Array<{ district: string; count: number }>;
  projectsByType: Array<{ type: string; count: number; fill: string }>;
  projectsOverTime: Array<{ month: string; projects: number }>;
}

interface Statistics {
  total_projects: number;
  projects_by_status: Record<string, number>;
  projects_by_type: Array<{ type: string; count: number; fill: string }>;
  projects_by_district: Array<{ district: string; count: number }>;
  projects_over_time: Array<{ month: string; projects: number }>;
  compliant_projects: number;
  compliance_rate: number;
  avg_compliance_score: number;
  pending_approvals: number;
}

const AnalyticsDashboard = () => {
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState<AnalyticsData>({
    projectsByDistrict: [],
    projectsByType: [],
    projectsOverTime: [],
  });

  const [stats, setStats] = useState({
    totalProjects: 0,
    compliantProjects: 0,
    pendingApprovals: 0,
    avgComplianceScore: 0,
  });

  useEffect(() => {
    fetchStatistics();
  }, []);

  const fetchStatistics = async () => {
    try {
      console.log('Fetching statistics...');
      const response = await projectsApi.statistics();
      console.log('Full API Response:', response);
      const apiStats: Statistics = response.data;
      
      console.log('API Statistics Data:', apiStats);
      console.log('Total Projects:', apiStats.total_projects);
      console.log('Projects by Status:', apiStats.projects_by_status);
      console.log('Projects by Type:', apiStats.projects_by_type);
      console.log('Projects by District:', apiStats.projects_by_district);
      
      setData({
        projectsByDistrict: apiStats.projects_by_district || [],
        projectsByType: apiStats.projects_by_type || [],
        projectsOverTime: apiStats.projects_over_time || [],
      });
      
      const newStats = {
        totalProjects: apiStats.total_projects || 0,
        compliantProjects: apiStats.compliant_projects || 0,
        pendingApprovals: apiStats.pending_approvals || 0,
        avgComplianceScore: apiStats.avg_compliance_score || 0,
      };
      
      console.log('Setting Stats to:', newStats);
      setStats(newStats);
      
    } catch (error: any) {
      console.error('Failed to fetch statistics:', error);
      console.error('Error response:', error.response?.data);
      console.error('Error status:', error.response?.status);
      console.error('Error detail:', JSON.stringify(error.response?.data?.detail, null, 2));
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center py-12">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Total Projects</p>
              <p className="text-2xl font-bold text-gray-900">{stats.totalProjects}</p>
            </div>
            <div className="bg-blue-100 p-3 rounded-lg">
              <Building2 className="h-6 w-6 text-blue-600" />
            </div>
          </div>
          <div className="mt-2 flex items-center text-sm text-green-600">
            <TrendingUp className="h-4 w-4 mr-1" />
            <span>+12% from last month</span>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Compliant</p>
              <p className="text-2xl font-bold text-gray-900">{stats.compliantProjects}</p>
            </div>
            <div className="bg-green-100 p-3 rounded-lg">
              <CheckCircle className="h-6 w-6 text-green-600" />
            </div>
          </div>
          <div className="mt-2 flex items-center text-sm text-gray-600">
            <span>{((stats.compliantProjects / stats.totalProjects) * 100).toFixed(1)}% compliance rate</span>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Pending Approvals</p>
              <p className="text-2xl font-bold text-gray-900">{stats.pendingApprovals}</p>
            </div>
            <div className="bg-yellow-100 p-3 rounded-lg">
              <AlertTriangle className="h-6 w-6 text-yellow-600" />
            </div>
          </div>
          <div className="mt-2 flex items-center text-sm text-gray-600">
            <span>Requires attention</span>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Avg. Compliance</p>
              <p className="text-2xl font-bold text-gray-900">{stats.avgComplianceScore}%</p>
            </div>
            <div className="bg-purple-100 p-3 rounded-lg">
              <TrendingUp className="h-6 w-6 text-purple-600" />
            </div>
          </div>
          <div className="mt-2 flex items-center text-sm text-green-600">
            <TrendingUp className="h-4 w-4 mr-1" />
            <span>+2% improvement</span>
          </div>
        </div>
      </div>

      {/* Charts Row 1 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Projects by District */}
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Projects by District</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={data.projectsByDistrict}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="district" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar dataKey="count" fill="#3b82f6" name="Projects" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Projects by Type */}
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Projects by Type</h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={data.projectsByType}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={(entry: any) => `${entry.type} ${((entry.percent || 0) * 100).toFixed(0)}%`}
                outerRadius={100}
                fill="#8884d8"
                dataKey="count"
              >
                {data.projectsByType.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.fill} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Projects Over Time */}
      <div className="card">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Projects Over Time</h3>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={data.projectsOverTime}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="month" />
            <YAxis />
            <Tooltip />
            <Legend />
            <Line type="monotone" dataKey="projects" stroke="#3b82f6" name="New Projects" strokeWidth={2} />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

export default AnalyticsDashboard;
