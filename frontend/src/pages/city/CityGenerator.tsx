import React, { useState, useCallback, useEffect } from 'react';
import {
  Box,
  Button,
  Card,
  CardContent,
  TextField,
  Typography,
  Grid,
  CircularProgress,
  Alert,
  Tabs,
  Tab,
  LinearProgress,
  Paper,
  Chip,
} from '@mui/material';
import {
  Map as MapIcon,
  Download as DownloadIcon,
  ViewInAr as ViewInArIcon,
  Place as PlaceIcon,
} from '@mui/icons-material';
import { GoogleMap, Polygon, DrawingManager, useJsApiLoader } from '@react-google-maps/api';
import axios from 'axios';

const libraries: ("drawing" | "places")[] = ["drawing", "places"];

interface BoundingBox {
  north: number;
  south: number;
  east: number;
  west: number;
}

interface GenerationRequest {
  name: string;
  bounding_box?: BoundingBox;
  polygon?: number[][];
  place_name?: string;
  target_parcel_width: number;
  min_building_height: number;
  max_building_height: number;
  export_format: string;
  enable_advanced_details: boolean;
  enable_windows: boolean;
  enable_vehicles: boolean;
  enable_street_lights: boolean;
  enable_crosswalks: boolean;
  vehicle_spacing: number;
  tree_spacing: number;
}

interface GenerationStatus {
  generation_id: string;
  status: string;
  progress: number;
  message: string;
  data_file?: string;
  model_file?: string;
  error?: string;
}

