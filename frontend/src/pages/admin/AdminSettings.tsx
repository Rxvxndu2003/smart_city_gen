import { Link } from 'react-router-dom';
import { ArrowLeft, Settings } from 'lucide-react';

const AdminSettings = () => {
    return (
        <div className="min-h-screen bg-gray-50">
            <header className="bg-white shadow-sm">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
                    <div className="flex items-center space-x-4">
                        <Link to="/admin" className="text-gray-600 hover:text-primary-600">
                            <ArrowLeft className="h-6 w-6" />
                        </Link>
                        <div>
                            <h1 className="text-2xl font-bold text-gray-900">System Settings</h1>
                            <p className="text-sm text-gray-600">Configure system-wide settings</p>
                        </div>
                    </div>
                </div>
            </header>

            <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
                <div className="bg-white rounded-lg shadow p-8 text-center">
                    <Settings className="h-16 w-16 text-gray-400 mx-auto mb-4" />
                    <h2 className="text-2xl font-semibold text-gray-900 mb-2">System Configuration</h2>
                    <p className="text-gray-600 mb-6">
                        Configure system-wide settings, API keys, and application preferences
                    </p>
                    <p className="text-sm text-gray-500">This feature is under development</p>
                </div>
            </main>
        </div>
    );
};

export default AdminSettings;
