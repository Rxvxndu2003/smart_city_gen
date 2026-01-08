"""
Comprehensive Report Service for Smart City Planning System.
Generates professional PDF reports combining all analysis results.
"""
import logging
import os
from datetime import datetime
from io import BytesIO
import json
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, 
    Image, PageBreak, Frame, PageTemplate
)
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics import renderPDF

from sqlalchemy.orm import Session
from app.models.project import Project
from app.models.analysis_result import AnalysisResult, AnalysisType

logger = logging.getLogger(__name__)

class ComprehensiveReportService:
    """Service for generating comprehensive project reports."""
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._create_custom_styles()
        
    def _create_custom_styles(self):
        """Create custom paragraph styles for professional look."""
        self.styles.add(ParagraphStyle(
            name='ReportTitle',
            parent=self.styles['Heading1'],
            fontSize=28,
            leading=34,
            alignment=TA_CENTER,
            spaceAfter=30,
            textColor=colors.HexColor('#1a237e')
        ))
        
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading2'],
            fontSize=18,
            leading=22,
            spaceBefore=20,
            spaceAfter=10,
            textColor=colors.HexColor('#283593'),
            borderPadding=(0, 0, 5, 0),
            borderWidth=0,
            borderColor=colors.HexColor('#283593')
        ))
        
        self.styles.add(ParagraphStyle(
            name='SubHeader',
            parent=self.styles['Heading3'],
            fontSize=14,
            leading=18,
            spaceBefore=15,
            spaceAfter=8,
            textColor=colors.HexColor('#303f9f')
        ))
        
        self.styles.add(ParagraphStyle(
            name='NormalJustified',
            parent=self.styles['Normal'],
            alignment=TA_JUSTIFY,
            fontSize=11,
            leading=14,
            spaceAfter=8
        ))
        
        self.styles.add(ParagraphStyle(
            name='ComplianceBadge',
            parent=self.styles['Normal'],
            fontSize=12,
            leading=16,
            alignment=TA_CENTER,
            textColor=colors.white,
            backColor=colors.green,
            borderPadding=5,
            borderRadius=5
        ))

    def generate_report(self, db: Session, project_id: int) -> BytesIO:
        """
        Generate comprehensive PDF report for a project.
        
        Args:
            db: Database session
            project_id: Project ID
            
        Returns:
            BytesIO containing the PDF
        """
        # Fetch project and analysis data
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise ValueError(f"Project with ID {project_id} not found")
            
        analyses = self._fetch_analyses(db, project_id)
        
        # Create PDF buffer
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=inch,
            leftMargin=inch,
            topMargin=inch,
            bottomMargin=inch
        )
        
        story = []
        
        # 1. Cover Page
        self._create_cover_page(story, project)
        
        # 2. Executive Summary
        self._create_executive_summary(story, project, analyses)
        
        # 3. Compliance Overview
        self._create_compliance_section(story, analyses)
        
        # 4. Structural Analysis
        if analyses.get(AnalysisType.STRUCTURAL):
            self._create_structural_section(story, analyses[AnalysisType.STRUCTURAL])
            
        # 5. Energy Analysis
        if analyses.get(AnalysisType.ENERGY):
            self._create_energy_section(story, analyses[AnalysisType.ENERGY])
            
        # 6. Green Space Analysis
        if analyses.get(AnalysisType.GREEN_SPACE):
            self._create_green_space_section(story, analyses[AnalysisType.GREEN_SPACE])
            
        # 7. Recommendations
        self._create_recommendations_section(story, analyses)
        
        # Build PDF
        doc.build(story, onFirstPage=self._header_footer, onLaterPages=self._header_footer)
        buffer.seek(0)
        return buffer

    def _fetch_analyses(self, db: Session, project_id: int) -> dict:
        """Fetch all latest analysis results for the project."""
        results = db.query(AnalysisResult).filter(
            AnalysisResult.project_id == project_id
        ).all()
        
        analyses = {}
        for result in results:
            # Store by type, overwriting if multiple (though we ideally keep latest)
            # Since we didn't order by date in query, assume latest is last updated
            # Ideally standard query should handle "latest by type"
            analyses[result.analysis_type] = result.analysis_data
            
        return analyses

    def _header_footer(self, canvas, doc):
        """Add header and footer to pages."""
        canvas.saveState()
        
        # Header
        canvas.setFont("Helvetica-Bold", 10)
        canvas.setFillColor(colors.gray)
        canvas.drawString(inch, A4[1] - 0.5 * inch, "Smart City Planning System")
        canvas.drawRightString(A4[0] - inch, A4[1] - 0.5 * inch, datetime.now().strftime("%Y-%m-%d"))
        
        # Footer
        canvas.setFont("Helvetica", 9)
        canvas.drawString(inch, 0.5 * inch, f"Generated Report")
        canvas.drawRightString(A4[0] - inch, 0.5 * inch, f"Page {doc.page}")
        
        canvas.restoreState()

    def _create_cover_page(self, story, project):
        """Create professional cover page."""
        story.append(Spacer(1, 2 * inch))
        story.append(Paragraph("PROJECT VALIDATION REPORT", self.styles['ReportTitle']))
        story.append(Spacer(1, 0.5 * inch))
        
        story.append(Paragraph(project.name, self.styles['Heading1']))
        story.append(Spacer(1, 0.2 * inch))
        story.append(Paragraph(f"Project ID: #{project.id}", self.styles['Normal']))
        story.append(Paragraph(f"Location: {project.location_city or 'Not specified'}, {project.location_district or ''}", self.styles['Normal']))
        
        story.append(Spacer(1, 2 * inch))
        
        # Status Badge logic
        status_color = colors.blue
        if project.status == "APPROVED": status_color = colors.green
        elif project.status == "REJECTED": status_color = colors.red
        
        status_style = ParagraphStyle(
            'Status', parent=self.styles['Normal'], 
            fontSize=16, alignment=TA_CENTER, 
            textColor=status_color
        )
        story.append(Paragraph(f"STATUS: {project.status}", status_style))
        
        story.append(PageBreak())

    def _create_executive_summary(self, story, project, analyses):
        """Create executive summary section."""
        story.append(Paragraph("Executive Summary", self.styles['SectionHeader']))
        
        # Project Overview
        story.append(Paragraph("Project Overview", self.styles['SubHeader']))
        desc = project.description or "No description provided."
        story.append(Paragraph(desc, self.styles['NormalJustified']))
        
        # Key Metrics Table
        data = [
            ['Metric', 'Value'],
            ['Calculated Floor Area', f"{project.site_area_m2 or 'N/A'} m²"],
            ['Building Type', project.project_type or 'N/A'],
            ['UDA Zone', project.uda_zone or 'N/A']
        ]
        
        t = Table(data, colWidths=[2.5*inch, 3.5*inch])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e8eaf6')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#1a237e')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#fafafa')),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#eeeeee'))
        ]))
        story.append(t)
        story.append(Spacer(1, 0.2 * inch))

    def _create_compliance_section(self, story, analyses):
        """Create compliance overview section."""
        story.append(Paragraph("Compliance Analysis", self.styles['SectionHeader']))
        
        data = [['Analysis Domain', 'Status', 'Score/Rating']]
        
        # Structural
        struct = analyses.get(AnalysisType.STRUCTURAL)
        if struct:
            status = "PASS" if struct.get('is_structurally_safe') else "FAIL"
            score = f"SF: {struct.get('safety_factor', 0)}"
            data.append(['Structural Integrity', status, score])
        else:
            data.append(['Structural Integrity', 'PENDING', '-'])
            
        # Energy
        energy = analyses.get(AnalysisType.ENERGY)
        if energy:
            status = "PASS" if energy.get('is_sustainable') else "WARNING"
            score = f"Rating: {energy.get('rating', 'N/A')}"
            data.append(['Energy Efficiency', status, score])
        else:
            data.append(['Energy Efficiency', 'PENDING', '-'])
            
        # Green Space
        green = analyses.get(AnalysisType.GREEN_SPACE)
        if green:
            status = "PASS" if green.get('is_compliant') else "FAIL"
            score = f"{green.get('green_space_percentage', 0)}% Coverage"
            data.append(['Green Space', status, score])
        else:
            data.append(['Green Space', 'PENDING', '-'])
            
        # Table Styling
        t = Table(data, colWidths=[3*inch, 1.5*inch, 2*inch])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3f51b5')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        # Dynamic row coloring based on status
        for i, row in enumerate(data[1:], start=1):
            status = row[1]
            if status == "PASS":
                t.setStyle(TableStyle([('TEXTCOLOR', (1, i), (1, i), colors.green)]))
            elif status == "FAIL":
                 t.setStyle(TableStyle([('TEXTCOLOR', (1, i), (1, i), colors.red)]))
            elif status == "WARNING":
                 t.setStyle(TableStyle([('TEXTCOLOR', (1, i), (1, i), colors.orange)]))
                 
        story.append(t)
        story.append(Spacer(1, 0.3 * inch))

    def _create_structural_section(self, story, data):
        """Create detailed structural analysis section."""
        story.append(Paragraph("Structural Integrity Details", self.styles['SectionHeader']))
        
        # Validation Info
        story.append(Paragraph(f"Validation Status: {data.get('validation_status', 'Unknown')}", self.styles['Normal']))
        story.append(Paragraph(f"Safety Factor: {data.get('safety_factor', 0)} (Min Required: 2.0)", self.styles['Normal']))
        
        # Load Table
        story.append(Paragraph("Load Calculations", self.styles['SubHeader']))
        loads = data.get('loads', {})
        load_data = [
            ['Load Type', 'Value (kN)'],
            ['Dead Load', f"{loads.get('dead_load_kn', 0):.2f}"],
            ['Live Load', f"{loads.get('live_load_kn', 0):.2f}"],
            ['Wind Load', f"{loads.get('wind_load_kn', 0):.2f}"],
            ['Seismic Load', f"{loads.get('seismic_load_kn', 0):.2f}"],
            ['Total Design Load', f"{loads.get('total_design_load_kn', 0):.2f}"]
        ]
        
        t = Table(load_data, colWidths=[3*inch, 3*inch])
        t.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ]))
        story.append(t)
        
        # Foundations
        story.append(Paragraph("Foundation Requirements", self.styles['SubHeader']))
        found = data.get('foundation', {})
        story.append(Paragraph(f"• Type: {found.get('type', 'N/A')}", self.styles['Normal']))
        story.append(Paragraph(f"• Required Depth: {found.get('required_depth_m', 0)} m", self.styles['Normal']))

    def _create_energy_section(self, story, data):
        """Create detailed energy analysis section."""
        story.append(Paragraph("Energy Efficiency Analysis", self.styles['SectionHeader']))
        
        story.append(Paragraph(f"Energy Rating: {data.get('rating', 'N/A')}", self.styles['Heading2']))
        story.append(Paragraph(f"Total Annual Consumption: {data.get('total_energy_kwh_year', 0):.2f} kWh/year", self.styles['Normal']))
        story.append(Paragraph(f"CO2 Emissions: {data.get('co2_emissions_kg_year', 0):.2f} kg/year", self.styles['Normal']))
        
        # Energy Breakdown Pie Chart
        story.append(Paragraph("Consumption Breakdown", self.styles['SubHeader']))
        breakdown = data.get('breakdown', {})
        
        d = Drawing(400, 200)
        pc = Pie()
        pc.x = 100
        pc.y = 50
        pc.width = 100
        pc.height = 100
        pc.data = [
            breakdown.get('heating_cooling', 0),
            breakdown.get('lighting', 0),
            breakdown.get('appliances', 0)
        ]
        pc.labels = ['HVAC', 'Lighting', 'Appliances']
        pc.simpleLabels = 0
        pc.slices.strokeWidth = 0.5
        d.add(pc)
        story.append(d)

    def _create_green_space_section(self, story, data):
        """Create detailed green space analysis section."""
        story.append(Paragraph("Green Space & Environment", self.styles['SectionHeader']))
        
        story.append(Paragraph(f"Green Space Coverage: {data.get('green_space_percentage', 0)}%", self.styles['Heading3']))
        story.append(Paragraph(f"Compliance: {data.get('compliance_status', 'N/A')}", self.styles['Normal']))
        
        # Environmental Benefits
        story.append(Paragraph("Environmental Benefits", self.styles['SubHeader']))
        benefits = data.get('environmental_benefits', {})
        story.append(Paragraph(f"• Temp Reduction: {benefits.get('temperature_reduction_celsius', 0):.1f}°C", self.styles['Normal']))
        story.append(Paragraph(f"• CO2 Absorption: {benefits.get('annual_co2_absorption_kg', 0):.0f} kg/year", self.styles['Normal']))
        story.append(Paragraph(f"• Air Quality Score: {benefits.get('air_quality_score', 0):.0f}/100", self.styles['Normal']))

    def _create_recommendations_section(self, story, analyses):
        """Create consolidated recommendations section."""
        story.append(Paragraph("Consolidated Recommendations", self.styles['SectionHeader']))
        
        all_recs = []
        
        if analyses.get(AnalysisType.STRUCTURAL):
            all_recs.extend(analyses[AnalysisType.STRUCTURAL].get('recommendations', []))
            
        if analyses.get(AnalysisType.ENERGY):
            all_recs.extend(analyses[AnalysisType.ENERGY].get('recommendations', []))
            
        if analyses.get(AnalysisType.GREEN_SPACE):
            all_recs.extend(analyses[AnalysisType.GREEN_SPACE].get('recommendations', []))
            
        if not all_recs:
            story.append(Paragraph("No specific recommendations generated.", self.styles['Normal']))
        else:
            for rec in all_recs:
                story.append(Paragraph(f"• {rec}", self.styles['NormalJustified']))


# Export singleton instance
comprehensive_report_service = ComprehensiveReportService()
