
import React, { useState } from 'react';
import {
    Box,
    Typography,
    TextField,
    Button,
    Paper,
    CircularProgress,
    FormControlLabel,
    Switch,
    Alert,
    Chip,
    Stack
} from '@mui/material';
import { Wand2, Sparkles } from 'lucide-react';
import { generationApi } from '../services/api';

interface TextToCityGenProps {
    projectId: number;
    onGenerationComplete: (data: any) => void;
}

export const TextToCityGen: React.FC<TextToCityGenProps> = ({ projectId, onGenerationComplete }) => {
    const [prompt, setPrompt] = useState('');
    const [loading, setLoading] = useState(false);
    const [enableAI, setEnableAI] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const handleGenerate = async () => {
        if (!prompt.trim()) return;

        setLoading(true);
        setError(null);
        try {
            const response = await generationApi.textToCity(projectId, {
                prompt: prompt,
                enable_ai_enhancement: enableAI
            });

            onGenerationComplete(response.data);
        } catch (err: any) {
            console.error('Text-to-City error:', err);
            setError(err.response?.data?.detail || 'Generation failed');
        } finally {
            setLoading(false);
        }
    };

    const suggestions = [
        "Eco-friendly district with dense vertical forests",
        "Futuristic cyberpunk downtown with neon lights",
        "Quiet suburban neighborhood with wide streets",
        "Car-free pedestrian zone with many parks",
        "Industrial logistics hub with wide roads"
    ];

    return (
        <Paper elevation={3} sx={{ p: 3, borderRadius: 2, background: 'linear-gradient(135deg, #1e293b 0%, #0f172a 100%)', color: 'white' }}>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 2, gap: 1 }}>
                <Wand2 size={24} color="#8b5cf6" />
                <Typography variant="h6" sx={{ fontWeight: 'bold', background: '-webkit-linear-gradient(45deg, #a78bfa, #2dd4bf)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
                    AI City Architect
                </Typography>
            </Box>

            <Typography variant="body2" sx={{ mb: 2, color: '#94a3b8' }}>
                Describe your dream city using natural language. Our AI will configure the engineering parameters for you.
            </Typography>

            <TextField
                fullWidth
                multiline
                rows={3}
                placeholder="e.g., 'A dense commercial district optimized for walkability...'"
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                sx={{
                    mb: 2,
                    bgcolor: 'rgba(255,255,255,0.05)',
                    borderRadius: 1,
                    '& .MuiOutlinedInput-root': { color: 'white' },
                    '& .MuiInputLabel-root': { color: '#94a3b8' }
                }}
                variant="outlined"
            />

            <Stack direction="row" flexWrap="wrap" gap={1} mb={2}>
                {suggestions.map((s, i) => (
                    <Chip
                        key={i}
                        label={s}
                        size="small"
                        onClick={() => setPrompt(s)}
                        icon={<Sparkles size={12} />}
                        sx={{
                            bgcolor: 'rgba(139, 92, 246, 0.15)',
                            color: '#a78bfa',
                            border: '1px solid rgba(139, 92, 246, 0.3)',
                            cursor: 'pointer',
                            '&:hover': { bgcolor: 'rgba(139, 92, 246, 0.25)' }
                        }}
                    />
                ))}
            </Stack>

            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <FormControlLabel
                    control={
                        <Switch
                            checked={enableAI}
                            onChange={(e) => setEnableAI(e.target.checked)}
                            color="secondary"
                        />
                    }
                    label={<Typography variant="body2" sx={{ color: '#cbd5e1' }}>Enable Visual Enhancement</Typography>}
                />

                <Button
                    variant="contained"
                    onClick={handleGenerate}
                    disabled={loading || !prompt.trim()}
                    startIcon={loading ? <CircularProgress size={20} color="inherit" /> : <Wand2 size={20} />}
                    sx={{
                        background: 'linear-gradient(45deg, #7c3aed, #2563eb)',
                        fontWeight: 'bold',
                        boxShadow: '0 0 15px rgba(124, 58, 237, 0.3)',
                        '&:hover': {
                            background: 'linear-gradient(45deg, #6d28d9, #1d4ed8)',
                            boxShadow: '0 0 20px rgba(124, 58, 237, 0.5)',
                        }
                    }}
                >
                    {loading ? 'Designing...' : 'Magic Generate'}
                </Button>
            </Box>

            {error && (
                <Alert severity="error" sx={{ mt: 2, bgcolor: 'rgba(239, 68, 68, 0.1)', color: '#fca5a5' }}>
                    {error}
                </Alert>
            )}
        </Paper>
    );
};
