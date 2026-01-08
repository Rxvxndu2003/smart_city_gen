import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Toaster } from 'react-hot-toast';

// Public pages
import Landing from './pages/public/Landing.tsx';
import Login from './pages/public/Login.tsx';
import Register from './pages/public/Register.tsx';

// Dashboard
import Dashboard from './pages/dashboard/Dashboard.tsx';

// Admin pages
import AdminDashboard from './pages/admin/AdminDashboard.tsx';
import UserManagement from './pages/admin/UserManagement.tsx';
import AdminProjects from './pages/admin/AdminProjects.tsx';
import AdminApprovals from './pages/admin/AdminApprovals.tsx';
import AdminSettings from './pages/admin/AdminSettings.tsx';

// Project pages
import ProjectsList from './pages/projects/ProjectsList.tsx';
import ProjectDetail from './pages/projects/ProjectDetail.tsx';
import CreateProject from './pages/projects/CreateProject.tsx';

// Approval pages
import ApprovalManagement from './pages/approvals/ApprovalManagement.tsx';

// City Generator
import CityGenerator from './pages/city/CityGenerator.tsx';

// Text-to-City Generator
import TextToCityPage from './pages/city/TextToCityPage.tsx';

// House Generator
import HouseGenerator from './pages/house/HouseGenerator.tsx';

// Floor Plan Generator
import FloorPlanGenerator from './pages/floorplan/FloorPlanGenerator.tsx';

// AI Assistant
import AIAssistant from './pages/assistant/AIAssistant.tsx';

// ML Training
import MLTraining from './pages/ml/MLTraining.tsx';

// Guards
import AuthGuard from './guards/AuthGuard.tsx';
import AdminGuard from './guards/AdminGuard.tsx';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
});

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <Router>
        <Routes>
          {/* Public routes */}
          <Route path="/" element={<Landing />} />
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />

          {/* Protected routes */}
          <Route
            path="/dashboard"
            element={
              <AuthGuard>
                <Dashboard />
              </AuthGuard>
            }
          />

          {/* Project routes */}
          <Route
            path="/projects"
            element={
              <AuthGuard>
                <ProjectsList />
              </AuthGuard>
            }
          />
          <Route
            path="/projects/create"
            element={
              <AuthGuard>
                <CreateProject />
              </AuthGuard>
            }
          />
          <Route
            path="/projects/:id"
            element={
              <AuthGuard>
                <ProjectDetail />
              </AuthGuard>
            }
          />

          {/* Approval routes */}
          <Route
            path="/approvals"
            element={
              <AuthGuard>
                <ApprovalManagement />
              </AuthGuard>
            }
          />

          {/* City Generator */}
          <Route
            path="/city-generator"
            element={
              <AuthGuard>
                <CityGenerator />
              </AuthGuard>
            }
          />

          {/* Text-to-City Generator */}
          <Route
            path="/text-to-city"
            element={
              <AuthGuard>
                <TextToCityPage />
              </AuthGuard>
            }
          />

          {/* House Generator */}
          <Route
            path="/house-generator"
            element={
              <AuthGuard>
                <HouseGenerator />
              </AuthGuard>
            }
          />

          {/* Floor Plan Generator */}
          <Route
            path="/floor-plan-generator"
            element={
              <AuthGuard>
                <FloorPlanGenerator />
              </AuthGuard>
            }
          />

          {/* AI Assistant */}
          <Route
            path="/ai-assistant"
            element={
              <AuthGuard>
                <AIAssistant />
              </AuthGuard>
            }
          />

          {/* ML Training */}
          <Route
            path="/ml-training"
            element={
              <AuthGuard>
                <MLTraining />
              </AuthGuard>
            }
          />

          {/* Admin routes */}
          <Route
            path="/admin"
            element={
              <AdminGuard>
                <AdminDashboard />
              </AdminGuard>
            }
          />
          <Route
            path="/admin/users"
            element={
              <AdminGuard>
                <UserManagement />
              </AdminGuard>
            }
          />
          <Route
            path="/admin/projects"
            element={
              <AdminGuard>
                <AdminProjects />
              </AdminGuard>
            }
          />
          <Route
            path="/admin/approvals"
            element={
              <AdminGuard>
                <AdminApprovals />
              </AdminGuard>
            }
          />
          <Route
            path="/admin/settings"
            element={
              <AdminGuard>
                <AdminSettings />
              </AdminGuard>
            }
          />

          {/* Fallback */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Router>
      <Toaster position="top-right" />
    </QueryClientProvider>
  );
}

export default App;
