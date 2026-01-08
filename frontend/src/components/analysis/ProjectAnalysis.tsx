import React from 'react';
import { Tabs, Tab, Card, CardContent, Typography, Box } from '@mui/material';
import { Zap, Building2, Trees } from 'lucide-react';
import EnergyAnalysis from './EnergyAnalysis';
import StructuralAnalysis from './StructuralAnalysis';
import GreenSpaceAnalysis from './GreenSpaceAnalysis';

interface ProjectAnalysisProps {
    projectId: number;
    projectData?: any;
}

const ProjectAnalysis: React.FC<ProjectAnalysisProps> = ({ projectId, projectData }) => {
    const [activeTab, setActiveTab] = React.useState(0);

    const handleTabChange = (_event: React.SyntheticEvent, newValue: number) => {
        setActiveTab(newValue);
    };

    return (
        <Box sx={{ maxWidth: 1200, mx: 'auto', py: 3 }}>
            <Card sx={{ mb: 3, background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' }}>
                <CardContent>
                    <Typography variant="h4" component="h1" fontWeight="bold" gutterBottom sx={{ color: 'white' }}>
                        Project Analysis & Validation
                    </Typography>
                    <Typography variant="body2" sx={{ color: 'rgba(255,255,255,0.9)' }}>
                        Advanced AI-powered analysis for energy efficiency, structural integrity, and sustainable green space optimization
                    </Typography>
                </CardContent>
            </Card>

            <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3, bgcolor: 'white', borderRadius: 1 }}>
                <Tabs value={activeTab} onChange={handleTabChange} variant="fullWidth">
                    <Tab
                        icon={<Zap size={20} />}
                        iconPosition="start"
                        label="Energy Efficiency"
                        sx={{ 
                            textTransform: 'none',
                            fontWeight: activeTab === 0 ? 'bold' : 'normal'
                        }}
                    />
                    <Tab
                        icon={<Building2 size={20} />}
                        iconPosition="start"
                        label="Structural Integrity"
                        sx={{ 
                            textTransform: 'none',
                            fontWeight: activeTab === 1 ? 'bold' : 'normal'
                        }}
                    />
                    <Tab
                        icon={<Trees size={20} />}
                        iconPosition="start"
                        label="Green Space"
                        sx={{ 
                            textTransform: 'none',
                            fontWeight: activeTab === 2 ? 'bold' : 'normal'
                        }}
                    />
                </Tabs>
            </Box>

            <Box role="tabpanel" hidden={activeTab !== 0}>
                {activeTab === 0 && <EnergyAnalysis projectId={projectId} projectData={projectData} />}
            </Box>

            <Box role="tabpanel" hidden={activeTab !== 1}>
                {activeTab === 1 && <StructuralAnalysis projectId={projectId} projectData={projectData} />}
            </Box>

            <Box role="tabpanel" hidden={activeTab !== 2}>
                {activeTab === 2 && <GreenSpaceAnalysis projectId={projectId} projectData={projectData} />}
            </Box>
        </Box>
    );
};

export default ProjectAnalysis;
