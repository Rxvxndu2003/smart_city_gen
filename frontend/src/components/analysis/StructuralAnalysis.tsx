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
    Box,
    Grid,
    CircularProgress,
    Chip
} from '@mui/material';
import { Building2, Shield, AlertTriangle, CheckCircle2, AlertCircle } from 'lucide-react';
import axios from 'axios';

interface StructuralAnalysisProps {
    projectId: number;
    projectData?: any;
}

interface StructuralResult {
    is_structurally_safe: boolean;
    is_recommended_safety: boolean;
    safety_factor: number;
    loads: {
        dead_load_kn: number;
        live_load_kn: number;
        wind_load_kn: number;
        seismic_load_kn: number;
        total_design_load_kn: number;
    };
    foundation: {
        type: string;
        required_area_m2: number;
        required_depth_m: number;
        bearing_capacity_kn_m2: number;
    };
    material_strength_mpa: number;
    recommendations: string[];
    validation_status: string;
}

const StructuralAnalysis: React.FC<StructuralAnalysisProps> = ({ projectId, projectData }) => {
    const [loading, setLoading] = useState(false);
    const [result, setResult] = useState<StructuralResult | null>(null);
    const [error, setError] = useState<string | null>(null);

    const [formData, setFormData] = useState({
        building_height: '',
        num_floors: '',
        floor_area: '',
        building_type: 'residential',
        location_zone: 'low',
        foundation_type: 'shallow',
        material: 'concrete',
        wall_thickness: '0.23'
    });

    // Auto-populate from project data if available and form is empty
    React.useEffect(() => {
        if (projectData) {
            setFormData(prev => ({
                ...prev,
                building_height: projectData.building_height?.toString() || prev.building_height,
                num_floors: projectData.num_floors?.toString() || prev.num_floors,
                // Estimate floor area from site area and coverage if not explicit
                floor_area: projectData.site_area && projectData.building_coverage
                    ? ((projectData.site_area * projectData.building_coverage / 100) / (projectData.num_floors || 1)).toFixed(2)
                    : prev.floor_area,
                building_type: projectData.project_type?.toLowerCase() || 'residential'
            }));
        }
    }, [projectData]);


    React.useEffect(() => {
        const fetchAnalysis = async () => {
            try {
                const token = localStorage.getItem('access_token');
                if (!token) return;

                const response = await axios.get(`/api/v1/structural/${projectId}/report`, {
                    headers: { 'Authorization': `Bearer ${token}` }
                });

                if (response.data.success && response.data.structural_analysis) {
                    setResult(response.data.structural_analysis);
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

            const response = await axios.post('/api/v1/structural/validate', {
                project_id: projectId,
                building_height: parseFloat(formData.building_height),
                num_floors: parseInt(formData.num_floors),
                floor_area: parseFloat(formData.floor_area),
                building_type: formData.building_type,
                location_zone: formData.location_zone,
                foundation_type: formData.foundation_type,
                material: formData.material,
                wall_thickness: parseFloat(formData.wall_thickness)
            }, {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            setResult(response.data.structural_analysis);
        } catch (err: any) {
            setError(err.response?.data?.detail || 'Failed to validate structural integrity');
        } finally {
            setLoading(false);
        }
    };

    const getSafetyChip = () => {
        if (!result) return null;

        if (result.safety_factor >= 2.5) {
            return <Chip label={`Excellent (SF: ${result.safety_factor})`} color="success" />;
        } else if (result.safety_factor >= 2.0) {
            return <Chip label={`Adequate (SF: ${result.safety_factor})`} color="warning" />;
        } else {
            return <Chip label={`Unsafe (SF: ${result.safety_factor})`} color="error" />;
        }
    };

    return (
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
            <Card>
                <CardContent>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                        <Building2 style={{ color: '#3b82f6' }} size={24} />
                        <Typography variant="h5" component="h2" fontWeight="bold">
                            Structural Integrity Validation
                        </Typography>
                    </Box>
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                        Advanced structural safety validation with load capacity analysis and seismic risk assessment
                    </Typography>

                    <form onSubmit={handleSubmit}>
                        <Grid container spacing={2}>
                            <Grid size={{ xs: 12, md: 6 }}>
                                <TextField
                                    fullWidth
                                    label="Building Height (m)"
                                    type="number"
                                    required
                                    value={formData.building_height}
                                    onChange={(e) => setFormData({ ...formData, building_height: e.target.value })}
                                    placeholder="Enter total height (e.g., 45 meters)"
                                    inputProps={{ step: '0.1', min: '0' }}
                                    helperText="From ground level to roof peak"
                                />
                            </Grid>

                            <Grid size={{ xs: 12, md: 6 }}>
                                <TextField
                                    fullWidth
                                    label="Number of Floors"
                                    type="number"
                                    required
                                    value={formData.num_floors}
                                    onChange={(e) => setFormData({ ...formData, num_floors: e.target.value })}
                                    placeholder="Enter floor count (e.g., 15 floors)"
                                    inputProps={{ min: '1' }}
                                    helperText="Including ground floor and basement (if any)"
                                />
                            </Grid>

                            <Grid size={{ xs: 12, md: 6 }}>
                                <TextField
                                    fullWidth
                                    label="Floor Area (m²)"
                                    type="number"
                                    required
                                    value={formData.floor_area}
                                    onChange={(e) => setFormData({ ...formData, floor_area: e.target.value })}
                                    placeholder="Enter typical floor area (e.g., 1200 m²)"
                                    inputProps={{ step: '0.01', min: '0' }}
                                    helperText="Average area per floor for load calculations"
                                />
                            </Grid>

                            <Grid size={{ xs: 12, md: 6 }}>
                                <TextField
                                    fullWidth
                                    label="Wall Thickness (m)"
                                    type="number"
                                    required
                                    value={formData.wall_thickness}
                                    onChange={(e) => setFormData({ ...formData, wall_thickness: e.target.value })}
                                    placeholder="Enter wall thickness (e.g., 0.23 meters)"
                                    inputProps={{ step: '0.01', min: '0' }}
                                    helperText="Typical structural wall thickness"
                                />
                            </Grid>

                            <Grid size={{ xs: 12, md: 6 }}>
                                <FormControl fullWidth>
                                    <InputLabel>Building Type</InputLabel>
                                    <Select
                                        value={formData.building_type}
                                        label="Building Type"
                                        onChange={(e) => setFormData({ ...formData, building_type: e.target.value })}
                                    >
                                        <MenuItem value="residential">Residential</MenuItem>
                                        <MenuItem value="commercial">Commercial</MenuItem>
                                        <MenuItem value="office">Office</MenuItem>
                                        <MenuItem value="mixed">Mixed Use</MenuItem>
                                    </Select>
                                </FormControl>
                            </Grid>

                            <Grid size={{ xs: 12, md: 6 }}>
                                <FormControl fullWidth>
                                    <InputLabel>Seismic/Wind Zone</InputLabel>
                                    <Select
                                        value={formData.location_zone}
                                        label="Seismic/Wind Zone"
                                        onChange={(e) => setFormData({ ...formData, location_zone: e.target.value })}
                                    >
                                        <MenuItem value="low">Low Risk</MenuItem>
                                        <MenuItem value="medium">Medium Risk</MenuItem>
                                        <MenuItem value="high">High Risk</MenuItem>
                                    </Select>
                                </FormControl>
                            </Grid>

                            <Grid size={{ xs: 12, md: 6 }}>
                                <FormControl fullWidth>
                                    <InputLabel>Foundation Type</InputLabel>
                                    <Select
                                        value={formData.foundation_type}
                                        label="Foundation Type"
                                        onChange={(e) => setFormData({ ...formData, foundation_type: e.target.value })}
                                    >
                                        <MenuItem value="shallow">Shallow Foundation</MenuItem>
                                        <MenuItem value="deep">Deep Foundation</MenuItem>
                                        <MenuItem value="pile">Pile Foundation</MenuItem>
                                    </Select>
                                </FormControl>
                            </Grid>

                            <Grid size={{ xs: 12, md: 6 }}>
                                <FormControl fullWidth>
                                    <InputLabel>Primary Material</InputLabel>
                                    <Select
                                        value={formData.material}
                                        label="Primary Material"
                                        onChange={(e) => setFormData({ ...formData, material: e.target.value })}
                                    >
                                        <MenuItem value="concrete">Concrete (M25)</MenuItem>
                                        <MenuItem value="brick">Brick Masonry</MenuItem>
                                        <MenuItem value="steel">Structural Steel</MenuItem>
                                    </Select>
                                </FormControl>
                            </Grid>
                        </Grid>

                        <Button
                            type="submit"
                            variant="contained"
                            fullWidth
                            disabled={loading}
                            sx={{ mt: 3 }}
                            startIcon={loading ? <CircularProgress size={20} /> : <Shield size={20} />}
                        >
                            {loading ? 'Validating...' : 'Validate Structural Integrity'}
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
                    {/* Safety Status Card */}
                    <Card
                        sx={{
                            border: 2,
                            borderColor: result.is_structurally_safe ? '#22c55e' : '#ef4444',
                            bgcolor: result.is_structurally_safe ? '#f0fdf4' : '#fef2f2'
                        }}
                    >
                        <CardContent sx={{ textAlign: 'center', pt: 3 }}>
                            {result.is_structurally_safe ? (
                                <CheckCircle2 size={64} style={{ color: '#16a34a', margin: '0 auto 16px' }} />
                            ) : (
                                <AlertTriangle size={64} style={{ color: '#dc2626', margin: '0 auto 16px' }} />
                            )}
                            <Typography variant="h4" fontWeight="bold" sx={{ mb: 2 }}>
                                {result.validation_status}
                            </Typography>
                            <Box sx={{ mb: 2 }}>{getSafetyChip()}</Box>
                            <Typography variant="body2" color="text.secondary">
                                {result.is_recommended_safety
                                    ? 'Exceeds recommended safety standards'
                                    : result.is_structurally_safe
                                        ? 'Meets minimum safety requirements'
                                        : 'Does not meet safety requirements - redesign needed'}
                            </Typography>
                        </CardContent>
                    </Card>

                    {/* Load Analysis */}
                    <Card>
                        <CardContent>
                            <Typography variant="h6" fontWeight="bold" sx={{ mb: 2 }}>
                                Load Analysis
                            </Typography>
                            <Grid container spacing={2}>
                                <Grid size={{ xs: 6, md: 3 }}>
                                    <Box sx={{ textAlign: 'center', p: 2, bgcolor: '#eff6ff', borderRadius: 2 }}>
                                        <Typography variant="body2" color="text.secondary" sx={{ mb: 0.5 }}>
                                            Dead Load
                                        </Typography>
                                        <Typography variant="h6" fontWeight="bold" sx={{ color: '#2563eb' }}>
                                            {result.loads.dead_load_kn.toFixed(0)} kN
                                        </Typography>
                                    </Box>
                                </Grid>
                                <Grid size={{ xs: 6, md: 3 }}>
                                    <Box sx={{ textAlign: 'center', p: 2, bgcolor: '#faf5ff', borderRadius: 2 }}>
                                        <Typography variant="body2" color="text.secondary" sx={{ mb: 0.5 }}>
                                            Live Load
                                        </Typography>
                                        <Typography variant="h6" fontWeight="bold" sx={{ color: '#9333ea' }}>
                                            {result.loads.live_load_kn.toFixed(0)} kN
                                        </Typography>
                                    </Box>
                                </Grid>
                                <Grid size={{ xs: 6, md: 3 }}>
                                    <Box sx={{ textAlign: 'center', p: 2, bgcolor: '#ecfeff', borderRadius: 2 }}>
                                        <Typography variant="body2" color="text.secondary" sx={{ mb: 0.5 }}>
                                            Wind Load
                                        </Typography>
                                        <Typography variant="h6" fontWeight="bold" sx={{ color: '#0891b2' }}>
                                            {result.loads.wind_load_kn.toFixed(0)} kN
                                        </Typography>
                                    </Box>
                                </Grid>
                                <Grid size={{ xs: 6, md: 3 }}>
                                    <Box sx={{ textAlign: 'center', p: 2, bgcolor: '#fff7ed', borderRadius: 2 }}>
                                        <Typography variant="body2" color="text.secondary" sx={{ mb: 0.5 }}>
                                            Seismic Load
                                        </Typography>
                                        <Typography variant="h6" fontWeight="bold" sx={{ color: '#f97316' }}>
                                            {result.loads.seismic_load_kn.toFixed(0)} kN
                                        </Typography>
                                    </Box>
                                </Grid>
                            </Grid>

                            <Box sx={{ pt: 2, mt: 2, borderTop: 1, borderColor: 'divider' }}>
                                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                    <Typography fontWeight="bold">Total Design Load</Typography>
                                    <Typography variant="h5" fontWeight="bold">
                                        {result.loads.total_design_load_kn.toFixed(0)} kN
                                    </Typography>
                                </Box>
                            </Box>

                            <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
                                Material Strength: {result.material_strength_mpa} MPa
                            </Typography>
                        </CardContent>
                    </Card>

                    {/* Foundation Requirements */}
                    <Card>
                        <CardContent>
                            <Typography variant="h6" fontWeight="bold" sx={{ mb: 2 }}>
                                Foundation Requirements
                            </Typography>
                            <Grid container spacing={2}>
                                <Grid size={{ xs: 12, md: 4 }}>
                                    <Typography variant="body2" color="text.secondary" sx={{ mb: 0.5 }}>
                                        Type
                                    </Typography>
                                    <Typography fontWeight="bold" sx={{ textTransform: 'capitalize' }}>
                                        {result.foundation.type} Foundation
                                    </Typography>
                                </Grid>
                                <Grid size={{ xs: 12, md: 4 }}>
                                    <Typography variant="body2" color="text.secondary" sx={{ mb: 0.5 }}>
                                        Required Area
                                    </Typography>
                                    <Typography fontWeight="bold">
                                        {result.foundation.required_area_m2.toFixed(2)} m²
                                    </Typography>
                                </Grid>
                                <Grid size={{ xs: 12, md: 4 }}>
                                    <Typography variant="body2" color="text.secondary" sx={{ mb: 0.5 }}>
                                        Required Depth
                                    </Typography>
                                    <Typography fontWeight="bold">
                                        {result.foundation.required_depth_m.toFixed(2)} m
                                    </Typography>
                                </Grid>
                            </Grid>
                            <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
                                Bearing Capacity: {result.foundation.bearing_capacity_kn_m2} kN/m²
                            </Typography>
                        </CardContent>
                    </Card>

                    {/* Recommendations */}
                    <Card>
                        <CardContent>
                            <Typography variant="h6" fontWeight="bold" sx={{ mb: 2 }}>
                                Structural Recommendations
                            </Typography>
                            <Box component="ul" sx={{ pl: 0, listStyle: 'none', display: 'flex', flexDirection: 'column', gap: 1 }}>
                                {result.recommendations.map((rec, index) => (
                                    <Box component="li" key={index} sx={{ display: 'flex', alignItems: 'flex-start', gap: 1 }}>
                                        <Typography sx={{ color: '#3b82f6', mt: 0.5 }}>•</Typography>
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

export default StructuralAnalysis;
