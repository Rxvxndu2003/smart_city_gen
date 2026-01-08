/**
 * Panorama360 Viewer Component
 * Displays 360° panoramic images using Pannellum
 */

import { Pannellum } from 'pannellum-react';
import { Box, Alert, Typography } from '@mui/material';

interface Panorama360ViewerProps {
    imageUrl: string;
    width?: string;
    height?: string;
    title?: string;
}

export default function Panorama360Viewer({
    imageUrl,
    width = '100%',
    height = '500px',
    title = '360° Virtual Tour'
}: Panorama360ViewerProps) {
    if (!imageUrl) {
        return (
            <Alert severity="info">
                No 360° panorama available. Enable 360° tour generation to view immersive views.
            </Alert>
        );
    }

    return (
        <Box sx={{ width, height, borderRadius: 2, overflow: 'hidden' }}>
            {title && (
                <Typography variant="h6" sx={{ mb: 1, fontWeight: 600 }}>
                    {title}
                </Typography>
            )}
            <Pannellum
                width="100%"
                height={height}
                image={imageUrl}
                pitch={10}
                yaw={180}
                hfov={110}
                autoLoad
                showZoomCtrl
                showFullscreenCtrl
                onLoad={() => {
                    console.log('Panorama loaded successfully');
                }}
            />
        </Box>
    );
}
