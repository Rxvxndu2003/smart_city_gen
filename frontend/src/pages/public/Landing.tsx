import { Link } from 'react-router-dom';
import { Building2, MapPin, FileCheck, Users, Sparkles, ArrowRight, CheckCircle } from 'lucide-react';

const Landing = () => {
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50">
      {/* Header */}
      <header className="bg-white/80 backdrop-blur-lg shadow-sm sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex justify-between items-center">
          <div className="flex items-center space-x-3 animate-fade-in">
            <div className="bg-gradient-to-br from-primary-500 to-purple-600 p-2 rounded-xl shadow-lg">
              <Building2 className="h-7 w-7 text-white" />
            </div>
            <h1 className="text-2xl font-bold text-gray-900">
              Smart City Planning
            </h1>
          </div>
          <div className="flex items-center space-x-4">
            <Link to="/login" className="text-gray-700 hover:text-primary-600 font-medium transition-colors">
              Login
            </Link>
            <Link to="/register" className="btn-primary flex items-center gap-2">
              Get Started
              <ArrowRight className="h-4 w-4" />
            </Link>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20 animate-slide-up">
        <div className="text-center">
          {/* Badge */}
          <div className="inline-flex items-center gap-2 bg-primary-100 text-primary-700 px-4 py-2 rounded-full text-sm font-semibold mb-8">
            <Sparkles className="h-4 w-4" />
            <span>AI-Powered Urban Development</span>
          </div>

          {/* Main Heading */}
          <h2 className="text-6xl font-extrabold text-gray-900 mb-6 leading-tight">
            Transform Your Urban
            <span className="block mt-2 bg-gradient-to-r from-primary-600 via-purple-600 to-pink-600 bg-clip-text text-transparent">
              Planning Vision
            </span>
          </h2>

          {/* Subheading */}
          <p className="text-xl text-gray-600 mb-10 max-w-3xl mx-auto leading-relaxed">
            Design compliant urban layouts with automated UDA regulation checking,
            stunning 3D visualizations, and streamlined engineer-approved workflows.
          </p>

          {/* CTA Buttons */}
          <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
            <Link to="/register" className="btn-primary text-lg px-8 py-4 flex items-center gap-2 shadow-2xl">
              <Sparkles className="h-5 w-5" />
              Start Planning Now
              <ArrowRight className="h-5 w-5" />
            </Link>
            <Link to="/login" className="btn-secondary text-lg px-8 py-4 flex items-center gap-2">
              Sign In
            </Link>
          </div>

          {/* Trust Indicators */}
          <div className="mt-12 flex flex-wrap items-center justify-center gap-6 text-sm text-gray-600">
            <div className="flex items-center gap-2">
              <CheckCircle className="h-5 w-5 text-success" />
              <span>UDA Compliant</span>
            </div>
            <div className="flex items-center gap-2">
              <CheckCircle className="h-5 w-5 text-success" />
              <span>AI-Enhanced</span>
            </div>
            <div className="flex items-center gap-2">
              <CheckCircle className="h-5 w-5 text-success" />
              <span>3D Visualization</span>
            </div>
          </div>
        </div>

        {/* Features Grid */}
        <div className="mt-32 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
          <div className="card-gradient group cursor-pointer">
            <div className="bg-gradient-to-br from-primary-100 to-primary-200 w-16 h-16 rounded-2xl flex items-center justify-center mx-auto mb-6 group-hover:scale-110 transition-transform duration-300">
              <MapPin className="h-8 w-8 text-primary-700" />
            </div>
            <h3 className="text-xl font-bold mb-3 text-gray-900">Site Analysis</h3>
            <p className="text-gray-600 leading-relaxed">
              Map-based site selection with intelligent boundary drawing and comprehensive location analysis
            </p>
          </div>

          <div className="card-gradient group cursor-pointer">
            <div className="bg-gradient-to-br from-purple-600/20 to-purple-600/30 w-16 h-16 rounded-2xl flex items-center justify-center mx-auto mb-6 group-hover:scale-110 transition-transform duration-300">
              <FileCheck className="h-8 w-8 text-purple-600" />
            </div>
            <h3 className="text-xl font-bold mb-3 text-gray-900">UDA Compliance</h3>
            <p className="text-gray-600 leading-relaxed">
              Automated checking against Sri Lankan UDA zoning regulations and building codes
            </p>
          </div>

          <div className="card-gradient group cursor-pointer">
            <div className="bg-gradient-to-br from-pink-600/20 to-pink-600/30 w-16 h-16 rounded-2xl flex items-center justify-center mx-auto mb-6 group-hover:scale-110 transition-transform duration-300">
              <Building2 className="h-8 w-8 text-pink-600" />
            </div>
            <h3 className="text-xl font-bold mb-3 text-gray-900">3D Generation</h3>
            <p className="text-gray-600 leading-relaxed">
              Professional 3D models with photorealistic rendering for immersive visualization
            </p>
          </div>

          <div className="card-gradient group cursor-pointer">
            <div className="bg-gradient-to-br from-orange-600/20 to-orange-600/30 w-16 h-16 rounded-2xl flex items-center justify-center mx-auto mb-6 group-hover:scale-110 transition-transform duration-300">
              <Users className="h-8 w-8 text-orange-600" />
            </div>
            <h3 className="text-xl font-bold mb-3 text-gray-900">Approval Workflow</h3>
            <p className="text-gray-600 leading-relaxed">
              Streamlined review process with architect, engineer, and regulator collaboration
            </p>
          </div>
        </div>

        {/* Stats Section */}
        <div className="mt-32 bg-white/60 backdrop-blur-lg rounded-3xl shadow-lg p-12">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-12">
            <div className="text-center">
              <div className="text-5xl font-extrabold bg-gradient-to-r from-primary-600 to-purple-600 bg-clip-text text-transparent mb-2">
                100%
              </div>
              <div className="text-gray-600 font-medium">UDA Compliant</div>
            </div>
            <div className="text-center">
              <div className="text-5xl font-extrabold bg-gradient-to-r from-purple-600 to-pink-600 bg-clip-text text-transparent mb-2">
                AI-Powered
              </div>
              <div className="text-gray-600 font-medium">Smart Generation</div>
            </div>
            <div className="text-center">
              <div className="text-5xl font-extrabold bg-gradient-to-r from-pink-600 to-orange-600 bg-clip-text text-transparent mb-2">
                Fast
              </div>
              <div className="text-gray-600 font-medium">Approval Process</div>
            </div>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="bg-white/60 backdrop-blur-lg mt-32 py-8 border-t border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <div className="flex items-center justify-center gap-2 mb-4">
            <div className="bg-gradient-to-br from-primary-500 to-purple-600 p-1.5 rounded-lg">
              <Building2 className="h-5 w-5 text-white" />
            </div>
            <span className="font-bold text-gray-900">Smart City Planning</span>
          </div>
          <p className="text-gray-600">&copy; 2025 Smart City Planning System. All rights reserved.</p>
        </div>
      </footer>
    </div>
  );
};

export default Landing;
