import toast from 'react-hot-toast';
import jsPDF from 'jspdf';

import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
    Upload,
    Image as ImageIcon,
    Box,
    Loader2,
    Wand2,
    AlertTriangle,
    Layout,
    Camera,
    Shield,
    CheckCircle,
    XCircle,
    TrendingUp,
    ArrowLeft,
    Save,
    // FilePlus
} from 'lucide-react';
import { projectsApi } from '../../services/api';
import { Dialog, DialogTitle, DialogContent, DialogActions, Button, TextField, Tabs, Tab } from '@mui/material';
import InteriorCustomizer from '../../components/tours/InteriorCustomizer';
// Temporarily disabled due to React 18/19 compatibility issue
// import GLBModelViewer from '../../components/floor-plan/GLBModelViewer';
// import Panorama360Viewer from '../../components/floor-plan/Panorama360Viewer';

// Access API base URL from environment or default
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

const FloorPlanGenerator = () => {
    const navigate = useNavigate();

    // Existing state
    const [selectedFile, setSelectedFile] = useState<File | null>(null);
    const [previewUrl, setPreviewUrl] = useState<string | null>(null);
    const [isGenerating, setIsGenerating] = useState(false);
    const [result, setResult] = useState<any>(null);
    const [error, setError] = useState<string | null>(null);
    const [provider, setProvider] = useState<'replicate' | 'getfloorplan'>('replicate');
    const [viewMode, setViewMode] = useState<'birdseye' | 'perspective'>('birdseye');

    // Hybrid 3D Generation state
    const [generationMode, setGenerationMode] = useState<'2d' | '3d' | 'complete'>('complete');
    const [model3D, setModel3D] = useState<any>(null);
    const [tour360, setTour360] = useState<any>(null);
    const [activeTab, setActiveTab] = useState(0);

    // UDA Validation state
    const [extractedData, setExtractedData] = useState<any>(null);
    const [udaValidation, setUdaValidation] = useState<any>(null);
    const [validatingUda, setValidatingUda] = useState(false);
    const [projectId, setProjectId] = useState<number | null>(null);
    const [buildingParams, setBuildingParams] = useState({
        front_setback: 10,
        rear_setback: 10,
        side_setback: 5,
        building_coverage: 60,
        parking_spaces: 1
    });

    // Save Project State
    const [isSaveModalOpen, setIsSaveModalOpen] = useState(false);
    const [newProjectName, setNewProjectName] = useState('');
    const [newProjectDescription, setNewProjectDescription] = useState('');
    const [isSaving, setIsSaving] = useState(false);

    // Room Tour State
    const [tourMode, setTourMode] = useState<'single' | 'tour'>('single');
    const [roomTourData, setRoomTourData] = useState<any>(null);
    const [selectedRoomIndex, setSelectedRoomIndex] = useState<number>(0);
    const [isGeneratingTour, setIsGeneratingTour] = useState(false);
    const [tourProgress, setTourProgress] = useState<string>('');

    // Interior Editor State
    const [editMode, setEditMode] = useState(false);
    const [editInstruction, setEditInstruction] = useState('');
    const [editHistory, setEditHistory] = useState<Array<{ instruction: string, url: string }>>([]);
    const [isEditing, setIsEditing] = useState(false);
    const [originalRoomImages, setOriginalRoomImages] = useState<{ [key: number]: string }>({});

    // GetFloorPlan State
    const [planId, setPlanId] = useState<string | null>(() => localStorage.getItem('getfloorplan_plan_id'));
    const [tourUrl, setTourUrl] = useState<string | null>(() => localStorage.getItem('getfloorplan_tour_url'));
    const [isUploadingPlan, setIsUploadingPlan] = useState(false);
    const [isProcessingPlan, setIsProcessingPlan] = useState(() => {
        const savedPlanId = localStorage.getItem('getfloorplan_plan_id');
        const savedTourUrl = localStorage.getItem('getfloorplan_tour_url');
        return !!savedPlanId && !savedTourUrl;
    });
    const [processingProgress, setProcessingProgress] = useState('');
    const [statusCheckInterval, setStatusCheckInterval] = useState<NodeJS.Timeout | null>(null);

    // Resume polling on page load if there's a plan ID without tour URL
    useEffect(() => {
        const savedPlanId = localStorage.getItem('getfloorplan_plan_id');
        const savedTourUrl = localStorage.getItem('getfloorplan_tour_url');
        
        if (savedPlanId && !savedTourUrl) {
            // Resume polling - set processing state to true
            setIsProcessingPlan(true);
            setPlanId(savedPlanId);
            
            const uploadTime = localStorage.getItem('getfloorplan_upload_time');
            if (uploadTime) {
                const elapsed = Math.floor((new Date().getTime() - new Date(uploadTime).getTime()) / 60000);
                setProcessingProgress(`Resuming status check... (${elapsed} min since upload)`);
            }
            
            toast('Resuming GetFloorPlan status check...', { duration: 4000 });
            pollFloorPlanStatus(savedPlanId);
        } else if (savedTourUrl) {
            // Tour is already ready, just load it
            setTourUrl(savedTourUrl);
        }

        // Cleanup on unmount
        return () => {
            if (statusCheckInterval) {
                clearInterval(statusCheckInterval);
            }
        };
    }, []); // Run once on mount

    const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
        const file = event.target.files?.[0];
        if (file) {
            setSelectedFile(file);
            const url = URL.createObjectURL(file);
            setPreviewUrl(url);
            setResult(null);
            setError(null);

            // Simulate extracted data for UDA validation
            // In production, this would come from actual floor plan analysis
            setExtractedData({
                floor_count: 2,
                total_floor_area: 150,
                dimensions: {
                    width: 10,
                    length: 15,
                    height: 3
                },
                rooms: [
                    { type: 'Living Room', width: 5, length: 6, area: 30 },
                    { type: 'Bedroom', width: 4, length: 5, area: 20 },
                    { type: 'Kitchen', width: 3, length: 4, area: 12 }
                ],
                file_type: 'image'
            });
            setProjectId(1); // Temporary project ID
        }
    };

    const validateAgainstUDA = async () => {
        if (!extractedData || !projectId) return;

        const token = localStorage.getItem('access_token');
        if (!token) {
            toast.error('Please log in to validate against UDA regulations');
            navigate('/login');
            return;
        }

        setValidatingUda(true);
        try {
            const buildingData = {
                building_width: extractedData.dimensions?.width || 10,
                building_length: extractedData.dimensions?.length || 12,
                building_height: (extractedData.dimensions?.height || 10) * extractedData.floor_count,
                floor_count: extractedData.floor_count || 1,
                total_floor_area: extractedData.total_floor_area || 0,
                building_coverage: buildingParams.building_coverage,
                parking_spaces: buildingParams.parking_spaces,
                rooms: extractedData.rooms || []
            };

            const plotData = {
                front_setback: buildingParams.front_setback,
                rear_setback: buildingParams.rear_setback,
                side_setback: buildingParams.side_setback
            };

            const response = await fetch(
                `${API_BASE_URL}/generation/${projectId}/house/validate-uda`,
                {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${token}`,
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ building_data: buildingData, plot_data: plotData })
                }
            );

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({ detail: 'Validation failed' }));
                throw new Error(errorData.detail || 'UDA validation failed');
            }

            const data = await response.json();
            setUdaValidation(data.validation_report);

            toast.error(`UDA Validation Complete!\n\nCompliance: ${data.validation_report.is_compliant ? 'PASS' : 'FAIL'}\nScore: ${data.validation_report.compliance_score}%\nViolations: ${data.validation_report.violations.length}\nWarnings: ${data.validation_report.warnings.length}`);

        } catch (err: any) {
            console.error('UDA validation error:', err);
            toast.error('Failed to validate against UDA regulations: ' + (err.message || 'Unknown error'));
        } finally {
            setValidatingUda(false);
        }
    };

    const handleSaveProject = async () => {
        if (!newProjectName.trim()) {
            toast.error('Please enter a project name');
            return;
        }

        setIsSaving(true);
        try {
            // 1. Create new project
            const projectData = {
                name: newProjectName,
                description: newProjectDescription || 'Generated from Floor Plan AI',
                project_type: 'Floor Plan AI',
                status: 'DRAFT',
                site_area_m2: extractedData?.total_floor_area ? extractedData.total_floor_area * 1.5 : 2000, // Estimate site area
                building_coverage: buildingParams.building_coverage,
                num_floors: extractedData?.floor_count || 1,
                // Add model URL immediately if available
                model_url: result?.model_url || result?.image_url
            };

            const createResponse = await projectsApi.create(projectData);
            const newProjectId = createResponse.data.id;

            // 2. If we have a validation report, save it (by re-running validation against new project)
            // Note: In a real app, we might want a dedicated endpoint to duplicate the report
            if (udaValidation) {
                const token = localStorage.getItem('access_token');
                if (token) {
                    const buildingData = {
                        building_width: extractedData?.dimensions?.width || 10,
                        building_length: extractedData?.dimensions?.length || 12,
                        building_height: (extractedData?.dimensions?.height || 10) * (extractedData?.floor_count || 1),
                        floor_count: extractedData?.floor_count || 1,
                        total_floor_area: extractedData?.total_floor_area || 0,
                        building_coverage: buildingParams.building_coverage,
                        parking_spaces: buildingParams.parking_spaces,
                        rooms: extractedData?.rooms || []
                    };

                    const plotData = {
                        front_setback: buildingParams.front_setback,
                        rear_setback: buildingParams.rear_setback,
                        side_setback: buildingParams.side_setback
                    };

                    // Re-validate against new project to save the report
                    await fetch(
                        `${API_BASE_URL}/generation/${newProjectId}/house/validate-uda`,
                        {
                            method: 'POST',
                            headers: {
                                'Authorization': `Bearer ${token}`,
                                'Content-Type': 'application/json'
                            },
                            body: JSON.stringify({ building_data: buildingData, plot_data: plotData })
                        }
                    );
                }
            }

            toast.success('Project saved successfully!');
            setIsSaveModalOpen(false);

            // Redirect to the new project
            setTimeout(() => {
                navigate(`/projects/${newProjectId}`);
            }, 1500);

        } catch (error: any) {
            console.error('Failed to save project:', error);
            toast.error('Failed to save project: ' + (error.response?.data?.detail || error.message));
        } finally {
            setIsSaving(false);
        }
    };

    // Download validation report as PDF
    const downloadValidationPDF = () => {
        if (!udaValidation) return;

        const doc = new jsPDF();
        const pageWidth = doc.internal.pageSize.getWidth();
        const pageHeight = doc.internal.pageSize.getHeight();
        const margin = 20;
        const contentWidth = pageWidth - 2 * margin;
        let yPos = 20;
        let currentPage = 1;

        // Helper function to add page numbers
        const addPageNumber = () => {
            doc.setFontSize(9);
            doc.setTextColor(150, 150, 150);
            doc.setFont('helvetica', 'normal');
            doc.text(`Page ${currentPage}`, pageWidth / 2, pageHeight - 10, { align: 'center' });
            doc.setTextColor(0, 0, 0);
        };

        // Helper function to add new page if needed
        const checkPageBreak = (requiredSpace: number) => {
            if (yPos + requiredSpace > pageHeight - 30) {
                addPageNumber();
                doc.addPage();
                currentPage++;
                yPos = margin;
                return true;
            }
            return false;
        };

        // Helper function to add wrapped text with better line height
        // Commented out to avoid unused variable warning
        // const addWrappedText = (text: string, x: number, fontSize: number, maxWidth: number, lineHeight: number = 1.4) => {
        //     doc.setFontSize(fontSize);
        //     const lines = doc.splitTextToSize(text, maxWidth);
        //     lines.forEach((line: string) => {
        //         checkPageBreak(fontSize * lineHeight);
        //         doc.text(line, x, yPos);
        //         yPos += fontSize * lineHeight * 0.35; // Convert to mm
        //     });
        // };

        // Helper to draw section divider
        // Commented out to avoid unused variable warning
        // const addSectionDivider = () => {
        //     doc.setDrawColor(220, 220, 220);
        //     doc.setLineWidth(0.5);
        //     doc.line(margin, yPos, pageWidth - margin, yPos);
        //     yPos += 8;
        // };

        // ===== COVER PAGE =====
        // Enhanced gradient background with smoother transitions
        doc.setFillColor(79, 70, 229); // Indigo-700
        doc.rect(0, 0, pageWidth, 40, 'F');
        doc.setFillColor(99, 102, 241); // Indigo-600
        doc.rect(0, 40, pageWidth, 40, 'F');
        doc.setFillColor(129, 140, 248); // Indigo-400
        doc.rect(0, 80, pageWidth, 30, 'F');
        doc.setFillColor(139, 92, 246); // Purple-500
        doc.rect(0, 110, pageWidth, 50, 'F');

        // Logo/Icon area with enhanced design
        // Outer decorative circle (shadow)
        doc.setFillColor(200, 200, 200);
        doc.circle(pageWidth / 2 + 0.5, 35.5, 13, 'F');

        // Main white circle
        doc.setFillColor(255, 255, 255);
        doc.circle(pageWidth / 2, 35, 13, 'F');

        // Inner colored circle
        doc.setFillColor(249, 250, 251);
        doc.circle(pageWidth / 2, 35, 11.5, 'F');

        // UDA text in logo
        doc.setFillColor(99, 102, 241);
        doc.setFontSize(18);
        doc.setFont('helvetica', 'bold');
        doc.setTextColor(99, 102, 241);
        doc.text('UDA', pageWidth / 2, 38.5, { align: 'center' });

        // Main title with better spacing
        doc.setTextColor(255, 255, 255);
        doc.setFontSize(32);
        doc.setFont('helvetica', 'bold');
        doc.text('UDA REGULATIONS', pageWidth / 2, 70, { align: 'center' });

        doc.setFontSize(26);
        doc.text('VALIDATION REPORT', pageWidth / 2, 88, { align: 'center' });

        // Subtitle with better positioning
        doc.setFontSize(11);
        doc.setFont('helvetica', 'normal');
        doc.setTextColor(237, 233, 254); // Light purple
        doc.text('Sri Lankan Building Standards Compliance Analysis', pageWidth / 2, 102, { align: 'center' });

        // Compliance Status Card
        yPos = 125;
        const cardHeight = 50;

        // Card shadow using gray rectangle (compatible method)
        doc.setFillColor(220, 220, 220);
        doc.roundedRect(margin + 1.5, yPos + 1.5, contentWidth, cardHeight, 4, 4, 'F');

        // Card background
        doc.setFillColor(255, 255, 255);
        doc.roundedRect(margin, yPos, contentWidth, cardHeight, 4, 4, 'F');

        // Card border with enhanced styling
        if (udaValidation.is_compliant) {
            doc.setDrawColor(34, 197, 94);
        } else {
            doc.setDrawColor(239, 68, 68);
        }
        doc.setLineWidth(1.5);
        doc.roundedRect(margin, yPos, contentWidth, cardHeight, 4, 4, 'S');

        // Status badge with better design
        const badgeY = yPos + 10;
        const badgeWidth = 100;
        const badgeHeight = 24;
        const badgeX = (pageWidth - badgeWidth) / 2;

        // Badge shadow
        doc.setFillColor(200, 200, 200);
        doc.roundedRect(badgeX + 0.5, badgeY + 0.5, badgeWidth, badgeHeight, 3, 3, 'F');

        // Badge background
        if (udaValidation.is_compliant) {
            doc.setFillColor(34, 197, 94);
        } else {
            doc.setFillColor(239, 68, 68);
        }
        doc.roundedRect(badgeX, badgeY, badgeWidth, badgeHeight, 3, 3, 'F');

        // Badge text
        doc.setTextColor(255, 255, 255);
        doc.setFontSize(13);
        doc.setFont('helvetica', 'bold');
        doc.text(
            udaValidation.is_compliant ? '✓ COMPLIANT' : '✗ NON-COMPLIANT',
            pageWidth / 2,
            badgeY + 15.5,
            { align: 'center' }
        );

        // Compliance score with label
        doc.setTextColor(100, 100, 100);
        doc.setFontSize(9);
        doc.setFont('helvetica', 'normal');
        doc.text('COMPLIANCE SCORE', pageWidth / 2, yPos + 40, { align: 'center' });

        doc.setTextColor(0, 0, 0);
        doc.setFontSize(32);
        doc.setFont('helvetica', 'bold');
        const score = udaValidation.compliance_score?.toFixed(0) || '0';
        doc.text(`${score}%`, pageWidth / 2, yPos + 48, { align: 'center' });

        // Summary statistics
        yPos = 185;
        const statBoxWidth = (contentWidth - 20) / 3;
        const statBoxHeight = 38;
        const statBoxSpacing = 10;

        // Violations stat with shadow
        // Shadow
        doc.setFillColor(230, 230, 230);
        doc.roundedRect(margin + 1, yPos + 1, statBoxWidth, statBoxHeight, 3, 3, 'F');

        // Box background
        doc.setFillColor(254, 242, 242);
        doc.roundedRect(margin, yPos, statBoxWidth, statBoxHeight, 3, 3, 'F');
        doc.setDrawColor(239, 68, 68);
        doc.setLineWidth(0.8);
        doc.roundedRect(margin, yPos, statBoxWidth, statBoxHeight, 3, 3, 'S');

        doc.setTextColor(220, 38, 38);
        doc.setFontSize(28);
        doc.setFont('helvetica', 'bold');
        doc.text(`${udaValidation.violations?.length || 0}`, margin + statBoxWidth / 2, yPos + 18, { align: 'center' });
        doc.setFontSize(9);
        doc.setFont('helvetica', 'bold');
        doc.setTextColor(127, 29, 29);
        doc.text('VIOLATIONS', margin + statBoxWidth / 2, yPos + 28, { align: 'center' });

        // Warnings stat with shadow
        const warningX = margin + statBoxWidth + statBoxSpacing;

        // Shadow
        doc.setFillColor(230, 230, 230);
        doc.roundedRect(warningX + 1, yPos + 1, statBoxWidth, statBoxHeight, 3, 3, 'F');

        // Box background
        doc.setFillColor(254, 249, 235);
        doc.roundedRect(warningX, yPos, statBoxWidth, statBoxHeight, 3, 3, 'F');
        doc.setDrawColor(217, 119, 6);
        doc.setLineWidth(0.8);
        doc.roundedRect(warningX, yPos, statBoxWidth, statBoxHeight, 3, 3, 'S');

        doc.setTextColor(217, 119, 6);
        doc.setFontSize(28);
        doc.setFont('helvetica', 'bold');
        doc.text(`${udaValidation.warnings?.length || 0}`, warningX + statBoxWidth / 2, yPos + 18, { align: 'center' });
        doc.setFontSize(9);
        doc.setFont('helvetica', 'bold');
        doc.setTextColor(120, 53, 15);
        doc.text('WARNINGS', warningX + statBoxWidth / 2, yPos + 28, { align: 'center' });

        // Passed stat with shadow
        const passedX = warningX + statBoxWidth + statBoxSpacing;

        // Shadow
        doc.setFillColor(230, 230, 230);
        doc.roundedRect(passedX + 1, yPos + 1, statBoxWidth, statBoxHeight, 3, 3, 'F');

        // Box background
        doc.setFillColor(240, 253, 244);
        doc.roundedRect(passedX, yPos, statBoxWidth, statBoxHeight, 3, 3, 'F');
        doc.setDrawColor(34, 197, 94);
        doc.setLineWidth(0.8);
        doc.roundedRect(passedX, yPos, statBoxWidth, statBoxHeight, 3, 3, 'S');

        doc.setTextColor(22, 163, 74);
        doc.setFontSize(28);
        doc.setFont('helvetica', 'bold');
        doc.text(`${udaValidation.passed_checks?.length || 0}`, passedX + statBoxWidth / 2, yPos + 18, { align: 'center' });
        doc.setFontSize(9);
        doc.setFont('helvetica', 'bold');
        doc.setTextColor(20, 83, 45);
        doc.text('PASSED CHECKS', passedX + statBoxWidth / 2, yPos + 28, { align: 'center' });

        // Report metadata
        yPos = 235;

        // Shadow
        doc.setFillColor(235, 235, 235);
        doc.roundedRect(margin + 1, yPos + 1, contentWidth, 28, 3, 3, 'F');

        // Background
        doc.setFillColor(249, 250, 251);
        doc.roundedRect(margin, yPos, contentWidth, 28, 3, 3, 'F');

        // Border
        doc.setDrawColor(229, 231, 235);
        doc.setLineWidth(0.5);
        doc.roundedRect(margin, yPos, contentWidth, 28, 3, 3, 'S');

        doc.setTextColor(75, 85, 99);
        doc.setFontSize(8);
        doc.setFont('helvetica', 'normal');
        doc.text('REPORT GENERATED', margin + 6, yPos + 10);
        doc.setFontSize(10);
        doc.setFont('helvetica', 'bold');
        doc.setTextColor(31, 41, 55);
        doc.text(new Date().toLocaleString('en-US', {
            dateStyle: 'medium',
            timeStyle: 'short'
        }), margin + 6, yPos + 18);

        doc.setFontSize(8);
        doc.setFont('helvetica', 'normal');
        doc.setTextColor(75, 85, 99);
        doc.text('SYSTEM', pageWidth - margin - 55, yPos + 10);
        doc.setFontSize(10);
        doc.setFont('helvetica', 'bold');
        doc.setTextColor(31, 41, 55);
        doc.text('Smart City Planning', pageWidth - margin - 55, yPos + 18);

        // Footer
        doc.setTextColor(156, 163, 175);
        doc.setFontSize(8);
        doc.setFont('helvetica', 'italic');
        doc.text('This report is generated automatically based on UDA regulations and building standards.', pageWidth / 2, pageHeight - 15, { align: 'center' });
        addPageNumber();

        // ===== DETAILS PAGES =====
        doc.addPage();
        currentPage++;
        yPos = margin;

        // Page header with enhanced styling
        doc.setFillColor(249, 250, 251);
        doc.rect(0, 0, pageWidth, 28, 'F');
        doc.setDrawColor(229, 231, 235);
        doc.setLineWidth(0.5);
        doc.line(0, 28, pageWidth, 28);

        doc.setTextColor(31, 41, 55);
        doc.setFontSize(15);
        doc.setFont('helvetica', 'bold');
        doc.text('DETAILED VALIDATION RESULTS', margin, 18);
        yPos = 38;

        // VIOLATIONS SECTION
        if (udaValidation.violations && udaValidation.violations.length > 0) {
            // Section header with enhanced styling
            doc.setFillColor(239, 68, 68);
            doc.rect(margin, yPos, 5, 14, 'F');
            doc.setTextColor(220, 38, 38);
            doc.setFontSize(17);
            doc.setFont('helvetica', 'bold');
            doc.text(`VIOLATIONS (${udaValidation.violations.length})`, margin + 10, yPos + 10);
            yPos += 17;

            doc.setTextColor(107, 114, 128);
            doc.setFontSize(9);
            doc.setFont('helvetica', 'italic');
            doc.text('Critical issues that must be addressed for compliance', margin, yPos);
            yPos += 10;

            udaValidation.violations.forEach((violation: any, index: number) => {
                checkPageBreak(40);

                // Item container with shadow and border
                const itemHeight = 30;

                // Shadow
                doc.setFillColor(240, 240, 240);
                doc.roundedRect(margin + 1, yPos + 1, contentWidth, itemHeight, 2, 2, 'F');

                // Background
                doc.setFillColor(254, 242, 242);
                doc.roundedRect(margin, yPos, contentWidth, itemHeight, 2, 2, 'F');

                // Border
                doc.setDrawColor(254, 202, 202);
                doc.setLineWidth(0.8);
                doc.roundedRect(margin, yPos, contentWidth, itemHeight, 2, 2, 'S');

                // Number badge with shadow
                doc.setFillColor(200, 200, 200);
                doc.circle(margin + 6.5, yPos + 7.5, 4.5, 'F');
                doc.setFillColor(220, 38, 38);
                doc.circle(margin + 6, yPos + 7, 4.5, 'F');
                doc.setTextColor(255, 255, 255);
                doc.setFontSize(9);
                doc.setFont('helvetica', 'bold');
                doc.text(`${index + 1}`, margin + 6, yPos + 9.5, { align: 'center' });

                // Rule name
                doc.setTextColor(31, 41, 55);
                doc.setFontSize(11);
                doc.setFont('helvetica', 'bold');
                const ruleName = violation.rule || violation.rule_name || 'Violation';
                doc.text(ruleName, margin + 15, yPos + 9);

                // Message
                doc.setTextColor(75, 85, 99);
                doc.setFontSize(9);
                doc.setFont('helvetica', 'normal');
                const messageLines = doc.splitTextToSize(violation.message, contentWidth - 22);
                doc.text(messageLines[0], margin + 15, yPos + 17);

                // Regulation reference
                if (violation.regulation) {
                    doc.setTextColor(156, 163, 175);
                    doc.setFontSize(8);
                    doc.setFont('helvetica', 'italic');
                    doc.text(`Ref: ${violation.regulation}`, margin + 15, yPos + 24);
                }

                yPos += itemHeight + 5;
            });
            yPos += 8;
        }

        // WARNINGS SECTION
        if (udaValidation.warnings && udaValidation.warnings.length > 0) {
            checkPageBreak(25);

            // Section header with enhanced styling
            doc.setFillColor(217, 119, 6);
            doc.rect(margin, yPos, 5, 14, 'F');
            doc.setTextColor(217, 119, 6);
            doc.setFontSize(17);
            doc.setFont('helvetica', 'bold');
            doc.text(`WARNINGS (${udaValidation.warnings.length})`, margin + 10, yPos + 10);
            yPos += 17;

            doc.setTextColor(107, 114, 128);
            doc.setFontSize(9);
            doc.setFont('helvetica', 'italic');
            doc.text('Items requiring attention for optimal compliance', margin, yPos);
            yPos += 10;

            udaValidation.warnings.forEach((warning: any, index: number) => {
                checkPageBreak(35);

                const itemHeight = 30;

                // Shadow
                doc.setFillColor(240, 240, 240);
                doc.roundedRect(margin + 1, yPos + 1, contentWidth, itemHeight, 2, 2, 'F');

                // Background
                doc.setFillColor(254, 249, 235);
                doc.roundedRect(margin, yPos, contentWidth, itemHeight, 2, 2, 'F');

                // Border
                doc.setDrawColor(253, 230, 138);
                doc.setLineWidth(0.8);
                doc.roundedRect(margin, yPos, contentWidth, itemHeight, 2, 2, 'S');

                // Number badge with shadow
                doc.setFillColor(200, 200, 200);
                doc.circle(margin + 6.5, yPos + 7.5, 4.5, 'F');
                doc.setFillColor(217, 119, 6);
                doc.circle(margin + 6, yPos + 7, 4.5, 'F');
                doc.setTextColor(255, 255, 255);
                doc.setFontSize(9);
                doc.setFont('helvetica', 'bold');
                doc.text(`${index + 1}`, margin + 6, yPos + 9.5, { align: 'center' });

                // Rule name
                doc.setTextColor(31, 41, 55);
                doc.setFontSize(11);
                doc.setFont('helvetica', 'bold');
                const ruleName = warning.rule || warning.rule_name || 'Warning';
                doc.text(ruleName, margin + 15, yPos + 9);

                // Message
                doc.setTextColor(75, 85, 99);
                doc.setFontSize(9);
                doc.setFont('helvetica', 'normal');
                const messageLines = doc.splitTextToSize(warning.message, contentWidth - 22);
                doc.text(messageLines[0], margin + 15, yPos + 17);

                // Regulation reference
                if (warning.regulation) {
                    doc.setTextColor(156, 163, 175);
                    doc.setFontSize(8);
                    doc.setFont('helvetica', 'italic');
                    doc.text(`Ref: ${warning.regulation}`, margin + 15, yPos + 24);
                }

                yPos += itemHeight + 5;
            });
            yPos += 8;
        }

        // PASSED CHECKS SECTION
        if (udaValidation.passed_checks && udaValidation.passed_checks.length > 0) {
            checkPageBreak(25);

            // Section header with enhanced styling
            doc.setFillColor(34, 197, 94);
            doc.rect(margin, yPos, 5, 14, 'F');
            doc.setTextColor(22, 163, 74);
            doc.setFontSize(17);
            doc.setFont('helvetica', 'bold');
            doc.text(`PASSED CHECKS (${udaValidation.passed_checks.length})`, margin + 10, yPos + 10);
            yPos += 17;

            doc.setTextColor(107, 114, 128);
            doc.setFontSize(9);
            doc.setFont('helvetica', 'italic');
            doc.text('Requirements successfully met', margin, yPos);
            yPos += 10;

            // Display in a grid format for passed checks
            const checksPerRow = 2;
            const checkBoxWidth = (contentWidth - 5) / checksPerRow;
            let checkIndex = 0;

            udaValidation.passed_checks.forEach((check: any) => {
                if (checkIndex % checksPerRow === 0 && checkIndex > 0) {
                    yPos += 16;
                    checkPageBreak(16);
                }

                const xPos = margin + (checkIndex % checksPerRow) * (checkBoxWidth + 5);

                // Shadow
                doc.setFillColor(235, 235, 235);
                doc.roundedRect(xPos + 0.5, yPos + 0.5, checkBoxWidth, 14, 2, 2, 'F');

                // Background
                doc.setFillColor(240, 253, 244);
                doc.roundedRect(xPos, yPos, checkBoxWidth, 14, 2, 2, 'F');

                // Border
                doc.setDrawColor(187, 247, 208);
                doc.setLineWidth(0.5);
                doc.roundedRect(xPos, yPos, checkBoxWidth, 14, 2, 2, 'S');

                // Checkmark
                doc.setTextColor(34, 197, 94);
                doc.setFontSize(10);
                doc.setFont('helvetica', 'bold');
                doc.text('✓', xPos + 4, yPos + 9.5);

                // Check name
                doc.setTextColor(31, 41, 55);
                doc.setFontSize(8);
                doc.setFont('helvetica', 'normal');
                const checkName = check.rule || check.rule_name || check.description || 'Check passed';
                const truncated = checkName.length > 35 ? checkName.substring(0, 35) + '...' : checkName;
                doc.text(truncated, xPos + 11, yPos + 9.5);

                checkIndex++;
            });
            yPos += 20;
        }

        // RECOMMENDATIONS SECTION
        if (udaValidation.recommendations && udaValidation.recommendations.length > 0) {
            checkPageBreak(25);

            // Section header with enhanced styling
            doc.setFillColor(59, 130, 246);
            doc.rect(margin, yPos, 5, 14, 'F');
            doc.setTextColor(59, 130, 246);
            doc.setFontSize(17);
            doc.setFont('helvetica', 'bold');
            doc.text(`RECOMMENDATIONS (${udaValidation.recommendations.length})`, margin + 10, yPos + 10);
            yPos += 17;

            doc.setTextColor(107, 114, 128);
            doc.setFontSize(9);
            doc.setFont('helvetica', 'italic');
            doc.text('Suggestions for improvement and best practices', margin, yPos);
            yPos += 10;

            udaValidation.recommendations.forEach((rec: any, index: number) => {
                checkPageBreak(30);

                const itemHeight = 28;

                // Shadow
                doc.setFillColor(240, 240, 240);
                doc.roundedRect(margin + 1, yPos + 1, contentWidth, itemHeight, 2, 2, 'F');

                // Background
                doc.setFillColor(239, 246, 255);
                doc.roundedRect(margin, yPos, contentWidth, itemHeight, 2, 2, 'F');

                // Border
                doc.setDrawColor(191, 219, 254);
                doc.setLineWidth(0.8);
                doc.roundedRect(margin, yPos, contentWidth, itemHeight, 2, 2, 'S');

                // Number badge with shadow
                doc.setFillColor(200, 200, 200);
                doc.circle(margin + 6.5, yPos + 7.5, 4.5, 'F');
                doc.setFillColor(59, 130, 246);
                doc.circle(margin + 6, yPos + 7, 4.5, 'F');
                doc.setTextColor(255, 255, 255);
                doc.setFontSize(9);
                doc.setFont('helvetica', 'bold');
                doc.text(`${index + 1}`, margin + 6, yPos + 9.5, { align: 'center' });

                // Category
                if (rec.category) {
                    doc.setTextColor(31, 41, 55);
                    doc.setFontSize(10);
                    doc.setFont('helvetica', 'bold');
                    doc.text(rec.category, margin + 15, yPos + 9);
                }

                // Message
                doc.setTextColor(75, 85, 99);
                doc.setFontSize(9);
                doc.setFont('helvetica', 'normal');
                const message = rec.message || rec;
                const messageLines = doc.splitTextToSize(message, contentWidth - 22);
                doc.text(messageLines[0], margin + 15, yPos + (rec.category ? 18 : 12));

                yPos += itemHeight + 5;
            });
        }

        // Final page number
        addPageNumber();

        // Save the PDF
        doc.save(`UDA_Validation_Report_${new Date().getTime()}.pdf`);
        toast.success('Professional PDF report downloaded!');
    };

    // Download 3D model image
    const download3DModel = async () => {
        if (!result?.image_url) return;

        try {
            const response = await fetch(result.image_url);
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `3D_FloorPlan_${new Date().getTime()}.png`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
            toast.success('3D model downloaded!');
        } catch (error) {
            toast.error('Failed to download 3D model');
        }
    };

    const handleGenerate = async () => {
        if (!selectedFile) return;

        setIsGenerating(true);
        setError(null);
        setResult(null);
        setModel3D(null);
        setTour360(null);

        const formData = new FormData();
        formData.append('file', selectedFile);

        // Use hybrid endpoint in complete mode, otherwise use original endpoint
        if (generationMode === 'complete') {
            formData.append('include_3d_model', 'true');
            formData.append('include_360_tour', 'true');
            formData.append('include_2d_renders', 'true');
            formData.append('prompt', "modern residential interior, photorealistic style, high quality textures");

            try {
                const response = await fetch(`${API_BASE_URL}/generation/floor-plan/generate-complete`, {
                    method: 'POST',
                    body: formData,
                });


                const data = await response.json();

                if (!response.ok) {
                    throw new Error(data.detail || 'Failed to generate complete package');
                }

                console.log('🔍 Hybrid Response:', data);

                // Store all results
                if (data.renders_2d) {  // Check if renders_2d exists (not just overall_view)
                    console.log('✅ Setting 2D result:', data.renders_2d);
                    // Store FULL renders_2d object with rooms array
                    setResult({
                        image_url: data.renders_2d.overall_view,  // Can be null
                        rooms: data.renders_2d.rooms || []
                    });
                }
                if (data.model_3d && data.model_3d.glb_url) {
                    console.log('✅ Setting 3D model:', data.model_3d);
                    setModel3D(data.model_3d);
                }
                if (data.tour_360) {
                    console.log('✅ Setting virtual tour:', data.tour_360);
                    setTour360(data.tour_360);
                }

                toast.success(`Complete generation finished! (${data.total_generation_time}s)`);
            } catch (err: any) {
                setError(err.message);
                toast.error(err.message);
            } finally {
                setIsGenerating(false);
            }
        } else {
            // Original 2D-only generation
            formData.append('provider', provider);
            formData.append('view_mode', viewMode);
            formData.append('prompt', "modern residential interior, photorealistic style, high quality textures");

            try {
                const response = await fetch(`${API_BASE_URL}/generation/floor-plan/design`, {
                    method: 'POST',
                    body: formData,
                });

                const data = await response.json();

                if (!response.ok) {
                    throw new Error(data.detail || 'Failed to generate design');
                }

                setResult(data);
                toast.success('2D interior generated successfully!');
            } catch (err: any) {
                setError(err.message);
                toast.error(err.message);
            } finally {
                setIsGenerating(false);
            }
        }
    };

    const handleGenerateRoomTour = async () => {
        if (!selectedFile) {
            toast.error('Please upload a floor plan first');
            return;
        }

        setIsGeneratingTour(true);
        setTourProgress('Initializing room tour generation...');
        setRoomTourData(null);

        const formData = new FormData();
        formData.append('file', selectedFile);
        formData.append('provider', provider);
        formData.append('prompt', 'modern photorealistic interior design, high quality, 8k');

        try {
            setTourProgress('Analyzing floor plan and detecting rooms...');

            const response = await fetch(`${API_BASE_URL}/generation/floor-plan/room-tour`, {
                method: 'POST',
                body: formData,
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.detail || 'Failed to generate room tour');
            }

            setRoomTourData(data);
            setSelectedRoomIndex(0);
            setTourProgress('');
            toast.success(`Room tour generated! ${data.success_rate} rooms completed`);

        } catch (err: any) {
            setError(err.message);
            toast.error(`Room tour generation failed: ${err.message}`);
            setTourProgress('');
        } finally {
            setIsGeneratingTour(false);
        }
    };

    // GetFloorPlan Upload Handler
    const handleGetFloorPlanUpload = async () => {
        if (!selectedFile) {
            toast.error('Please upload a floor plan first');
            return;
        }

        const token = localStorage.getItem('access_token');
        if (!token) {
            toast.error('Please log in to use GetFloorPlan');
            navigate('/login');
            return;
        }

        setIsUploadingPlan(true);
        setError(null);
        setPlanId(null);
        setTourUrl(null);

        const formData = new FormData();
        formData.append('file', selectedFile);
        formData.append('file_name', selectedFile.name);

        try {
            const response = await fetch(`${API_BASE_URL}/getfloorplan/upload-plan`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                },
                body: formData,
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.detail || 'Failed to upload floor plan to GetFloorPlan');
            }

            const newPlanId = String(data.plan_id);
            setPlanId(newPlanId);
            localStorage.setItem('getfloorplan_plan_id', newPlanId);
            localStorage.setItem('getfloorplan_upload_time', new Date().toISOString());
            setIsProcessingPlan(true);
            setProcessingProgress('Floor plan uploaded! Processing will take 30-120 minutes. You can safely close this page.');
            toast.success('Floor plan uploaded! Processing started. Plan ID saved - you can check back later.', {
                duration: 6000,
            });

            // Start polling for status
            pollFloorPlanStatus(newPlanId, token);

        } catch (err: any) {
            setError(err.message);
            toast.error(`Upload failed: ${err.message}`);
            setIsProcessingPlan(false);
        } finally {
            setIsUploadingPlan(false);
        }
    };

    // Poll GetFloorPlan Status
    const pollFloorPlanStatus = (plan_id: string, initialToken?: string) => {
        // Clear any existing interval
        if (statusCheckInterval) {
            clearInterval(statusCheckInterval);
        }

        // Check immediately
        checkPlanStatus(plan_id, initialToken);

        // Then check every 2 minutes (120000ms)
        const interval = setInterval(() => {
            checkPlanStatus(plan_id);
        }, 120000);

        setStatusCheckInterval(interval);
    };

    // Refresh token helper
    const refreshAuthToken = async (): Promise<string | null> => {
        try {
            const refreshToken = localStorage.getItem('refresh_token');
            if (!refreshToken) {
                return null;
            }

            const response = await fetch(`${API_BASE_URL}/auth/refresh`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ refresh_token: refreshToken }),
            });

            if (response.ok) {
                const data = await response.json();
                localStorage.setItem('access_token', data.access_token);
                return data.access_token;
            }
            return null;
        } catch (error) {
            console.error('Token refresh failed:', error);
            return null;
        }
    };

    // Check Plan Status
    const checkPlanStatus = async (plan_id: string, initialToken?: string) => {
        try {
            // Try to get a valid token (refresh if needed)
            let token = initialToken || localStorage.getItem('access_token');
            
            if (!token) {
                console.log('No token found, attempting refresh...');
                token = await refreshAuthToken();
                if (!token) {
                    console.error('Unable to get valid token for status check');
                    setProcessingProgress('Session expired. Please log in again and return to this page.');
                    return;
                }
            }

            const response = await fetch(`${API_BASE_URL}/getfloorplan/check-plan-status`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ 
                    plan_ids: [parseInt(plan_id)],
                    language: 'en'
                }),
            });

            // Handle 401 (token expired) by refreshing
            if (response.status === 401) {
                console.log('Token expired, refreshing...');
                const newToken = await refreshAuthToken();
                if (newToken) {
                    // Retry with new token
                    return checkPlanStatus(plan_id, newToken);
                } else {
                    setProcessingProgress('Session expired. Please log in again and return to this page to check status.');
                    toast.error('Session expired. Please log in again.');
                    if (statusCheckInterval) {
                        clearInterval(statusCheckInterval);
                        setStatusCheckInterval(null);
                    }
                    return;
                }
            }

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.detail || 'Failed to check plan status');
            }

            console.log('📊 GetFloorPlan Status:', data);

            // Backend returns: { success: bool, message: string, results: [{ status: 0|1, widget_link: string, ... }] }
            if (data.results && data.results.length > 0) {
                const planResult = data.results[0]; // First result for our plan
                
                if (planResult.status === 1) {
                    // Plan is ready!
                    const widgetLink = planResult.widget_link;
                    setTourUrl(widgetLink);
                    localStorage.setItem('getfloorplan_tour_url', widgetLink);
                    localStorage.removeItem('getfloorplan_plan_id'); // Clean up
                    localStorage.removeItem('getfloorplan_upload_time');
                    setIsProcessingPlan(false);
                    setProcessingProgress('');
                    
                    // Clear polling interval
                    if (statusCheckInterval) {
                        clearInterval(statusCheckInterval);
                        setStatusCheckInterval(null);
                    }

                    toast.success('360° tour is ready! Your floor plan has been processed.', {
                        duration: 8000,
                    });
                } else if (planResult.status === 0) {
                    // Still processing - show elapsed time
                    const uploadTime = localStorage.getItem('getfloorplan_upload_time');
                    let timeMessage = '';
                    if (uploadTime) {
                        const elapsed = Math.floor((new Date().getTime() - new Date(uploadTime).getTime()) / 60000);
                        timeMessage = ` (${elapsed} min elapsed)`;
                    }
                    setProcessingProgress(`Processing... ${data.message || 'Generating 3D renders and 360° tour'}${timeMessage}`);
                }
            } else {
                // No results yet, still processing
                setProcessingProgress('Processing... Waiting for GetFloorPlan to start');
            }

        } catch (err: any) {
            console.error('Status check error:', err);
            // Don't stop polling on network errors, just log them
            setProcessingProgress(`Status check error: ${err.message}. Will retry...`);
        }
    };

    const downloadRoomTourVideo = async () => {
        if (!roomTourData || !roomTourData.rooms) {
            toast.error('No room tour data available');
            return;
        }

        const loadingToast = toast.loading('Generating video... This may take a moment');

        try {
            const formData = new FormData();
            formData.append('rooms', JSON.stringify(roomTourData.rooms));
            formData.append('filename', `room_tour_${Date.now()}.mp4`);

            const response = await fetch(`${API_BASE_URL}/generation/floor-plan/room-tour-video`, {
                method: 'POST',
                body: formData,
            });

            if (!response.ok) {
                throw new Error('Failed to generate video');
            }

            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `room_tour_${Date.now()}.mp4`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);

            toast.dismiss(loadingToast);
            toast.success('Video downloaded successfully!');
        } catch (err: any) {
            toast.dismiss(loadingToast);
            toast.error(`Video generation failed: ${err.message}`);
        }
    };

    const downloadRoomImage = async (imageUrl: string, roomType: string) => {
        try {
            const response = await fetch(imageUrl);
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `${roomType.replace(/\s+/g, '_')}_interior.jpg`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
            toast.success('Image downloaded successfully!');
        } catch (err) {
            toast.error('Failed to download image');
        }
    };

    // Download GLB model
    const downloadGLBModel = async (glbUrl: string) => {
        try {
            const response = await fetch(glbUrl, { mode: 'cors' });
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `floor_plan_3d_model_${Date.now()}.glb`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
            toast.success('3D Model downloaded successfully!');
        } catch (err) {
            // Fallback: open in new tab if CORS fails
            window.open(glbUrl, '_blank');
            toast.success('Opening model in new tab');
        }
    };

    // Download walkthrough image
    const downloadWalkthroughImage = async (imageUrl: string, viewName: string) => {
        try {
            const response = await fetch(imageUrl);
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `walkthrough_${viewName.replace(/\s+/g, '_')}_${Date.now()}.jpg`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
            toast.success(`${viewName} image downloaded!`);
        } catch (err) {
            toast.error('Failed to download image');
        }
    };

    // Download all walkthrough images
    const downloadAllWalkthroughImages = async () => {
        if (!tour360?.walkthrough_views) return;
        
        toast.success('Downloading all images...');
        for (const view of tour360.walkthrough_views) {
            await downloadWalkthroughImage(view.url, view.view);
            // Small delay between downloads
            await new Promise(resolve => setTimeout(resolve, 500));
        }
        toast.success('All images downloaded!');
    };

    const handleApplyEdit = async () => {
        if (!editInstruction.trim()) {
            toast.error('Please enter an edit instruction');
            return;
        }

        if (!roomTourData || !roomTourData.rooms[selectedRoomIndex]) {
            toast.error('No room selected');
            return;
        }

        const currentRoom = roomTourData.rooms[selectedRoomIndex];
        const currentImageUrl = currentRoom.image_url;

        // Save original if first edit
        if (!originalRoomImages[selectedRoomIndex]) {
            setOriginalRoomImages(prev => ({
                ...prev,
                [selectedRoomIndex]: currentImageUrl
            }));
        }

        setIsEditing(true);
        const loadingToast = toast.loading('Applying edit... This may take 10-15 seconds');

        try {
            const formData = new FormData();
            formData.append('image_url', currentImageUrl);
            formData.append('instruction', editInstruction);
            formData.append('guidance_scale', '7.5');
            formData.append('image_guidance_scale', '1.5');
            formData.append('steps', '50');

            const response = await fetch(`${API_BASE_URL}/generation/floor-plan/edit-interior`, {
                method: 'POST',
                body: formData
            });

            const data = await response.json();

            if (data.success && data.edited_url) {
                // Update room image
                const updatedRooms = [...roomTourData.rooms];
                updatedRooms[selectedRoomIndex] = {
                    ...currentRoom,
                    image_url: data.edited_url
                };
                setRoomTourData({
                    ...roomTourData,
                    rooms: updatedRooms
                });

                // Add to history
                setEditHistory([...editHistory, {
                    instruction: editInstruction,
                    url: data.edited_url
                }]);

                setEditInstruction('');
                toast.dismiss(loadingToast);
                toast.success('Edit applied successfully!');
            } else {
                throw new Error(data.reason || 'Failed to apply edit');
            }
        } catch (err: any) {
            toast.dismiss(loadingToast);
            toast.error(`Edit failed: ${err.message}`);
        } finally {
            setIsEditing(false);
        }
    };

    const handleUndoEdit = () => {
        if (editHistory.length === 0) {
            toast.error('No edits to undo');
            return;
        }

        const originalUrl = originalRoomImages[selectedRoomIndex];
        if (!originalUrl) {
            toast.error('Original image not found');
            return;
        }

        // Revert to original
        const updatedRooms = [...roomTourData.rooms];
        updatedRooms[selectedRoomIndex] = {
            ...updatedRooms[selectedRoomIndex],
            image_url: originalUrl
        };
        setRoomTourData({
            ...roomTourData,
            rooms: updatedRooms
        });

        // Clear edit history for this room
        setEditHistory([]);
        toast.success('Reverted to original');
    };

    return (
        <div className="min-h-screen bg-gradient-to-br from-cyan-50 via-blue-50 to-purple-50">
            <div className="container mx-auto p-6 max-w-7xl">
                {/* Back Button */}
                <button
                    onClick={() => navigate('/dashboard')}
                    className="flex items-center text-primary-600 hover:text-primary-700 mb-4 font-medium transition-colors"
                >
                    <ArrowLeft className="h-5 w-5 mr-2" />
                    Back to Dashboard
                </button>

                {/* Header */}
                <div className="flex items-center justify-between mb-8">
                    <div>
                        <h1 className="text-3xl font-bold bg-gradient-to-r from-purple-600 to-blue-600 bg-clip-text text-transparent">
                            Floor Plan AI
                        </h1>
                        <p className="text-gray-500 mt-2">
                            Upload your 2D plan, transform it into 3D visualization, and validate against UDA regulations.
                        </p>
                    </div>
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                    {/* Left Column - Input Section */}
                    <div className="lg:col-span-1 space-y-6">
                        <div className="bg-white rounded-lg border shadow-sm">
                            <div className="p-6 pb-4 border-b">
                                <h3 className="font-semibold text-lg">Upload Floor Plan</h3>
                            </div>
                            <div className="p-6 space-y-6">
                                {/* Step 1: Select Provider */}
                                <div>
                                    <label className="text-sm font-medium text-gray-700 mb-2 block">1. Select AI Provider</label>
                                    <div className="flex gap-4">
                                        <button
                                            onClick={() => setProvider('replicate')}
                                            className={`flex-1 px-4 py-2 rounded-md text-sm font-medium transition-colors border ${provider === 'replicate'
                                                ? 'bg-slate-900 text-white border-slate-900'
                                                : 'bg-white text-slate-900 border-gray-200 hover:bg-slate-50'
                                                }`}
                                        >
                                            AI Render (Fast)
                                        </button>
                                        <button
                                            onClick={() => setProvider('getfloorplan')}
                                            className={`flex-1 px-4 py-2 rounded-md text-sm font-medium transition-colors border ${provider === 'getfloorplan'
                                                ? 'bg-slate-900 text-white border-slate-900'
                                                : 'bg-white text-slate-900 border-gray-200 hover:bg-slate-50'
                                                }`}
                                        >
                                            3D Model (Full)
                                        </button>
                                    </div>
                                </div>

                                {/* Step 2: Select View Mode */}
                                {provider === 'replicate' && (
                                    <>
                                        {/* View Mode Selection */}
                                        <div>
                                            <label className="text-sm font-medium text-gray-700 mb-2 block">2. Select View Mode</label>
                                            <div className="flex gap-4">
                                                <button
                                                    onClick={() => setViewMode('birdseye')}
                                                    className={`flex-1 px-4 py-2 rounded-md text-sm font-medium transition-colors border flex items-center justify-center gap-2 ${viewMode === 'birdseye'
                                                        ? 'bg-blue-600 text-white border-blue-600'
                                                        : 'bg-white text-slate-900 border-gray-200 hover:bg-slate-50'
                                                        }`}
                                                >
                                                    <Layout className="h-4 w-4" />
                                                    Bird's Eye
                                                </button>
                                                <button
                                                    onClick={() => setViewMode('perspective')}
                                                    className={`flex-1 px-4 py-2 rounded-md text-sm font-medium transition-colors border flex items-center justify-center gap-2 ${viewMode === 'perspective'
                                                        ? 'bg-blue-600 text-white border-blue-600'
                                                        : 'bg-white text-slate-900 border-gray-200 hover:bg-slate-50'
                                                        }`}
                                                >
                                                    <Camera className="h-4 w-4" />
                                                    Room View
                                                </button>
                                            </div>
                                            <p className="text-[10px] text-gray-400 mt-1 italic">
                                                {viewMode === 'birdseye'
                                                    ? "Shows the full house layout from above (Dollhouse style)."
                                                    : "Zooms into a specific room (Perspective style)."}
                                            </p>
                                        </div>

                                        {/* Generation Mode Selection */}
                                        <div>
                                            <label className="text-sm font-medium text-gray-700 mb-2 block">3. Generation Mode</label>
                                            <div className="grid grid-cols-2 gap-2">
                                                <button
                                                    onClick={() => setGenerationMode('2d')}
                                                    className={`px-4 py-2 rounded-md text-sm font-medium transition-colors border flex items-center justify-center gap-2 ${generationMode === '2d'
                                                        ? 'bg-green-600 text-white border-green-600'
                                                        : 'bg-white text-slate-900 border-gray-200 hover:bg-slate-50'
                                                        }`}
                                                >
                                                    <ImageIcon className="h-4 w-4" />
                                                    2D Only
                                                </button>
                                                <button
                                                    onClick={() => setGenerationMode('complete')}
                                                    className={`px-4 py-2 rounded-md text-sm font-medium transition-colors border flex items-center justify-center gap-2 ${generationMode === 'complete'
                                                        ? 'bg-purple-600 text-white border-purple-600'
                                                        : 'bg-white text-slate-900 border-gray-200 hover:bg-slate-50'
                                                        }`}
                                                >
                                                    <Wand2 className="h-4 w-4" />
                                                    Complete (3D+360°)
                                                </button>
                                            </div>
                                            <p className="text-[10px] text-gray-400 mt-1 italic">
                                                {generationMode === '2d'
                                                    ? "2D photorealistic renders only (~15s)"
                                                    : "Complete: 3D model + 360° tour + 2D renders (~90s)"}
                                            </p>
                                        </div>
                                    </>
                                )}

                                {/* Step 3: Upload */}
                                <div className="border-2 border-dashed border-gray-200 rounded-lg p-6 text-center hover:border-blue-500 transition-colors">
                                    <input
                                        type="file"
                                        accept="image/*"
                                        onChange={handleFileSelect}
                                        className="hidden"
                                        id="floor-plan-upload"
                                    />
                                    <label htmlFor="floor-plan-upload" className="cursor-pointer block">
                                        {previewUrl ? (
                                            <img
                                                src={previewUrl}
                                                alt="Floor Plan Preview"
                                                className="max-h-48 mx-auto rounded shadow-sm"
                                            />
                                        ) : (
                                            <div className="flex flex-col items-center py-4">
                                                <Upload className="h-10 w-10 text-gray-400 mb-2" />
                                                <span className="text-gray-600 font-medium">Click to upload 2D Plan</span>
                                                <span className="text-[10px] text-gray-400 mt-1">Supports JPG, PNG</span>
                                            </div>
                                        )}
                                    </label>
                                </div>

                                {/* GetFloorPlan Upload and Status (when provider is getfloorplan) */}
                                {provider === 'getfloorplan' && (selectedFile || planId || isProcessingPlan) && (
                                    <div className="space-y-4">
                                        {/* Upload Button */}
                                        {!planId && selectedFile && (
                                            <button
                                                onClick={handleGetFloorPlanUpload}
                                                disabled={isUploadingPlan}
                                                className="w-full inline-flex items-center justify-center whitespace-nowrap rounded-md text-sm font-medium transition-colors h-10 px-4 py-2 bg-gradient-to-r from-green-600 to-teal-600 hover:from-green-700 hover:to-teal-700 text-white disabled:opacity-50"
                                            >
                                                {isUploadingPlan ? (
                                                    <>
                                                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                                        Uploading to GetFloorPlan...
                                                    </>
                                                ) : (
                                                    <>
                                                        <Upload className="mr-2 h-4 w-4" />
                                                        Upload to GetFloorPlan
                                                    </>
                                                )}
                                            </button>
                                        )}

                                        {/* Processing Status */}
                                        {isProcessingPlan && (
                                            <div className="rounded-lg border border-blue-200 bg-blue-50 p-4">
                                                <div className="flex items-start gap-3">
                                                    <Loader2 className="h-5 w-5 text-blue-600 animate-spin mt-0.5" />
                                                    <div className="flex-1">
                                                        <h5 className="font-medium text-blue-900 mb-1">Processing Floor Plan</h5>
                                                        <p className="text-xs text-blue-700">{processingProgress}</p>
                                                        <div className="mt-3 space-y-2">
                                                            <p className="text-xs text-blue-600">
                                                                ⏱️ Processing takes 30-120 minutes. You can safely close this page.
                                                            </p>
                                                            <p className="text-xs text-blue-600">
                                                                🔒 Your plan ID is saved. You can log back in later to check status.
                                                            </p>
                                                            <p className="text-xs text-blue-600">
                                                                🔄 Auto-checking every 2 minutes. Token auto-refreshes if needed.
                                                            </p>
                                                        </div>
                                                        {planId && (
                                                            <div className="mt-3 space-y-2">
                                                                <p className="text-xs text-blue-500 font-mono">
                                                                    Plan ID: {planId}
                                                                </p>
                                                                <button
                                                                    onClick={() => checkPlanStatus(planId)}
                                                                    className="text-xs px-3 py-1 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors mr-2"
                                                                >
                                                                    Check Status Now
                                                                </button>
                                                                <button
                                                                    onClick={() => {
                                                                        if (confirm('Clear saved plan ID and stop checking? You can still retrieve it from GetFloorPlan directly.')) {
                                                                            localStorage.removeItem('getfloorplan_plan_id');
                                                                            localStorage.removeItem('getfloorplan_upload_time');
                                                                            setPlanId(null);
                                                                            setIsProcessingPlan(false);
                                                                            if (statusCheckInterval) {
                                                                                clearInterval(statusCheckInterval);
                                                                                setStatusCheckInterval(null);
                                                                            }
                                                                            toast('Plan ID cleared');
                                                                        }
                                                                    }}
                                                                    className="text-xs px-3 py-1 bg-gray-600 text-white rounded hover:bg-gray-700 transition-colors"
                                                                >
                                                                    Clear Session
                                                                </button>
                                                            </div>
                                                        )}
                                                    </div>
                                                </div>
                                            </div>
                                        )}

                                        {/* Success - Tour Ready */}
                                        {tourUrl && !isProcessingPlan && (
                                            <div className="rounded-lg border border-green-200 bg-green-50 p-4">
                                                <div className="flex items-start gap-3">
                                                    <CheckCircle className="h-5 w-5 text-green-600 mt-0.5" />
                                                    <div className="flex-1">
                                                        <h5 className="font-medium text-green-900 mb-1">360° Tour Ready!</h5>
                                                        <p className="text-xs text-green-700 mb-2">Your virtual tour is ready to view below</p>
                                                        <a
                                                            href={tourUrl}
                                                            target="_blank"
                                                            rel="noopener noreferrer"
                                                            className="text-xs text-green-600 hover:text-green-700 underline"
                                                        >
                                                            Open in new tab →
                                                        </a>
                                                    </div>
                                                </div>
                                            </div>
                                        )}

                                        {/* GetFloorPlan Info */}
                                        <div className="rounded-lg border border-gray-200 bg-gray-50 p-3">
                                            <p className="text-xs text-gray-600">
                                                <strong>GetFloorPlan</strong> creates professional 3D models and 360° virtual tours.
                                                Processing time: 30-120 minutes.
                                            </p>
                                        </div>
                                    </div>
                                )}

                                {/* Replicate Generate Button (when provider is replicate) */}
                                {provider === 'replicate' && selectedFile && (
                                    <button
                                        onClick={handleGenerate}
                                        disabled={isGenerating}
                                        className="w-full inline-flex items-center justify-center whitespace-nowrap rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 h-10 px-4 py-2 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white"
                                    >
                                        {isGenerating ? (
                                            <>
                                                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                                Generating...
                                            </>
                                        ) : (
                                            <>
                                                <Wand2 className="mr-2 h-4 w-4" />
                                                Transform into 3D
                                            </>
                                        )}
                                    </button>
                                )}

                                {/* Room Tour Toggle and Button (only for replicate) */}
                                {provider === 'replicate' && selectedFile && result && (
                                    <div className="space-y-3 p-4 bg-gradient-to-r from-purple-50 to-pink-50 rounded-lg border border-purple-200">
                                        <div className="flex items-center justify-between">
                                            <label className="text-sm font-medium text-gray-700">🏠 Room Tour Mode</label>
                                            <label className="relative inline-flex items-center cursor-pointer">
                                                <input
                                                    type="checkbox"
                                                    className="sr-only peer"
                                                    checked={tourMode === 'tour'}
                                                    onChange={(e) => setTourMode(e.target.checked ? 'tour' : 'single')}
                                                />
                                                <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-purple-300 rounded-full peer peer-checked:after:translate-x-full rtl:peer-checked:after:-translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:start-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-purple-600"></div>
                                            </label>
                                        </div>

                                        {tourMode === 'tour' && (
                                            <button
                                                onClick={handleGenerateRoomTour}
                                                disabled={isGeneratingTour}
                                                className="w-full inline-flex items-center justify-center whitespace-nowrap rounded-md text-sm font-medium transition-colors h-10 px-4 py-2 bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white disabled:opacity-50"
                                            >
                                                {isGeneratingTour ? (
                                                    <>
                                                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                                        {tourProgress || 'Generating Tour...'}
                                                    </>
                                                ) : (
                                                    <>
                                                        <Box className="mr-2 h-4 w-4" />
                                                        Generate Room Tour
                                                    </>
                                                )}
                                            </button>
                                        )}

                                        {tourMode === 'tour' && !roomTourData && !isGeneratingTour && (
                                            <p className="text-xs text-gray-600 text-center">
                                                Click to generate individual 3D views for each room
                                            </p>
                                        )}
                                    </div>
                                )}

                                {error && (
                                    <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-red-900 flex items-start gap-3">
                                        <AlertTriangle className="h-5 w-5 text-red-600 mt-0.5" />
                                        <div>
                                            <h5 className="font-medium mb-1">Error</h5>
                                            <div className="text-xs opacity-90">{error}</div>
                                        </div>
                                    </div>
                                )}
                            </div>
                        </div>

                        {/* Building Parameters Card */}
                        {extractedData && (
                            <div className="bg-white rounded-lg border shadow-sm">
                                <div className="p-6 pb-4 border-b">
                                    <div className="flex items-center">
                                        <div className="bg-gradient-to-br from-purple-600 to-pink-600 rounded-lg p-2.5 mr-3">
                                            <TrendingUp className="h-5 w-5 text-white" />
                                        </div>
                                        <h3 className="font-semibold text-lg">Building Parameters</h3>
                                    </div>
                                </div>
                                <div className="p-6 space-y-3">
                                    <div className="bg-gray-50 rounded-lg p-3">
                                        <label className="block text-xs text-gray-600 mb-1">Front Setback (feet)</label>
                                        <input
                                            type="number"
                                            value={buildingParams.front_setback}
                                            onChange={(e) => setBuildingParams({ ...buildingParams, front_setback: Number(e.target.value) })}
                                            className="w-full px-2 py-1 border border-gray-300 rounded text-sm"
                                        />
                                    </div>
                                    <div className="bg-gray-50 rounded-lg p-3">
                                        <label className="block text-xs text-gray-600 mb-1">Rear Setback (feet)</label>
                                        <input
                                            type="number"
                                            value={buildingParams.rear_setback}
                                            onChange={(e) => setBuildingParams({ ...buildingParams, rear_setback: Number(e.target.value) })}
                                            className="w-full px-2 py-1 border border-gray-300 rounded text-sm"
                                        />
                                    </div>
                                    <div className="bg-gray-50 rounded-lg p-3">
                                        <label className="block text-xs text-gray-600 mb-1">Side Setback (feet)</label>
                                        <input
                                            type="number"
                                            value={buildingParams.side_setback}
                                            onChange={(e) => setBuildingParams({ ...buildingParams, side_setback: Number(e.target.value) })}
                                            className="w-full px-2 py-1 border border-gray-300 rounded text-sm"
                                        />
                                    </div>
                                    <div className="bg-gray-50 rounded-lg p-3">
                                        <label className="block text-xs text-gray-600 mb-1">Building Coverage (%)</label>
                                        <input
                                            type="number"
                                            value={buildingParams.building_coverage}
                                            onChange={(e) => setBuildingParams({ ...buildingParams, building_coverage: Number(e.target.value) })}
                                            className="w-full px-2 py-1 border border-gray-300 rounded text-sm"
                                        />
                                    </div>
                                    <div className="bg-gray-50 rounded-lg p-3">
                                        <label className="block text-xs text-gray-600 mb-1">Parking Spaces</label>
                                        <input
                                            type="number"
                                            value={buildingParams.parking_spaces}
                                            onChange={(e) => setBuildingParams({ ...buildingParams, parking_spaces: Number(e.target.value) })}
                                            className="w-full px-2 py-1 border border-gray-300 rounded text-sm"
                                        />
                                    </div>

                                    <button
                                        onClick={validateAgainstUDA}
                                        disabled={validatingUda}
                                        className="w-full px-4 py-3 bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white font-semibold rounded-lg transition-all disabled:opacity-50 flex items-center justify-center shadow-md hover:shadow-lg mt-4"
                                    >
                                        {validatingUda ? (
                                            <>
                                                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                                                Validating...
                                            </>
                                        ) : (
                                            <>
                                                <Shield className="h-4 w-4 mr-2" />
                                                Validate UDA Regulations
                                            </>
                                        )}
                                    </button>
                                </div>
                            </div>
                        )}
                    </div>

                    {/* Right Column - Results */}
                    <div className="lg:col-span-2 space-y-6">
                        {/* 3D Visualization Output */}
                        <div className="bg-slate-50 rounded-lg border shadow-sm min-h-[400px] flex flex-col">
                            <div className="p-6 pb-4 border-b bg-white rounded-t-lg">
                                <h3 className="font-semibold text-lg text-slate-900">Generation Results</h3>
                                {generationMode === 'complete' && (
                                    <p className="text-sm text-gray-500 mt-1">Complete package: 2D Renders, 3D Model & 360° Tour</p>
                                )}
                            </div>
                            <div className="p-6 flex-1 flex items-center justify-center">
                                {/* GetFloorPlan 360° Tour Display */}
                                {provider === 'getfloorplan' && tourUrl ? (
                                    <div className="w-full h-full space-y-4">
                                        <div className="rounded-lg border border-green-200 bg-green-50 p-4">
                                            <div className="flex items-center gap-3">
                                                <CheckCircle className="h-5 w-5 text-green-600" />
                                                <div>
                                                    <h5 className="font-medium text-green-900">360° Virtual Tour Ready</h5>
                                                    <p className="text-xs text-green-700 mt-1">
                                                        Interactive 3D walkthrough created by GetFloorPlan
                                                    </p>
                                                </div>
                                            </div>
                                        </div>
                                        <div className="rounded-lg overflow-hidden shadow-xl border-2 border-gray-200" style={{ height: '600px' }}>
                                            <iframe
                                                src={tourUrl}
                                                className="w-full h-full"
                                                title="GetFloorPlan 360° Virtual Tour"
                                                frameBorder="0"
                                                allowFullScreen
                                            />
                                        </div>
                                        <div className="flex justify-end">
                                            <button
                                                onClick={() => window.open(tourUrl, '_blank')}
                                                className="inline-flex items-center justify-center whitespace-nowrap rounded-md text-sm font-medium border border-gray-200 bg-white text-gray-900 hover:bg-gray-100 h-9 px-4 py-2 shadow-sm transition-all"
                                            >
                                                <Camera className="mr-2 h-4 w-4" />
                                                Open in Full Screen
                                            </button>
                                        </div>
                                    </div>
                                ) : (result?.image_url || model3D || tour360) ? (
                                    <div className="space-y-4 w-full">
                                        {/* Tabs for different views */}
                                        {generationMode === 'complete' && (
                                            <Tabs value={activeTab} onChange={(_e: React.SyntheticEvent, newValue: number) => setActiveTab(newValue)}>
                                                <Tab label="2D Renders" />
                                                <Tab label="3D Model" disabled={!model3D?.glb_url} />
                                                <Tab label="360° Tour" disabled={!tour360?.walkthrough_views && !tour360?.panorama_url} />
                                            </Tabs>
                                        )}

                                        {/* Tab Content */}
                                        {(activeTab === 0 || generationMode === '2d') && result && (
                                            <div className="space-y-6">
                                                {/* Bird's Eye View (optional) */}
                                                {result.image_url && (
                                                    <div>
                                                        <h4 className="font-semibold text-md mb-2 text-gray-700">Bird's Eye View</h4>
                                                        <img
                                                            src={result.image_url}
                                                            alt="Overall House View"
                                                            className="w-full rounded-lg shadow-xl"
                                                        />
                                                    </div>
                                                )}

                                                {/* Individual Room Renders Gallery */}
                                                {(result as any).rooms && (result as any).rooms.length > 0 && (
                                                    <div>
                                                        <h4 className="font-semibold text-md mb-3 text-gray-700">
                                                            Individual Room Renders ({(result as any).rooms.length})
                                                        </h4>
                                                        <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                                                            {(result as any).rooms.map((room: any, index: number) => (
                                                                <div key={index} className="relative group overflow-hidden rounded-lg shadow-md hover:shadow-xl transition-shadow">
                                                                    <img
                                                                        src={room.image_url}
                                                                        alt={room.room_type}
                                                                        className="w-full h-48 object-cover"
                                                                    />
                                                                    <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/70 to-transparent text-white p-3">
                                                                        <p className="text-sm font-medium">{room.room_type}</p>
                                                                    </div>
                                                                </div>
                                                            ))}
                                                        </div>
                                                    </div>
                                                )}

                                                <div className="flex justify-end pt-2 gap-2">
                                                    <button
                                                        onClick={download3DModel}
                                                        className="inline-flex items-center justify-center whitespace-nowrap rounded-md text-xs font-medium border border-gray-200 bg-white text-gray-900 hover:bg-gray-100 h-9 px-4 py-2 shadow-sm transition-all"
                                                    >
                                                        <ImageIcon className="mr-2 h-4 w-4" />
                                                        Download All Images
                                                    </button>
                                                    <button
                                                        className="inline-flex items-center justify-center whitespace-nowrap rounded-md text-xs font-medium border border-transparent bg-blue-600 text-white hover:bg-blue-700 h-9 px-4 py-2 shadow-sm transition-all"
                                                        onClick={() => {
                                                            setNewProjectName('Modern Residential Layout');
                                                            setIsSaveModalOpen(true);
                                                        }}
                                                    >
                                                        <Save className="mr-2 h-4 w-4" />
                                                        Save to Project
                                                    </button>
                                                </div>
                                            </div>
                                        )}

                                        {/* 3D Model Tab */}
                                        {activeTab === 1 && model3D?.glb_url && (
                                            <div className="space-y-4">
                                                <div className="text-center p-8 bg-white rounded-xl shadow-sm border border-green-100">
                                                    <Box className="h-16 w-16 text-green-500 mx-auto mb-4" />
                                                    <h3 className="font-semibold text-lg text-green-700">3D Model Ready!</h3>
                                                    <p className="text-sm text-gray-600 mb-6">Interactive 3D GLB model generated successfully.</p>
                                                    <button
                                                        onClick={() => downloadGLBModel(model3D.glb_url)}
                                                        className="inline-flex items-center justify-center whitespace-nowrap rounded-md text-sm font-medium border border-gray-200 bg-white text-gray-900 hover:bg-gray-100 h-9 px-4 py-2 shadow-sm transition-all"
                                                    >
                                                        <Box className="mr-2 h-4 w-4" />
                                                        Download GLB Model
                                                    </button>
                                                </div>
                                            </div>
                                        )}

                                        {/* 360° Tour / Walkthrough Tab */}
                                        {activeTab === 2 && (tour360?.panorama_url || tour360?.walkthrough_views) && (
                                            <div className="space-y-4">
                                                {tour360?.walkthrough_views ? (
                                                    <div className="space-y-4">
                                                        <div className="text-center p-4 bg-white rounded-xl shadow-sm border border-purple-100">
                                                            <Camera className="h-12 w-12 text-purple-500 mx-auto mb-3" />
                                                            <h3 className="font-semibold text-lg text-purple-700">Virtual Walkthrough Ready!</h3>
                                                            <p className="text-sm text-gray-600 mb-4">{tour360.walkthrough_views.length} viewpoints generated</p>
                                                        </div>
                                                        
                                                        {/* AI Interior Customization Component */}
                                                        {tour360.walkthrough_views.length > 0 && (
                                                            <InteriorCustomizer
                                                                tourImageId={tour360.id || 1}
                                                                tourImageUrl={tour360.walkthrough_views[0].url}
                                                                onImageUpdated={(newUrl) => {
                                                                    // Update the first view with customized image
                                                                    const updatedViews = [...tour360.walkthrough_views];
                                                                    updatedViews[0] = { ...updatedViews[0], url: newUrl };
                                                                    setTour360({
                                                                        ...tour360,
                                                                        walkthrough_views: updatedViews
                                                                    });
                                                                }}
                                                            />
                                                        )}
                                                        
                                                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                                            {tour360.walkthrough_views.map((view: any, index: number) => (
                                                                <div key={index} className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
                                                                    <img 
                                                                        src={view.url} 
                                                                        alt={view.view}
                                                                        className="w-full h-48 object-cover cursor-pointer hover:opacity-90 transition-opacity"
                                                                        onClick={() => window.open(view.url, '_blank')}
                                                                    />
                                                                    <div className="p-3 flex items-center justify-between">
                                                                        <p className="text-sm font-semibold text-gray-700 capitalize">{view.view.replace('_', ' ')}</p>
                                                                        <button
                                                                            onClick={(e) => {
                                                                                e.stopPropagation();
                                                                                downloadWalkthroughImage(view.url, view.view);
                                                                            }}
                                                                            className="p-1.5 rounded-md hover:bg-gray-100 transition-colors"
                                                                            title="Download image"
                                                                        >
                                                                            <svg className="w-4 h-4 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                                                                            </svg>
                                                                        </button>
                                                                    </div>
                                                                </div>
                                                            ))}
                                                        </div>
                                                        <div className="flex justify-end mt-4">
                                                            <button
                                                                onClick={downloadAllWalkthroughImages}
                                                                className="inline-flex items-center justify-center whitespace-nowrap rounded-md text-sm font-medium border border-gray-200 bg-white text-gray-900 hover:bg-gray-100 h-9 px-4 py-2 shadow-sm transition-all"
                                                            >
                                                                <svg className="mr-2 h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                                                                </svg>
                                                                Download All Images
                                                            </button>
                                                        </div>
                                                    </div>
                                                ) : tour360?.panorama_url ? (
                                                    <div className="text-center p-8 bg-white rounded-xl shadow-sm border border-purple-100">
                                                        <Camera className="h-16 w-16 text-purple-500 mx-auto mb-4" />
                                                        <h3 className="font-semibold text-lg text-purple-700">360° Tour Ready!</h3>
                                                        <p className="text-sm text-gray-600 mb-6">Immersive panoramic view generated successfully.</p>
                                                        <button
                                                            onClick={() => window.open(tour360.panorama_url, '_blank')}
                                                            className="inline-flex items-center justify-center whitespace-nowrap rounded-md text-sm font-medium border border-gray-200 bg-white text-gray-900 hover:bg-gray-100 h-9 px-4 py-2 shadow-sm transition-all"
                                                        >
                                                            <Camera className="mr-2 h-4 w-4" />
                                                            View 360° Tour
                                                        </button>
                                                    </div>
                                                ) : null}
                                            </div>
                                        )}
                                    </div>
                                ) : result?.model_url ? (
                                    <div className="text-center p-8 bg-white rounded-xl shadow-sm border border-green-100">
                                        <Box className="h-16 w-16 text-green-500 mx-auto mb-4" />
                                        <h3 className="font-semibold text-lg text-green-700">3D Model Ready</h3>
                                        <p className="text-sm text-gray-600 mb-6">Interactive 3D model generated by CubiCasa.</p>
                                        <button
                                            className="w-full inline-flex items-center justify-center whitespace-nowrap rounded-md text-sm font-medium bg-slate-900 text-white hover:bg-slate-800 h-10 px-4 py-2"
                                            onClick={() => window.open(result.model_url, '_blank')}
                                        >
                                            Launch 3D Player
                                        </button>
                                    </div>
                                ) : (
                                    <div className="text-center text-gray-400">
                                        <ImageIcon className="h-16 w-16 mx-auto mb-4 opacity-20" />
                                        <p className="text-sm max-w-[200px] mx-auto">Your generated 3D interior will appear here once ready.</p>
                                    </div>
                                )}
                            </div>
                        </div>

                        {/* Room Tour Viewer */}
                        {roomTourData && tourMode === 'tour' && (
                            <div className="bg-white rounded-lg border shadow-sm">
                                <div className="p-6 pb-4 border-b">
                                    <div className="flex items-center justify-between">
                                        <div>
                                            <h3 className="font-semibold text-lg text-slate-900">
                                                🏠 3D Room Tour ({roomTourData.success_rate})
                                            </h3>
                                            <span className="text-xs bg-purple-100 text-purple-700 px-3 py-1 rounded-full font-medium mt-1 inline-block">
                                                {roomTourData.rooms.length} Rooms
                                            </span>
                                        </div>
                                        <button
                                            onClick={downloadRoomTourVideo}
                                            className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-purple-600 to-pink-600 text-white rounded-lg hover:from-purple-700 hover:to-pink-700 transition-all shadow-md hover:shadow-lg"
                                        >
                                            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
                                            </svg>
                                            <span className="font-medium">Download Video</span>
                                        </button>
                                    </div>
                                </div>

                                <div className="p-6">
                                    {/* Room Navigation Tabs */}
                                    <div className="flex gap-2 mb-6 overflow-x-auto pb-2">
                                        {roomTourData.rooms.map((room: any, idx: number) => (
                                            <button
                                                key={idx}
                                                onClick={() => setSelectedRoomIndex(idx)}
                                                className={`px-4 py-2 rounded-lg text-sm font-medium whitespace-nowrap transition-all ${selectedRoomIndex === idx
                                                    ? 'bg-purple-600 text-white shadow-md'
                                                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                                                    }`}
                                            >
                                                {room.room_type}
                                            </button>
                                        ))}
                                    </div>

                                    {/* Active Room Display */}
                                    {roomTourData.rooms[selectedRoomIndex] && (
                                        <div className="space-y-4">
                                            <div className="relative rounded-lg overflow-hidden shadow-xl">
                                                {roomTourData.rooms[selectedRoomIndex].status === 'completed' ? (
                                                    <img
                                                        src={roomTourData.rooms[selectedRoomIndex].image_url}
                                                        alt={roomTourData.rooms[selectedRoomIndex].room_type}
                                                        className="w-full h-auto"
                                                    />
                                                ) : (
                                                    <div className="bg-gray-100 p-12 text-center">
                                                        <XCircle className="h-12 w-12 text-red-400 mx-auto mb-2" />
                                                        <p className="text-sm text-gray-600">
                                                            Failed to generate this room
                                                        </p>
                                                    </div>
                                                )}
                                            </div>

                                            {/* Room Info */}
                                            <div className="bg-gradient-to-r from-purple-50 to-pink-50 rounded-lg p-4">
                                                <h4 className="font-semibold text-gray-900 mb-2">
                                                    {roomTourData.rooms[selectedRoomIndex].room_type}
                                                </h4>
                                                <div className="grid grid-cols-2 gap-4 text-sm">
                                                    <div>
                                                        <span className="text-gray-600">Dimensions:</span>
                                                        <p className="font-medium text-gray-900">{roomTourData.rooms[selectedRoomIndex].dimensions}</p>
                                                    </div>
                                                    {roomTourData.rooms[selectedRoomIndex].area && (
                                                        <div>
                                                            <span className="text-gray-600">Area:</span>
                                                            <p className="font-medium text-gray-900">{roomTourData.rooms[selectedRoomIndex].area} m²</p>
                                                        </div>
                                                    )}
                                                </div>
                                            </div>

                                            {/* Download Image Button */}
                                            {roomTourData.rooms[selectedRoomIndex]?.status === 'completed' && (
                                                <button
                                                    onClick={() => downloadRoomImage(
                                                        roomTourData.rooms[selectedRoomIndex].image_url,
                                                        roomTourData.rooms[selectedRoomIndex].room_type
                                                    )}
                                                    className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium text-center flex items-center justify-center gap-2"
                                                >
                                                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                                                    </svg>
                                                    Download Image
                                                </button>
                                            )}

                                            {/* Navigation Buttons */}
                                            <div className="flex gap-2 justify-between mt-3">
                                                <button
                                                    onClick={() => setSelectedRoomIndex(Math.max(0, selectedRoomIndex - 1))}
                                                    disabled={selectedRoomIndex === 0}
                                                    className="flex-1 px-4 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-lg font-medium disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                                                >
                                                    ← Previous
                                                </button>
                                                <button
                                                    onClick={() => setSelectedRoomIndex(Math.min(roomTourData.rooms.length - 1, selectedRoomIndex + 1))}
                                                    disabled={selectedRoomIndex === roomTourData.rooms.length - 1}
                                                    className="flex-1 px-4 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-lg font-medium disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                                                >
                                                    Next →
                                                </button>
                                            </div>

                                            {/* Edit Mode Toggle */}
                                            {roomTourData.rooms[selectedRoomIndex]?.status === 'completed' && (
                                                <div className="mt-4">
                                                    <button
                                                        onClick={() => setEditMode(!editMode)}
                                                        className={`w-full px-4 py-2 rounded-lg font-medium transition-all ${editMode
                                                            ? 'bg-purple-600 text-white'
                                                            : 'bg-gradient-to-r from-purple-600 to-pink-600 text-white hover:from-purple-700 hover:to-pink-700'
                                                            }`}
                                                    >
                                                        {editMode ? '✓ Exit Edit Mode' : '✏️ Edit Interior Design'}
                                                    </button>
                                                </div>
                                            )}

                                            {/* Edit Interface */}
                                            {editMode && (
                                                <div className="mt-4 p-4 bg-gradient-to-r from-purple-50 to-pink-50 rounded-lg border border-purple-200">
                                                    <label className="block text-sm font-medium text-gray-700 mb-2">
                                                        What would you like to change?
                                                    </label>
                                                    <input
                                                        type="text"
                                                        value={editInstruction}
                                                        onChange={(e) => setEditInstruction(e.target.value)}
                                                        placeholder="e.g., change wall color to navy blue"
                                                        className="w-full px-4 py-2 border border-purple-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                                                        disabled={isEditing}
                                                    />

                                                    {/* Action Buttons */}
                                                    <div className="flex gap-2 mt-3">
                                                        <button
                                                            onClick={handleApplyEdit}
                                                            disabled={isEditing || !editInstruction.trim()}
                                                            className="flex-1 bg-purple-600 text-white py-2 rounded-lg hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed font-medium"
                                                        >
                                                            {isEditing ? 'Applying...' : 'Apply Edit'}
                                                        </button>
                                                        <button
                                                            onClick={handleUndoEdit}
                                                            disabled={isEditing || editHistory.length === 0}
                                                            className="px-4 bg-gray-200 hover:bg-gray-300 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed font-medium"
                                                        >
                                                            Undo
                                                        </button>
                                                    </div>

                                                    {/* Quick Edit Presets */}
                                                    <div className="mt-4">
                                                        <p className="text-xs text-gray-600 mb-2">Quick Edits:</p>
                                                        <div className="grid grid-cols-2 gap-2">
                                                            {[
                                                                { label: 'Modern Style', instruction: 'make it more modern and minimalist' },
                                                                { label: 'Warm Lighting', instruction: 'add warm and cozy lighting' },
                                                                { label: 'Add Plants', instruction: 'add indoor plants and greenery' },
                                                                { label: 'Hardwood Floor', instruction: 'change to hardwood flooring' }
                                                            ].map((preset) => (
                                                                <button
                                                                    key={preset.label}
                                                                    onClick={() => {
                                                                        setEditInstruction(preset.instruction);
                                                                    }}
                                                                    disabled={isEditing}
                                                                    className="text-xs px-3 py-2 bg-white border border-purple-200 rounded-lg hover:bg-purple-50 hover:border-purple-300 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                                                                >
                                                                    {preset.label}
                                                                </button>
                                                            ))}
                                                        </div>
                                                    </div>

                                                    {/* Edit History */}
                                                    {editHistory.length > 0 && (
                                                        <div className="mt-4">
                                                            <p className="text-xs text-gray-600 mb-2">Edit History ({editHistory.length})</p>
                                                            <div className="space-y-1">
                                                                {editHistory.map((edit, idx) => (
                                                                    <div key={idx} className="flex items-center justify-between text-xs p-2 bg-white rounded border border-purple-100">
                                                                        <span className="text-gray-700">✓ {edit.instruction}</span>
                                                                    </div>
                                                                ))}
                                                            </div>
                                                        </div>
                                                    )}
                                                </div>
                                            )}
                                        </div>
                                    )}
                                </div>
                            </div>
                        )}

                        {/* UDA Validation Report */}
                        {udaValidation && (
                            <div className="bg-white rounded-lg border shadow-sm">
                                <div className="p-6 pb-4 border-b">
                                    <div className="flex items-center justify-between">
                                        <div className="flex items-center">
                                            <div className="bg-gradient-to-br from-purple-600 to-pink-600 rounded-lg p-2.5 mr-3">
                                                <Shield className="h-5 w-5 text-white" />
                                            </div>
                                            <div>
                                                <h3 className="font-semibold text-lg">UDA Regulations Report</h3>
                                                <p className="text-sm text-gray-600">Sri Lankan building standards compliance</p>
                                            </div>
                                        </div>
                                        <button
                                            onClick={downloadValidationPDF}
                                            className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-purple-600 to-pink-600 text-white rounded-lg hover:from-purple-700 hover:to-pink-700 transition-all shadow-md hover:shadow-lg"
                                        >
                                            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                                            </svg>
                                            <span className="font-medium">Download Report</span>
                                        </button>
                                    </div>
                                </div>

                                <div className="p-6 space-y-4">
                                    {/* Compliance Score */}
                                    <div className="bg-gray-50 rounded-lg p-4">
                                        <div className="flex items-center justify-between mb-2">
                                            <span className="text-sm font-medium text-gray-700">UDA Compliance Score</span>
                                            <span className="text-2xl font-bold text-gray-900">
                                                {udaValidation.compliance_score?.toFixed(0)}%
                                            </span>
                                        </div>
                                        <div className="w-full bg-gray-200 rounded-full h-3">
                                            <div
                                                className={`h-3 rounded-full transition-all ${udaValidation.compliance_score >= 80
                                                    ? 'bg-green-500'
                                                    : udaValidation.compliance_score >= 60
                                                        ? 'bg-yellow-500'
                                                        : 'bg-red-500'
                                                    }`}
                                                style={{ width: `${udaValidation.compliance_score}%` }}
                                            ></div>
                                        </div>
                                        <div className="flex items-center mt-2">
                                            {udaValidation.is_compliant ? (
                                                <CheckCircle className="h-5 w-5 text-green-500 mr-2" />
                                            ) : (
                                                <XCircle className="h-5 w-5 text-red-500 mr-2" />
                                            )}
                                            <span className={`text-sm font-medium ${udaValidation.is_compliant ? 'text-green-700' : 'text-red-700'}`}>
                                                {udaValidation.is_compliant ? 'UDA Compliant' : 'Non-Compliant - Violations Found'}
                                            </span>
                                        </div>
                                    </div>

                                    {/* Violations */}
                                    {udaValidation.violations && udaValidation.violations.length > 0 && (
                                        <div>
                                            <h4 className="text-sm font-semibold text-red-700 flex items-center mb-2">
                                                <XCircle className="h-4 w-4 mr-2" />
                                                Violations ({udaValidation.violations.length})
                                            </h4>
                                            <div className="space-y-2">
                                                {udaValidation.violations.map((violation: any, index: number) => (
                                                    <div key={index} className="bg-red-50 border-l-4 border-red-500 rounded-lg p-3">
                                                        <div className="flex items-start">
                                                            <XCircle className="h-4 w-4 text-red-600 mr-2 mt-0.5 flex-shrink-0" />
                                                            <div className="flex-1">
                                                                <p className="text-sm font-semibold text-red-900">{violation.rule}</p>
                                                                <p className="text-xs text-red-700 mt-1">{violation.message}</p>
                                                                <p className="text-xs text-red-600 mt-1 italic">{violation.regulation}</p>
                                                            </div>
                                                        </div>
                                                    </div>
                                                ))}
                                            </div>
                                        </div>
                                    )}

                                    {/* Warnings */}
                                    {udaValidation.warnings && udaValidation.warnings.length > 0 && (
                                        <div>
                                            <h4 className="text-sm font-semibold text-yellow-700 flex items-center mb-2">
                                                <AlertTriangle className="h-4 w-4 mr-2" />
                                                Warnings ({udaValidation.warnings.length})
                                            </h4>
                                            <div className="space-y-2">
                                                {udaValidation.warnings.map((warning: any, index: number) => (
                                                    <div key={index} className="bg-yellow-50 border-l-4 border-yellow-500 rounded-lg p-3">
                                                        <div className="flex items-start">
                                                            <AlertTriangle className="h-4 w-4 text-yellow-600 mr-2 mt-0.5 flex-shrink-0" />
                                                            <div className="flex-1">
                                                                <p className="text-sm font-semibold text-yellow-900">{warning.rule}</p>
                                                                <p className="text-xs text-yellow-700 mt-1">{warning.message}</p>
                                                                <p className="text-xs text-yellow-600 mt-1 italic">{warning.regulation}</p>
                                                            </div>
                                                        </div>
                                                    </div>
                                                ))}
                                            </div>
                                        </div>
                                    )}

                                    {/* Passed Checks */}
                                    {udaValidation.passed_checks && udaValidation.passed_checks.length > 0 && (
                                        <div>
                                            <h4 className="text-sm font-semibold text-green-700 flex items-center mb-2">
                                                <CheckCircle className="h-4 w-4 mr-2" />
                                                Passed Checks ({udaValidation.passed_checks.length})
                                            </h4>
                                            <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                                                {udaValidation.passed_checks.map((check: any, index: number) => (
                                                    <div key={index} className="bg-green-50 border border-green-200 rounded-lg p-2">
                                                        <div className="flex items-center">
                                                            <CheckCircle className="h-3 w-3 text-green-600 mr-2 flex-shrink-0" />
                                                            <p className="text-xs font-medium text-green-900">{check.rule}</p>
                                                        </div>
                                                    </div>
                                                ))}
                                            </div>
                                        </div>
                                    )}

                                    {/* Recommendations */}
                                    {udaValidation.recommendations && udaValidation.recommendations.length > 0 && (
                                        <div>
                                            <h4 className="text-sm font-semibold text-blue-700 flex items-center mb-2">
                                                <TrendingUp className="h-4 w-4 mr-2" />
                                                Recommendations ({udaValidation.recommendations.length})
                                            </h4>
                                            <div className="space-y-2">
                                                {udaValidation.recommendations.map((rec: any, index: number) => (
                                                    <div key={index} className="bg-blue-50 border-l-4 border-blue-400 rounded-lg p-3">
                                                        <p className="text-xs font-semibold text-blue-900">{rec.category}</p>
                                                        <p className="text-xs text-blue-700 mt-1">{rec.message}</p>
                                                    </div>
                                                ))}
                                            </div>
                                        </div>
                                    )}
                                </div>
                            </div>
                        )}
                    </div>
                </div>
                {/* Save Project Modal */}
                <Dialog open={isSaveModalOpen} onClose={() => setIsSaveModalOpen(false)} maxWidth="sm" fullWidth>
                    <DialogTitle>Save as New Project</DialogTitle>
                    <DialogContent>
                        <div className="space-y-4 pt-2">
                            <p className="text-sm text-gray-500">
                                Create a new project from your generated floor plan design.
                                The 3D model and validation report will be saved.
                            </p>
                            <TextField
                                autoFocus
                                margin="dense"
                                label="Project Name"
                                type="text"
                                fullWidth
                                variant="outlined"
                                value={newProjectName}
                                onChange={(e) => setNewProjectName(e.target.value)}
                            />
                            <TextField
                                margin="dense"
                                label="Description (Optional)"
                                type="text"
                                fullWidth
                                multiline
                                rows={3}
                                variant="outlined"
                                value={newProjectDescription}
                                onChange={(e) => setNewProjectDescription(e.target.value)}
                            />
                        </div>
                    </DialogContent>
                    <DialogActions>
                        <Button onClick={() => setIsSaveModalOpen(false)} color="inherit">
                            Cancel
                        </Button>
                        <Button
                            onClick={handleSaveProject}
                            variant="contained"
                            color="primary"
                            disabled={isSaving}
                            startIcon={isSaving ? <Loader2 className="animate-spin h-4 w-4" /> : <Save className="h-4 w-4" />}
                        >
                            {isSaving ? 'Saving...' : 'Create Project'}
                        </Button>
                    </DialogActions>
                </Dialog>
            </div >
        </div >
    );
};

export default FloorPlanGenerator;
