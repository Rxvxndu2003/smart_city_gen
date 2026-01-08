
import React, { useState } from 'react';
import { Box, Paper, Typography, Button, Avatar, Fade } from '@mui/material';
import { Play, User, DollarSign, Shield, Gavel } from 'lucide-react';

interface AgentMessage {
    agent_id: string;
    agent_name: string;
    content: string;
}

interface AICouncilProps {
    projectId: number;
}

export const AICouncil: React.FC<AICouncilProps> = ({ projectId }) => {
    const [messages, setMessages] = useState<AgentMessage[]>([]);
    const [consensus, setConsensus] = useState<string | null>(null);
    const [isLoading, setIsLoading] = useState(false);
    const [currentTyping, setCurrentTyping] = useState<string | null>(null);

    // Hardcoded demo logic for the prototype if API fails or for speed
    const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

    const handleConvene = async () => {
        setIsLoading(true);
        setMessages([]);
        setConsensus(null);

        try {
            const token = localStorage.getItem('access_token');
            const response = await fetch(`${API_BASE_URL}/agents/convene`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({ project_id: projectId })
            });

            if (!response.ok) throw new Error("Connection failed");

            const data = await response.json();

            // Simulate typing effect
            let delay = 0;
            for (const msg of data.conversation) {
                setCurrentTyping(msg.agent_name);
                await new Promise(r => setTimeout(r, 1500)); // typing delay
                setMessages(prev => [...prev, msg]);
                delay += 1500;
            }

            setCurrentTyping(null);
            await new Promise(r => setTimeout(r, 1000));
            setConsensus(data.consensus);

        } catch (error) {
            console.error(error);
        } finally {
            setIsLoading(false);
        }
    };

    const getAgentIcon = (id: string) => {
        switch (id) {
            case 'eco': return <span className="text-green-500">🌿</span>;
            case 'dev': return <DollarSign size={20} className="text-blue-500" />;
            case 'regulator': return <Shield size={20} className="text-red-500" />;
            case 'mayor': return <Gavel size={20} className="text-purple-500" />;
            default: return <User />;
        }
    };

    return (
        <Box sx={{ p: 3 }}>
            <Box display="flex" justifyContent="space-between" alignItems="center" mb={4}>
                <div>
                    <Typography variant="h5" fontWeight="bold" color="text.primary">AI City Council</Typography>
                    <Typography variant="body2" color="text.secondary">
                        Simulate a multi-agent debate to optimize your project.
                    </Typography>
                </div>
                <Button
                    variant="contained"
                    onClick={handleConvene}
                    disabled={isLoading}
                    startIcon={<Play size={16} />}
                    sx={{
                        bgcolor: 'black',
                        '&:hover': { bgcolor: '#333' }
                    }}
                >
                    {isLoading ? 'Council is sitting...' : 'Convene Council'}
                </Button>
            </Box>

            {!messages.length && !isLoading && (
                <Box textAlign="center" py={10} bgcolor="#f8fafc" borderRadius={2}>
                    <Typography variant="h6" color="text.secondary">Ready to start the session.</Typography>
                </Box>
            )}

            <Box display="flex" flexDirection="column" gap={2}>
                {messages.map((msg, i) => (
                    <Fade in={true} key={i}>
                        <Paper
                            sx={{
                                p: 2,
                                display: 'flex',
                                gap: 2,
                                borderLeft: `4px solid ${msg.agent_id === 'eco' ? '#22c55e' :
                                    msg.agent_id === 'dev' ? '#3b82f6' :
                                        msg.agent_id === 'regulator' ? '#ef4444' : '#a855f7'
                                    }`
                            }}
                        >
                            <Avatar sx={{ bgcolor: 'transparent', border: '1px solid #eee' }}>
                                {getAgentIcon(msg.agent_id)}
                            </Avatar>
                            <div>
                                <Typography variant="subtitle2" fontWeight="bold">
                                    {msg.agent_name}
                                </Typography>
                                <Typography variant="body1">
                                    {msg.content}
                                </Typography>
                            </div>
                        </Paper>
                    </Fade>
                ))}

                {currentTyping && (
                    <Typography variant="caption" sx={{ fontStyle: 'italic', ml: 2, color: 'gray' }}>
                        {currentTyping} is typing...
                    </Typography>
                )}

                {consensus && (
                    <Fade in={true}>
                        <Paper sx={{ p: 3, bgcolor: '#f0fdf4', border: '1px solid #bbf7d0', mt: 2 }}>
                            <Box display="flex" alignItems="center" gap={1} mb={1}>
                                <Gavel size={20} className="text-green-700" />
                                <Typography variant="h6" color="success.main" fontWeight="bold">
                                    Final Consensus
                                </Typography>
                            </Box>
                            <Typography variant="body1" color="green.900">
                                {consensus}
                            </Typography>
                        </Paper>
                    </Fade>
                )}
            </Box>
        </Box>
    );
};
