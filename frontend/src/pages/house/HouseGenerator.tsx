import toast from 'react-hot-toast';

import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  FileText,
  Upload,
  Box,
  Shield,
  CheckCircle,
  XCircle,
  AlertTriangle,
  Download,
  TrendingUp,
  ArrowLeft,
  Building2
} from 'lucide-react';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

const HouseGenerator = () => {
  const navigate = useNavigate();

  // State management
  const [prompt, setPrompt] = useState('');
  const [generatingFromPrompt, setGeneratingFromPrompt] = useState(false);
  const [promptModelUrl, setPromptModelUrl] = useState<string | null>(null);
  // Prompt-based 3D generation
  const generateHouseFromPrompt = async () => {
    if (!prompt) return;
    const token = localStorage.getItem('access_token');
    if (!token) {
      toast.error('Please log in to generate 3D models');
      navigate('/login');
      return;
    }
    setGeneratingFromPrompt(true);
    setPromptModelUrl(null);
    try {
      const response = await fetch(`${API_BASE_URL}/generation/text-to-3d`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ prompt })
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Generation failed' }));
        let errorMessage = errorData.detail || 'Failed to generate 3D model';

        // Handle object/array error details (e.g. from Pydantic)
        if (typeof errorMessage === 'object') {
          errorMessage = JSON.stringify(errorMessage);
        }

        throw new Error(errorMessage);
      }

      const data = await response.json();

      // Handle model URL logic
      let modelUrl = data.model_url || data.model_path;
      if (modelUrl && !modelUrl.startsWith('http')) {
        // Construct absolute URL if path is relative
        const apiOrigin = new URL(API_BASE_URL).origin;
        // Ensure modelUrl starts with /
        const cleanPath = modelUrl.startsWith('/') ? modelUrl : `/${modelUrl}`;
        modelUrl = `${apiOrigin}${cleanPath}`;
      }

      setPromptModelUrl(modelUrl || null);
      toast.success('3D house model generated from prompt!');
    } catch (err: any) {
      console.error('Prompt generation error:', err);
      toast.error('Failed to generate 3D house model from prompt: ' + (err.message || 'Unknown error'));
    } finally {
      setGeneratingFromPrompt(false);
    }
  };
  const [drawingFile, setDrawingFile] = useState<File | null>(null);
  const [uploadingDrawing, setUploadingDrawing] = useState(false);
  const [extractedData, setExtractedData] = useState<any>(null);
  const [generatingHouse, setGeneratingHouse] = useState(false);
  const [houseModelUrl, setHouseModelUrl] = useState<string | null>(null);
  const [udaValidation, setUdaValidation] = useState<any>(null);
  const [validatingUda, setValidatingUda] = useState(false);
  const [projectId, setProjectId] = useState<number | null>(null);

  // Building parameters for validation (user can edit)
  const [buildingParams, setBuildingParams] = useState({
    front_setback: 10,
    rear_setback: 10,
    side_setback: 5,
    building_coverage: 60,
    parking_spaces: 1
  });

  const handleDrawingFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      const fileExt = file.name.split('.').pop()?.toLowerCase();
      if (!['pdf', 'dwg', 'dxf'].includes(fileExt || '')) {
        toast.error('Please upload a PDF, DWG, or DXF file');
        return;
      }
      setDrawingFile(file);
    }
  };

  const uploadAndProcessDrawing = async () => {
    if (!drawingFile) return;

    const token = localStorage.getItem('access_token');
    if (!token) {
      toast.error('Please log in to upload drawings');
      navigate('/login');
      return;
    }

    setUploadingDrawing(true);
    try {
      // For now, use a temporary project ID (1) - in production, create a new project
      const tempProjectId = 1;
      setProjectId(tempProjectId);

      const formData = new FormData();
      formData.append('file', drawingFile);

      const response = await fetch(
        `${API_BASE_URL}/generation/${tempProjectId}/house/upload-drawing`,
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`
          },
          body: formData
        }
      );

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Upload failed' }));
        throw new Error(errorData.detail || 'Failed to upload drawing');
      }

      const data = await response.json();
      setExtractedData(data.extracted_data);

      toast.success(`Drawing processed successfully!\n\nExtracted Information:\n- Floor Count: ${data.extracted_data.floor_count}\n- Total Area: ${data.extracted_data.total_floor_area?.toFixed(1)}m²\n- Rooms Detected: ${data.extracted_data.rooms?.length || 0}`);

    } catch (err: any) {
      console.error('Upload error:', err);
      toast.error('Failed to process drawing: ' + (err.message || 'Unknown error'));
    } finally {
      setUploadingDrawing(false);
    }
  };

  const generateHouseFrom2D = async () => {
    if (!extractedData || !projectId) return;

    const token = localStorage.getItem('access_token');
    if (!token) {
      toast.error('Please log in to generate 3D models');
      navigate('/login');
      return;
    }

    setGeneratingHouse(true);
    try {
      const response = await fetch(
        `${API_BASE_URL}/generation/${projectId}/house/generate-from-drawing`,
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({ extracted_data: extractedData })
        }
      );

      if (!response.ok) {
        let errorMsg = 'Failed to generate 3D model';
        try {
          const errorData = await response.json();
          errorMsg = errorData.detail || errorMsg;
        } catch { }
        throw new Error(errorMsg);
      }

      const data = await response.json();
      setHouseModelUrl(data.model_url);

      toast.success('3D house model generated successfully from your 2D drawing!');

    } catch (err: any) {
      console.error('Generation error:', err);
      toast.error('Failed to generate 3D house model: ' + (err.message || 'Unknown error'));
    } finally {
      setGeneratingHouse(false);
    }
  };

  const validateAgainstUDA = async () => {
    if (!extractedData || !projectId) return;

    const token = localStorage.getItem('access_token');
    if (!token) {
      toast.error('Please log in to validate against UDA regulations');
      navigate('/login');
      return;
    }

    setValidatingUda(true);
    try {
      const buildingData = {
        building_width: extractedData.dimensions?.width || 10,
        building_length: extractedData.dimensions?.length || 12,
        building_height: (extractedData.dimensions?.height || 10) * extractedData.floor_count,
        floor_count: extractedData.floor_count || 1,
        total_floor_area: extractedData.total_floor_area || 0,
        building_coverage: buildingParams.building_coverage,
        parking_spaces: buildingParams.parking_spaces,
        rooms: extractedData.rooms || []
      };

      const plotData = {
        front_setback: buildingParams.front_setback,
        rear_setback: buildingParams.rear_setback,
        side_setback: buildingParams.side_setback
      };

      const response = await fetch(
        `${API_BASE_URL}/generation/${projectId}/house/validate-uda`,
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({ building_data: buildingData, plot_data: plotData })
        }
      );

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Validation failed' }));
        throw new Error(errorData.detail || 'UDA validation failed');
      }

      const data = await response.json();
      setUdaValidation(data.validation_report);

      if (data.validation_report.is_compliant) {
        toast.success(`UDA Validation Complete!\n\nCompliance: PASS ✓\nScore: ${data.validation_report.compliance_score}%\nViolations: ${data.validation_report.violations.length}\nWarnings: ${data.validation_report.warnings.length}`);
      } else {
        toast.error(`UDA Validation Complete!\n\nCompliance: FAIL ✗\nScore: ${data.validation_report.compliance_score}%\nViolations: ${data.validation_report.violations.length}\nWarnings: ${data.validation_report.warnings.length}`);
      }

    } catch (err: any) {
      console.error('UDA validation error:', err);
      toast.error('Failed to validate against UDA regulations: ' + (err.message || 'Unknown error'));
    } finally {
      setValidatingUda(false);
    }
  };

  const downloadHouseModel = async () => {
    if (!houseModelUrl && !promptModelUrl) {
      toast.error('No 3D model available to download');
      return;
    }

    const modelUrl = houseModelUrl || promptModelUrl;
    
    if (!modelUrl) {
      toast.error('No valid model URL available');
      return;
    }
    
    try {
      const response = await fetch(modelUrl, { mode: 'cors' });
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `house_model_${Date.now()}.glb`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);

      toast.success('House model downloaded successfully!');
    } catch (err: any) {
      console.error('Download error:', err);
      // Fallback: open in new tab if CORS fails
      if (modelUrl) {
        window.open(modelUrl, '_blank');
        toast('Opening model in new tab');
      }
    }
  };

  const resetForm = () => {
    setDrawingFile(null);
    setExtractedData(null);
    setHouseModelUrl(null);
    setUdaValidation(null);
    setProjectId(null);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-amber-50 via-orange-50 to-red-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <button
            onClick={() => navigate('/dashboard')}
            className="flex items-center text-primary-600 hover:text-primary-700 mb-4 font-medium transition-colors"
          >
            <ArrowLeft className="h-5 w-5 mr-2" />
            Back to Dashboard
          </button>

          <div className="bg-white rounded-2xl shadow-xl p-6 border border-gray-100">
            <div className="flex items-start justify-between">
              <div className="flex items-center space-x-4">
                <div className="p-3 bg-gradient-to-br from-amber-600 to-orange-600 rounded-xl shadow-md">
                  <Building2 className="h-8 w-8 text-white" />
                </div>
                <div>
                  <h1 className="text-3xl font-bold text-gray-900">2D Drawing to 3D House Generator</h1>
                  <p className="text-gray-600 mt-1">Upload floor plans and generate 3D models with UDA compliance analysis</p>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Prompt-based Generation Card */}
          <div className="card bg-gradient-to-br from-yellow-50 to-orange-50 border-2 border-yellow-100 mb-6">
            <div className="flex items-center mb-4">
              <div className="bg-gradient-to-br from-yellow-600 to-orange-600 rounded-lg p-2.5 mr-3">
                <Box className="h-5 w-5 text-white" />
              </div>
              <div>
                <h3 className="text-lg font-semibold text-gray-900">Generate 3D House from Prompt</h3>
                <p className="text-xs text-gray-600">Describe your house and generate a 3D model</p>
              </div>
            </div>
            <div className="space-y-3">
              <textarea
                className="w-full px-3 py-2 border border-gray-300 rounded text-sm"
                rows={3}
                placeholder="e.g. A modern two-story house with large windows and a flat roof"
                value={prompt}
                onChange={e => setPrompt(e.target.value)}
                disabled={generatingFromPrompt}
              />
              <button
                onClick={generateHouseFromPrompt}
                disabled={generatingFromPrompt || !prompt}
                className="w-full px-4 py-3 bg-gradient-to-r from-yellow-600 to-orange-600 hover:from-yellow-700 hover:to-orange-700 text-white font-semibold rounded-lg transition-all disabled:opacity-50 flex items-center justify-center shadow-md hover:shadow-lg"
              >
                {generatingFromPrompt ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                    Generating 3D Model...
                  </>
                ) : (
                  <>
                    <Box className="h-4 w-4 mr-2" />
                    Generate from Prompt
                  </>
                )}
              </button>
              {promptModelUrl && (
                <div className="bg-green-50 border-2 border-green-200 rounded-lg p-4 mt-2">
                  <div className="flex items-center mb-2">
                    <CheckCircle className="h-5 w-5 text-green-600 mr-2" />
                    <span className="text-sm font-semibold text-green-900">3D Model Ready</span>
                  </div>
                  <a
                    href={promptModelUrl}
                    download
                    className="inline-block px-4 py-2 bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-700 hover:to-emerald-700 text-white font-semibold rounded-lg transition-all shadow-md hover:shadow-lg"
                  >
                    <Download className="h-4 w-4 mr-2 inline" />
                    Download 3D Model
                  </a>
                </div>
              )}
            </div>
          </div>
          {/* Left Column - Upload and Generation */}
          <div className="lg:col-span-1 space-y-6">

            {/* File Upload Card */}
            <div className="card bg-gradient-to-br from-blue-50 to-indigo-50 border-2 border-blue-100">
              <div className="flex items-center mb-4">
                <div className="bg-gradient-to-br from-blue-600 to-indigo-600 rounded-lg p-2.5 mr-3">
                  <FileText className="h-5 w-5 text-white" />
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-gray-900">Upload 2D Drawing</h3>
                  <p className="text-xs text-gray-600">PDF, DWG, or DXF files</p>
                </div>
              </div>

              {!extractedData ? (
                <div className="space-y-3">
                  <div className="bg-white rounded-lg p-6 border-2 border-dashed border-blue-200">
                    <input
                      type="file"
                      accept=".pdf,.dwg,.dxf"
                      onChange={handleDrawingFileSelect}
                      className="hidden"
                      id="drawing-upload"
                    />
                    <label
                      htmlFor="drawing-upload"
                      className="cursor-pointer flex flex-col items-center"
                    >
                      <FileText className="h-16 w-16 text-blue-400 mb-3" />
                      <p className="text-sm font-medium text-gray-700 text-center">
                        {drawingFile ? drawingFile.name : 'Click to upload 2D drawing'}
                      </p>
                      <p className="text-xs text-gray-500 mt-1">PDF, DWG, or DXF files (Max 50MB)</p>
                    </label>
                  </div>

                  {drawingFile && (
                    <button
                      onClick={uploadAndProcessDrawing}
                      disabled={uploadingDrawing}
                      className="w-full px-4 py-3 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white font-semibold rounded-lg transition-all disabled:opacity-50 flex items-center justify-center shadow-md hover:shadow-lg"
                    >
                      {uploadingDrawing ? (
                        <>
                          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                          Processing Drawing...
                        </>
                      ) : (
                        <>
                          <Upload className="h-4 w-4 mr-2" />
                          Process Drawing
                        </>
                      )}
                    </button>
                  )}
                </div>
              ) : (
                <div className="space-y-3">
                  <div className="bg-green-50 border-2 border-green-200 rounded-lg p-4">
                    <div className="flex items-center mb-3">
                      <CheckCircle className="h-5 w-5 text-green-600 mr-2" />
                      <h4 className="text-sm font-semibold text-green-900">Drawing Processed Successfully</h4>
                    </div>
                    <div className="grid grid-cols-2 gap-2 text-xs">
                      <div className="bg-white rounded p-2">
                        <p className="text-gray-600">Floor Count</p>
                        <p className="font-bold text-gray-900">{extractedData.floor_count}</p>
                      </div>
                      <div className="bg-white rounded p-2">
                        <p className="text-gray-600">Total Area</p>
                        <p className="font-bold text-gray-900">{extractedData.total_floor_area?.toFixed(1)} m²</p>
                      </div>
                      <div className="bg-white rounded p-2">
                        <p className="text-gray-600">Rooms Detected</p>
                        <p className="font-bold text-gray-900">{extractedData.rooms?.length || 0}</p>
                      </div>
                      <div className="bg-white rounded p-2">
                        <p className="text-gray-600">File Type</p>
                        <p className="font-bold text-gray-900">{extractedData.file_type?.toUpperCase()}</p>
                      </div>
                    </div>
                  </div>

                  <button
                    onClick={resetForm}
                    className="w-full px-4 py-2 text-sm text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-lg transition-all"
                  >
                    Upload New Drawing
                  </button>
                </div>
              )}
            </div>

            {/* Building Parameters Card */}
            {extractedData && (
              <div className="card bg-gradient-to-br from-purple-50 to-pink-50 border-2 border-purple-100">
                <div className="flex items-center mb-4">
                  <div className="bg-gradient-to-br from-purple-600 to-pink-600 rounded-lg p-2.5 mr-3">
                    <TrendingUp className="h-5 w-5 text-white" />
                  </div>
                  <h3 className="text-lg font-semibold text-gray-900">Building Parameters</h3>
                </div>

                <div className="space-y-3">
                  <div className="bg-white rounded-lg p-3">
                    <label className="block text-xs text-gray-600 mb-1">Front Setback (feet)</label>
                    <input
                      type="number"
                      value={buildingParams.front_setback}
                      onChange={(e) => setBuildingParams({ ...buildingParams, front_setback: Number(e.target.value) })}
                      className="w-full px-2 py-1 border border-gray-300 rounded text-sm"
                    />
                  </div>
                  <div className="bg-white rounded-lg p-3">
                    <label className="block text-xs text-gray-600 mb-1">Rear Setback (feet)</label>
                    <input
                      type="number"
                      value={buildingParams.rear_setback}
                      onChange={(e) => setBuildingParams({ ...buildingParams, rear_setback: Number(e.target.value) })}
                      className="w-full px-2 py-1 border border-gray-300 rounded text-sm"
                    />
                  </div>
                  <div className="bg-white rounded-lg p-3">
                    <label className="block text-xs text-gray-600 mb-1">Side Setback (feet)</label>
                    <input
                      type="number"
                      value={buildingParams.side_setback}
                      onChange={(e) => setBuildingParams({ ...buildingParams, side_setback: Number(e.target.value) })}
                      className="w-full px-2 py-1 border border-gray-300 rounded text-sm"
                    />
                  </div>
                  <div className="bg-white rounded-lg p-3">
                    <label className="block text-xs text-gray-600 mb-1">Building Coverage (%)</label>
                    <input
                      type="number"
                      value={buildingParams.building_coverage}
                      onChange={(e) => setBuildingParams({ ...buildingParams, building_coverage: Number(e.target.value) })}
                      className="w-full px-2 py-1 border border-gray-300 rounded text-sm"
                    />
                  </div>
                  <div className="bg-white rounded-lg p-3">
                    <label className="block text-xs text-gray-600 mb-1">Parking Spaces</label>
                    <input
                      type="number"
                      value={buildingParams.parking_spaces}
                      onChange={(e) => setBuildingParams({ ...buildingParams, parking_spaces: Number(e.target.value) })}
                      className="w-full px-2 py-1 border border-gray-300 rounded text-sm"
                    />
                  </div>
                </div>
              </div>
            )}

            {/* Action Buttons */}
            {extractedData && (
              <div className="card bg-gradient-to-br from-green-50 to-emerald-50 border-2 border-green-100">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Actions</h3>

                <div className="space-y-3">
                  {!houseModelUrl && (
                    <button
                      onClick={generateHouseFrom2D}
                      disabled={generatingHouse}
                      className="w-full px-4 py-3 bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-700 hover:to-emerald-700 text-white font-semibold rounded-lg transition-all disabled:opacity-50 flex items-center justify-center shadow-md hover:shadow-lg"
                    >
                      {generatingHouse ? (
                        <>
                          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                          Generating 3D Model...
                        </>
                      ) : (
                        <>
                          <Box className="h-4 w-4 mr-2" />
                          Generate 3D House Model
                        </>
                      )}
                    </button>
                  )}

                  {houseModelUrl && (
                    <div className="bg-blue-50 border-2 border-blue-200 rounded-lg p-4">
                      <div className="flex items-center mb-3">
                        <CheckCircle className="h-5 w-5 text-blue-600 mr-2" />
                        <h4 className="text-sm font-semibold text-blue-900">3D Model Ready</h4>
                      </div>
                      <button
                        onClick={downloadHouseModel}
                        className="w-full px-4 py-2 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white font-semibold rounded-lg transition-all flex items-center justify-center shadow-md hover:shadow-lg"
                      >
                        <Download className="h-4 w-4 mr-2" />
                        Download House Model
                      </button>
                    </div>
                  )}

                  <button
                    onClick={validateAgainstUDA}
                    disabled={validatingUda}
                    className="w-full px-4 py-3 bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white font-semibold rounded-lg transition-all disabled:opacity-50 flex items-center justify-center shadow-md hover:shadow-lg"
                  >
                    {validatingUda ? (
                      <>
                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                        Validating...
                      </>
                    ) : (
                      <>
                        <Shield className="h-4 w-4 mr-2" />
                        Validate UDA Regulations
                      </>
                    )}
                  </button>
                </div>
              </div>
            )}
          </div>

          {/* Right Column - Results */}
          <div className="lg:col-span-2 space-y-6">

            {/* Extracted Rooms Details */}
            {extractedData && extractedData.rooms && extractedData.rooms.length > 0 && (
              <div className="card">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Detected Rooms</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  {extractedData.rooms.map((room: any, index: number) => (
                    <div key={index} className="bg-gray-50 rounded-lg p-3 border border-gray-200">
                      <h4 className="font-semibold text-gray-900 text-sm">{room.type}</h4>
                      <div className="mt-2 space-y-1 text-xs text-gray-600">
                        <p>Dimensions: {room.width}m × {room.length}m</p>
                        <p>Area: {room.area?.toFixed(2)} m²</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* UDA Validation Report */}
            {udaValidation && (
              <div className="card bg-gradient-to-br from-purple-50 to-pink-50 border-2 border-purple-200">
                <div className="flex items-center mb-4">
                  <div className="bg-gradient-to-br from-purple-600 to-pink-600 rounded-lg p-2.5 mr-3">
                    <Shield className="h-5 w-5 text-white" />
                  </div>
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900">UDA House Regulations Report</h3>
                    <p className="text-sm text-gray-600">Sri Lankan building standards compliance</p>
                  </div>
                </div>

                {/* Compliance Score */}
                <div className="mb-4 bg-white rounded-lg p-4">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-medium text-gray-700">UDA Compliance Score</span>
                    <span className="text-2xl font-bold text-gray-900">
                      {udaValidation.compliance_score?.toFixed(0)}%
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-3">
                    <div
                      className={`h-3 rounded-full transition-all ${udaValidation.compliance_score >= 80
                          ? 'bg-green-500'
                          : udaValidation.compliance_score >= 60
                            ? 'bg-yellow-500'
                            : 'bg-red-500'
                        }`}
                      style={{ width: `${udaValidation.compliance_score}%` }}
                    ></div>
                  </div>
                  <div className="flex items-center mt-2">
                    {udaValidation.is_compliant ? (
                      <CheckCircle className="h-5 w-5 text-green-500 mr-2" />
                    ) : (
                      <XCircle className="h-5 w-5 text-red-500 mr-2" />
                    )}
                    <span className={`text-sm font-medium ${udaValidation.is_compliant ? 'text-green-700' : 'text-red-700'}`}>
                      {udaValidation.is_compliant ? 'UDA Compliant' : 'Non-Compliant - Violations Found'}
                    </span>
                  </div>
                </div>

                {/* Violations */}
                {udaValidation.violations && udaValidation.violations.length > 0 && (
                  <div className="mb-4">
                    <h4 className="text-sm font-semibold text-red-700 flex items-center mb-2">
                      <XCircle className="h-4 w-4 mr-2" />
                      Violations ({udaValidation.violations.length})
                    </h4>
                    <div className="space-y-2">
                      {udaValidation.violations.map((violation: any, index: number) => (
                        <div key={index} className="bg-red-50 border-l-4 border-red-500 rounded-lg p-3">
                          <div className="flex items-start">
                            <XCircle className="h-4 w-4 text-red-600 mr-2 mt-0.5 flex-shrink-0" />
                            <div className="flex-1">
                              <p className="text-sm font-semibold text-red-900">{violation.rule}</p>
                              <p className="text-xs text-red-700 mt-1">{violation.message}</p>
                              <p className="text-xs text-red-600 mt-1 italic">{violation.regulation}</p>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Warnings */}
                {udaValidation.warnings && udaValidation.warnings.length > 0 && (
                  <div className="mb-4">
                    <h4 className="text-sm font-semibold text-yellow-700 flex items-center mb-2">
                      <AlertTriangle className="h-4 w-4 mr-2" />
                      Warnings ({udaValidation.warnings.length})
                    </h4>
                    <div className="space-y-2">
                      {udaValidation.warnings.map((warning: any, index: number) => (
                        <div key={index} className="bg-yellow-50 border-l-4 border-yellow-500 rounded-lg p-3">
                          <div className="flex items-start">
                            <AlertTriangle className="h-4 w-4 text-yellow-600 mr-2 mt-0.5 flex-shrink-0" />
                            <div className="flex-1">
                              <p className="text-sm font-semibold text-yellow-900">{warning.rule}</p>
                              <p className="text-xs text-yellow-700 mt-1">{warning.message}</p>
                              <p className="text-xs text-yellow-600 mt-1 italic">{warning.regulation}</p>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Passed Checks */}
                {udaValidation.passed_checks && udaValidation.passed_checks.length > 0 && (
                  <div className="mb-4">
                    <h4 className="text-sm font-semibold text-green-700 flex items-center mb-2">
                      <CheckCircle className="h-4 w-4 mr-2" />
                      Passed Checks ({udaValidation.passed_checks.length})
                    </h4>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                      {udaValidation.passed_checks.map((check: any, index: number) => (
                        <div key={index} className="bg-green-50 border border-green-200 rounded-lg p-2">
                          <div className="flex items-center">
                            <CheckCircle className="h-3 w-3 text-green-600 mr-2 flex-shrink-0" />
                            <p className="text-xs font-medium text-green-900">{check.rule}</p>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Recommendations */}
                {udaValidation.recommendations && udaValidation.recommendations.length > 0 && (
                  <div>
                    <h4 className="text-sm font-semibold text-blue-700 flex items-center mb-2">
                      <TrendingUp className="h-4 w-4 mr-2" />
                      Recommendations ({udaValidation.recommendations.length})
                    </h4>
                    <div className="space-y-2">
                      {udaValidation.recommendations.map((rec: any, index: number) => (
                        <div key={index} className="bg-blue-50 border-l-4 border-blue-400 rounded-lg p-3">
                          <p className="text-xs font-semibold text-blue-900">{rec.category}</p>
                          <p className="text-xs text-blue-700 mt-1">{rec.message}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Welcome Card - shown when no data */}
            {!extractedData && (
              <div className="card text-center py-12">
                <Building2 className="h-16 w-16 text-gray-300 mx-auto mb-4" />
                <h3 className="text-xl font-semibold text-gray-900 mb-2">Welcome to House Generator</h3>
                <p className="text-gray-600 max-w-md mx-auto">
                  Upload your 2D architectural drawings (PDF, DWG, or DXF) to generate 3D house models and
                  validate against Sri Lankan UDA building regulations.
                </p>
                <div className="mt-6 bg-blue-50 rounded-lg p-4 max-w-2xl mx-auto">
                  <h4 className="text-sm font-semibold text-blue-900 mb-2">Features:</h4>
                  <ul className="text-xs text-blue-700 space-y-1 text-left">
                    <li>✓ Automatic dimension extraction from floor plans</li>
                    <li>✓ Room detection and classification</li>
                    <li>✓ 3D house model generation</li>
                    <li>✓ UDA building regulations compliance check</li>
                    <li>✓ Detailed violation reports and recommendations</li>
                  </ul>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default HouseGenerator;
