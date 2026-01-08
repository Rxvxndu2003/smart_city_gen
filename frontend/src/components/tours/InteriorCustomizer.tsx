import React, { useState, useRef, useEffect } from 'react';
import {
    Box,
    Card,
    CardContent,
    Typography,
    Button,
    Dialog,
    DialogTitle,
    DialogContent,
    DialogActions,
    Chip,
    Stack,
    TextField,
    CircularProgress,
    Alert,
    Grid,
    Tabs,
    Tab,
    Paper
} from '@mui/material';
import { Brush, Palette, Undo, Download, Sparkles } from 'lucide-react';
import axios from 'axios';
import toast from 'react-hot-toast';

interface InteriorCustomizerProps {
    tourImageId: number;
    tourImageUrl: string;
    onImageUpdated: (newUrl: string) => void;
}

interface DetectedObject {
    object_type: string;
    description: string;
    style: string;
    color: string;
    material: string;
    bbox: number[];
    mask_id: string;
}

interface FurniturePreset {
    id: number;
    name: string;
    prompt: string;
    category: string;
}

interface ColorPreset {
    id: number;
    name: string;
    color: string;
    hex_code: string;
}

interface Presets {
    furniture: {
        [key: string]: FurniturePreset[];
    };
    wall_colors: ColorPreset[];
    flooring: FurniturePreset[];
}

