from app.database import SessionLocal
from app.models.project import Project, ProjectStatus

db = SessionLocal()
try:
    # Update all DRAFT projects to UNDER_ARCHITECT_REVIEW
    projects = db.query(Project).filter(Project.status == ProjectStatus.DRAFT).all()
    print(f'\nUpdating {len(projects)} DRAFT projects to UNDER_ARCHITECT_REVIEW...\n')
    
    for p in projects:
        old_status = p.status.value
        p.status = ProjectStatus.UNDER_ARCHITECT_REVIEW
        print(f'ID: {p.id} | Name: {p.name[:40]} | {old_status} -> UNDER_ARCHITECT_REVIEW')
    
    db.commit()
    print(f'\nSuccessfully updated {len(projects)} projects!')
    print('These projects will now appear in the approval page.\n')
except Exception as e:
    db.rollback()
    print(f'Error: {e}')
finally:
    db.close()
