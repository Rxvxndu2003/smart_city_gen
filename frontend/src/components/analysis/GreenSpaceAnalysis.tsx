import React, { useState } from 'react';
import {
    Card,
    CardContent,
    Typography,
    Button,
    TextField,
    Select,
    MenuItem,
    FormControl,
    InputLabel,
    Alert,
    LinearProgress,
    Box,
    CircularProgress,
    Chip,
    Stack
} from '@mui/material';
import { Trees, Leaf, ThermometerSun, Wind, CheckCircle, XCircle, AlertCircle } from 'lucide-react';
import axios from 'axios';

interface GreenSpaceAnalysisProps {
    projectId: number;
    projectData?: any;
}

interface GreenSpaceResult {
    is_compliant: boolean;
    is_sustainable: boolean;
    green_space_percentage: number;
    min_required_percentage: number;
    recommended_percentage: number;
    areas: {
        total_area_m2: number;
        building_footprint_m2: number;
        available_green_space_m2: number;
        min_required_m2: number;
        recommended_m2: number;
    };
    parks: {
        total_parks: number;
        park_area_m2: number;
        garden_area_m2: number;
        landscaping_area_m2: number;
        park_types: string[];
    };
    trees: {
        min_trees: number;
        recommended_trees: number;
        min_canopy_area_m2: number;
        recommended_canopy_area_m2: number;
    };
    environmental_benefits: {
        temperature_reduction_celsius: number;
        annual_co2_absorption_kg: number;
        air_quality_score: number;
        biodiversity_score: number;
    };
    recommendations: string[];
    compliance_status: string;
}

