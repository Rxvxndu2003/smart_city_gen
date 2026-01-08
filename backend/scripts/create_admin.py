"""
Script to create an admin user for the Smart City system
"""
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy.orm import Session
from app.database import engine, SessionLocal, Base
from app.models.user import User
from app.models.role import Role, UserRole
from app.services.auth_service import AuthService
from datetime import datetime

def create_default_roles(db: Session):
    """Create default system roles"""
    roles_data = [
        {"name": "Admin", "display_name": "Administrator", "description": "Full system administrator access"},
        {"name": "ProjectOwner", "display_name": "Project Owner", "description": "Can create and manage own projects"},
        {"name": "Architect", "display_name": "Architect", "description": "Can design and submit layouts for review"},
        {"name": "Engineer", "display_name": "Engineer", "description": "Can review and approve technical aspects"},
        {"name": "Regulator", "display_name": "Regulator", "description": "Can perform final regulatory approval"},
        {"name": "Contractor", "display_name": "Contractor", "description": "Can view approved designs"},
        {"name": "Investor", "display_name": "Investor", "description": "Can view project financials"},
        {"name": "Viewer", "display_name": "Viewer", "description": "Read-only access to public information"},
    ]
    
    print("\n📋 Creating default roles...")
    created_roles = []
    
    for role_data in roles_data:
        # Check if role exists
        existing_role = db.query(Role).filter(Role.name == role_data["name"]).first()
        if not existing_role:
            role = Role(**role_data)
            db.add(role)
            created_roles.append(role_data["name"])
            print(f"  ✅ Created role: {role_data['name']}")
        else:
            print(f"  ⏭️  Role already exists: {role_data['name']}")
    
    db.commit()
    return created_roles

def create_admin_user(db: Session):
    """Create admin user"""
    print("\n👤 Creating admin user...")
    
    # Check if admin already exists
    existing_admin = db.query(User).filter(User.email == "admin@smartcity.lk").first()
    if existing_admin:
        print("  ⚠️  Admin user already exists!")
        print(f"     Email: admin@smartcity.lk")
        return existing_admin
    
    # Create admin user
    admin_data = {
        "full_name": "System Administrator",
        "email": "admin@smartcity.lk",
        "phone": "+94712345678",
        "is_active": True,
    }
    
    # Hash password
    hashed_password = AuthService.hash_password("admin123")
    
    admin = User(**admin_data, hashed_password=hashed_password)
    db.add(admin)
    db.commit()
    db.refresh(admin)
    
    print(f"  ✅ Created admin user:")
    print(f"     Email: admin@smartcity.lk")
    print(f"     Password: admin123")
    print(f"     ⚠️  CHANGE THIS PASSWORD IMMEDIATELY!")
    
    # Assign Admin role
    admin_role = db.query(Role).filter(Role.name == "Admin").first()
    if admin_role:
        user_role = UserRole(user_id=admin.id, role_id=admin_role.id)
        db.add(user_role)
        db.commit()
        print(f"  ✅ Assigned 'Admin' role")
    
    return admin

def create_test_users(db: Session):
    """Create test users for each role"""
    print("\n👥 Creating test users...")
    
    test_users = [
        {
            "full_name": "John Architect",
            "email": "architect@smartcity.lk",
            "phone": "+94712345679",
            "role": "Architect",
            "password": "arch123"
        },
        {
            "full_name": "Sarah Engineer",
            "email": "engineer@smartcity.lk",
            "phone": "+94712345680",
            "role": "Engineer",
            "password": "eng123"
        },
        {
            "full_name": "Mike Regulator",
            "email": "regulator@smartcity.lk",
            "phone": "+94712345681",
            "role": "Regulator",
            "password": "reg123"
        },
        {
            "full_name": "Jane Owner",
            "email": "owner@smartcity.lk",
            "phone": "+94712345682",
            "role": "ProjectOwner",
            "password": "owner123"
        },
    ]
    
    created_users = []
    
    for user_data in test_users:
        # Check if user exists
        existing_user = db.query(User).filter(User.email == user_data["email"]).first()
        if existing_user:
            print(f"  ⏭️  User already exists: {user_data['email']}")
            continue
        
        # Create user
        role_name = user_data.pop("role")
        password = user_data.pop("password")
        
        hashed_password = AuthService.hash_password(password)
        user = User(**user_data, hashed_password=hashed_password, is_active=True)
        db.add(user)
        db.commit()
        db.refresh(user)
        
        # Assign role
        role = db.query(Role).filter(Role.name == role_name).first()
        if role:
            user_role = UserRole(user_id=user.id, role_id=role.id)
            db.add(user_role)
            db.commit()
        
        print(f"  ✅ Created {role_name}: {user_data['email']} (password: {password})")
        created_users.append(user_data["email"])
    
    return created_users

def main():
    """Main setup function"""
    print("=" * 60)
    print("🚀 Smart City - Initial Setup")
    print("=" * 60)
    
    try:
        # Create tables
        print("\n🗄️  Creating database tables...")
        Base.metadata.create_all(bind=engine)
        print("  ✅ Tables created")
        
        # Create session
        db = SessionLocal()
        
        try:
            # Create roles
            create_default_roles(db)
            
            # Create admin user
            create_admin_user(db)
            
            # Create test users
            response = input("\n❓ Create test users for each role? (y/n): ")
            if response.lower() == 'y':
                create_test_users(db)
            
            print("\n" + "=" * 60)
            print("✅ Setup Complete!")
            print("=" * 60)
            print("\n📝 Login Credentials:")
            print("   Admin: admin@smartcity.lk / admin123")
            print("\n🚀 Start the server:")
            print("   uvicorn app.main:app --reload")
            print("\n🌐 Access the application:")
            print("   Frontend: http://localhost:5173")
            print("   API Docs: http://localhost:8000/api/docs")
            print("\n⚠️  Remember to change the admin password!")
            print("=" * 60)
            
        finally:
            db.close()
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nMake sure:")
        print("1. MySQL is running")
        print("2. Database 'smart_city' exists")
        print("3. Database credentials in .env are correct")
        print("4. Run: alembic upgrade head (if migrations exist)")
        sys.exit(1)

if __name__ == "__main__":
    main()