const InteriorCustomizer: React.FC<InteriorCustomizerProps> = ({
    tourImageId,
    tourImageUrl,
    onImageUpdated
}) => {
    const [editMode, setEditMode] = useState<'select' | 'replace' | 'color' | null>(null);
    const [detectedObject, setDetectedObject] = useState<DetectedObject | null>(null);
    const [loading, setLoading] = useState(false);
    const [replacementPrompt, setReplacementPrompt] = useState('');
    const [selectedPreset, setSelectedPreset] = useState('');
    const [presets, setPresets] = useState<Presets | null>(null);
    const [activeTab, setActiveTab] = useState(0);
    const [currentImageUrl, setCurrentImageUrl] = useState(tourImageUrl);
    const canvasRef = useRef<HTMLCanvasElement>(null);
    const imageRef = useRef<HTMLImageElement>(null);

    // Load presets on mount
    useEffect(() => {
        loadPresets();
    }, []);

    // Update canvas when image URL changes
    useEffect(() => {
        setCurrentImageUrl(tourImageUrl);
        if (imageRef.current) {
            imageRef.current.src = tourImageUrl;
        }
    }, [tourImageUrl]);

    const loadPresets = async () => {
        try {
            const response = await axios.get('/api/v1/interior/customization-presets');
            setPresets(response.data);
        } catch (error) {
            console.error('Failed to load presets:', error);
            toast.error('Failed to load furniture presets');
        }
    };

    const handleImageClick = async (event: React.MouseEvent<HTMLCanvasElement>) => {
        if (editMode !== 'select') return;

        const canvas = canvasRef.current;
        if (!canvas) return;

        const rect = canvas.getBoundingClientRect();
        const scaleX = canvas.width / rect.width;
        const scaleY = canvas.height / rect.height;
        
        const x = Math.floor((event.clientX - rect.left) * scaleX);
        const y = Math.floor((event.clientY - rect.top) * scaleY);

        setLoading(true);
        toast.loading('Detecting object...', { id: 'detect' });

        try {
            const token = localStorage.getItem('access_token');
            const response = await axios.post(
                '/api/v1/interior/detect-object',
                {
                    image_id: tourImageId,
                    image_url: tourImageUrl,
                    click_x: x,
                    click_y: y
                },
                {
                    headers: {
                        'Authorization': `Bearer ${token}`
                    }
                }
            );

            setDetectedObject(response.data);
            setEditMode('replace');
            
            // Draw bounding box
            drawBoundingBox(response.data.bbox, response.data.object_type);
            
            toast.success(`Detected: ${response.data.description}`, { id: 'detect' });
        } catch (error: any) {
            console.error('Detection error:', error);
            toast.error(error.response?.data?.detail || 'Failed to detect object', { id: 'detect' });
        } finally {
            setLoading(false);
        }
    };

    const drawBoundingBox = (bbox: number[], label: string) => {
        const canvas = canvasRef.current;
        const ctx = canvas?.getContext('2d');
        if (!ctx || !canvas || !imageRef.current) return;

        // Clear and redraw image
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        ctx.drawImage(imageRef.current, 0, 0, canvas.width, canvas.height);

        // Draw bounding box
        const [x1, y1, x2, y2] = bbox;
        ctx.strokeStyle = '#00ff00';
        ctx.lineWidth = 3;
        ctx.strokeRect(x1, y1, x2 - x1, y2 - y1);

        // Draw label background
        ctx.fillStyle = '#00ff00';
        const labelText = label || 'Object';
        ctx.font = 'bold 16px Arial';
        const textWidth = ctx.measureText(labelText).width;
        ctx.fillRect(x1, y1 - 30, textWidth + 20, 30);

        // Draw label text
        ctx.fillStyle = '#000';
        ctx.fillText(labelText, x1 + 10, y1 - 8);
    };

    const handleReplaceFurniture = async () => {
        if (!detectedObject) return;

        setLoading(true);
        const loadingToast = toast.loading('AI is generating your customization... This may take 30-60 seconds');

        try {
            const token = localStorage.getItem('access_token');
            const response = await axios.post(
                '/api/v1/interior/replace-furniture',
                {
                    image_id: tourImageId,
                    image_url: currentImageUrl,
                    mask_id: detectedObject.mask_id,
                    replacement_prompt: replacementPrompt || selectedPreset
                },
                {
                    headers: {
                        'Authorization': `Bearer ${token}`
                    }
                }
            );

            toast.success('Furniture replaced successfully!', { id: loadingToast });
            
            // Update tour with new image
            const newImageUrl = response.data.customized_image_url;
            setCurrentImageUrl(newImageUrl);
            onImageUpdated(newImageUrl);
            
            // Reset state
            setEditMode(null);
            setDetectedObject(null);
            setReplacementPrompt('');
            setSelectedPreset('');
            
            // Clear canvas and reload with new image
            if (imageRef.current) {
                imageRef.current.src = newImageUrl;
            }
        } catch (error: any) {
            console.error('Replacement error:', error);
            toast.error(error.response?.data?.detail || 'Failed to replace furniture', { id: loadingToast });
        } finally {
            setLoading(false);
        }
    };

    const handlePresetSelect = (preset: FurniturePreset) => {
        setSelectedPreset(preset.prompt);
        setReplacementPrompt(preset.prompt);
    };

    const handleImageLoad = () => {
        const canvas = canvasRef.current;
        const ctx = canvas?.getContext('2d');
        if (!ctx || !imageRef.current || !canvas) return;

        canvas.width = imageRef.current.naturalWidth;
        canvas.height = imageRef.current.naturalHeight;
        ctx.drawImage(imageRef.current, 0, 0);
    };

    const resetCanvas = () => {
        setEditMode(null);
        setDetectedObject(null);
        setReplacementPrompt('');
        setSelectedPreset('');
        
        const canvas = canvasRef.current;
        const ctx = canvas?.getContext('2d');
        if (!ctx || !canvas || !imageRef.current) return;
        
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        ctx.drawImage(imageRef.current, 0, 0, canvas.width, canvas.height);
    };

    const getPresetsByCategory = (category: string): FurniturePreset[] => {
        if (!presets) return [];
        const categoryKey = category === 'furniture' ? 'sofas' : `${category}s`;
        return presets.furniture[categoryKey] || [];
    };

    return (
        <Card sx={{ mt: 2, boxShadow: 3 }}>
            <CardContent>
                <Stack direction="row" alignItems="center" spacing={2} sx={{ mb: 2 }}>
                    <Sparkles size={24} color="#1976d2" />
                    <Typography variant="h6">
                        AI Interior Customization
                    </Typography>
                </Stack>

                <Stack direction="row" spacing={2} sx={{ mb: 2, flexWrap: 'wrap', gap: 1 }}>
                    <Button
                        variant={editMode === 'select' ? 'contained' : 'outlined'}
                        startIcon={<Brush size={18} />}
                        onClick={() => setEditMode('select')}
                        disabled={loading}
                    >
                        Select Furniture
                    </Button>
                    <Button
                        variant={editMode === 'color' ? 'contained' : 'outlined'}
                        startIcon={<Palette size={18} />}
                        onClick={() => setEditMode('color')}
                        disabled={loading}
                    >
                        Change Wall Color
                    </Button>
                    <Button
                        variant="outlined"
                        startIcon={<Undo size={18} />}
                        onClick={resetCanvas}
                        disabled={loading}
                    >
                        Reset
                    </Button>
                    <Button
                        variant="outlined"
                        startIcon={<Download size={18} />}
                        onClick={() => {
                            const link = document.createElement('a');
                            link.href = currentImageUrl;
                            link.download = 'customized-interior.png';
                            link.click();
                        }}
                    >
                        Download
                    </Button>
                </Stack>

                {editMode === 'select' && (
                    <Alert severity="info" sx={{ mb: 2 }}>
                        <strong>Click on any furniture</strong> in the image to select it for replacement
                    </Alert>
                )}

                {editMode === 'color' && (
                    <Alert severity="info" sx={{ mb: 2 }}>
                        Wall color change feature - Coming soon! Select walls then choose a new color.
                    </Alert>
                )}

                {/* Canvas for interactive editing */}
                <Box sx={{ position: 'relative', mb: 2 }}>
                    <canvas
                        ref={canvasRef}
                        onClick={handleImageClick}
                        style={{
                            width: '100%',
                            maxWidth: 800,
                            height: 'auto',
                            border: '2px solid #ddd',
                            borderRadius: 8,
                            cursor: editMode === 'select' ? 'crosshair' : 'default',
                            display: 'block'
                        }}
                    />
                    <img
                        ref={imageRef}
                        src={currentImageUrl}
                        alt="Tour"
                        style={{ display: 'none' }}
                        onLoad={handleImageLoad}
                        crossOrigin="anonymous"
                    />
                    {loading && (
                        <Box
                            sx={{
                                position: 'absolute',
                                top: '50%',
                                left: '50%',
                                transform: 'translate(-50%, -50%)',
                                backgroundColor: 'rgba(255, 255, 255, 0.9)',
                                padding: 3,
                                borderRadius: 2,
                                textAlign: 'center'
                            }}
                        >
                            <CircularProgress />
                            <Typography sx={{ mt: 2 }}>Processing...</Typography>
                        </Box>
                    )}
                </Box>

                {/* Detected Object Dialog */}
                {detectedObject && (
                    <Dialog 
                        open={editMode === 'replace'} 
                        onClose={() => setEditMode(null)} 
                        maxWidth="md" 
                        fullWidth
                    >
                        <DialogTitle>
                            Replace {detectedObject.object_type}
                        </DialogTitle>
                        <DialogContent>
                            <Stack spacing={3} sx={{ mt: 2 }}>
                                <Box>
                                    <Typography variant="subtitle2" gutterBottom color="text.secondary">
                                        Current Item:
                                    </Typography>
                                    <Typography variant="body1" sx={{ mb: 1 }}>
                                        {detectedObject.description}
                                    </Typography>
                                    <Stack direction="row" spacing={1} sx={{ mt: 1 }}>
                                        <Chip label={detectedObject.style} size="small" color="primary" variant="outlined" />
                                        <Chip label={detectedObject.color} size="small" color="secondary" variant="outlined" />
                                        <Chip label={detectedObject.material} size="small" variant="outlined" />
                                    </Stack>
                                </Box>

                                <Tabs value={activeTab} onChange={(_event: React.SyntheticEvent, newValue: number) => setActiveTab(newValue)}>
                                    <Tab label="Preset Options" />
                                    <Tab label="Custom Description" />
                                </Tabs>

                                {activeTab === 0 && presets && (
                                    <Box>
                                        <Typography variant="subtitle2" gutterBottom>
                                            Quick Replace Options:
                                        </Typography>
                                        <Grid container spacing={2} sx={{ mt: 1 }}>
                                            {getPresetsByCategory(detectedObject.object_type).length > 0 ? (
                                                getPresetsByCategory(detectedObject.object_type).map((preset) => (
                                                    <Grid item xs={12} sm={6} key={preset.id}>
                                                        <Paper
                                                            sx={{
                                                                p: 2,
                                                                cursor: 'pointer',
                                                                border: selectedPreset === preset.prompt ? '2px solid #1976d2' : '1px solid #ddd',
                                                                '&:hover': {
                                                                    backgroundColor: '#f5f5f5'
                                                                }
                                                            }}
                                                            onClick={() => handlePresetSelect(preset)}
                                                        >
                                                            <Typography variant="body2" fontWeight="bold">
                                                                {preset.name}
                                                            </Typography>
                                                        </Paper>
                                                    </Grid>
                                                ))
                                            ) : (
                                                <Grid item xs={12}>
                                                    <Alert severity="info">
                                                        No presets available for {detectedObject.object_type}. 
                                                        Please use custom description.
                                                    </Alert>
                                                </Grid>
                                            )}
                                        </Grid>
                                    </Box>
                                )}

                                {activeTab === 1 && (
                                    <Box>
                                        <TextField
                                            fullWidth
                                            label="Describe your desired furniture"
                                            value={replacementPrompt}
                                            onChange={(e) => setReplacementPrompt(e.target.value)}
                                            placeholder="e.g., brown leather sofa with chrome legs"
                                            helperText="Be specific about style, color, and material for best results"
                                            multiline
                                            rows={3}
                                        />
                                        <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                                            Examples: "modern gray velvet sofa", "rustic wooden dining table", "minimalist white desk"
                                        </Typography>
                                    </Box>
                                )}
                            </Stack>
                        </DialogContent>
                        <DialogActions>
                            <Button onClick={() => setEditMode(null)}>Cancel</Button>
                            <Button
                                variant="contained"
                                onClick={handleReplaceFurniture}
                                disabled={!replacementPrompt && !selectedPreset || loading}
                                startIcon={loading ? <CircularProgress size={16} /> : <Sparkles size={16} />}
                            >
                                {loading ? 'Generating...' : 'Replace with AI'}
                            </Button>
                        </DialogActions>
                    </Dialog>
                )}
            </CardContent>
        </Card>
    );
};

export default InteriorCustomizer;
