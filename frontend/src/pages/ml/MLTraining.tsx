import React, { useState, useEffect } from 'react';
import { Upload, Database, Brain, TrendingUp, AlertCircle, CheckCircle, Play, Download, Image as ImageIcon, Box, Sparkles } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

interface DatasetInfo {
  total_samples: number;
  samples: Array<{
    sample_id: string;
    added_at: string;
    metadata_path: string;
  }>;
  created_at?: string;
  updated_at?: string;
}

interface ModelInfo {
  model_available: boolean;
  model_metadata?: {
    loaded_at: string;
    model_path: string;
    model_version: string;
    trained_at: string;
  };
}

const MLTraining: React.FC = () => {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState<'dataset' | 'train' | 'generate'>('dataset');
  
  // Dataset state
  const [datasetInfo, setDatasetInfo] = useState<DatasetInfo | null>(null);
  const [floorPlanFile, setFloorPlanFile] = useState<File | null>(null);
  const [model3DFile, setModel3DFile] = useState<File | null>(null);
  const [metadata, setMetadata] = useState({
    rooms: '',
    bedrooms: '',
    bathrooms: '',
    floor_area: '',
    style: '',
    description: ''
  });
  
  // Training state
  const [modelInfo, setModelInfo] = useState<ModelInfo | null>(null);
  const [trainingConfig, setTrainingConfig] = useState({
    epochs: 100,
    batch_size: 16,
    learning_rate: 0.001,
    validation_split: 0.2
  });
  const [isTraining, setIsTraining] = useState(false);
  
  // Generation state
  const [generationFloorPlan, setGenerationFloorPlan] = useState<File | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [generatedModelUrl, setGeneratedModelUrl] = useState<string | null>(null);
  
  // Status messages
  const [message, setMessage] = useState<{ type: 'success' | 'error' | 'info', text: string } | null>(null);

  useEffect(() => {
    loadDatasetInfo();
    loadModelInfo();
  }, []);

  const loadDatasetInfo = async () => {
    try {
      const token = localStorage.getItem('access_token');
      if (!token) {
        setMessage({ type: 'error', text: 'Please login to access ML Training' });
        setTimeout(() => navigate('/login'), 2000);
        return;
      }
      
      const response = await fetch('http://localhost:8000/api/v1/generation/ml/dataset/info', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (response.status === 401) {
        setMessage({ type: 'error', text: 'Session expired. Please login again.' });
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        setTimeout(() => navigate('/login'), 2000);
        return;
      }
      
      if (response.ok) {
        const data = await response.json();
        setDatasetInfo(data.dataset);
      }
    } catch (error) {
      console.error('Failed to load dataset info:', error);
    }
  };

  const loadModelInfo = async () => {
    try {
      const token = localStorage.getItem('access_token');
      if (!token) return;
      
      const response = await fetch('http://localhost:8000/api/v1/generation/ml/model/info', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (response.status === 401) {
        return; // Already handled in loadDatasetInfo
      }
      
      if (response.ok) {
        const data = await response.json();
        setModelInfo(data);
      }
    } catch (error) {
      console.error('Failed to load model info:', error);
    }
  };

  const handleAddWithAutoFloorplan = async () => {
    if (!model3DFile) {
      setMessage({ type: 'error', text: 'Please select a 3D house image' });
      return;
    }

    try {
      const token = localStorage.getItem('access_token');
      if (!token) {
        setMessage({ type: 'error', text: 'Please login to add training data' });
        setTimeout(() => navigate('/login'), 2000);
        return;
      }

      const formData = new FormData();
      formData.append('house_3d_image', model3DFile);
      formData.append('floors', '2');
      formData.append('style', metadata.style || 'modern');
      
      const metadataObj = {
        rooms: metadata.rooms ? parseInt(metadata.rooms) : undefined,
        bedrooms: metadata.bedrooms ? parseInt(metadata.bedrooms) : undefined,
        bathrooms: metadata.bathrooms ? parseInt(metadata.bathrooms) : undefined,
        floor_area: metadata.floor_area ? parseFloat(metadata.floor_area) : undefined,
        description: metadata.description || undefined
      };
      
      formData.append('metadata', JSON.stringify(metadataObj));

      const response = await fetch('http://localhost:8000/api/v1/generation/ml/dataset/add-with-auto-floorplan', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        },
        body: formData
      });

      if (response.status === 401) {
        setMessage({ type: 'error', text: 'Session expired. Please login again.' });
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        setTimeout(() => navigate('/login'), 2000);
        return;
      }

      const data = await response.json();

      if (response.ok) {
        setMessage({ type: 'success', text: `✨ Training sample added with auto-generated floor plan! Dataset now has ${data.dataset_info.total_samples} samples.` });
        setModel3DFile(null);
        setMetadata({
          rooms: '',
          bedrooms: '',
          bathrooms: '',
          floor_area: '',
          style: '',
          description: ''
        });
        loadDatasetInfo();
      } else {
        setMessage({ type: 'error', text: data.detail || 'Failed to add training data' });
      }
    } catch (error) {
      setMessage({ type: 'error', text: 'Failed to add training data' });
      console.error(error);
    }
  };

  const handleAddTrainingData = async () => {
    if (!floorPlanFile || !model3DFile) {
      setMessage({ type: 'error', text: 'Please select both floor plan image and 3D model file' });
      return;
    }

    try {
      const token = localStorage.getItem('access_token');
      if (!token) {
        setMessage({ type: 'error', text: 'Please login to add training data' });
        setTimeout(() => navigate('/login'), 2000);
        return;
      }

      const formData = new FormData();
      formData.append('floor_plan_image', floorPlanFile);
      formData.append('model_3d_file', model3DFile);
      
      const metadataObj = {
        rooms: metadata.rooms ? parseInt(metadata.rooms) : undefined,
        bedrooms: metadata.bedrooms ? parseInt(metadata.bedrooms) : undefined,
        bathrooms: metadata.bathrooms ? parseInt(metadata.bathrooms) : undefined,
        floor_area: metadata.floor_area ? parseFloat(metadata.floor_area) : undefined,
        style: metadata.style || undefined,
        description: metadata.description || undefined
      };
      
      formData.append('metadata', JSON.stringify(metadataObj));

      const response = await fetch('http://localhost:8000/api/v1/generation/ml/dataset/add', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        },
        body: formData
      });

      if (response.status === 401) {
        setMessage({ type: 'error', text: 'Session expired. Please login again.' });
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        setTimeout(() => navigate('/login'), 2000);
        return;
      }

      const data = await response.json();

      if (response.ok) {
        setMessage({ type: 'success', text: `Training sample added! Dataset now has ${data.dataset_info.total_samples} samples.` });
        setFloorPlanFile(null);
        setModel3DFile(null);
        setMetadata({
          rooms: '',
          bedrooms: '',
          bathrooms: '',
          floor_area: '',
          style: '',
          description: ''
        });
        loadDatasetInfo();
      } else {
        setMessage({ type: 'error', text: data.detail || 'Failed to add training data' });
      }
    } catch (error) {
      setMessage({ type: 'error', text: 'Failed to add training data' });
      console.error(error);
    }
  };

  const handleStartTraining = async () => {
    if (!datasetInfo || datasetInfo.total_samples < 10) {
      setMessage({ type: 'error', text: 'Need at least 10 training samples to start training' });
      return;
    }

    try {
      const token = localStorage.getItem('access_token');
      if (!token) {
        setMessage({ type: 'error', text: 'Please login to start training' });
        setTimeout(() => navigate('/login'), 2000);
        return;
      }

      setIsTraining(true);
      
      const response = await fetch('http://localhost:8000/api/v1/generation/ml/train', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(trainingConfig)
      });

      if (response.status === 401) {
        setMessage({ type: 'error', text: 'Session expired. Please login again.' });
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        setIsTraining(false);
        setTimeout(() => navigate('/login'), 2000);
        return;
      }

      const data = await response.json();

      if (response.ok) {
        setMessage({ 
          type: 'success', 
          text: `Training started with ${data.config.training_samples} samples! This will run in the background.` 
        });
        
        // Reload model info after a delay
        setTimeout(() => {
          loadModelInfo();
          setIsTraining(false);
        }, 5000);
      } else {
        setMessage({ type: 'error', text: data.detail || 'Failed to start training' });
        setIsTraining(false);
      }
    } catch (error) {
      setMessage({ type: 'error', text: 'Failed to start training' });
      setIsTraining(false);
      console.error(error);
    }
  };

  const handleGenerateWithML = async () => {
    if (!generationFloorPlan) {
      setMessage({ type: 'error', text: 'Please select a floor plan image' });
      return;
    }

    if (!modelInfo?.model_available) {
      setMessage({ type: 'error', text: 'No trained model available. Please train a model first.' });
      return;
    }

    try {
      const token = localStorage.getItem('access_token');
      if (!token) {
        setMessage({ type: 'error', text: 'Please login to generate models' });
        setTimeout(() => navigate('/login'), 2000);
        return;
      }

      setIsGenerating(true);
      const formData = new FormData();
      formData.append('floor_plan_image', generationFloorPlan);

      // Use project ID 1 for demo (should be dynamic in production)
      const response = await fetch('http://localhost:8000/api/v1/generation/1/house/generate-ml', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        },
        body: formData
      });

      if (response.status === 401) {
        setMessage({ type: 'error', text: 'Session expired. Please login again.' });
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        setIsGenerating(false);
        setTimeout(() => navigate('/login'), 2000);
        return;
      }

      const data = await response.json();

      if (response.ok) {
        setMessage({ type: 'success', text: '3D house model generated using ML!' });
        setGeneratedModelUrl(data.download_url);
      } else {
        setMessage({ type: 'error', text: data.detail || 'Failed to generate 3D model' });
      }
    } catch (error) {
      setMessage({ type: 'error', text: 'Failed to generate 3D model' });
      console.error(error);
    } finally {
      setIsGenerating(false);
    }
  };

  const handleDownloadModel = async () => {
    if (!generatedModelUrl) return;
    
    try {
      const token = localStorage.getItem('access_token');
      if (!token) {
        setMessage({ type: 'error', text: 'Please login to download models' });
        return;
      }

      const response = await fetch(`http://localhost:8000${generatedModelUrl}`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.status === 401) {
        setMessage({ type: 'error', text: 'Session expired. Please login again.' });
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        setTimeout(() => navigate('/login'), 2000);
        return;
      }

      if (!response.ok) {
        throw new Error('Download failed');
      }

      // Create blob from response and trigger download
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'generated_house_model.glb';
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      
      setMessage({ type: 'success', text: 'Model downloaded successfully!' });
    } catch (error) {
      setMessage({ type: 'error', text: 'Failed to download model' });
      console.error(error);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-3">
            <Brain className="w-8 h-8 text-purple-600" />
            ML House Generator Training
          </h1>
          <p className="text-gray-600 mt-2">
            Train deep learning models on your 2D floor plans to generate accurate 3D house models
          </p>
        </div>

        {/* Status Message */}
        {message && (
          <div className={`mb-6 p-4 rounded-lg flex items-start gap-3 ${
            message.type === 'success' ? 'bg-green-50 border border-green-200' :
            message.type === 'error' ? 'bg-red-50 border border-red-200' :
            'bg-blue-50 border border-blue-200'
          }`}>
            {message.type === 'success' ? <CheckCircle className="w-5 h-5 text-green-600 mt-0.5" /> :
             message.type === 'error' ? <AlertCircle className="w-5 h-5 text-red-600 mt-0.5" /> :
             <AlertCircle className="w-5 h-5 text-blue-600 mt-0.5" />}
            <div>
              <p className={`font-medium ${
                message.type === 'success' ? 'text-green-800' :
                message.type === 'error' ? 'text-red-800' :
                'text-blue-800'
              }`}>
                {message.text}
              </p>
            </div>
            <button
              onClick={() => setMessage(null)}
              className="ml-auto text-gray-400 hover:text-gray-600"
            >
              ×
            </button>
          </div>
        )}

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Training Samples</p>
                <p className="text-3xl font-bold text-gray-900 mt-1">
                  {datasetInfo?.total_samples || 0}
                </p>
              </div>
              <Database className="w-12 h-12 text-blue-500" />
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Model Status</p>
                <p className="text-lg font-semibold text-gray-900 mt-1">
                  {modelInfo?.model_available ? 'Trained' : 'Not Trained'}
                </p>
              </div>
              {modelInfo?.model_available ? (
                <CheckCircle className="w-12 h-12 text-green-500" />
              ) : (
                <AlertCircle className="w-12 h-12 text-gray-400" />
              )}
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Minimum Required</p>
                <p className="text-3xl font-bold text-gray-900 mt-1">10</p>
              </div>
              <TrendingUp className="w-12 h-12 text-purple-500" />
            </div>
          </div>
        </div>

        {/* Tabs */}
        <div className="bg-white rounded-lg shadow mb-6">
          <div className="border-b border-gray-200">
            <nav className="flex -mb-px">
              <button
                onClick={() => setActiveTab('dataset')}
                className={`px-6 py-4 text-sm font-medium border-b-2 ${
                  activeTab === 'dataset'
                    ? 'border-purple-500 text-purple-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                <Database className="w-5 h-5 inline mr-2" />
                Dataset Management
              </button>
              <button
                onClick={() => setActiveTab('train')}
                className={`px-6 py-4 text-sm font-medium border-b-2 ${
                  activeTab === 'train'
                    ? 'border-purple-500 text-purple-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                <Brain className="w-5 h-5 inline mr-2" />
                Train Model
              </button>
              <button
                onClick={() => setActiveTab('generate')}
                className={`px-6 py-4 text-sm font-medium border-b-2 ${
                  activeTab === 'generate'
                    ? 'border-purple-500 text-purple-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                <Box className="w-5 h-5 inline mr-2" />
                Generate 3D
              </button>
            </nav>
          </div>

          <div className="p-6">
            {/* Dataset Tab */}
            {activeTab === 'dataset' && (
              <div className="space-y-6">
                {/* Quick Upload - Only 3D Images */}
                <div className="bg-gradient-to-r from-purple-50 to-pink-50 border-2 border-purple-200 rounded-lg p-6">
                  <div className="flex items-start gap-4">
                    <div className="bg-purple-100 p-3 rounded-lg">
                      <Upload className="w-6 h-6 text-purple-600" />
                    </div>
                    <div className="flex-1">
                      <h3 className="text-lg font-semibold text-purple-900 mb-2">
                        ✨ Quick Upload - Only Have 3D Images?
                      </h3>
                      <p className="text-sm text-purple-700 mb-4">
                        Don't have floor plans? No problem! Upload just your 3D house images and we'll auto-generate simplified floor plans for training.
                      </p>
                      
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {/* 3D Image Upload */}
                        <div>
                          <label className="block text-sm font-medium text-purple-900 mb-2">
                            Upload 3D House Image
                          </label>
                          <div className="border-2 border-dashed border-purple-300 rounded-lg p-4 text-center hover:border-purple-500 transition-colors bg-white">
                            <Box className="w-10 h-10 text-purple-400 mx-auto mb-2" />
                            <input
                              type="file"
                              accept="image/png,image/jpeg,image/jpg"
                              onChange={(e) => setModel3DFile(e.target.files?.[0] || null)}
                              className="hidden"
                              id="quick-3d-upload"
                            />
                            <label htmlFor="quick-3d-upload" className="cursor-pointer">
                              <span className="text-purple-600 hover:text-purple-700 font-medium">
                                Select image
                              </span>
                            </label>
                            <p className="text-xs text-gray-500 mt-1">PNG or JPG</p>
                            {model3DFile && (
                              <p className="text-sm text-green-600 mt-2 font-medium">
                                ✓ {model3DFile.name}
                              </p>
                            )}
                          </div>
                        </div>

                        {/* Quick Metadata */}
                        <div className="space-y-2">
                          <div>
                            <label className="block text-xs font-medium text-purple-900 mb-1">Style</label>
                            <select
                              value={metadata.style}
                              onChange={(e) => setMetadata({ ...metadata, style: e.target.value })}
                              className="w-full px-2 py-1.5 text-sm border border-purple-300 rounded focus:ring-purple-500 focus:border-purple-500"
                            >
                              <option value="modern">Modern</option>
                              <option value="traditional">Traditional</option>
                              <option value="contemporary">Contemporary</option>
                            </select>
                          </div>
                          <div className="grid grid-cols-3 gap-2">
                            <div>
                              <label className="block text-xs font-medium text-purple-900 mb-1">Rooms</label>
                              <input
                                type="number"
                                value={metadata.rooms}
                                onChange={(e) => setMetadata({ ...metadata, rooms: e.target.value })}
                                className="w-full px-2 py-1.5 text-sm border border-purple-300 rounded"
                                placeholder="5"
                              />
                            </div>
                            <div>
                              <label className="block text-xs font-medium text-purple-900 mb-1">Beds</label>
                              <input
                                type="number"
                                value={metadata.bedrooms}
                                onChange={(e) => setMetadata({ ...metadata, bedrooms: e.target.value })}
                                className="w-full px-2 py-1.5 text-sm border border-purple-300 rounded"
                                placeholder="3"
                              />
                            </div>
                            <div>
                              <label className="block text-xs font-medium text-purple-900 mb-1">Baths</label>
                              <input
                                type="number"
                                value={metadata.bathrooms}
                                onChange={(e) => setMetadata({ ...metadata, bathrooms: e.target.value })}
                                className="w-full px-2 py-1.5 text-sm border border-purple-300 rounded"
                                placeholder="2"
                              />
                            </div>
                          </div>
                        </div>
                      </div>

                      <button
                        onClick={handleAddWithAutoFloorplan}
                        disabled={!model3DFile}
                        className="mt-4 w-full bg-purple-600 text-white px-6 py-2.5 rounded-lg hover:bg-purple-700 disabled:bg-gray-300 disabled:cursor-not-allowed flex items-center justify-center gap-2 font-medium shadow-md"
                      >
                        <Sparkles className="w-5 h-5" />
                        Auto-Generate Floor Plan & Add to Dataset
                      </button>
                      <p className="text-xs text-purple-600 mt-2 text-center">
                        We'll create a simplified floor plan automatically from your 3D image!
                      </p>
                    </div>
                  </div>
                </div>

                {/* Divider */}
                <div className="relative">
                  <div className="absolute inset-0 flex items-center">
                    <div className="w-full border-t border-gray-300"></div>
                  </div>
                  <div className="relative flex justify-center text-sm">
                    <span className="px-4 bg-gray-50 text-gray-500">Or upload both files manually</span>
                  </div>
                </div>

                <div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">Add Training Sample (Manual)</h3>
                  <p className="text-sm text-gray-600 mb-6">`
                    Upload a 2D floor plan image and its corresponding 3D house model to train the AI.
                  </p>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {/* Floor Plan Upload */}
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        2D Floor Plan Image
                      </label>
                      <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center hover:border-purple-500 transition-colors">
                        <ImageIcon className="w-12 h-12 text-gray-400 mx-auto mb-3" />
                        <input
                          type="file"
                          accept="image/png,image/jpeg,image/jpg"
                          onChange={(e) => setFloorPlanFile(e.target.files?.[0] || null)}
                          className="hidden"
                          id="floor-plan-upload"
                        />
                        <label htmlFor="floor-plan-upload" className="cursor-pointer">
                          <span className="text-purple-600 hover:text-purple-700 font-medium">
                            Upload image
                          </span>
                          <span className="text-gray-500"> or drag and drop</span>
                        </label>
                        <p className="text-xs text-gray-500 mt-2">PNG or JPG (max 10MB)</p>
                        {floorPlanFile && (
                          <p className="text-sm text-green-600 mt-3 font-medium">
                            ✓ {floorPlanFile.name}
                          </p>
                        )}
                      </div>
                    </div>

                    {/* 3D Model Upload */}
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        3D House Model File
                      </label>
                      <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center hover:border-purple-500 transition-colors">
                        <Box className="w-12 h-12 text-gray-400 mx-auto mb-3" />
                        <input
                          type="file"
                          accept=".glb,.obj,.fbx"
                          onChange={(e) => setModel3DFile(e.target.files?.[0] || null)}
                          className="hidden"
                          id="model-3d-upload"
                        />
                        <label htmlFor="model-3d-upload" className="cursor-pointer">
                          <span className="text-purple-600 hover:text-purple-700 font-medium">
                            Upload model
                          </span>
                          <span className="text-gray-500"> or drag and drop</span>
                        </label>
                        <p className="text-xs text-gray-500 mt-2">GLB, OBJ, or FBX (max 50MB)</p>
                        {model3DFile && (
                          <p className="text-sm text-green-600 mt-3 font-medium">
                            ✓ {model3DFile.name}
                          </p>
                        )}
                      </div>
                    </div>
                  </div>

                  {/* Metadata Form */}
                  <div className="mt-6 grid grid-cols-2 md:grid-cols-3 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Total Rooms
                      </label>
                      <input
                        type="number"
                        value={metadata.rooms}
                        onChange={(e) => setMetadata({ ...metadata, rooms: e.target.value })}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-purple-500 focus:border-purple-500"
                        placeholder="e.g., 5"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Bedrooms
                      </label>
                      <input
                        type="number"
                        value={metadata.bedrooms}
                        onChange={(e) => setMetadata({ ...metadata, bedrooms: e.target.value })}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-purple-500 focus:border-purple-500"
                        placeholder="e.g., 3"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Bathrooms
                      </label>
                      <input
                        type="number"
                        value={metadata.bathrooms}
                        onChange={(e) => setMetadata({ ...metadata, bathrooms: e.target.value })}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-purple-500 focus:border-purple-500"
                        placeholder="e.g., 2"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Floor Area (sq.m)
                      </label>
                      <input
                        type="number"
                        step="0.1"
                        value={metadata.floor_area}
                        onChange={(e) => setMetadata({ ...metadata, floor_area: e.target.value })}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-purple-500 focus:border-purple-500"
                        placeholder="e.g., 150.5"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Style
                      </label>
                      <input
                        type="text"
                        value={metadata.style}
                        onChange={(e) => setMetadata({ ...metadata, style: e.target.value })}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-purple-500 focus:border-purple-500"
                        placeholder="e.g., Modern"
                      />
                    </div>
                    <div className="md:col-span-1">
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Description
                      </label>
                      <input
                        type="text"
                        value={metadata.description}
                        onChange={(e) => setMetadata({ ...metadata, description: e.target.value })}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-purple-500 focus:border-purple-500"
                        placeholder="Optional description"
                      />
                    </div>
                  </div>

                  <button
                    onClick={handleAddTrainingData}
                    disabled={!floorPlanFile || !model3DFile}
                    className="mt-6 w-full bg-purple-600 text-white px-6 py-3 rounded-lg hover:bg-purple-700 disabled:bg-gray-300 disabled:cursor-not-allowed flex items-center justify-center gap-2 font-medium"
                  >
                    <Upload className="w-5 h-5" />
                    Add to Training Dataset
                  </button>
                </div>

                {/* Dataset List */}
                {datasetInfo && datasetInfo.total_samples > 0 && (
                  <div className="mt-8">
                    <h4 className="text-md font-semibold text-gray-900 mb-3">
                      Training Samples ({datasetInfo.total_samples})
                    </h4>
                    <div className="bg-gray-50 rounded-lg p-4 max-h-60 overflow-y-auto">
                      {datasetInfo.samples.map((sample) => (
                        <div key={sample.sample_id} className="bg-white rounded p-3 mb-2 flex justify-between items-center">
                          <div>
                            <p className="text-sm font-medium text-gray-900">{sample.sample_id}</p>
                            <p className="text-xs text-gray-500">
                              Added: {new Date(sample.added_at).toLocaleString()}
                            </p>
                          </div>
                          <CheckCircle className="w-5 h-5 text-green-500" />
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Train Tab */}
            {activeTab === 'train' && (
              <div className="space-y-6">
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">Train ML Model</h3>
                  <p className="text-sm text-gray-600 mb-6">
                    Configure and train a deep learning model on your dataset. Training may take several hours depending on dataset size.
                  </p>

                  {datasetInfo && datasetInfo.total_samples < 10 && (
                    <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-6">
                      <div className="flex items-start gap-3">
                        <AlertCircle className="w-5 h-5 text-yellow-600 mt-0.5" />
                        <div>
                          <p className="font-medium text-yellow-800">Insufficient Training Data</p>
                          <p className="text-sm text-yellow-700 mt-1">
                            You need at least 10 training samples. Currently have {datasetInfo.total_samples}.
                            Add more samples in the Dataset Management tab.
                          </p>
                        </div>
                      </div>
                    </div>
                  )}

                  <div className="grid grid-cols-2 gap-4 mb-6">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Epochs
                      </label>
                      <input
                        type="number"
                        value={trainingConfig.epochs}
                        onChange={(e) => setTrainingConfig({ ...trainingConfig, epochs: parseInt(e.target.value) })}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-purple-500 focus:border-purple-500"
                        min="10"
                        max="1000"
                      />
                      <p className="text-xs text-gray-500 mt-1">Number of training iterations</p>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Batch Size
                      </label>
                      <input
                        type="number"
                        value={trainingConfig.batch_size}
                        onChange={(e) => setTrainingConfig({ ...trainingConfig, batch_size: parseInt(e.target.value) })}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-purple-500 focus:border-purple-500"
                        min="1"
                        max="64"
                      />
                      <p className="text-xs text-gray-500 mt-1">Samples per batch</p>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Learning Rate
                      </label>
                      <input
                        type="number"
                        step="0.0001"
                        value={trainingConfig.learning_rate}
                        onChange={(e) => setTrainingConfig({ ...trainingConfig, learning_rate: parseFloat(e.target.value) })}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-purple-500 focus:border-purple-500"
                        min="0.0001"
                        max="0.1"
                      />
                      <p className="text-xs text-gray-500 mt-1">Model learning rate</p>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Validation Split
                      </label>
                      <input
                        type="number"
                        step="0.05"
                        value={trainingConfig.validation_split}
                        onChange={(e) => setTrainingConfig({ ...trainingConfig, validation_split: parseFloat(e.target.value) })}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-purple-500 focus:border-purple-500"
                        min="0.1"
                        max="0.5"
                      />
                      <p className="text-xs text-gray-500 mt-1">Data for validation (0.0-1.0)</p>
                    </div>
                  </div>

                  <button
                    onClick={handleStartTraining}
                    disabled={!datasetInfo || datasetInfo.total_samples < 10 || isTraining}
                    className="w-full bg-purple-600 text-white px-6 py-3 rounded-lg hover:bg-purple-700 disabled:bg-gray-300 disabled:cursor-not-allowed flex items-center justify-center gap-2 font-medium"
                  >
                    {isTraining ? (
                      <>
                        <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                        Training in Progress...
                      </>
                    ) : (
                      <>
                        <Play className="w-5 h-5" />
                        Start Training
                      </>
                    )}
                  </button>

                  {modelInfo?.model_available && (
                    <div className="mt-6 bg-green-50 border border-green-200 rounded-lg p-4">
                      <div className="flex items-start gap-3">
                        <CheckCircle className="w-5 h-5 text-green-600 mt-0.5" />
                        <div className="flex-1">
                          <p className="font-medium text-green-800">Model Trained Successfully</p>
                          <div className="text-sm text-green-700 mt-2 space-y-1">
                            <p>Version: {modelInfo.model_metadata?.model_version}</p>
                            <p>Trained: {modelInfo.model_metadata?.trained_at ? new Date(modelInfo.model_metadata.trained_at).toLocaleString() : 'N/A'}</p>
                          </div>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Generate Tab */}
            {activeTab === 'generate' && (
              <div className="space-y-6">
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">Generate 3D House Model</h3>
                  <p className="text-sm text-gray-600 mb-6">
                    Upload a 2D floor plan and let the trained AI generate a 3D house model.
                  </p>

                  {!modelInfo?.model_available && (
                    <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-6">
                      <div className="flex items-start gap-3">
                        <AlertCircle className="w-5 h-5 text-yellow-600 mt-0.5" />
                        <div>
                          <p className="font-medium text-yellow-800">No Trained Model Available</p>
                          <p className="text-sm text-yellow-700 mt-1">
                            Please add training data and train a model before generating 3D models.
                          </p>
                        </div>
                      </div>
                    </div>
                  )}

                  <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center hover:border-purple-500 transition-colors">
                    <ImageIcon className="w-16 h-16 text-gray-400 mx-auto mb-4" />
                    <input
                      type="file"
                      accept="image/png,image/jpeg,image/jpg"
                      onChange={(e) => setGenerationFloorPlan(e.target.files?.[0] || null)}
                      className="hidden"
                      id="generation-upload"
                    />
                    <label htmlFor="generation-upload" className="cursor-pointer">
                      <span className="text-purple-600 hover:text-purple-700 font-medium text-lg">
                        Upload 2D Floor Plan
                      </span>
                      <span className="text-gray-500"> or drag and drop</span>
                    </label>
                    <p className="text-sm text-gray-500 mt-2">PNG or JPG (max 10MB)</p>
                    {generationFloorPlan && (
                      <p className="text-md text-green-600 mt-4 font-medium">
                        ✓ {generationFloorPlan.name}
                      </p>
                    )}
                  </div>

                  <button
                    onClick={handleGenerateWithML}
                    disabled={!generationFloorPlan || !modelInfo?.model_available || isGenerating}
                    className="mt-6 w-full bg-purple-600 text-white px-6 py-3 rounded-lg hover:bg-purple-700 disabled:bg-gray-300 disabled:cursor-not-allowed flex items-center justify-center gap-2 font-medium"
                  >
                    {isGenerating ? (
                      <>
                        <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                        Generating 3D Model...
                      </>
                    ) : (
                      <>
                        <Box className="w-5 h-5" />
                        Generate 3D House Model
                      </>
                    )}
                  </button>

                  {generatedModelUrl && (
                    <div className="mt-6 bg-green-50 border border-green-200 rounded-lg p-4">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <CheckCircle className="w-5 h-5 text-green-600" />
                          <p className="font-medium text-green-800">3D Model Generated Successfully!</p>
                        </div>
                        <button
                          onClick={handleDownloadModel}
                          className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 flex items-center gap-2"
                        >
                          <Download className="w-4 h-4" />
                          Download GLB
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default MLTraining;
