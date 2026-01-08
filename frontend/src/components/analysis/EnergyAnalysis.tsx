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
    Grid
} from '@mui/material';
import { Zap, Sun, Leaf, TrendingDown, AlertCircle, CheckCircle } from 'lucide-react';
import axios from 'axios';

interface EnergyAnalysisProps {
    projectId: number;
    projectData?: any;
}

interface EnergyResult {
    total_energy_kwh_year: number;
    energy_per_m2: number;
    rating: string;
    breakdown: {
        heating_cooling: number;
        lighting: number;
        appliances: number;
        solar_gain: number;
    };
    co2_emissions_kg_year: number;
    recommendations: string[];
    is_sustainable: boolean;
}

const EnergyAnalysis: React.FC<EnergyAnalysisProps> = ({ projectId, projectData }) => {
    const [loading, setLoading] = useState(false);
    const [result, setResult] = useState<EnergyResult | null>(null);
    const [error, setError] = useState<string | null>(null);

    const [formData, setFormData] = useState({
        floor_area: '',
        building_volume: '',
        window_area: '',
        orientation: 'north',
        insulation_quality: 'medium',
        num_floors: '1',
        building_type: 'residential'
    });

    // Auto-populate from project data
    React.useEffect(() => {
        if (projectData) {
            const floorArea = projectData.site_area && projectData.building_coverage && projectData.num_floors
                ? ((projectData.site_area * projectData.building_coverage / 100) * projectData.num_floors).toFixed(2)
                : '';

            const estimatedVolume = floorArea ? (parseFloat(floorArea) * 3).toFixed(2) : ''; // Assume 3m ceiling

            setFormData(prev => ({
                ...prev,
                floor_area: floorArea || prev.floor_area,
                building_volume: estimatedVolume || prev.building_volume,
                num_floors: projectData.num_floors?.toString() || prev.num_floors,
                building_type: projectData.project_type?.toLowerCase() || 'residential'
            }));
        }
    }, [projectData]);

    React.useEffect(() => {
        const fetchAnalysis = async () => {
            try {
                const token = localStorage.getItem('access_token');
                if (!token) return;

                const response = await axios.get(`/api/v1/energy/${projectId}/report`, {
                    headers: { 'Authorization': `Bearer ${token}` }
                });

                if (response.data.success && response.data.energy_analysis) {
                    setResult(response.data.energy_analysis);
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

            const response = await axios.post('/api/v1/energy/calculate', {
                project_id: projectId,
                floor_area: parseFloat(formData.floor_area),
                building_volume: parseFloat(formData.building_volume),
                window_area: parseFloat(formData.window_area),
                orientation: formData.orientation,
                insulation_quality: formData.insulation_quality,
                num_floors: parseInt(formData.num_floors),
                building_type: formData.building_type
            }, {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            setResult(response.data.energy_analysis);
        } catch (err: any) {
            setError(err.response?.data?.detail || 'Failed to calculate energy efficiency');
        } finally {
            setLoading(false);
        }
    };

    const getRatingColor = (rating: string) => {
        const colors: Record<string, { text: string; bg: string; border: string }> = {
            'A+': { text: '#16a34a', bg: '#f0fdf4', border: '#bbf7d0' },
            'A': { text: '#22c55e', bg: '#f0fdf4', border: '#bbf7d0' },
            'B': { text: '#84cc16', bg: '#f7fee7', border: '#d9f99d' },
            'C': { text: '#eab308', bg: '#fefce8', border: '#fef08a' },
            'D': { text: '#f97316', bg: '#fff7ed', border: '#fed7aa' },
            'E': { text: '#ef4444', bg: '#fef2f2', border: '#fecaca' }
        };
        return colors[rating] || { text: '#6b7280', bg: '#f9fafb', border: '#e5e7eb' };
    };

    return (
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
            <Card>
                <CardContent>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                        <Zap style={{ color: '#eab308' }} size={24} />
                        <Typography variant="h5" component="h2" fontWeight="bold">
                            Energy Efficiency Analysis
                        </Typography>
                    </Box>
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                        AI-powered energy consumption calculator with real-time sustainability insights and carbon footprint analysis
                    </Typography>

                    <form onSubmit={handleSubmit}>
                        <Grid container spacing={2}>
                            <Grid size={{ xs: 12, md: 6 }}>
                                <TextField
                                    fullWidth
                                    label="Floor Area (m²)"
                                    type="number"
                                    required
                                    value={formData.floor_area}
                                    onChange={(e) => setFormData({ ...formData, floor_area: e.target.value })}
                                    placeholder="Enter total floor area (e.g., 1200 m²)"
                                    inputProps={{ step: '0.01', min: '0' }}
                                    helperText="Total built-up area of all floors"
                                />
                            </Grid>

                            <Grid size={{ xs: 12, md: 6 }}>
                                <TextField
                                    fullWidth
                                    label="Building Volume (m³)"
                                    type="number"
                                    required
                                    value={formData.building_volume}
                                    onChange={(e) => setFormData({ ...formData, building_volume: e.target.value })}
                                    placeholder="Enter building volume (e.g., 3600 m³)"
                                    inputProps={{ step: '0.01', min: '0' }}
                                    helperText="Total enclosed volume for HVAC calculations"
                                />
                            </Grid>

                            <Grid size={{ xs: 12, md: 6 }}>
                                <TextField
                                    fullWidth
                                    label="Window Area (m²)"
                                    type="number"
                                    required
                                    value={formData.window_area}
                                    onChange={(e) => setFormData({ ...formData, window_area: e.target.value })}
                                    placeholder="Enter total window area (e.g., 180 m²)"
                                    inputProps={{ step: '0.01', min: '0' }}
                                    helperText="Affects natural lighting and thermal efficiency"
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
                                    placeholder="e.g., 3"
                                />
                            </Grid>

                            <Grid size={{ xs: 12, md: 6 }}>
                                <FormControl fullWidth>
                                    <InputLabel>Building Orientation</InputLabel>
                                    <Select
                                        value={formData.orientation}
                                        label="Building Orientation"
                                        onChange={(e) => setFormData({ ...formData, orientation: e.target.value })}
                                    >
                                        <MenuItem value="north">North</MenuItem>
                                        <MenuItem value="south">South</MenuItem>
                                        <MenuItem value="east">East</MenuItem>
                                        <MenuItem value="west">West</MenuItem>
                                    </Select>
                                </FormControl>
                            </Grid>

                            <Grid size={{ xs: 12, md: 6 }}>
                                <FormControl fullWidth>
                                    <InputLabel>Insulation Quality</InputLabel>
                                    <Select
                                        value={formData.insulation_quality}
                                        label="Insulation Quality"
                                        onChange={(e) => setFormData({ ...formData, insulation_quality: e.target.value })}
                                    >
                                        <MenuItem value="poor">Poor</MenuItem>
                                        <MenuItem value="medium">Medium</MenuItem>
                                        <MenuItem value="good">Good</MenuItem>
                                    </Select>
                                </FormControl>
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
                                        <MenuItem value="mixed">Mixed Use</MenuItem>
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
                            startIcon={loading ? <CircularProgress size={20} /> : <Zap size={20} />}
                        >
                            {loading ? 'Calculating...' : 'Calculate Energy Efficiency'}
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
                    {/* Energy Rating Card */}
                    <Card
                        sx={{
                            border: 2,
                            borderColor: getRatingColor(result.rating).border,
                            bgcolor: getRatingColor(result.rating).bg
                        }}
                    >
                        <CardContent sx={{ textAlign: 'center' }}>
                            <Typography
                                variant="h1"
                                sx={{
                                    fontSize: '4rem',
                                    fontWeight: 'bold',
                                    color: getRatingColor(result.rating).text,
                                    mb: 1
                                }}
                            >
                                {result.rating}
                            </Typography>
                            <Typography variant="h6" fontWeight="medium" sx={{ mb: 2 }}>
                                Energy Rating
                            </Typography>
                            <Typography variant="h4" fontWeight="semibold">
                                {result.energy_per_m2.toFixed(2)} kWh/m²/year
                            </Typography>
                            <Box sx={{ mt: 2 }}>
                                {result.is_sustainable ? (
                                    <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 1, color: '#16a34a' }}>
                                        <CheckCircle size={20} />
                                        <Typography fontWeight="medium">Sustainable Building</Typography>
                                    </Box>
                                ) : (
                                    <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 1, color: '#f97316' }}>
                                        <AlertCircle size={20} />
                                        <Typography fontWeight="medium">Improvement Recommended</Typography>
                                    </Box>
                                )}
                            </Box>
                        </CardContent>
                    </Card>

                    {/* Energy Breakdown */}
                    <Card>
                        <CardContent>
                            <Typography variant="h6" fontWeight="bold" sx={{ mb: 2 }}>
                                Energy Consumption Breakdown
                            </Typography>
                            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                                <Box>
                                    <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                                        <Typography variant="body2" fontWeight="medium">Heating/Cooling</Typography>
                                        <Typography variant="body2" color="text.secondary">
                                            {result.breakdown.heating_cooling.toFixed(0)} kWh/year
                                        </Typography>
                                    </Box>
                                    <LinearProgress
                                        variant="determinate"
                                        value={(result.breakdown.heating_cooling / result.total_energy_kwh_year) * 100}
                                        sx={{ height: 8, borderRadius: 1 }}
                                    />
                                </Box>

                                <Box>
                                    <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                                        <Typography variant="body2" fontWeight="medium">Lighting</Typography>
                                        <Typography variant="body2" color="text.secondary">
                                            {result.breakdown.lighting.toFixed(0)} kWh/year
                                        </Typography>
                                    </Box>
                                    <LinearProgress
                                        variant="determinate"
                                        value={(result.breakdown.lighting / result.total_energy_kwh_year) * 100}
                                        sx={{ height: 8, borderRadius: 1 }}
                                    />
                                </Box>

                                <Box>
                                    <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                                        <Typography variant="body2" fontWeight="medium">Appliances</Typography>
                                        <Typography variant="body2" color="text.secondary">
                                            {result.breakdown.appliances.toFixed(0)} kWh/year
                                        </Typography>
                                    </Box>
                                    <LinearProgress
                                        variant="determinate"
                                        value={(result.breakdown.appliances / result.total_energy_kwh_year) * 100}
                                        sx={{ height: 8, borderRadius: 1 }}
                                    />
                                </Box>

                                <Box>
                                    <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                                            <Sun size={16} style={{ color: '#eab308' }} />
                                            <Typography variant="body2" fontWeight="medium">Solar Gain (Benefit)</Typography>
                                        </Box>
                                        <Typography variant="body2" sx={{ color: '#16a34a' }}>
                                            -{Math.abs(result.breakdown.solar_gain).toFixed(0)} kWh/year
                                        </Typography>
                                    </Box>
                                </Box>

                                <Box sx={{ pt: 2, borderTop: 1, borderColor: 'divider' }}>
                                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                        <Typography fontWeight="bold">Total Annual Energy</Typography>
                                        <Typography variant="h5" fontWeight="bold">
                                            {result.total_energy_kwh_year.toFixed(0)} kWh/year
                                        </Typography>
                                    </Box>
                                </Box>

                                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                    <Leaf size={16} style={{ color: '#16a34a' }} />
                                    <Typography variant="body2" color="text.secondary">
                                        CO₂ Emissions: {result.co2_emissions_kg_year.toFixed(0)} kg/year
                                    </Typography>
                                </Box>
                            </Box>
                        </CardContent>
                    </Card>

                    {/* Recommendations */}
                    <Card>
                        <CardContent>
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                                <TrendingDown size={20} style={{ color: '#3b82f6' }} />
                                <Typography variant="h6" fontWeight="bold">
                                    Optimization Recommendations
                                </Typography>
                            </Box>
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

export default EnergyAnalysis;
