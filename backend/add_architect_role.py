from app.database import SessionLocal
from app.models.role import UserRole

db = SessionLocal()
try:
    # User ID 3 (ravidu@gmail.com)
    # Role ID 4 is Architect
    
    # Check if already has the role
    existing = db.query(UserRole).filter(
        UserRole.user_id == 3,
        UserRole.role_id == 4  # Architect
    ).first()
    
    if existing:
        print("User already has Architect role")
    else:
        new_role = UserRole(user_id=3, role_id=4, assigned_by=1)
        db.add(new_role)
        db.commit()
        print("✓ Added Architect role to ravidu@gmail.com (ID: 3)")
        print("Now you can see projects in the approval page!")
except Exception as e:
    db.rollback()
    print(f"Error: {e}")
finally:
    db.close()