const CityGenerator: React.FC = () => {
  const [tabValue, setTabValue] = useState(0);
  const [generationName, setGenerationName] = useState('');
  const [placeName, setPlaceName] = useState('');
  const [parcelWidth, setParcelWidth] = useState(15);
  const [minHeight, setMinHeight] = useState(8);
  const [maxHeight, setMaxHeight] = useState(30);
  const [exportFormat, setExportFormat] = useState('glb');

  // Advanced 3D details
  const [enableAdvancedDetails, setEnableAdvancedDetails] = useState(true);
  const [enableWindows, setEnableWindows] = useState(true);
  const [enableVehicles, setEnableVehicles] = useState(true);
  const [enableStreetLights, setEnableStreetLights] = useState(true);
  const [enableCrosswalks, setEnableCrosswalks] = useState(true);
  const [vehicleSpacing, setVehicleSpacing] = useState(20);
  const [treeSpacing] = useState(8); // Currently not configurable in UI

  const [polygon, setPolygon] = useState<google.maps.LatLng[]>([]);
  const [boundingBox, setBoundingBox] = useState<BoundingBox | null>(null);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const [generationId, setGenerationId] = useState<string | null>(null);
  const [status, setStatus] = useState<GenerationStatus | null>(null);

  // Hybrid Generation (NEW)
  const [enableAIEnhancement, setEnableAIEnhancement] = useState(false);
  const [enhancementStrength, setEnhancementStrength] = useState(0.7);
  const [numViews, setNumViews] = useState(4);
  const [estimatedCost, setEstimatedCost] = useState(0);
  const [useHybridMode, setUseHybridMode] = useState(false);

  // Google Maps
  const { isLoaded } = useJsApiLoader({
    googleMapsApiKey: import.meta.env.VITE_GOOGLE_MAPS_API_KEY || '',
    libraries,
  });

  const [, setMap] = useState<google.maps.Map | null>(null);
  const [mapCenter] = useState({ lat: 6.9271, lng: 79.8612 }); // Colombo, Sri Lanka

  // Poll status when generation is in progress
  useEffect(() => {
    if (!generationId || !status || status.status === 'completed' || status.status === 'failed') {
      return;
    }

    const interval = setInterval(async () => {
      try {
        const response = await axios.get(`/api/v1/city-generator/status/${generationId}`);
        setStatus(response.data);

        if (response.data.status === 'completed') {
          setSuccess('City generation completed successfully!');
          clearInterval(interval);
        } else if (response.data.status === 'failed') {
          setError(response.data.error || 'Generation failed');
          clearInterval(interval);
        }
      } catch (err) {
        console.error('Error polling status:', err);
      }
    }, 2000);

    return () => clearInterval(interval);
  }, [generationId, status]);

  const handlePolygonComplete = useCallback((poly: google.maps.Polygon) => {
    const path = poly.getPath();
    const coordinates: google.maps.LatLng[] = [];

    for (let i = 0; i < path.getLength(); i++) {
      coordinates.push(path.getAt(i));
    }

    setPolygon(coordinates);

    // Calculate bounding box
    const bounds = new google.maps.LatLngBounds();
    coordinates.forEach(coord => bounds.extend(coord));

    setBoundingBox({
      north: bounds.getNorthEast().lat(),
      south: bounds.getSouthWest().lat(),
      east: bounds.getNorthEast().lng(),
      west: bounds.getSouthWest().lng(),
    });

    // Remove the drawing
    poly.setMap(null);
  }, []);

  // Calculate estimated cost when settings change
  useEffect(() => {
    if (enableAIEnhancement) {
      const costPerImage = 0.0023; // SDXL cost
      setEstimatedCost(numViews * costPerImage);
    } else {
      setEstimatedCost(0);
    }
  }, [enableAIEnhancement, numViews]);

  const handleGenerate = async () => {
    setLoading(true);
    setError(null);
    setSuccess(null);
    setGenerationId(null);
    setStatus(null);

    try {
      // Validate input
      if (!generationName) {
        throw new Error('Please provide a name for this generation');
      }

      if (tabValue === 0 && !placeName) {
        throw new Error('Please enter a place name');
      }

      if (tabValue === 1 && polygon.length === 0) {
        throw new Error('Please draw a polygon on the map');
      }

      // Prepare request
      const request: GenerationRequest = {
        name: generationName,
        target_parcel_width: parcelWidth,
        min_building_height: minHeight,
        max_building_height: maxHeight,
        export_format: exportFormat,
        enable_advanced_details: enableAdvancedDetails,
        enable_windows: enableWindows,
        enable_vehicles: enableVehicles,
        enable_street_lights: enableStreetLights,
        enable_crosswalks: enableCrosswalks,
        vehicle_spacing: vehicleSpacing,
        tree_spacing: treeSpacing,
      };

      if (tabValue === 0) {
        request.place_name = placeName;
      } else {
        request.polygon = polygon.map(coord => [coord.lat(), coord.lng()]);
      }

      // Choose endpoint based on mode
      const endpoint = useHybridMode
        ? '/api/v1/city-generator/generate-hybrid'
        : '/api/v1/city-generator/generate';

      // Add hybrid-specific fields if using hybrid mode
      if (useHybridMode) {
        (request as any).enable_ai_enhancement = enableAIEnhancement;
        (request as any).enhancement_strength = enhancementStrength;
        (request as any).num_views = numViews;
      }

      // Submit generation request
      const response = await axios.post(endpoint, request);

      setGenerationId(response.data.generation_id);
      setStatus({
        generation_id: response.data.generation_id,
        status: 'queued',
        progress: 0,
        message: 'Task queued',
      });

    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Failed to start generation');
    } finally {
      setLoading(false);
    }
  };

  const handleDownloadModel = () => {
    if (status?.model_file) {
      // In production, serve files through proper endpoint
      window.open(`/api/v1/exports/download?file=${status.model_file}`, '_blank');
    }
  };

  const handleViewPreview = async () => {
    if (generationId) {
      try {
        const response = await axios.get(`/api/v1/city-generator/preview/${generationId}`);
        console.log('Preview data:', response.data);
        // TODO: Display preview data on map
      } catch (err) {
        console.error('Error loading preview:', err);
      }
    }
  };

  const clearPolygon = () => {
    setPolygon([]);
    setBoundingBox(null);
  };

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        <MapIcon sx={{ verticalAlign: 'middle', mr: 1 }} />
        Geo-Realistic City Generator
      </Typography>

      <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
        Generate 3D city models from real-world geographic data using OpenStreetMap
      </Typography>

      <Grid container spacing={3}>
        {/* Left Panel - Configuration */}
        <Grid size={{ xs: 12, md: 5 }}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Generation Settings
              </Typography>

              <TextField
                fullWidth
                label="Generation Name"
                value={generationName}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) => setGenerationName(e.target.value)}
                margin="normal"
                required
              />

              <Box sx={{ borderBottom: 1, borderColor: 'divider', mt: 2 }}>
                <Tabs value={tabValue} onChange={(_: React.SyntheticEvent, v: number) => setTabValue(v)}>
                  <Tab label="Place Name" icon={<PlaceIcon />} iconPosition="start" />
                  <Tab label="Draw Area" icon={<MapIcon />} iconPosition="start" />
                </Tabs>
              </Box>

              {tabValue === 0 && (
                <Box sx={{ mt: 2 }}>
                  <TextField
                    fullWidth
                    label="Place Name"
                    value={placeName}
                    onChange={(e: React.ChangeEvent<HTMLInputElement>) => setPlaceName(e.target.value)}
                    placeholder="e.g., Colombo Fort, Sri Lanka"
                    helperText="Enter a location to geocode"
                  />
                </Box>
              )}

              {tabValue === 1 && (
                <Box sx={{ mt: 2 }}>
                  <Alert severity="info" sx={{ mb: 2 }}>
                    Use the drawing tools on the map to select an area
                  </Alert>

                  {polygon.length > 0 && (
                    <Box>
                      <Chip
                        label={`${polygon.length} points selected`}
                        color="success"
                        onDelete={clearPolygon}
                        sx={{ mb: 1 }}
                      />
                      {boundingBox && (
                        <Typography variant="caption" display="block" color="text.secondary">
                          Bounds: {boundingBox.south.toFixed(4)}, {boundingBox.west.toFixed(4)} to{' '}
                          {boundingBox.north.toFixed(4)}, {boundingBox.east.toFixed(4)}
                        </Typography>
                      )}
                    </Box>
                  )}
                </Box>
              )}

              <Typography variant="subtitle2" sx={{ mt: 3, mb: 1 }}>
                Building Parameters
              </Typography>

              <TextField
                fullWidth
                type="number"
                label="Target Parcel Width (m)"
                value={parcelWidth}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) => setParcelWidth(Number(e.target.value))}
                margin="normal"
              />

              <Grid container spacing={2}>
                <Grid size={{ xs: 6 }}>
                  <TextField
                    fullWidth
                    type="number"
                    label="Min Building Height (m)"
                    value={minHeight}
                    onChange={(e: React.ChangeEvent<HTMLInputElement>) => setMinHeight(Number(e.target.value))}
                    margin="normal"
                  />
                </Grid>
                <Grid size={{ xs: 6 }}>
                  <TextField
                    fullWidth
                    type="number"
                    label="Max Building Height (m)"
                    value={maxHeight}
                    onChange={(e: React.ChangeEvent<HTMLInputElement>) => setMaxHeight(Number(e.target.value))}
                    margin="normal"
                  />
                </Grid>
              </Grid>

              <TextField
                fullWidth
                select
                label="Export Format"
                value={exportFormat}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) => setExportFormat(e.target.value)}
                margin="normal"
                SelectProps={{ native: true }}
              >
                <option value="glb">GLB (Binary)</option>
                <option value="gltf">GLTF (Separate)</option>
              </TextField>

              <Typography variant="subtitle2" sx={{ mt: 3, mb: 1 }}>
                Advanced 3D Details (Realistic Features)
              </Typography>

              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <Typography variant="body2">Enable Advanced Details</Typography>
                  <input
                    type="checkbox"
                    checked={enableAdvancedDetails}
                    onChange={(e) => setEnableAdvancedDetails(e.target.checked)}
                  />
                </Box>

                {enableAdvancedDetails && (
                  <>
                    <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', pl: 2 }}>
                      <Typography variant="body2">Windows on Buildings</Typography>
                      <input
                        type="checkbox"
                        checked={enableWindows}
                        onChange={(e) => setEnableWindows(e.target.checked)}
                      />
                    </Box>

                    <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', pl: 2 }}>
                      <Typography variant="body2">Vehicles on Roads</Typography>
                      <input
                        type="checkbox"
                        checked={enableVehicles}
                        onChange={(e) => setEnableVehicles(e.target.checked)}
                      />
                    </Box>

                    {enableVehicles && (
                      <TextField
                        fullWidth
                        type="number"
                        label="Vehicle Spacing (m)"
                        value={vehicleSpacing}
                        onChange={(e: React.ChangeEvent<HTMLInputElement>) => setVehicleSpacing(Number(e.target.value))}
                        size="small"
                        sx={{ pl: 4 }}
                        helperText="Distance between vehicles on roads"
                      />
                    )}

                    <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', pl: 2 }}>
                      <Typography variant="body2">Street Lights</Typography>
                      <input
                        type="checkbox"
                        checked={enableStreetLights}
                        onChange={(e) => setEnableStreetLights(e.target.checked)}
                      />
                    </Box>

                    <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', pl: 2 }}>
                      <Typography variant="body2">Crosswalk Markings</Typography>
                      <input
                        type="checkbox"
                        checked={enableCrosswalks}
                        onChange={(e) => setEnableCrosswalks(e.target.checked)}
                      />
                    </Box>

                    <Alert severity="info" sx={{ mt: 1, fontSize: '0.75rem' }}>
                      Advanced details add realism but increase generation time and file size
                    </Alert>
                  </>
                )}
              </Box>

              {/* Hybrid Generation (NEW) */}
              <Typography variant="subtitle2" sx={{ mt: 3, mb: 1 }}>
                🚀 Hybrid Generation (Blender + AI Enhancement)
              </Typography>

              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <Typography variant="body2">Enable Hybrid Mode</Typography>
                  <input
                    type="checkbox"
                    checked={useHybridMode}
                    onChange={(e) => setUseHybridMode(e.target.checked)}
                  />
                </Box>

                {useHybridMode && (
                  <>
                    <Alert severity="info" sx={{ fontSize: '0.75rem' }}>
                      Hybrid mode combines Blender's precise geometry with AI-powered photorealistic enhancement
                    </Alert>

                    <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', pl: 2 }}>
                      <Typography variant="body2">Enable AI Enhancement (Replicate)</Typography>
                      <input
                        type="checkbox"
                        checked={enableAIEnhancement}
                        onChange={(e) => setEnableAIEnhancement(e.target.checked)}
                      />
                    </Box>

                    {enableAIEnhancement && (
                      <>
                        <Box sx={{ pl: 4 }}>
                          <Typography variant="caption" gutterBottom>
                            Enhancement Strength: {(enhancementStrength * 100).toFixed(0)}%
                          </Typography>
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                            <Typography variant="caption">Subtle</Typography>
                            <input
                              type="range"
                              min="0"
                              max="1"
                              step="0.1"
                              value={enhancementStrength}
                              onChange={(e) => setEnhancementStrength(Number(e.target.value))}
                              style={{ flex: 1 }}
                            />
                            <Typography variant="caption">Strong</Typography>
                          </Box>
                        </Box>

                        <TextField
                          fullWidth
                          type="number"
                          label="Number of Camera Views"
                          value={numViews}
                          onChange={(e: React.ChangeEvent<HTMLInputElement>) => setNumViews(Number(e.target.value))}
                          size="small"
                          inputProps={{ min: 1, max: 8 }}
                          sx={{ pl: 4 }}
                          helperText="More views = better coverage but higher cost"
                        />

                        <Alert severity="success" sx={{ pl: 4, fontSize: '0.75rem' }}>
                          💰 Estimated Cost: ${estimatedCost.toFixed(4)} USD
                          <br />
                          ({numViews} views × $0.0023 per image)
                        </Alert>
                      </>
                    )}
                  </>
                )}
              </Box>

              <Button
                fullWidth
                variant="contained"
                color="primary"
                onClick={handleGenerate}
                disabled={loading || (status?.status === 'processing')}
                startIcon={<ViewInArIcon />}
                sx={{ mt: 3 }}
              >
                {loading ? 'Starting...' : 'Generate 3D City'}
              </Button>

              {error && (
                <Alert severity="error" sx={{ mt: 2 }}>
                  {error}
                </Alert>
              )}

              {success && (
                <Alert severity="success" sx={{ mt: 2 }}>
                  {success}
                </Alert>
              )}
            </CardContent>
          </Card>

          {/* Status Card */}
          {status && (
            <Card sx={{ mt: 2 }}>
              <CardContent>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                  <Typography variant="h6">Generation Status</Typography>
                  {status.status !== 'completed' && status.status !== 'failed' && (
                    <CircularProgress size={24} />
                  )}
                </Box>

                <Chip
                  label={status.status.toUpperCase()}
                  color={
                    status.status === 'completed' ? 'success' :
                      status.status === 'failed' ? 'error' :
                        'primary'
                  }
                  sx={{ mb: 2 }}
                />

                <Typography variant="body2" color="text.secondary" gutterBottom>
                  {status.message}
                </Typography>

                <LinearProgress
                  variant="determinate"
                  value={status.progress * 100}
                  sx={{ mt: 2, mb: 1 }}
                />

                <Typography variant="caption" color="text.secondary">
                  {Math.round(status.progress * 100)}% complete
                </Typography>

                {status.status === 'completed' && status.model_file && (
                  <Box sx={{ mt: 2 }}>
                    <Button
                      fullWidth
                      variant="outlined"
                      startIcon={<DownloadIcon />}
                      onClick={handleDownloadModel}
                    >
                      Download 3D Model
                    </Button>

                    <Button
                      fullWidth
                      variant="outlined"
                      startIcon={<MapIcon />}
                      onClick={handleViewPreview}
                      sx={{ mt: 1 }}
                    >
                      View Preview Data
                    </Button>
                  </Box>
                )}
              </CardContent>
            </Card>
          )}
        </Grid>

        {/* Right Panel - Map */}
        <Grid size={{ xs: 12, md: 7 }}>
          <Paper sx={{ height: '700px', position: 'relative' }}>
            {isLoaded ? (
              <GoogleMap
                mapContainerStyle={{ width: '100%', height: '100%' }}
                center={mapCenter}
                zoom={13}
                onLoad={setMap}
                options={{
                  mapTypeControl: true,
                  streetViewControl: false,
                }}
              >
                {tabValue === 1 && (
                  <DrawingManager
                    onPolygonComplete={handlePolygonComplete}
                    options={{
                      drawingControl: true,
                      drawingControlOptions: {
                        position: google.maps.ControlPosition.TOP_CENTER,
                        drawingModes: [google.maps.drawing.OverlayType.POLYGON],
                      },
                      polygonOptions: {
                        fillColor: '#2196F3',
                        fillOpacity: 0.3,
                        strokeColor: '#2196F3',
                        strokeWeight: 2,
                        editable: true,
                      },
                    }}
                  />
                )}

                {polygon.length > 0 && (
                  <Polygon
                    paths={polygon}
                    options={{
                      fillColor: '#4CAF50',
                      fillOpacity: 0.3,
                      strokeColor: '#4CAF50',
                      strokeWeight: 2,
                    }}
                  />
                )}
              </GoogleMap>
            ) : (
              <Box
                sx={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  height: '100%',
                }}
              >
                <CircularProgress />
              </Box>
            )}
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
};

export default CityGenerator;
