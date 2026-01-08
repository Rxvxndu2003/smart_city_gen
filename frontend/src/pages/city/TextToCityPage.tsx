import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft, Wand2, Sparkles, Loader2 } from 'lucide-react';
import { Paper, Box, Typography, TextField, Button, FormControl, InputLabel, Select, MenuItem, Chip, Stack, Alert, LinearProgress } from '@mui/material';
import toast from 'react-hot-toast';
import { generationApi, projectsApi } from '../../services/api';

const TextToCityPage: React.FC = () => {
    const navigate = useNavigate();
    const [prompt, setPrompt] = useState('');
    const [loading, setLoading] = useState(false);
    const [enableAI] = useState(true); // setEnableAI removed to avoid unused warning
    const [gridSizePreset, setGridSizePreset] = useState<'small' | 'medium' | 'large'>('medium');
    const [error, setError] = useState<string | null>(null);
    const [, setGeneratedModelUrl] = useState<string | null>(null);

    const suggestions = [
        "Eco-friendly district with dense vertical forests",
        "Futuristic cyberpunk downtown with neon lights",
        "Quiet suburban neighborhood with wide streets",
        "Car-free pedestrian zone with many parks",
        "Industrial logistics hub with wide roads",
        "Dense high-rise eco-metropolis with sustainable green parks"
    ];

    const gridSizeInfo = {
        small: { size: '6x6', time: '2-3 min', description: 'Fast generation, smaller area' },
        medium: { size: '8x8', time: '4-6 min', description: 'Balanced quality and speed' },
        large: { size: '10x10', time: '8-12 min', description: 'Large area, detailed city' }
    };

    const handleGenerate = async () => {
        if (!prompt.trim()) {
            toast.error('Please enter a prompt');
            return;
        }

        setLoading(true);
        setError(null);
        setGeneratedModelUrl(null);

        try {
            // Create a temporary project for this generation
            const projectResponse = await projectsApi.create({
                name: `AI City: ${prompt.substring(0, 50)}...`,
                description: `Generated from prompt: ${prompt}`,
                project_type: 'Mixed-Use',
                site_area_m2: 10000,
                district: 'AI Generated'
            });

            const projectId = projectResponse.data.id;

            // Generate city with text-to-city endpoint
            const response = await generationApi.textToCity(projectId, {
                prompt: prompt,
                enable_ai_enhancement: enableAI,
                grid_size_preset: gridSizePreset
            });

            setGeneratedModelUrl(response.data.model_url);
            toast.success('City generated successfully!');

            // Navigate to project detail page
            setTimeout(() => {
                navigate(`/projects/${projectId}`);
            }, 2000);

        } catch (err: any) {
            console.error('Text-to-City error:', err);
            const errorMsg = err.response?.data?.detail || 'Generation failed';
            setError(errorMsg);
            toast.error(errorMsg);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-gradient-to-br from-purple-50 via-pink-50 to-blue-50">
            <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
                {/* Header */}
                <button
                    onClick={() => navigate('/dashboard')}
                    className="flex items-center text-purple-600 hover:text-purple-700 mb-6 font-medium transition-colors"
                >
                    <ArrowLeft className="h-5 w-5 mr-2" />
                    Back to Dashboard
                </button>

                {/* Main Card */}
                <Paper elevation={6} sx={{ p: 4, borderRadius: 3, background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', color: 'white' }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 3, gap: 2 }}>
                        <Wand2 size={32} color="#fbbf24" />
                        <Typography variant="h3" sx={{ fontWeight: 'bold', background: '-webkit-linear-gradient(45deg, #fbbf24, #f472b6)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
                            AI City Architect
                        </Typography>
                    </Box>

                    <Typography variant="h6" sx={{ mb: 4, color: '#e9d5ff', opacity: 0.9 }}>
                        Describe your dream city using natural language. Our AI will design and generate a complete 3D city model for you.
                    </Typography>

                    {/* Prompt Input */}
                    <TextField
                        fullWidth
                        multiline
                        rows={4}
                        placeholder="e.g., 'A dense commercial district optimized for walkability with lots of green spaces...'"
                        value={prompt}
                        onChange={(e) => setPrompt(e.target.value)}
                        sx={{
                            mb: 3,
                            bgcolor: 'rgba(255,255,255,0.95)',
                            borderRadius: 2,
                            '& .MuiOutlinedInput-root': {
                                color: '#1f2937',
                                fontSize: '1.1rem',
                                '& fieldset': { borderColor: 'transparent' }
                            }
                        }}
                        variant="outlined"
                    />

                    {/* Suggestions */}
                    <Stack direction="row" flexWrap="wrap" gap={1.5} mb={3}>
                        {suggestions.map((s, i) => (
                            <Chip
                                key={i}
                                label={s}
                                size="small"
                                onClick={() => setPrompt(s)}
                                icon={<Sparkles size={14} />}
                                sx={{
                                    bgcolor: 'rgba(251, 191, 36, 0.2)',
                                    color: '#fbbf24',
                                    border: '1.5px solid rgba(251, 191, 36, 0.4)',
                                    cursor: 'pointer',
                                    fontSize: '0.85rem',
                                    fontWeight: 500,
                                    '&:hover': {
                                        bgcolor: 'rgba(251, 191, 36, 0.3)',
                                        transform: 'translateY(-2px)',
                                        transition: 'all 0.2s'
                                    }
                                }}
                            />
                        ))}
                    </Stack>

                    {/* Grid Size Selector */}
                    <FormControl fullWidth sx={{ mb: 3 }}>
                        <InputLabel sx={{ color: 'white', '&.Mui-focused': { color: '#fbbf24' } }}>City Size</InputLabel>
                        <Select
                            value={gridSizePreset}
                            onChange={(e) => setGridSizePreset(e.target.value as any)}
                            label="City Size"
                            sx={{
                                bgcolor: 'rgba(255,255,255,0.15)',
                                color: 'white',
                                '& .MuiOutlinedInput-notchedOutline': { borderColor: 'rgba(255,255,255,0.3)' },
                                '&:hover .MuiOutlinedInput-notchedOutline': { borderColor: 'rgba(255,255,255,0.5)' },
                                '&.Mui-focused .MuiOutlinedInput-notchedOutline': { borderColor: '#fbbf24' },
                                '& .MuiSvgIcon-root': { color: 'white' }
                            }}
                        >
                            {(['small', 'medium', 'large'] as const).map((preset) => (
                                <MenuItem key={preset} value={preset}>
                                    <Box>
                                        <Typography variant="body1" sx={{ fontWeight: 600, textTransform: 'capitalize' }}>
                                            {preset} ({gridSizeInfo[preset].size})
                                        </Typography>
                                        <Typography variant="caption" sx={{ color: 'text.secondary' }}>
                                            {gridSizeInfo[preset].time} • {gridSizeInfo[preset].description}
                                        </Typography>
                                    </Box>
                                </MenuItem>
                            ))}
                        </Select>
                    </FormControl>

                    {/* Generate Button */}
                    <Button
                        variant="contained"
                        onClick={handleGenerate}
                        disabled={loading || !prompt.trim()}
                        fullWidth
                        size="large"
                        startIcon={loading ? <Loader2 className="animate-spin" size={24} /> : <Wand2 size={24} />}
                        sx={{
                            background: 'linear-gradient(45deg, #fbbf24, #f59e0b)',
                            color: '#1f2937',
                            fontWeight: 'bold',
                            fontSize: '1.1rem',
                            py: 2,
                            boxShadow: '0 8px 20px rgba(251, 191, 36, 0.4)',
                            '&:hover': {
                                background: 'linear-gradient(45deg, #f59e0b, #d97706)',
                                boxShadow: '0 12px 28px rgba(251, 191, 36, 0.6)',
                                transform: 'translateY(-2px)',
                                transition: 'all 0.3s'
                            },
                            '&:disabled': {
                                background: 'rgba(255,255,255,0.2)',
                                color: 'rgba(255,255,255,0.5)'
                            }
                        }}
                    >
                        {loading ? 'Generating Your City...' : '✨ Generate City'}
                    </Button>

                    {/* Loading Progress */}
                    {loading && (
                        <Box sx={{ mt: 3 }}>
                            <LinearProgress sx={{
                                bgcolor: 'rgba(255,255,255,0.2)',
                                '& .MuiLinearProgress-bar': { bgcolor: '#fbbf24' }
                            }} />
                            <Typography variant="body2" sx={{ mt: 2, textAlign: 'center', color: '#e9d5ff' }}>
                                ⏱️ Estimated time: {gridSizeInfo[gridSizePreset].time}
                            </Typography>
                            <Typography variant="caption" sx={{ display: 'block', textAlign: 'center', color: '#c4b5fd', mt: 1 }}>
                                Creating your city... This may take a few minutes.
                            </Typography>
                        </Box>
                    )}

                    {/* Error Message */}
                    {error && (
                        <Alert severity="error" sx={{ mt: 3, bgcolor: 'rgba(239, 68, 68, 0.15)', color: '#fca5a5' }}>
                            {error}
                        </Alert>
                    )}
                </Paper>

                {/* Info Section */}
                <Box sx={{ mt: 4, px: 2 }}>
                    <Typography variant="h6" sx={{ color: '#6b21a8', fontWeight: 600, mb: 2 }}>
                        💡 How it works
                    </Typography>
                    <Box sx={{ bgcolor: 'white', borderRadius: 2, p: 3, boxShadow: '0 4px 12px rgba(0,0,0,0.08)' }}>
                        <ul className="space-y-2 text-gray-700">
                            <li>🎨 <strong>Natural Language Processing:</strong> Our AI understands your description and maps it to urban planning parameters</li>
                            <li>🏗️ <strong>3D Generation:</strong> Blender creates a detailed 3D city model based on your specifications</li>
                            <li>✨ <strong>AI Enhancement:</strong> Optional photorealistic rendering makes your city look stunning</li>
                            <li>📦 <strong>Download & Share:</strong> Export your city as a GLB file for use in other applications</li>
                        </ul>
                    </Box>
                </Box>
            </div>
        </div>
    );
};

export default TextToCityPage;
