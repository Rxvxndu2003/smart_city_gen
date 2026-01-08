"""
Exports router - Generate PDF reports and export project data.
"""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.models.project import Project
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from pathlib import Path
from datetime import datetime
import json
import logging
from app.services.comprehensive_report_service import comprehensive_report_service

logger = logging.getLogger(__name__)

router = APIRouter()

# Create exports directory
EXPORTS_DIR = Path("storage/exports")
EXPORTS_DIR.mkdir(parents=True, exist_ok=True)

@router.post("/pdf/{project_id}")
async def generate_pdf_report(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate a PDF report for a project."""
    # Get project
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Generate PDF
    pdf_path = EXPORTS_DIR / f"project_{project_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    
    try:
        doc = SimpleDocTemplate(
            str(pdf_path),
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18
        )
        
        # Container for elements
        elements = []
        styles = getSampleStyleSheet()
        
        # Title style
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1e40af'),
            spaceAfter=30,
            alignment=TA_CENTER
        )
        
        # Add title
        title = Paragraph(f"Project Report: {project.name}", title_style)
        elements.append(title)
        elements.append(Spacer(1, 0.2*inch))
        
        # Add project details
        details_data = [
            ['Project Information', ''],
            ['Name:', project.name or 'N/A'],
            ['Type:', project.project_type or 'N/A'],
            ['District:', project.location_district or 'N/A'],
            ['Status:', project.status.value if project.status else 'N/A'],
            ['Created:', project.created_at.strftime('%Y-%m-%d') if project.created_at else 'N/A'],
            ['', ''],
            ['Site Details', ''],
            ['Site Area:', f"{project.site_area_m2} m²" if project.site_area_m2 else 'N/A'],
            ['Building Coverage:', f"{project.building_coverage}%" if project.building_coverage else 'N/A'],
            ['Open Space:', f"{project.open_space_percentage}%" if project.open_space_percentage else 'N/A'],
            ['', ''],
            ['Building Parameters', ''],
            ['Number of Floors:', str(project.num_floors) if project.num_floors else 'N/A'],
            ['Building Height:', f"{project.building_height} m" if project.building_height else 'N/A'],
            ['Floor Area Ratio:', str(project.floor_area_ratio) if project.floor_area_ratio else 'N/A'],
            ['Parking Spaces:', str(project.parking_spaces) if project.parking_spaces else 'N/A']
        ]
        
        table = Table(details_data, colWidths=[2.5*inch, 3.5*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (1, 0), colors.HexColor('#3b82f6')),
            ('TEXTCOLOR', (0, 0), (1, 0), colors.whitesmoke),
            ('BACKGROUND', (0, 7), (1, 7), colors.HexColor('#3b82f6')),
            ('TEXTCOLOR', (0, 7), (1, 7), colors.whitesmoke),
            ('BACKGROUND', (0, 12), (1, 12), colors.HexColor('#3b82f6')),
            ('TEXTCOLOR', (0, 12), (1, 12), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey)
        ]))
        
        elements.append(table)
        elements.append(Spacer(1, 0.5*inch))
        
        # Add description if available
        if project.description:
            elements.append(Paragraph("Project Description", styles['Heading2']))
            elements.append(Spacer(1, 0.1*inch))
            elements.append(Paragraph(project.description, styles['Normal']))
            elements.append(Spacer(1, 0.3*inch))
        
        # Add footer
        footer_text = f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Smart City Planning System"
        footer = Paragraph(footer_text, ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=8,
            textColor=colors.grey,
            alignment=TA_CENTER
        ))
        elements.append(Spacer(1, 0.5*inch))
        elements.append(footer)
        
        # Build PDF
        doc.build(elements)
        
        return {
            "success": True,
            "message": "PDF report generated successfully",
            "file_path": str(pdf_path),
            "filename": pdf_path.name,
            "download_url": f"/api/v1/exports/download/{pdf_path.name}"
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {str(e)}")

@router.post("/comprehensive-report/{project_id}")
async def generate_comprehensive_report(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate a comprehensive professional PDF report for a project.
    Includes all analysis results (Structural, Energy, Green Space).
    """
    # Verify project exists
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    try:
        # Generate PDF using service
        pdf_buffer = comprehensive_report_service.generate_report(db, project_id)
        
        # Save to exports directory
        filename = f"comprehensive_report_{project_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        file_path = EXPORTS_DIR / filename
        
        with open(file_path, "wb") as f:
            f.write(pdf_buffer.getvalue())
            
        return {
            "success": True,
            "message": "Comprehensive report generated successfully",
            "file_path": str(file_path),
            "filename": filename,
            "download_url": f"/api/v1/exports/download/{filename}"
        }
        
    except Exception as e:
        logger.error(f"Comprehensive report generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Report generation failed: {str(e)}")

@router.get("/download/{filename}")
async def download_export(
    filename: str,
    current_user: User = Depends(get_current_user)
):
    """Download an exported file."""
    file_path = EXPORTS_DIR / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(
        path=file_path,
        filename=filename,
        media_type="application/pdf"
    )

@router.get("/json/{project_id}")
async def export_project_json(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Export project data as JSON."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Convert project to dict
    project_data = {
        "id": project.id,
        "name": project.name,
        "description": project.description,
        "project_type": project.project_type,
        "location_district": project.location_district,
        "location_city": project.location_city,
        "location_address": project.location_address,
        "status": project.status.value if project.status else None,
        "site_area_m2": float(project.site_area_m2) if project.site_area_m2 else None,
        "uda_zone": project.uda_zone,
        "building_coverage": float(project.building_coverage) if project.building_coverage else None,
        "floor_area_ratio": float(project.floor_area_ratio) if project.floor_area_ratio else None,
        "num_floors": project.num_floors,
        "building_height": float(project.building_height) if project.building_height else None,
        "open_space_percentage": float(project.open_space_percentage) if project.open_space_percentage else None,
        "parking_spaces": project.parking_spaces,
        "owner_name": project.owner_name,
        "model_url": project.model_url,
        "predicted_compliance": project.predicted_compliance,
        "compliance_confidence": float(project.compliance_confidence) if project.compliance_confidence else None,
        "compliance_score": float(project.compliance_score) if project.compliance_score else None,
        "prediction_message": project.prediction_message,
        "predicted_at": project.predicted_at.isoformat() if project.predicted_at else None,
        "created_at": project.created_at.isoformat() if project.created_at else None,
        "updated_at": project.updated_at.isoformat() if project.updated_at else None
    }
    
    return project_data

@router.get("/list")
async def list_exports(
    current_user: User = Depends(get_current_user)
):
    """List all exported files."""
    exports = []
    
    for file_path in EXPORTS_DIR.iterdir():
        if file_path.is_file():
            exports.append({
                "filename": file_path.name,
                "size": file_path.stat().st_size,
                "created": file_path.stat().st_mtime
            })
    
    return {"exports": exports}
