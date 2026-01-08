import { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import toast from 'react-hot-toast';
import {
  Building2,
  ArrowLeft,
  CheckCircle,
  XCircle,
  AlertTriangle,
  FileText,
  MapPin,
  Calendar,
  User,
  Activity,
  TrendingUp,
  Brain,
  FileDown,
  Download,
  Trash2,
  Box,
  MessageSquare,
  Lock,
  Shield,
  ExternalLink,
  Database
} from 'lucide-react';
import { projectsApi, validationApi, approvalsApi, blockchainApi } from '../../services/api';
import FileUpload from '../../components/FileUpload';
import ProjectAnalysis from '../../components/analysis/ProjectAnalysis';

import { AICouncil } from '../../components/AICouncil';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

interface Project {
  id: number;
  name: string;
  description: string;
  project_type: string;
  district: string;
  status: string;
  site_area: number;
  building_coverage: number;
  floor_area_ratio: number;
  num_floors: number;
  building_height: number;
  open_space_percentage: number;
  parking_spaces: number;
  created_at: string;
  owner_name?: string;
  model_url?: string;
  enhanced_renders_metadata?: any[];
  predicted_compliance?: number;
  compliance_confidence?: number;
  compliance_score?: number;
  prediction_message?: string;
  predicted_at?: string;
}

interface ValidationRule {
  rule_id?: string;
  description?: string;
  rule_name?: string;
  status?: string;
  is_valid?: boolean;
  message: string;
  severity: string;
}

interface ValidationResult {
  is_compliant: boolean;
  compliance_score: number;
  rules: ValidationRule[];
  recommendations: string[];
}

const ProjectDetail = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [project, setProject] = useState<Project | null>(null);
  const [validation, setValidation] = useState<ValidationResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [validating, setValidating] = useState(false);
  const [error, setError] = useState('');
  const [generating3D, setGenerating3D] = useState(false);
  const [generationStatus, setGenerationStatus] = useState<string>('');
  const [generationProgress, setGenerationProgress] = useState<number>(0);
  const [modelUrl, setModelUrl] = useState<string | null>(null);
  const [exporting, setExporting] = useState(false);
  const [predicting, setPredicting] = useState(false);
  const [prediction, setPrediction] = useState<any>(null);
  const [submitting, setSubmitting] = useState(false);
  const [approvalHistory, setApprovalHistory] = useState<any[]>([]);

  // Edit mode for rejected projects
  const [isEditMode, setIsEditMode] = useState(false);
  const [editedProject, setEditedProject] = useState<Partial<Project>>({});
  const [saving, setSaving] = useState(false);

  // Blockchain states
  const [blockchainRecords, setBlockchainRecords] = useState<any[]>([]);
  const [blockchainStatus, setBlockchainStatus] = useState<any>(null);
  const [storingOnBlockchain, setStoringOnBlockchain] = useState(false);
  const [blockchainError, setBlockchainError] = useState('');

  // Advanced 3D details configuration
  const [showAdvancedOptions, setShowAdvancedOptions] = useState(false);
  const [enableAdvancedDetails, setEnableAdvancedDetails] = useState(true);
  const [enableWindows, setEnableWindows] = useState(true);
  const [enableVehicles, setEnableVehicles] = useState(true);
  const [enableStreetLights, setEnableStreetLights] = useState(true);
  const [enableCrosswalks, setEnableCrosswalks] = useState(true);
  const [vehicleSpacing, setVehicleSpacing] = useState(20);
  const [treeSpacing] = useState(8); // Currently not configurable in UI

  // Hybrid Generation (NEW)
  const [useHybridMode, setUseHybridMode] = useState(false);
  const [enableAIEnhancement, setEnableAIEnhancement] = useState(false);
  const [enhancementStrength, setEnhancementStrength] = useState(0.7);
  const [numViews, setNumViews] = useState(4);
  const [, setEstimatedCost] = useState(0);
  const [enhancedRenders, setEnhancedRenders] = useState<any[]>([]);

  useEffect(() => {
    if (id) {
      fetchProject();
      runValidation();
      fetchApprovalHistory();
      fetchBlockchainStatus();
      fetchBlockchainRecords();
    }
  }, [id]);

  const loadSavedPrediction = useCallback(async () => {
    if (!project) return;

    const token = localStorage.getItem('access_token');
    if (!token) return;

    console.log('Loading saved prediction for project:', project.id, 'predicted_at:', project.predicted_at);

    try {
      const response = await fetch(`${API_BASE_URL}/ml/predict/${project.id}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        const data = await response.json();
        console.log('Loaded prediction data:', data);
        setPrediction(data);
      }
    } catch (err) {
      console.error('Failed to load saved prediction:', err);
      // Fallback to basic prediction data from project
      setPrediction({
        predicted_compliance: project.predicted_compliance === 1,
        confidence: project.compliance_confidence || 0,
        compliance_score: project.compliance_score || 0,
        message: project.prediction_message || ''
      });
    }
  }, [project]);

  // Load saved prediction when project is fetched
  useEffect(() => {
    // Check if there's a saved prediction by looking at predicted_at timestamp
    if (project?.predicted_at) {
      // If there's a saved prediction, fetch the full prediction with checks
      loadSavedPrediction();
    }
  }, [project, loadSavedPrediction]);

  // Calculate estimated cost for hybrid generation
  useEffect(() => {
    if (enableAIEnhancement) {
      const costPerImage = 0.0023; // SDXL cost
      setEstimatedCost(numViews * costPerImage);
    } else {
      setEstimatedCost(0);
    }
  }, [enableAIEnhancement, numViews]);

  // Load enhanced renders from project data (for persistence across page refreshes)
  useEffect(() => {
    if (project?.enhanced_renders_metadata) {
      setEnhancedRenders(project.enhanced_renders_metadata);
    }
  }, [project]);

  const fetchProject = async () => {
    setLoading(true);
    setError('');
    try {
      const response = await projectsApi.get(Number(id));
      console.log('Fetched project data:', response.data);
      setProject(response.data);
      // Load model URL from database if it exists
      if (response.data.model_url) {
        setModelUrl(response.data.model_url);
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load project');
    } finally {
      setLoading(false);
    }
  };

  const fetchApprovalHistory = async () => {
    try {
      const response = await approvalsApi.getHistory(Number(id));
      setApprovalHistory(response.data.approval_history || []);
    } catch (err: any) {
      console.error('Failed to load approval history:', err);
    }
  };

  const runValidation = async () => {
    setValidating(true);
    try {
      const response = await validationApi.validate(Number(id));
      // Backend returns { validation_result, ml_recommendations }
      const validationData = response.data.validation_result;
      setValidation({
        is_compliant: validationData.is_compliant,
        compliance_score: validationData.compliance_score,
        rules: validationData.detailed_results || [],
        recommendations: response.data.ml_recommendations?.compliance_tips || []
      });
    } catch (err: any) {
      console.error('Validation error:', err);
    } finally {
      setValidating(false);
    }
  };

  const submitForReview = async () => {
    if (!project) return;

    const confirmed = window.confirm(
      'Submit this project for review? Once submitted, the project will be reviewed by architects, engineers, and regulators.'
    );

    if (!confirmed) return;

    setSubmitting(true);
    const token = localStorage.getItem('access_token');

    try {
      const response = await fetch(`${API_BASE_URL}/projects/${project.id}/status?new_status=UNDER_ARCHITECT_REVIEW`, {
        method: 'PATCH',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to submit project');
      }

      toast.success('Project submitted for review successfully!');
      fetchProject(); // Refresh project data
    } catch (err: any) {
      toast.error('Error: ' + (err.message || 'Failed to submit project'));
    } finally {
      setSubmitting(false);
    }
  };

  const handleEditProject = () => {
    if (!project) return;
    setEditedProject({
      name: project.name,
      description: project.description,
      project_type: project.project_type,
      district: project.district,
      site_area: project.site_area,
      building_coverage: project.building_coverage,
      floor_area_ratio: project.floor_area_ratio,
      num_floors: project.num_floors,
      building_height: project.building_height,
      open_space_percentage: project.open_space_percentage,
      parking_spaces: project.parking_spaces,
      owner_name: project.owner_name,
    });
    setIsEditMode(true);
  };

  const handleCancelEdit = () => {
    setIsEditMode(false);
    setEditedProject({});
  };

  const handleSaveChanges = async () => {
    if (!project || !id) return;

    const token = localStorage.getItem('access_token');
    if (!token) {
      toast.error('Please log in to save changes');
      navigate('/login');
      return;
    }

    setSaving(true);
    try {
      await projectsApi.update(Number(id), editedProject);

      // Fetch fresh project data from server to ensure we have all updated fields
      await fetchProject();

      setIsEditMode(false);
      setEditedProject({});

      // Re-run validation with updated project data
      await runValidation();

      toast.success('Project updated successfully! Compliance analysis has been updated.');
    } catch (err: any) {
      console.error('Update error:', err);
      toast.error('Error: ' + (err.response?.data?.detail || 'Failed to update project'));
    } finally {
      setSaving(false);
    }
  };

  const handleResubmitProject = async () => {
    if (!project || !id) return;

    const token = localStorage.getItem('access_token');
    if (!token) {
      toast.error('Please log in to resubmit');
      navigate('/login');
      return;
    }

    if (!confirm('Are you sure you want to resubmit this project for review?')) {
      return;
    }

    setSubmitting(true);
    try {
      const response = await fetch(`${API_BASE_URL}/projects/${project.id}/status?new_status=UNDER_ARCHITECT_REVIEW`, {
        method: 'PATCH',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to resubmit project');
      }

      toast.success('Project resubmitted for review successfully!');

      // Refresh all project data
      await fetchProject();
      await fetchApprovalHistory();

      // Re-run validation for the resubmitted project
      await runValidation();

    } catch (err: any) {
      toast.error('Error: ' + (err.message || 'Failed to resubmit project'));
    } finally {
      setSubmitting(false);
    }
  };

  const generateCityLayout = async () => {
    if (!project) return;

    const token = localStorage.getItem('access_token');
    if (!token) {
      toast.error('Please log in to generate city layouts');
      navigate('/login');
      return;
    }

    setGenerating3D(true);
    setGenerationStatus('Starting city layout generation...');
    setGenerationProgress(10);

    try {
      // Choose endpoint based on mode
      const endpoint = useHybridMode
        ? `${API_BASE_URL}/generation/${project.id}/city-hybrid`
        : `${API_BASE_URL}/generation/${project.id}/city`;

      const requestBody: any = {
        grid_size: 4,
        block_size: 30,
        road_width: 6,
        // Advanced 3D details
        enable_advanced_details: enableAdvancedDetails,
        enable_windows: enableWindows,
        enable_vehicles: enableVehicles,
        enable_street_lights: enableStreetLights,
        enable_crosswalks: enableCrosswalks,
        vehicle_spacing: vehicleSpacing,
        tree_spacing: treeSpacing
      };

      // Add hybrid-specific fields if using hybrid mode
      if (useHybridMode) {
        requestBody.enable_ai_enhancement = enableAIEnhancement;
        requestBody.enhancement_strength = enhancementStrength;
        requestBody.num_views = numViews;
      }

      const response = await fetch(endpoint, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(requestBody)
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
        if (response.status === 401) {
          toast.error('Session expired. Please log in again.');
          navigate('/login');
          return;
        }
        throw new Error(errorData.detail || `HTTP ${response.status}`);
      }

      const data = await response.json();
      console.log('City generation completed:', data);
      setGenerationStatus('✓ City layout generated successfully!');
      setGenerationProgress(100);

      setModelUrl(data.model_url);

      // Store enhanced renders if available
      if (data.enhanced_renders && data.enhanced_renders.length > 0) {
        setEnhancedRenders(data.enhanced_renders);
      }

      setTimeout(async () => {
        setGenerating3D(false);
        setGenerationStatus('');
        setGenerationProgress(0);
        await fetchProject();

        // Re-run validation after generating new 3D model
        await runValidation();

        toast.success(`City layout generated! Grid: ${data.grid_size}x${data.grid_size}, Size: ${(data.file_size / (1024 * 1024)).toFixed(2)} MB`);
      }, 1000);

    } catch (err: any) {
      console.error('City generation error:', err);
      setGenerating3D(false);
      setGenerationStatus('');
      setGenerationProgress(0);
      toast.error('Failed to generate city layout: ' + (err.message || 'Unknown error'));
    }
  };

  const download3DModel = async () => {
    if (!project) return;

    const token = localStorage.getItem('access_token');
    if (!token) {
      toast.error('Please log in to download 3D models');
      navigate('/login');
      return;
    }

    try {
      const response = await fetch(`${API_BASE_URL}/generation/${project.id}/download`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (!response.ok) {
        throw new Error('Failed to download 3D model');
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;

      const isCity = project.model_url?.includes('city.glb');
      const modelType = isCity ? 'city' : 'building';
      a.download = `${project.name.replace(/[^a-z0-9]/gi, '_')}_${modelType}.glb`;

      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);

      toast.success(`${isCity ? 'City' : 'Building'} model downloaded successfully!`);
    } catch (err) {
      console.error('Download error:', err);
      toast.error('Failed to download 3D model');
    }
  };

  const delete3DModel = async () => {
    if (!project) return;

    if (!confirm('Are you sure you want to delete this 3D model? This action cannot be undone.')) {
      return;
    }

    const token = localStorage.getItem('access_token');
    if (!token) {
      toast.error('Please log in to delete 3D models');
      navigate('/login');
      return;
    }

    try {
      const response = await fetch(`${API_BASE_URL}/generation/${project.id}/delete`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (!response.ok) {
        throw new Error('Failed to delete 3D model');
      }

      setModelUrl(null);
      await fetchProject();

      // Re-run validation after deleting 3D model
      await runValidation();

      toast.success('3D model deleted successfully!');
    } catch (err: any) {
      console.error('Delete error:', err);
      toast.error('Failed to delete 3D model: ' + (err.message || 'Unknown error'));
    }
  };

  const exportPDF = async () => {
    if (!project) return;

    setExporting(true);
    try {
      const response = await fetch(`${API_BASE_URL}/exports/pdf/${project.id}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        }
      });

      if (!response.ok) throw new Error('Export failed');

      const data = await response.json();

      // Download the file
      const downloadUrl = `${API_BASE_URL.replace('/api/v1', '')}${data.download_url}`;
      const downloadResponse = await fetch(downloadUrl, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        }
      });

      const blob = await downloadResponse.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = data.filename;
      a.click();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error('Export failed:', err);
      toast.error('Failed to export PDF');
    } finally {
      setExporting(false);
    }
  };

  const exportComprehensivePDF = async () => {
    if (!project) return;

    setExporting(true);
    try {
      const response = await fetch(`${API_BASE_URL}/exports/comprehensive-report/${project.id}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        }
      });

      if (!response.ok) throw new Error('Export failed');

      const data = await response.json();

      // Download the file
      const downloadUrl = `${API_BASE_URL.replace('/api/v1', '')}${data.download_url}`;
      const downloadResponse = await fetch(downloadUrl, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        }
      });

      const blob = await downloadResponse.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = data.filename;
      a.click();
      window.URL.revokeObjectURL(url);

      toast.success('Comprehensive report downloaded!');
    } catch (err) {
      console.error('Export failed:', err);
      toast.error('Failed to export comprehensive report');
    } finally {
      setExporting(false);
    }
  };

  const exportJSON = async () => {
    if (!project) return;

    try {
      const response = await fetch(`${API_BASE_URL}/exports/json/${project.id}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        }
      });

      if (!response.ok) throw new Error('Export failed');

      const data = await response.json();

      // Download as JSON file
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `project_${project.id}_${project.name.replace(/\s+/g, '_')}.json`;
      a.click();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error('Export failed:', err);
      toast.error('Failed to export JSON');
    }
  };

  const predictCompliance = async () => {
    if (!project) return;

    const token = localStorage.getItem('access_token');
    if (!token) {
      toast.error('Please log in to run compliance check');
      navigate('/login');
      return;
    }

    setPredicting(true);
    try {
      const response = await fetch(`${API_BASE_URL}/ml/predict/${project.id}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
        if (response.status === 401) {
          toast.error('Session expired. Please log in again.');
          navigate('/login');
          return;
        }
        throw new Error(errorData.detail || `HTTP ${response.status}`);
      }

      const data = await response.json();
      setPrediction(data);
      // Refresh project data to load saved prediction
      await fetchProject();
    } catch (err: any) {
      console.error('Prediction failed:', err);
      toast.error('Failed to predict compliance: ' + (err.message || 'Unknown error'));
    } finally {
      setPredicting(false);
    }
  };

  // Blockchain functions
  const fetchBlockchainStatus = async () => {
    try {
      const response = await blockchainApi.getStatus();
      setBlockchainStatus(response.data);
    } catch (err: any) {
      console.error('Failed to fetch blockchain status:', err);
    }
  };

  const fetchBlockchainRecords = async () => {
    if (!id) return;
    try {
      const response = await blockchainApi.getProjectRecords(Number(id));
      setBlockchainRecords(response.data.database_records || []);
    } catch (err: any) {
      console.error('Failed to fetch blockchain records:', err);
    }
  };

  const storeOnBlockchain = async (recordType: string = 'DESIGN_HASH') => {
    if (!project) return;

    const confirmed = window.confirm(
      `Store this project on blockchain?\n\nThis will create an immutable record of the current project state.\n\nRecord Type: ${recordType}\n\nNote: This action cannot be undone and will be permanently stored on the Ethereum blockchain.`
    );

    if (!confirmed) return;

    setStoringOnBlockchain(true);
    setBlockchainError('');

    try {
      const metadata = {
        version: '1.0',
        stored_at: new Date().toISOString(),
        project_name: project.name,
        status: project.status,
      };

      const response = await blockchainApi.storeProject(project.id, recordType, metadata);

      if (response.data.success) {
        toast.success(
          `✅ Successfully stored on blockchain!\n\n` +
          `Transaction Hash: ${response.data.transaction_hash}\n` +
          `IPFS Hash: ${response.data.ipfs_hash}\n\n` +
          `View on Etherscan: https://sepolia.etherscan.io/tx/${response.data.transaction_hash}`
        );

        // Refresh blockchain records
        await fetchBlockchainRecords();
      }
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || err.message || 'Failed to store on blockchain';
      setBlockchainError(errorMessage);
      toast.error(`Error storing on blockchain: ${errorMessage}`);
    } finally {
      setStoringOnBlockchain(false);
    }
  };

  const viewOnEtherscan = (txHash: string) => {
    window.open(`https://sepolia.etherscan.io/tx/${txHash}`, '_blank');
  };

  const viewOnIPFS = (ipfsHash: string) => {
    window.open(`https://gateway.pinata.cloud/ipfs/${ipfsHash}`, '_blank');
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'APPROVED':
        return 'bg-green-100 text-green-800';
      case 'REJECTED':
        return 'bg-red-100 text-red-800';
      case 'DRAFT':
        return 'bg-gray-100 text-gray-800';
      default:
        return 'bg-yellow-100 text-yellow-800';
    }
  };

  const getRuleIcon = (status: string) => {
    switch (status) {
      case 'PASS':
        return <CheckCircle className="h-5 w-5 text-green-500" />;
      case 'FAIL':
        return <XCircle className="h-5 w-5 text-red-500" />;
      case 'WARNING':
        return <AlertTriangle className="h-5 w-5 text-yellow-500" />;
      default:
        return <AlertTriangle className="h-5 w-5 text-gray-500" />;
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  if (error || !project) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <XCircle className="h-16 w-16 text-red-500 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">Error Loading Project</h3>
          <p className="text-gray-600 mb-6">{error}</p>
          <button onClick={() => navigate('/projects')} className="btn-primary">
            Back to Projects
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 via-blue-50 to-indigo-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <button
            onClick={() => navigate('/projects')}
            className="flex items-center text-primary-600 hover:text-primary-700 mb-4 font-medium transition-colors"
          >
            <ArrowLeft className="h-5 w-5 mr-2" />
            Back to Projects
          </button>
          <div className="bg-white rounded-2xl shadow-xl p-6 border border-gray-100">
            <div className="flex items-start justify-between">
              <div className="flex items-center space-x-4">
                <div className="p-3 bg-gradient-to-br from-primary-600 to-indigo-600 rounded-xl shadow-md">
                  <Building2 className="h-8 w-8 text-white" />
                </div>
                <div>
                  <h1 className="text-3xl font-bold text-gray-900">{project.name}</h1>
                  <p className="text-gray-600 mt-1">{project.description}</p>
                </div>
              </div>
              <div className="flex items-center space-x-2">
                {project.status === 'DRAFT' && (
                  <button
                    onClick={submitForReview}
                    disabled={submitting}
                    className="px-4 py-2 text-sm font-semibold text-white bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-700 hover:to-emerald-700 rounded-lg transition-all disabled:opacity-50 flex items-center shadow-md hover:shadow-lg"
                  >
                    <CheckCircle className="h-4 w-4 mr-2" />
                    {submitting ? 'Submitting...' : 'Submit for Review'}
                  </button>
                )}
                {project.status === 'REJECTED' && !isEditMode && (
                  <>
                    <button
                      onClick={handleEditProject}
                      className="px-4 py-2 text-sm font-semibold text-white bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 rounded-lg transition-all flex items-center shadow-md hover:shadow-lg"
                    >
                      <FileText className="h-4 w-4 mr-2" />
                      Edit Project
                    </button>
                    <button
                      onClick={handleResubmitProject}
                      disabled={submitting}
                      className="px-4 py-2 text-sm font-semibold text-white bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-700 hover:to-emerald-700 rounded-lg transition-all disabled:opacity-50 flex items-center shadow-md hover:shadow-lg"
                    >
                      <CheckCircle className="h-4 w-4 mr-2" />
                      {submitting ? 'Resubmitting...' : 'Resubmit for Review'}
                    </button>
                  </>
                )}
                {isEditMode && (
                  <>
                    <button
                      onClick={handleSaveChanges}
                      disabled={saving}
                      className="px-4 py-2 text-sm font-semibold text-white bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-700 hover:to-emerald-700 rounded-lg transition-all disabled:opacity-50 flex items-center shadow-md hover:shadow-lg"
                    >
                      <CheckCircle className="h-4 w-4 mr-2" />
                      {saving ? 'Saving...' : 'Save Changes'}
                    </button>
                    <button
                      onClick={handleCancelEdit}
                      className="px-4 py-2 text-sm font-semibold text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-lg transition-all flex items-center shadow-sm hover:shadow-md"
                    >
                      <XCircle className="h-4 w-4 mr-2" />
                      Cancel
                    </button>
                  </>
                )}
                <button
                  onClick={exportJSON}
                  className="px-4 py-2 text-sm font-semibold text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-lg transition-all flex items-center shadow-sm hover:shadow-md"
                >
                  <FileDown className="h-4 w-4 mr-2" />
                  Export JSON
                </button>
                <button
                  onClick={exportPDF}
                  disabled={exporting}
                  className="px-4 py-2 text-sm font-semibold text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-lg transition-all flex items-center shadow-sm hover:shadow-md"
                >
                  <FileText className="h-4 w-4 mr-2" />
                  {exporting ? '...' : 'Brief PDF'}
                </button>
                <button
                  onClick={exportComprehensivePDF}
                  disabled={exporting}
                  className="px-4 py-2 text-sm font-semibold text-white bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 rounded-lg transition-all disabled:opacity-50 flex items-center shadow-md hover:shadow-lg"
                >
                  <FileDown className="h-4 w-4 mr-2" />
                  {exporting ? 'Generating...' : 'Full Report'}
                </button>
                <span className={`px-4 py-2 rounded-full text-sm font-bold shadow-sm ${getStatusColor(project.status)}`}>
                  {project.status.replace(/_/g, ' ')}
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Rejection Notice Banner */}
        {project.status === 'REJECTED' && approvalHistory.length > 0 && (
          <div className="mb-6 bg-red-50 border-2 border-red-200 rounded-xl p-4">
            <div className="flex items-start">
              <div className="flex-shrink-0">
                <XCircle className="h-6 w-6 text-red-600" />
              </div>
              <div className="ml-3 flex-1">
                <h3 className="text-sm font-semibold text-red-900">Project Rejected</h3>
                <div className="mt-2 text-sm text-red-700">
                  {approvalHistory
                    .filter(a => a.status_to === 'REJECTED')
                    .slice(0, 1)
                    .map((approval, index) => (
                      <div key={index}>
                        {approval.comment && (
                          <p className="mb-2">
                            <span className="font-medium">Reason: </span>
                            {approval.comment}
                          </p>
                        )}
                        <p className="text-xs text-red-600">
                          Rejected by {approval.user_name} on {new Date(approval.timestamp).toLocaleString()}
                        </p>
                      </div>
                    ))}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Analysis Tabs Section */}
        <div className="mb-8">
          <ProjectAnalysis projectId={project.id} projectData={project} />
        </div>

        {/* Main Content Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Column - Project Details */}
          <div className="lg:col-span-1 space-y-6">



            {/* 3D Model Section - Generate City Only */}
            <div className="card bg-gradient-to-br from-indigo-50 to-purple-50 border-2 border-indigo-100">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center">
                  <div className="bg-gradient-to-br from-indigo-600 to-purple-600 rounded-lg p-2.5 mr-3">
                    <Box className="h-5 w-5 text-white" />
                  </div>
                  <h3 className="text-lg font-semibold text-gray-900">3D City Model</h3>
                </div>
                <button
                  onClick={() => setShowAdvancedOptions(!showAdvancedOptions)}
                  className="text-xs px-3 py-1.5 bg-white hover:bg-gray-50 text-gray-700 font-medium rounded-lg transition-all border border-gray-300 flex items-center"
                >
                  <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                  </svg>
                  {showAdvancedOptions ? 'Hide' : 'Options'}
                </button>
              </div>

              {/* Advanced Options Panel */}
              {showAdvancedOptions && !generating3D && !modelUrl && (
                <div className="bg-white rounded-lg p-4 mb-4 border-2 border-indigo-100">
                  <h4 className="text-sm font-semibold text-gray-900 mb-3 flex items-center">
                    <svg className="w-4 h-4 mr-1.5 text-indigo-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4" />
                    </svg>
                    Advanced 3D Details
                  </h4>

                  <div className="space-y-2.5">
                    {/* Master Toggle */}
                    <label className="flex items-center justify-between p-2.5 rounded-lg hover:bg-gray-50 cursor-pointer transition">
                      <span className="text-sm font-medium text-gray-700 flex items-center">
                        <svg className="w-4 h-4 mr-2 text-indigo-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z" />
                        </svg>
                        Enable Advanced Details
                      </span>
                      <input
                        type="checkbox"
                        checked={enableAdvancedDetails}
                        onChange={(e) => setEnableAdvancedDetails(e.target.checked)}
                        className="w-4 h-4 text-indigo-600 border-gray-300 rounded focus:ring-indigo-500"
                      />
                    </label>

                    {enableAdvancedDetails && (
                      <>
                        {/* Windows */}
                        <label className="flex items-center justify-between p-2.5 pl-8 rounded-lg hover:bg-gray-50 cursor-pointer transition">
                          <span className="text-sm text-gray-600">🪟 Windows on Buildings</span>
                          <input
                            type="checkbox"
                            checked={enableWindows}
                            onChange={(e) => setEnableWindows(e.target.checked)}
                            className="w-4 h-4 text-indigo-600 border-gray-300 rounded focus:ring-indigo-500"
                          />
                        </label>

                        {/* Vehicles */}
                        <label className="flex items-center justify-between p-2.5 pl-8 rounded-lg hover:bg-gray-50 cursor-pointer transition">
                          <span className="text-sm text-gray-600">🚗 Vehicles on Roads</span>
                          <input
                            type="checkbox"
                            checked={enableVehicles}
                            onChange={(e) => setEnableVehicles(e.target.checked)}
                            className="w-4 h-4 text-indigo-600 border-gray-300 rounded focus:ring-indigo-500"
                          />
                        </label>

                        {enableVehicles && (
                          <div className="pl-8 pr-2">
                            <label className="text-xs text-gray-600 mb-1 block">Vehicle Spacing (m)</label>
                            <input
                              type="number"
                              min="10"
                              max="50"
                              value={vehicleSpacing}
                              onChange={(e) => setVehicleSpacing(Number(e.target.value))}
                              className="w-full text-sm px-3 py-1.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                            />
                          </div>
                        )}

                        {/* Street Lights */}
                        <label className="flex items-center justify-between p-2.5 pl-8 rounded-lg hover:bg-gray-50 cursor-pointer transition">
                          <span className="text-sm text-gray-600">💡 Street Lights</span>
                          <input
                            type="checkbox"
                            checked={enableStreetLights}
                            onChange={(e) => setEnableStreetLights(e.target.checked)}
                            className="w-4 h-4 text-indigo-600 border-gray-300 rounded focus:ring-indigo-500"
                          />
                        </label>

                        {/* Crosswalks */}
                        <label className="flex items-center justify-between p-2.5 pl-8 rounded-lg hover:bg-gray-50 cursor-pointer transition">
                          <span className="text-sm text-gray-600">🚶 Crosswalk Markings</span>
                          <input
                            type="checkbox"
                            checked={enableCrosswalks}
                            onChange={(e) => setEnableCrosswalks(e.target.checked)}
                            className="w-4 h-4 text-indigo-600 border-gray-300 rounded focus:ring-indigo-500"
                          />
                        </label>

                        <div className="mt-3 p-2.5 bg-blue-50 rounded-lg border border-blue-100">
                          <p className="text-xs text-blue-700 flex items-start">
                            <svg className="w-4 h-4 mr-1.5 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                            </svg>
                            <span>Advanced details increase generation time (2-4 min) but add realistic features like glass windows, cars, and lighting.</span>
                          </p>
                        </div>
                      </>
                    )}
                  </div>
                </div>
              )}

              {/* Hybrid Generation Controls (NEW) */}
              <div className="mt-4 p-4 bg-gradient-to-br from-purple-50 to-indigo-50 rounded-lg border border-purple-200">
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center space-x-2">
                    <span className="text-lg">🚀</span>
                    <label className="text-sm font-semibold text-gray-900">
                      Advanced Rendering Mode
                    </label>
                  </div>
                  <input
                    type="checkbox"
                    checked={useHybridMode}
                    onChange={(e) => setUseHybridMode(e.target.checked)}
                    className="w-4 h-4 text-purple-600 border-gray-300 rounded focus:ring-purple-500"
                  />
                </div>

                {useHybridMode && (
                  <div className="space-y-3 pl-6 border-l-2 border-purple-300">
                    <div className="text-xs text-purple-700 bg-purple-100 p-2 rounded">
                      💡 Creates photorealistic city views using advanced AI technology
                    </div>

                    <div className="flex items-center justify-between">
                      <label className="text-sm font-medium text-gray-700">
                        Generate Photorealistic Views
                      </label>
                      <input
                        type="checkbox"
                        checked={enableAIEnhancement}
                        onChange={(e) => setEnableAIEnhancement(e.target.checked)}
                        className="w-4 h-4 text-purple-600 border-gray-300 rounded focus:ring-purple-500"
                      />
                    </div>

                    {enableAIEnhancement && (
                      <div className="space-y-3 bg-white p-3 rounded border border-purple-200">
                        <div>
                          <label className="text-xs font-medium text-gray-700 block mb-1">
                            Realism Level: {(enhancementStrength * 100).toFixed(0)}%
                          </label>
                          <div className="flex items-center gap-2">
                            <span className="text-xs text-gray-500">Subtle</span>
                            <input
                              type="range"
                              min="0"
                              max="1"
                              step="0.1"
                              value={enhancementStrength}
                              onChange={(e) => setEnhancementStrength(Number(e.target.value))}
                              className="flex-1 h-2 bg-purple-200 rounded-lg appearance-none cursor-pointer"
                            />
                            <span className="text-xs text-gray-500">Strong</span>
                          </div>
                        </div>

                        <div>
                          <label className="text-xs font-medium text-gray-700 block mb-1">
                            Number of Camera Views
                          </label>
                          <input
                            type="number"
                            min="1"
                            max="8"
                            value={numViews}
                            onChange={(e) => setNumViews(Number(e.target.value))}
                            className="w-full px-3 py-1.5 text-sm border border-gray-300 rounded focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                          />
                          <p className="text-xs text-gray-500 mt-1">More views = better coverage (1-8)</p>
                        </div>


                      </div>
                    )}
                  </div>
                )}
              </div>

              <button
                onClick={generateCityLayout}
                disabled={generating3D}
                className="w-full text-sm px-4 py-3 bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-700 hover:to-emerald-700 text-white font-semibold rounded-lg transition-all duration-300 disabled:opacity-50 shadow-md hover:shadow-lg flex items-center justify-center"
              >
                {generating3D ? 'Generating...' : '🏙️ Generate City'}
              </button>

              {generating3D ? (
                <div className="bg-white rounded-lg p-6">
                  <div className="text-center">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto mb-4"></div>
                    <p className="text-sm font-semibold text-gray-900 mb-2">{generationStatus || 'Generating 3D city...'}</p>
                    {generationProgress > 0 && (
                      <div className="w-full bg-gray-200 rounded-full h-2 mb-2">
                        <div
                          className="bg-indigo-600 h-2 rounded-full transition-all duration-500"
                          style={{ width: `${generationProgress}%` }}
                        ></div>
                      </div>
                    )}
                    <p className="text-xs text-gray-500">Please wait...</p>
                  </div>
                </div>
              ) : modelUrl ? (
                <div className="space-y-4">
                  <div className="bg-white rounded-lg p-6 border-2 border-indigo-200">
                    <div className="flex items-center justify-between mb-4">
                      <div className="flex items-center space-x-3">
                        <div className="bg-gradient-to-br from-indigo-600 to-purple-600 rounded-lg p-2.5">
                          <Box className="h-5 w-5 text-white" />
                        </div>
                        <div>
                          <h4 className="text-base font-bold text-gray-900">3D Model Ready</h4>
                          <p className="text-sm text-gray-600">
                            {modelUrl?.includes('city.glb') ? 'City Layout Generated' : '3D Model Available'}
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center space-x-2 bg-green-100 text-green-700 px-3 py-1.5 rounded-full text-xs font-semibold">
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
                        </svg>
                        <span>Ready</span>
                      </div>
                    </div>

                    <div className="flex gap-3">
                      <button
                        onClick={download3DModel}
                        className="flex-1 bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 text-white font-semibold py-3 px-4 rounded-lg transition-all duration-300 flex items-center justify-center shadow-md hover:shadow-lg transform hover:scale-105"
                      >
                        <Download className="h-5 w-5 mr-2" />
                        <span>Download Model</span>
                      </button>

                      <button
                        onClick={delete3DModel}
                        className="bg-gradient-to-r from-red-600 to-rose-600 hover:from-red-700 hover:to-rose-700 text-white font-semibold py-3 px-4 rounded-lg transition-all duration-300 flex items-center justify-center shadow-md hover:shadow-lg transform hover:scale-105"
                        title="Delete 3D Model"
                      >
                        <Trash2 className="h-5 w-5" />
                      </button>
                    </div>

                    <div className="mt-3 pt-3 border-t border-indigo-100">
                      <div className="flex items-center justify-center space-x-3 text-xs text-gray-600">
                        <div className="flex items-center">
                          <svg className="w-3.5 h-3.5 mr-1 text-indigo-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                          </svg>
                          <span className="font-medium">Format: GLB</span>
                        </div>
                        <span className="text-gray-400">•</span>
                        <div className="flex items-center">
                          <svg className="w-3.5 h-3.5 mr-1 text-indigo-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
                          </svg>
                          <span className="font-medium">Web optimized</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="bg-white rounded-lg p-8 text-center">
                  <Box className="h-12 w-12 text-gray-400 mx-auto mb-3" />
                  <p className="text-sm text-gray-600 mb-1">No 3D city model yet</p>
                  <p className="text-xs text-gray-500">Click "Generate City" to create a 3D city layout</p>
                </div>
              )}
            </div>

            {/* Enhanced Renders Gallery */}
            {enhancedRenders.length > 0 && (
              <div className="mt-8">
                <h3 className="text-lg font-semibold mb-4 flex items-center">
                  <svg className="w-5 h-5 mr-2 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                  </svg>
                  AI-Enhanced City Views ({enhancedRenders.filter(r => r.status === 'completed').length}/{enhancedRenders.length})
                </h3>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {enhancedRenders.map((render, index) => (
                    <div key={index} className="bg-white rounded-lg shadow-sm overflow-hidden border border-gray-200">
                      <div className="p-3 bg-gray-50 border-b border-gray-200">
                        <h4 className="font-medium text-sm flex items-center justify-between">
                          <span>{render.view_name || `View ${index + 1}`}</span>
                          {render.status === 'completed' ? (
                            <span className="text-xs bg-green-100 text-green-700 px-2 py-1 rounded">✓ Enhanced</span>
                          ) : (
                            <span className="text-xs bg-yellow-100 text-yellow-700 px-2 py-1 rounded">⚠ {render.status}</span>
                          )}
                        </h4>
                      </div>

                      <div className="grid grid-cols-2 gap-2 p-3">
                        <div>
                          <p className="text-xs text-gray-500 mb-1">Original</p>
                          {render.original && (
                            <div className="relative group">
                              <img
                                src={`http://localhost:8000/${render.original}`}
                                alt={`Original ${render.view_name}`}
                                className="w-full h-32 object-cover rounded border border-gray-200"
                              />
                              <a
                                href={`http://localhost:8000/${render.original}`}
                                download
                                className="absolute inset-0 bg-black bg-opacity-0 group-hover:bg-opacity-40 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-all"
                              >
                                <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                                </svg>
                              </a>
                            </div>
                          )}
                        </div>

                        <div>
                          <p className="text-xs text-gray-500 mb-1">AI-Enhanced</p>
                          {render.enhanced ? (
                            <div className="relative group">
                              <img
                                src={`http://localhost:8000/${render.enhanced}`}
                                alt={`Enhanced ${render.view_name}`}
                                className="w-full h-32 object-cover rounded border border-purple-200"
                              />
                              <a
                                href={`http://localhost:8000/${render.enhanced}`}
                                download
                                className="absolute inset-0 bg-black bg-opacity-0 group-hover:bg-opacity-40 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-all"
                              >
                                <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                                </svg>
                              </a>
                            </div>
                          ) : (
                            <div className="w-full h-32 bg-gray-100 rounded border border-gray-200 flex items-center justify-center">
                              <p className="text-xs text-gray-400">Not available</p>
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* ML Compliance Prediction */}
            <div className="card bg-gradient-to-br from-green-50 to-emerald-50 border-2 border-green-100">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center">
                  <div className="bg-gradient-to-br from-green-600 to-emerald-600 rounded-lg p-2.5 mr-3">
                    <Brain className="h-5 w-5 text-white" />
                  </div>
                  <h3 className="text-lg font-semibold text-gray-900">Compliance Check</h3>
                </div>
                <button
                  onClick={predictCompliance}
                  disabled={predicting}
                  className="text-sm px-4 py-2 bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-700 hover:to-emerald-700 text-white font-semibold rounded-lg transition-all duration-300 disabled:opacity-50 shadow-md hover:shadow-lg"
                >
                  {predicting ? 'Predicting...' : 'Run Prediction'}
                </button>
              </div>

              {prediction ? (
                <div className="space-y-4">
                  <div className={`p-4 rounded-lg border-2 ${prediction.predicted_compliance
                    ? 'bg-green-50 border-green-200'
                    : 'bg-red-50 border-red-200'
                    }`}>
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm font-medium text-gray-700">Compliance Status</span>
                      {prediction.predicted_compliance ? (
                        <CheckCircle className="h-5 w-5 text-green-600" />
                      ) : (
                        <XCircle className="h-5 w-5 text-red-600" />
                      )}
                    </div>
                    <p className={`text-lg font-bold ${prediction.predicted_compliance ? 'text-green-900' : 'text-red-900'
                      }`}>
                      {prediction.predicted_compliance ? 'Likely Compliant' : 'Likely Non-Compliant'}
                    </p>
                  </div>

                  <div className="grid grid-cols-2 gap-3">
                    <div className="p-3 bg-gray-50 rounded-lg">
                      <p className="text-xs text-gray-600 mb-1">Confidence</p>
                      <p className="text-lg font-semibold text-gray-900">
                        {(prediction.confidence * 100).toFixed(1)}%
                      </p>
                    </div>
                    <div className="p-3 bg-gray-50 rounded-lg">
                      <p className="text-xs text-gray-600 mb-1">Score</p>
                      <p className="text-lg font-semibold text-gray-900">
                        {(prediction.compliance_score * 100).toFixed(1)}%
                      </p>
                    </div>
                  </div>

                  {prediction.checks && prediction.checks.length > 0 && (
                    <div className="bg-white rounded-lg p-4 border border-gray-200">
                      <h4 className="text-sm font-semibold text-gray-900 mb-3 flex items-center">
                        <Activity className="h-4 w-4 mr-2 text-blue-600" />
                        Compliance Measures Checked
                      </h4>
                      <div className="space-y-2">
                        {prediction.checks.map((check: any, index: number) => (
                          <div
                            key={index}
                            className={`p-3 rounded-lg border ${check.status === 'PASS'
                              ? 'bg-green-50 border-green-200'
                              : check.status === 'WARNING'
                                ? 'bg-yellow-50 border-yellow-200'
                                : 'bg-red-50 border-red-200'
                              }`}
                          >
                            <div className="flex items-start justify-between">
                              <div className="flex-1">
                                <div className="flex items-center mb-1">
                                  {check.status === 'PASS' ? (
                                    <CheckCircle className="h-4 w-4 text-green-600 mr-2" />
                                  ) : check.status === 'WARNING' ? (
                                    <AlertTriangle className="h-4 w-4 text-yellow-600 mr-2" />
                                  ) : (
                                    <XCircle className="h-4 w-4 text-red-600 mr-2" />
                                  )}
                                  <span className="text-sm font-medium text-gray-900">{check.name}</span>
                                </div>
                                <p className="text-xs text-gray-600 ml-6">{check.message}</p>
                                <p className="text-xs text-gray-500 ml-6 mt-1">
                                  Expected: {check.expected_range}
                                </p>
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  <p className="text-xs text-gray-500 italic">{prediction.message}</p>
                </div>
              ) : (
                <div className="text-center py-6 text-gray-500">
                  <Brain className="h-12 w-12 mx-auto mb-2 text-gray-300" />
                  <p className="text-sm">No compliance check yet</p>
                  <p className="text-xs">Click &quot;Run Prediction&quot; to check compliance</p>
                </div>
              )}
            </div>

            {/* File Uploads */}
            <div className="card bg-gradient-to-br from-white to-gray-50">
              <div className="flex items-center mb-4">
                <div className="bg-gradient-to-br from-primary-600 to-indigo-600 rounded-lg p-2.5 mr-3">
                  <FileText className="h-5 w-5 text-white" />
                </div>
                <h3 className="text-lg font-semibold text-gray-900">Project Documents</h3>
              </div>
              <FileUpload projectId={project.id} />
            </div>

            {/* Basic Info */}
            <div className="card bg-gradient-to-br from-blue-50 to-indigo-50 border-2 border-blue-100">
              <div className="flex items-center mb-4">
                <div className="bg-gradient-to-br from-blue-600 to-indigo-600 rounded-lg p-2.5 mr-3">
                  <Building2 className="h-5 w-5 text-white" />
                </div>
                <h3 className="text-lg font-semibold text-gray-900">Project Information</h3>
              </div>
              <div className="space-y-3">
                {isEditMode ? (
                  <>
                    <div className="bg-white rounded-lg p-3 shadow-sm">
                      <label className="block text-xs text-gray-600 mb-1">Project Name</label>
                      <input
                        type="text"
                        value={editedProject.name || ''}
                        onChange={(e) => setEditedProject({ ...editedProject, name: e.target.value })}
                        className="w-full px-2 py-1 border border-gray-300 rounded text-sm"
                      />
                    </div>
                    <div className="bg-white rounded-lg p-3 shadow-sm">
                      <label className="block text-xs text-gray-600 mb-1">Description</label>
                      <textarea
                        value={editedProject.description || ''}
                        onChange={(e) => setEditedProject({ ...editedProject, description: e.target.value })}
                        className="w-full px-2 py-1 border border-gray-300 rounded text-sm"
                        rows={3}
                      />
                    </div>
                    <div className="bg-white rounded-lg p-3 shadow-sm">
                      <label className="block text-xs text-gray-600 mb-1">Type</label>
                      <input
                        type="text"
                        value={editedProject.project_type || ''}
                        onChange={(e) => setEditedProject({ ...editedProject, project_type: e.target.value })}
                        className="w-full px-2 py-1 border border-gray-300 rounded text-sm"
                      />
                    </div>
                    <div className="bg-white rounded-lg p-3 shadow-sm">
                      <label className="block text-xs text-gray-600 mb-1">District</label>
                      <input
                        type="text"
                        value={editedProject.district || ''}
                        onChange={(e) => setEditedProject({ ...editedProject, district: e.target.value })}
                        className="w-full px-2 py-1 border border-gray-300 rounded text-sm"
                      />
                    </div>
                    <div className="bg-white rounded-lg p-3 shadow-sm">
                      <label className="block text-xs text-gray-600 mb-1">Owner Name</label>
                      <input
                        type="text"
                        value={editedProject.owner_name || ''}
                        onChange={(e) => setEditedProject({ ...editedProject, owner_name: e.target.value })}
                        className="w-full px-2 py-1 border border-gray-300 rounded text-sm"
                      />
                    </div>
                  </>
                ) : (
                  <>
                    <div className="flex items-center text-sm bg-white rounded-lg p-3 shadow-sm">
                      <FileText className="h-5 w-5 text-blue-600 mr-3" />
                      <span className="text-gray-600">Type:</span>
                      <span className="ml-auto font-semibold text-gray-900">{project.project_type}</span>
                    </div>
                    <div className="flex items-center text-sm bg-white rounded-lg p-3 shadow-sm">
                      <MapPin className="h-5 w-5 text-blue-600 mr-3" />
                      <span className="text-gray-600">District:</span>
                      <span className="ml-auto font-semibold text-gray-900">{project.district}</span>
                    </div>
                    <div className="flex items-center text-sm bg-white rounded-lg p-3 shadow-sm">
                      <Calendar className="h-5 w-5 text-blue-600 mr-3" />
                      <span className="text-gray-600">Created:</span>
                      <span className="ml-auto font-semibold text-gray-900">
                        {new Date(project.created_at).toLocaleDateString()}
                      </span>
                    </div>
                    {project.owner_name && (
                      <div className="flex items-center text-sm bg-white rounded-lg p-3 shadow-sm">
                        <User className="h-5 w-5 text-blue-600 mr-3" />
                        <span className="text-gray-600">Owner:</span>
                        <span className="ml-auto font-semibold text-gray-900">{project.owner_name}</span>
                      </div>
                    )}
                  </>
                )}
              </div>
            </div>

            {/* Building Parameters */}
            <div className="card bg-gradient-to-br from-purple-50 to-pink-50 border-2 border-purple-100">
              <div className="flex items-center mb-4">
                <div className="bg-gradient-to-br from-purple-600 to-pink-600 rounded-lg p-2.5 mr-3">
                  <TrendingUp className="h-5 w-5 text-white" />
                </div>
                <h3 className="text-lg font-semibold text-gray-900">Building Parameters</h3>
              </div>
              <div className="space-y-2">
                {isEditMode ? (
                  <>
                    <div className="bg-white rounded-lg p-3 shadow-sm">
                      <label className="block text-xs text-gray-600 mb-1">Site Area (m²)</label>
                      <input
                        type="number"
                        value={editedProject.site_area || ''}
                        onChange={(e) => setEditedProject({ ...editedProject, site_area: Number(e.target.value) })}
                        className="w-full px-2 py-1 border border-gray-300 rounded text-sm"
                      />
                    </div>
                    <div className="bg-white rounded-lg p-3 shadow-sm">
                      <label className="block text-xs text-gray-600 mb-1">Building Coverage (%)</label>
                      <input
                        type="number"
                        value={editedProject.building_coverage || ''}
                        onChange={(e) => setEditedProject({ ...editedProject, building_coverage: Number(e.target.value) })}
                        className="w-full px-2 py-1 border border-gray-300 rounded text-sm"
                      />
                    </div>
                    <div className="bg-white rounded-lg p-3 shadow-sm">
                      <label className="block text-xs text-gray-600 mb-1">Floor Area Ratio</label>
                      <input
                        type="number"
                        step="0.1"
                        value={editedProject.floor_area_ratio || ''}
                        onChange={(e) => setEditedProject({ ...editedProject, floor_area_ratio: Number(e.target.value) })}
                        className="w-full px-2 py-1 border border-gray-300 rounded text-sm"
                      />
                    </div>
                    <div className="bg-white rounded-lg p-3 shadow-sm">
                      <label className="block text-xs text-gray-600 mb-1">Number of Floors</label>
                      <input
                        type="number"
                        value={editedProject.num_floors || ''}
                        onChange={(e) => setEditedProject({ ...editedProject, num_floors: Number(e.target.value) })}
                        className="w-full px-2 py-1 border border-gray-300 rounded text-sm"
                      />
                    </div>
                    <div className="bg-white rounded-lg p-3 shadow-sm">
                      <label className="block text-xs text-gray-600 mb-1">Building Height (m)</label>
                      <input
                        type="number"
                        value={editedProject.building_height || ''}
                        onChange={(e) => setEditedProject({ ...editedProject, building_height: Number(e.target.value) })}
                        className="w-full px-2 py-1 border border-gray-300 rounded text-sm"
                      />
                    </div>
                    <div className="bg-white rounded-lg p-3 shadow-sm">
                      <label className="block text-xs text-gray-600 mb-1">Open Space (%)</label>
                      <input
                        type="number"
                        value={editedProject.open_space_percentage || ''}
                        onChange={(e) => setEditedProject({ ...editedProject, open_space_percentage: Number(e.target.value) })}
                        className="w-full px-2 py-1 border border-gray-300 rounded text-sm"
                      />
                    </div>
                    <div className="bg-white rounded-lg p-3 shadow-sm">
                      <label className="block text-xs text-gray-600 mb-1">Parking Spaces</label>
                      <input
                        type="number"
                        value={editedProject.parking_spaces || ''}
                        onChange={(e) => setEditedProject({ ...editedProject, parking_spaces: Number(e.target.value) })}
                        className="w-full px-2 py-1 border border-gray-300 rounded text-sm"
                      />
                    </div>
                  </>
                ) : (
                  <>
                    <div className="flex justify-between text-sm bg-white rounded-lg p-3 shadow-sm hover:shadow-md transition-shadow">
                      <span className="text-gray-600 font-medium">Site Area</span>
                      <span className="font-bold text-gray-900">{project.site_area} m²</span>
                    </div>
                    <div className="flex justify-between text-sm bg-white rounded-lg p-3 shadow-sm hover:shadow-md transition-shadow">
                      <span className="text-gray-600 font-medium">Building Coverage</span>
                      <span className="font-bold text-gray-900">{project.building_coverage}%</span>
                    </div>
                    <div className="flex justify-between text-sm bg-white rounded-lg p-3 shadow-sm hover:shadow-md transition-shadow">
                      <span className="text-gray-600 font-medium">Floor Area Ratio</span>
                      <span className="font-bold text-gray-900">{project.floor_area_ratio}</span>
                    </div>
                    <div className="flex justify-between text-sm bg-white rounded-lg p-3 shadow-sm hover:shadow-md transition-shadow">
                      <span className="text-gray-600 font-medium">Number of Floors</span>
                      <span className="font-bold text-gray-900">{project.num_floors}</span>
                    </div>
                    <div className="flex justify-between text-sm bg-white rounded-lg p-3 shadow-sm hover:shadow-md transition-shadow">
                      <span className="text-gray-600 font-medium">Building Height</span>
                      <span className="font-bold text-gray-900">{project.building_height} m</span>
                    </div>
                    <div className="flex justify-between text-sm bg-white rounded-lg p-3 shadow-sm hover:shadow-md transition-shadow">
                      <span className="text-gray-600 font-medium">Open Space</span>
                      <span className="font-bold text-gray-900">{project.open_space_percentage}%</span>
                    </div>
                    <div className="flex justify-between text-sm bg-white rounded-lg p-3 shadow-sm hover:shadow-md transition-shadow">
                      <span className="text-gray-600 font-medium">Parking Spaces</span>
                      <span className="font-bold text-gray-900">{project.parking_spaces}</span>
                    </div>
                  </>
                )}
              </div>
            </div>
          </div>

          {/* Right Column - Validation Results */}
          <div className="lg:col-span-2 space-y-6">

            {/* AI City Council (NEW) */}
            <div className="card border-2 border-indigo-100 bg-gradient-to-br from-indigo-50 to-white">
              <AICouncil projectId={project.id} />
            </div>

            {/* Compliance Score */}
            {validation && (
              <div className="card">
                <div className="flex items-center justify-between mb-6">
                  <h3 className="text-lg font-semibold text-gray-900">Compliance Analysis</h3>
                  {validating && <span className="text-sm text-gray-500">Validating...</span>}
                </div>

                <div className="mb-6">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-medium text-gray-700">Compliance Score</span>
                    <span className="text-2xl font-bold text-gray-900">
                      {validation.compliance_score?.toFixed(1) ?? '0.0'}%
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-3">
                    <div
                      className={`h-3 rounded-full transition-all ${(validation.compliance_score ?? 0) >= 80
                        ? 'bg-green-500'
                        : (validation.compliance_score ?? 0) >= 60
                          ? 'bg-yellow-500'
                          : 'bg-red-500'
                        }`}
                      style={{ width: `${validation.compliance_score ?? 0}%` }}
                    ></div>
                  </div>
                  <div className="flex items-center mt-2">
                    {validation.is_compliant ? (
                      <CheckCircle className="h-5 w-5 text-green-500 mr-2" />
                    ) : (
                      <XCircle className="h-5 w-5 text-red-500 mr-2" />
                    )}
                    <span className={`text-sm font-medium ${validation.is_compliant ? 'text-green-700' : 'text-red-700'}`}>
                      {validation.is_compliant ? 'Compliant with UDA regulations' : 'Non-compliant with UDA regulations'}
                    </span>
                  </div>
                </div>

                {/* Rules */}
                <div className="space-y-3">
                  <h4 className="text-sm font-semibold text-gray-700 flex items-center">
                    <Activity className="h-4 w-4 mr-2" />
                    Validation Rules ({validation.rules?.length ?? 0})
                  </h4>
                  {validation.rules?.map((rule, index) => {
                    const status = rule.is_valid ? 'PASS' : (rule.severity === 'ERROR' ? 'FAIL' : 'WARNING');
                    return (
                      <div
                        key={index}
                        className={`p-4 rounded-lg border ${status === 'PASS'
                          ? 'bg-green-50 border-green-200'
                          : status === 'FAIL'
                            ? 'bg-red-50 border-red-200'
                            : 'bg-yellow-50 border-yellow-200'
                          }`}
                      >
                        <div className="flex items-start">
                          {getRuleIcon(status)}
                          <div className="ml-3 flex-1">
                            <p className="text-sm font-medium text-gray-900">{rule.description || rule.rule_name || 'Validation Rule'}</p>
                            <p className="text-sm text-gray-600 mt-1">{rule.message}</p>
                            {!rule.is_valid && rule.severity && (
                              <span className={`inline-block mt-2 px-2 py-1 text-xs font-medium rounded-full ${rule.severity === 'ERROR'
                                ? 'bg-red-100 text-red-700'
                                : 'bg-yellow-100 text-yellow-700'
                                }`}>
                                {rule.severity}
                              </span>
                            )}
                          </div>
                        </div>
                      </div>
                    )
                  })}
                </div>

                {/* Recommendations */}
                {(validation.recommendations?.length ?? 0) > 0 && (
                  <div className="mt-6">
                    <h4 className="text-sm font-semibold text-gray-700 flex items-center mb-3">
                      <TrendingUp className="h-4 w-4 mr-2" />
                      Recommendations
                    </h4>
                    <div className="space-y-2">
                      {validation.recommendations?.map((rec, index) => (
                        <div key={index} className="flex items-start p-3 bg-blue-50 rounded-lg">
                          <div className="flex-shrink-0 mt-0.5">
                            <div className="h-2 w-2 rounded-full bg-blue-500"></div>
                          </div>
                          <p className="ml-3 text-sm text-gray-700">{rec}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}

            {!validation && !validating && (
              <div className="card text-center py-8">
                <Activity className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">No Validation Results</h3>
                <p className="text-gray-600 mb-4">Run validation to check UDA compliance</p>
                <button onClick={runValidation} className="btn-primary">
                  Run Validation
                </button>
              </div>
            )}

            {/* Approval History */}
            {approvalHistory.length > 0 && (
              <div className="card">
                <div className="flex items-center mb-4">
                  <div className="bg-gradient-to-br from-blue-600 to-indigo-600 rounded-lg p-2 mr-3">
                    <MessageSquare className="h-5 w-5 text-white" />
                  </div>
                  <h3 className="text-lg font-semibold text-gray-900">Approval History</h3>
                </div>
                <div className="space-y-4">
                  {approvalHistory.map((approval: any, index: number) => (
                    <div key={index} className="border-l-4 border-blue-500 pl-4 py-3 bg-gray-50 rounded-r-lg">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="flex items-center space-x-2 mb-1">
                            <User className="h-4 w-4 text-gray-500" />
                            <span className="text-sm font-semibold text-gray-900">{approval.user_name}</span>
                            <span className="text-xs text-gray-500">({approval.user_role})</span>
                          </div>
                          <div className="flex items-center space-x-2 mb-2">
                            <span className={`px-2 py-1 text-xs font-medium rounded-full ${approval.status_to === 'APPROVED'
                              ? 'bg-green-100 text-green-700'
                              : approval.status_to === 'REJECTED'
                                ? 'bg-red-100 text-red-700'
                                : 'bg-blue-100 text-blue-700'
                              }`}>
                              {approval.status_from} → {approval.status_to}
                            </span>
                            <span className="text-xs text-gray-500">
                              {new Date(approval.timestamp).toLocaleString()}
                            </span>
                          </div>
                          {approval.comment && (
                            <div className="mt-2 p-3 bg-white rounded-lg border border-gray-200">
                              <p className="text-sm text-gray-700">{approval.comment}</p>
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Blockchain Records */}
            <div className="card">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center">
                  <div className="bg-gradient-to-br from-purple-600 to-indigo-600 rounded-lg p-2 mr-3">
                    <Shield className="h-5 w-5 text-white" />
                  </div>
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900">Permanent Records</h3>
                    <p className="text-sm text-gray-500">Secure and tamper-proof document verification</p>
                  </div>
                </div>
                {blockchainStatus?.blockchain?.available && (
                  <div className="flex items-center space-x-2">
                    <div className="flex items-center">
                      <div className="h-2 w-2 bg-green-500 rounded-full mr-2 animate-pulse"></div>
                      <span className="text-xs text-gray-600">Connected</span>
                    </div>
                  </div>
                )}
              </div>

              {/* Blockchain Status */}
              {blockchainStatus && (
                <div className="mb-4 p-4 bg-gradient-to-r from-purple-50 to-indigo-50 rounded-lg border border-purple-200">
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div>
                      <p className="text-xs text-gray-600 mb-1">Verification Status</p>
                      <p className="text-sm font-medium text-gray-900">
                        {blockchainStatus.blockchain?.network?.includes('sepolia') ? 'Test Network' : 'Live Network'}
                      </p>
                    </div>
                    <div>
                      <p className="text-xs text-gray-600 mb-1">Backup Storage</p>
                      <p className="text-sm font-medium text-gray-900">
                        Cloud ({blockchainStatus.ipfs?.provider || 'Unknown'})
                      </p>
                    </div>
                    <div>
                      <p className="text-xs text-gray-600 mb-1">Saved Versions</p>
                      <p className="text-sm font-medium text-gray-900">
                        {blockchainRecords.length} stored
                      </p>
                    </div>
                  </div>
                </div>
              )}

              {/* Store on Blockchain Button */}
              <div className="mb-4">
                <button
                  onClick={() => storeOnBlockchain('DESIGN_HASH')}
                  disabled={storingOnBlockchain || !blockchainStatus?.blockchain?.available}
                  className="btn-primary w-full md:w-auto flex items-center justify-center disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {storingOnBlockchain ? (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                      Creating Permanent Record...
                    </>
                  ) : (
                    <>
                      <Lock className="h-4 w-4 mr-2" />
                      Save Permanent Record
                    </>
                  )}
                </button>
                {blockchainError && (
                  <p className="text-sm text-red-600 mt-2">{blockchainError}</p>
                )}
                {!blockchainStatus?.blockchain?.available && (
                  <p className="text-sm text-amber-600 mt-2">
                    ⚠️ Permanent record service is currently unavailable
                  </p>
                )}
              </div>

              {/* Blockchain Records List */}
              {blockchainRecords.length > 0 ? (
                <div className="space-y-3">
                  <h4 className="text-sm font-semibold text-gray-700 flex items-center">
                    <Database className="h-4 w-4 mr-2" />
                    Verified Document History
                  </h4>
                  {blockchainRecords.map((record: any, index: number) => (
                    <div key={record.id || index} className="border border-gray-200 rounded-lg p-4 bg-white hover:shadow-md transition-shadow">
                      <div className="flex items-start justify-between mb-3">
                        <div className="flex-1">
                          <div className="flex items-center space-x-2 mb-2">
                            <span className="px-2 py-1 text-xs font-medium rounded-full bg-purple-100 text-purple-700">
                              {record.record_type}
                            </span>
                            <span className="text-xs text-gray-500">
                              {new Date(record.created_at).toLocaleString()}
                            </span>
                          </div>

                          {record.metadata && (
                            <div className="text-xs text-gray-600 mb-2">
                              {Object.entries(record.metadata).map(([key, value]: [string, any]) => (
                                <span key={key} className="mr-3">
                                  <span className="font-medium">{key}:</span> {String(value)}
                                </span>
                              ))}
                            </div>
                          )}

                          <div className="grid grid-cols-1 gap-2 mt-2">
                            <div className="flex items-center text-xs">
                              <span className="text-gray-500 mr-2">Certificate ID:</span>
                              <code className="bg-gray-100 px-2 py-1 rounded text-xs font-mono">
                                {record.transaction_hash?.substring(0, 16)}...
                              </code>
                              <button
                                onClick={() => viewOnEtherscan(record.transaction_hash)}
                                className="ml-2 text-purple-600 hover:text-purple-800 flex items-center"
                                title="View verification certificate"
                              >
                                <ExternalLink className="h-3 w-3" />
                              </button>
                            </div>

                            <div className="flex items-center text-xs">
                              <span className="text-gray-500 mr-2">Document Storage:</span>
                              <code className="bg-gray-100 px-2 py-1 rounded text-xs font-mono">
                                {record.ipfs_hash?.substring(0, 16)}...
                              </code>
                              <button
                                onClick={() => viewOnIPFS(record.ipfs_hash)}
                                className="ml-2 text-purple-600 hover:text-purple-800 flex items-center"
                                title="View stored document"
                              >
                                <ExternalLink className="h-3 w-3" />
                              </button>
                            </div>

                            <div className="flex items-center text-xs">
                              <span className="text-gray-500 mr-2">Digital Fingerprint:</span>
                              <code className="bg-gray-100 px-2 py-1 rounded text-xs font-mono">
                                {record.data_hash?.substring(0, 32)}...
                              </code>
                            </div>
                          </div>
                        </div>
                      </div>

                      <div className="flex items-center justify-between pt-3 border-t border-gray-100">
                        <div className="flex items-center text-xs text-gray-500">
                          <CheckCircle className="h-3 w-3 mr-1 text-green-500" />
                          Permanently verified and secured
                        </div>
                        {record.created_by && (
                          <div className="text-xs text-gray-500">
                            By: {record.created_by}
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8 text-gray-500">
                  <Shield className="h-12 w-12 mx-auto mb-3 text-gray-300" />
                  <p className="text-sm font-medium">No permanent records yet</p>
                  <p className="text-xs mt-1">
                    Save this project as a permanent record for verification and audit purposes
                  </p>
                </div>
              )}

              {/* Info Box */}
              <div className="mt-4 p-4 bg-blue-50 rounded-lg border border-blue-200">
                <div className="flex items-start">
                  <div className="flex-shrink-0">
                    <Lock className="h-5 w-5 text-blue-600" />
                  </div>
                  <div className="ml-3">
                    <h4 className="text-sm font-medium text-blue-900">About Permanent Records</h4>
                    <div className="mt-2 text-xs text-blue-700 space-y-1">
                      <p>• Records are stored permanently and securely</p>
                      <p>• Document data is backed up on cloud storage</p>
                      <p>• Cannot be modified or deleted once saved</p>
                      <p>• Provides official proof of submission and approvals</p>
                      <p>• Publicly verifiable for transparency</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ProjectDetail;