const GreenSpaceAnalysis: React.FC<GreenSpaceAnalysisProps> = ({ projectId, projectData }) => {
    const [loading, setLoading] = useState(false);
    const [result, setResult] = useState<GreenSpaceResult | null>(null);
    const [error, setError] = useState<string | null>(null);

    const [formData, setFormData] = useState({
        total_area: '',
        building_type: 'residential',
        num_buildings: '',
        building_footprint: ''
    });

    // Auto-populate from project data
    React.useEffect(() => {
        if (projectData) {
            const footprint = projectData.site_area && projectData.building_coverage
                ? (projectData.site_area * projectData.building_coverage / 100).toFixed(2)
                : '';

            setFormData(prev => ({
                ...prev,
                total_area: projectData.site_area?.toString() || prev.total_area,
                building_type: projectData.project_type?.toLowerCase() || 'residential',
                building_footprint: footprint || prev.building_footprint,
                num_buildings: '1' // Default assumption
            }));
        }
    }, [projectData]);

    React.useEffect(() => {
        const fetchAnalysis = async () => {
            try {
                const token = localStorage.getItem('access_token');
                if (!token) return;

                const response = await axios.get(`/api/v1/green-space/${projectId}/report`, {
                    headers: { 'Authorization': `Bearer ${token}` }
                });

                if (response.data.success && response.data.green_space_analysis) {
                    setResult(response.data.green_space_analysis);
                }
            } catch (err) {
                console.error("Failed to fetch existing analysis", err);
            }
        };

        fetchAnalysis();
    }, [projectId]);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        setError(null);

        try {
            const token = localStorage.getItem('access_token');
            if (!token) {
                setError('Authentication required. Please log in.');
                setLoading(false);
                return;
            }

            const response = await axios.post('/api/v1/green-space/calculate', {
                project_id: projectId,
                total_area: parseFloat(formData.total_area),
                building_type: formData.building_type,
                num_buildings: parseInt(formData.num_buildings),
                building_footprint: parseFloat(formData.building_footprint)
            }, {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            setResult(response.data.green_space_analysis);
        } catch (err: any) {
            setError(err.response?.data?.detail || 'Failed to calculate green space');
        } finally {
            setLoading(false);
        }
    };

    return (
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
            <Card>
                <CardContent>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                        <Trees style={{ color: '#16a34a' }} size={24} />
                        <Typography variant="h5" component="h2" fontWeight="bold">
                            Green Space Optimization
                        </Typography>
                    </Box>
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                        Smart green space planning with environmental impact analysis, biodiversity scoring, and urban heat mitigation
                    </Typography>

                    <form onSubmit={handleSubmit}>
                        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                            <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
                                <Box sx={{ flex: '1 1 calc(50% - 8px)', minWidth: '250px' }}>
                                    <TextField
                                        fullWidth
                                        label="Total Project Area (m²)"
                                        type="number"
                                        required
                                        value={formData.total_area}
                                        onChange={(e) => setFormData({ ...formData, total_area: e.target.value })}
                                        placeholder="Enter site area (e.g., 25,000 m²)"
                                        inputProps={{ step: '0.01', min: '0' }}
                                        helperText="Complete project site boundary area"
                                    />
                                </Box>

                                <Box sx={{ flex: '1 1 calc(50% - 8px)', minWidth: '250px' }}>
                                    <TextField
                                        fullWidth
                                        label="Building Footprint (m²)"
                                        type="number"
                                        required
                                        value={formData.building_footprint}
                                        onChange={(e) => setFormData({ ...formData, building_footprint: e.target.value })}
                                        placeholder="Enter covered area (e.g., 8,500 m²)"
                                        inputProps={{ step: '0.01', min: '0' }}
                                        helperText="Total ground area occupied by structures"
                                    />
                                </Box>

                                <Box sx={{ flex: '1 1 calc(50% - 8px)', minWidth: '250px' }}>
                                    <TextField
                                        fullWidth
                                        label="Number of Buildings"
                                        type="number"
                                        required
                                        value={formData.num_buildings}
                                        onChange={(e) => setFormData({ ...formData, num_buildings: e.target.value })}
                                        placeholder="Enter building count (e.g., 8 buildings)"
                                        inputProps={{ min: '1' }}
                                        helperText="Total structures in the project"
                                    />
                                </Box>

                                <Box sx={{ flex: '1 1 calc(50% - 8px)', minWidth: '250px' }}>
                                    <FormControl fullWidth>
                                        <InputLabel>Development Type</InputLabel>
                                        <Select
                                            value={formData.building_type}
                                            label="Development Type"
                                            onChange={(e) => setFormData({ ...formData, building_type: e.target.value })}
                                        >
                                            <MenuItem value="residential">Residential (15% min)</MenuItem>
                                            <MenuItem value="commercial">Commercial (10% min)</MenuItem>
                                            <MenuItem value="mixed">Mixed Use (12.5% min)</MenuItem>
                                        </Select>
                                    </FormControl>
                                </Box>
                            </Box>
                        </Box>

                        <Button
                            type="submit"
                            variant="contained"
                            fullWidth
                            disabled={loading}
                            sx={{ mt: 3 }}
                            startIcon={loading ? <CircularProgress size={20} /> : <Leaf size={20} />}
                        >
                            {loading ? 'Calculating...' : 'Calculate Green Space'}
                        </Button>
                    </form>

                    {error && (
                        <Alert severity="error" sx={{ mt: 2 }} icon={<AlertCircle size={20} />}>
                            {error}
                        </Alert>
                    )}
                </CardContent>
            </Card>

            {result && (
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                    {/* Compliance Status */}
                    <Card
                        sx={{
                            border: 2,
                            borderColor: result.is_compliant ? '#22c55e' : '#ef4444',
                            bgcolor: result.is_compliant ? '#f0fdf4' : '#fef2f2'
                        }}
                    >
                        <CardContent sx={{ textAlign: 'center', pt: 3 }}>
                            {result.is_compliant ? (
                                <CheckCircle size={64} style={{ color: '#16a34a', margin: '0 auto 16px' }} />
                            ) : (
                                <XCircle size={64} style={{ color: '#dc2626', margin: '0 auto 16px' }} />
                            )}
                            <Typography variant="h2" fontWeight="bold" sx={{ mb: 1 }}>
                                {result.green_space_percentage.toFixed(1)}%
                            </Typography>
                            <Typography variant="h6" fontWeight="medium" sx={{ mb: 2 }}>
                                Green Space Coverage
                            </Typography>
                            <Box sx={{ display: 'flex', justifyContent: 'center', gap: 1, mb: 2 }}>
                                <Chip
                                    label={result.compliance_status}
                                    color={result.is_compliant ? "success" : "error"}
                                />
                                {result.is_sustainable && (
                                    <Chip label="Sustainable" sx={{ bgcolor: '#16a34a', color: 'white' }} />
                                )}
                            </Box>
                            <Typography variant="body2" color="text.secondary">
                                Minimum Required: {result.min_required_percentage}% | Recommended: {result.recommended_percentage}%
                            </Typography>
                        </CardContent>
                    </Card>

                    {/* Area Breakdown */}
                    <Card>
                        <CardContent>
                            <Typography variant="h6" fontWeight="bold" sx={{ mb: 2 }}>
                                Area Distribution
                            </Typography>
                            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                                <Box>
                                    <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                                        <Typography variant="body2" fontWeight="medium">Total Project Area</Typography>
                                        <Typography variant="body2" fontWeight="bold">
                                            {result.areas.total_area_m2.toFixed(0)} m²
                                        </Typography>
                                    </Box>
                                </Box>

                                <Box>
                                    <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                                        <Typography variant="body2" fontWeight="medium">Building Footprint</Typography>
                                        <Typography variant="body2" color="text.secondary">
                                            {result.areas.building_footprint_m2.toFixed(0)} m²
                                        </Typography>
                                    </Box>
                                    <LinearProgress
                                        variant="determinate"
                                        value={(result.areas.building_footprint_m2 / result.areas.total_area_m2) * 100}
                                        sx={{ height: 8, borderRadius: 1, bgcolor: '#e5e7eb' }}
                                    />
                                </Box>

                                <Box>
                                    <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                                        <Typography variant="body2" fontWeight="medium" sx={{ color: '#16a34a' }}>
                                            Available Green Space
                                        </Typography>
                                        <Typography variant="body2" fontWeight="bold" sx={{ color: '#16a34a' }}>
                                            {result.areas.available_green_space_m2.toFixed(0)} m²
                                        </Typography>
                                    </Box>
                                    <LinearProgress
                                        variant="determinate"
                                        value={(result.areas.available_green_space_m2 / result.areas.total_area_m2) * 100}
                                        sx={{ height: 8, borderRadius: 1 }}
                                    />
                                </Box>
                            </Box>
                        </CardContent>
                    </Card>

                    {/* Park Planning */}
                    <Card>
                        <CardContent>
                            <Typography variant="h6" fontWeight="bold" sx={{ mb: 2 }}>
                                Park & Garden Planning
                            </Typography>
                            <Stack direction="row" spacing={2} sx={{ mb: 2, flexWrap: "wrap" }}>
                                <Box sx={{ flex: "1 1 45%", minWidth: "300px" }}>
                                    <Box sx={{ textAlign: 'center', p: 2, bgcolor: '#f0fdf4', borderRadius: 2 }}>
                                        <Typography variant="h4" fontWeight="bold" sx={{ color: '#16a34a' }}>
                                            {result.parks.total_parks}
                                        </Typography>
                                        <Typography variant="body2" color="text.secondary">Parks</Typography>
                                    </Box>
                                </Box>
                                <Box sx={{ flex: "1 1 45%", minWidth: "300px" }}>
                                    <Box sx={{ textAlign: 'center', p: 2, bgcolor: '#ecfdf5', borderRadius: 2 }}>
                                        <Typography variant="h4" fontWeight="bold" sx={{ color: '#059669' }}>
                                            {result.parks.park_area_m2.toFixed(0)}
                                        </Typography>
                                        <Typography variant="body2" color="text.secondary">Park Area (m²)</Typography>
                                    </Box>
                                </Box>
                                <Box sx={{ flex: "1 1 45%", minWidth: "300px" }}>
                                    <Box sx={{ textAlign: 'center', p: 2, bgcolor: '#f7fee7', borderRadius: 2 }}>
                                        <Typography variant="h4" fontWeight="bold" sx={{ color: '#65a30d' }}>
                                            {result.parks.garden_area_m2.toFixed(0)}
                                        </Typography>
                                        <Typography variant="body2" color="text.secondary">Gardens (m²)</Typography>
                                    </Box>
                                </Box>
                                <Box sx={{ flex: "1 1 45%", minWidth: "300px" }}>
                                    <Box sx={{ textAlign: 'center', p: 2, bgcolor: '#f0fdfa', borderRadius: 2 }}>
                                        <Typography variant="h4" fontWeight="bold" sx={{ color: '#0f766e' }}>
                                            {result.parks.landscaping_area_m2.toFixed(0)}
                                        </Typography>
                                        <Typography variant="body2" color="text.secondary">Landscaping (m²)</Typography>
                                    </Box>
                                </Box>
                            </Stack>

                            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                                {result.parks.park_types.map((type, index) => (
                                    <Chip key={index} label={type} variant="outlined" />
                                ))}
                            </Box>
                        </CardContent>
                    </Card>

                    {/* Tree Coverage */}
                    <Card>
                        <CardContent>
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                                <Trees size={20} style={{ color: '#16a34a' }} />
                                <Typography variant="h6" fontWeight="bold">
                                    Tree Coverage Requirements
                                </Typography>
                            </Box>
                            <Stack direction="row" spacing={2} sx={{ flexWrap: "wrap" }}>
                                <Box sx={{ flex: "1 1 45%", minWidth: "300px" }}>
                                    <Box sx={{ p: 2, bgcolor: '#fef3c7', borderRadius: 2 }}>
                                        <Typography variant="body2" color="text.secondary" sx={{ mb: 0.5 }}>
                                            Minimum Trees
                                        </Typography>
                                        <Typography variant="h4" fontWeight="bold" sx={{ color: '#d97706' }}>
                                            {result.trees.min_trees}
                                        </Typography>
                                        <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5 }}>
                                            Canopy: {result.trees.min_canopy_area_m2.toFixed(0)} m²
                                        </Typography>
                                    </Box>
                                </Box>
                                <Box sx={{ flex: "1 1 45%", minWidth: "300px" }}>
                                    <Box sx={{ p: 2, bgcolor: '#f0fdf4', borderRadius: 2 }}>
                                        <Typography variant="body2" color="text.secondary" sx={{ mb: 0.5 }}>
                                            Recommended Trees
                                        </Typography>
                                        <Typography variant="h4" fontWeight="bold" sx={{ color: '#16a34a' }}>
                                            {result.trees.recommended_trees}
                                        </Typography>
                                        <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5 }}>
                                            Canopy: {result.trees.recommended_canopy_area_m2.toFixed(0)} m²
                                        </Typography>
                                    </Box>
                                </Box>
                            </Stack>
                        </CardContent>
                    </Card>

                    {/* Environmental Benefits */}
                    <Card>
                        <CardContent>
                            <Typography variant="h6" fontWeight="bold" sx={{ mb: 2 }}>
                                Environmental Benefits
                            </Typography>
                            <Stack direction="row" spacing={2} sx={{ flexWrap: "wrap" }}>
                                <Box sx={{ flex: "1 1 45%", minWidth: "300px" }}>
                                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, p: 2, bgcolor: '#eff6ff', borderRadius: 2 }}>
                                        <ThermometerSun size={32} style={{ color: '#2563eb' }} />
                                        <Box>
                                            <Typography variant="body2" color="text.secondary">
                                                Temperature Reduction
                                            </Typography>
                                            <Typography variant="h5" fontWeight="bold" sx={{ color: '#2563eb' }}>
                                                {result.environmental_benefits.temperature_reduction_celsius.toFixed(1)}°C
                                            </Typography>
                                        </Box>
                                    </Box>
                                </Box>

                                <Box sx={{ flex: "1 1 45%", minWidth: "300px" }}>
                                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, p: 2, bgcolor: '#f0fdf4', borderRadius: 2 }}>
                                        <Leaf size={32} style={{ color: '#16a34a' }} />
                                        <Box>
                                            <Typography variant="body2" color="text.secondary">
                                                CO₂ Absorption
                                            </Typography>
                                            <Typography variant="h5" fontWeight="bold" sx={{ color: '#16a34a' }}>
                                                {result.environmental_benefits.annual_co2_absorption_kg.toFixed(0)} kg/year
                                            </Typography>
                                        </Box>
                                    </Box>
                                </Box>

                                <Box sx={{ flex: "1 1 45%", minWidth: "300px" }}>
                                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, p: 2, bgcolor: '#ecfeff', borderRadius: 2 }}>
                                        <Wind size={32} style={{ color: '#0891b2' }} />
                                        <Box>
                                            <Typography variant="body2" color="text.secondary">
                                                Air Quality Score
                                            </Typography>
                                            <Typography variant="h5" fontWeight="bold" sx={{ color: '#0891b2' }}>
                                                {result.environmental_benefits.air_quality_score.toFixed(0)}/100
                                            </Typography>
                                        </Box>
                                    </Box>
                                </Box>

                                <Box sx={{ flex: "1 1 45%", minWidth: "300px" }}>
                                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, p: 2, bgcolor: '#faf5ff', borderRadius: 2 }}>
                                        <Trees size={32} style={{ color: '#9333ea' }} />
                                        <Box>
                                            <Typography variant="body2" color="text.secondary">
                                                Biodiversity Score
                                            </Typography>
                                            <Typography variant="h5" fontWeight="bold" sx={{ color: '#9333ea' }}>
                                                {result.environmental_benefits.biodiversity_score.toFixed(0)}/100
                                            </Typography>
                                        </Box>
                                    </Box>
                                </Box>
                            </Stack>
                        </CardContent>
                    </Card>

                    {/* Recommendations */}
                    <Card>
                        <CardContent>
                            <Typography variant="h6" fontWeight="bold" sx={{ mb: 2 }}>
                                Green Space Recommendations
                            </Typography>
                            <Box component="ul" sx={{ pl: 0, listStyle: 'none', display: 'flex', flexDirection: 'column', gap: 1 }}>
                                {result.recommendations.map((rec, index) => (
                                    <Box component="li" key={index} sx={{ display: 'flex', alignItems: 'flex-start', gap: 1 }}>
                                        <Typography sx={{ color: '#22c55e', mt: 0.5 }}>•</Typography>
                                        <Typography variant="body2">{rec}</Typography>
                                    </Box>
                                ))}
                            </Box>
                        </CardContent>
                    </Card>
                </Box>
            )}
        </Box>
    );
};

export default GreenSpaceAnalysis;
