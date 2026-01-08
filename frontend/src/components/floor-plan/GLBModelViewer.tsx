/**
 * GLBModel Viewer Component
 * Displays 3D GLB models using Three.js and React Three Fiber
 */

import { Suspense } from 'react';
import { Canvas } from '@react-three/fiber';
import { OrbitControls, Stage, useGLTF } from '@react-three/drei';
import { Box, CircularProgress, Typography, Alert } from '@mui/material';

interface GLBModelViewerProps {
    modelUrl: string;
    width?: string;
    height?: string;
}

function Model({ url }: { url: string }) {
    const { scene } = useGLTF(url);
    return <primitive object={scene} />;
}

export default function GLBModelViewer({ modelUrl, width = '100%', height = '500px' }: GLBModelViewerProps) {
    if (!modelUrl) {
        return (
            <Alert severity="info">
                No 3D model available. Enable 3D generation to view interactive models.
            </Alert>
        );
    }

    return (
        <Box sx={{ width, height, bgcolor: '#f5f5f5', borderRadius: 2, overflow: 'hidden' }}>
            <Suspense fallback={
                <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%' }}>
                    <CircularProgress />
                    <Typography sx={{ ml: 2 }}>Loading 3D Model...</Typography>
                </Box>
            }>
                <Canvas>
                    <Stage environment="city" intensity={0.6}>
                        <Model url={modelUrl} />
                    </Stage>
                    <OrbitControls enablePan={true} enableZoom={true} enableRotate={true} />
                </Canvas>
            </Suspense>
        </Box>
    );
}
