#!/usr/bin/env python3
"""
Database viewer script for Smart City Planning System
Usage: python view_db.py
"""
from app.database import SessionLocal
from app.models.user import User
from app.models.role import Role, UserRole
from app.models.project import Project
from sqlalchemy import text

def view_users():
    """Display all users and their roles"""
    print("\n" + "="*80)
    print("USERS")
    print("="*80)
    
    db = SessionLocal()
    try:
        users = db.query(User).all()
        for user in users:
            roles = [ur.role.name for ur in user.user_roles]
            print(f"\nID: {user.id}")
            print(f"  Email: {user.email}")
            print(f"  Name: {user.full_name}")
            print(f"  Phone: {user.phone or 'N/A'}")
            print(f"  Active: {user.is_active}")
            print(f"  Roles: {', '.join(roles) if roles else 'No roles'}")
            print(f"  Created: {user.created_at}")
    finally:
        db.close()

def view_roles():
    """Display all available roles"""
    print("\n" + "="*80)
    print("AVAILABLE ROLES")
    print("="*80)
    
    db = SessionLocal()
    try:
        roles = db.query(Role).all()
        for role in roles:
            print(f"\nID: {role.id}")
            print(f"  Name: {role.name}")
            print(f"  Display Name: {role.display_name}")
            print(f"  Description: {role.description or 'N/A'}")
    finally:
        db.close()

def view_projects():
    """Display all projects"""
    print("\n" + "="*80)
    print("PROJECTS")
    print("="*80)
    
    db = SessionLocal()
    try:
        projects = db.query(Project).all()
        if not projects:
            print("\nNo projects found.")
        else:
            for project in projects:
                owner = db.query(User).filter(User.id == project.owner_id).first()
                print(f"\nID: {project.id}")
                print(f"  Name: {project.name}")
                print(f"  Type: {project.project_type or 'N/A'}")
                print(f"  District: {project.location_district or 'N/A'}")
                print(f"  Status: {project.status}")
                print(f"  Site Area: {project.site_area_m2} m²" if project.site_area_m2 else "  Site Area: N/A")
                print(f"  Owner: {owner.full_name if owner else 'Unknown'}")
                print(f"  Created: {project.created_at}")
    finally:
        db.close()

def view_statistics():
    """Display database statistics"""
    print("\n" + "="*80)
    print("DATABASE STATISTICS")
    print("="*80)
    
    db = SessionLocal()
    try:
        user_count = db.query(User).count()
        project_count = db.query(Project).count()
        role_count = db.query(Role).count()
        
        print(f"\nTotal Users: {user_count}")
        print(f"Total Projects: {project_count}")
        print(f"Total Roles: {role_count}")
        
        # Active users
        active_users = db.query(User).filter(User.is_active == True).count()
        print(f"Active Users: {active_users}")
        
        # Users by role
        print("\nUsers by Role:")
        result = db.execute(text("""
            SELECT r.name, r.display_name, COUNT(ur.user_id) as user_count
            FROM roles r
            LEFT JOIN user_roles ur ON r.id = ur.role_id
            GROUP BY r.id, r.name, r.display_name
            ORDER BY user_count DESC
        """))
        for row in result:
            print(f"  {row[1]}: {row[2]} users")
            
    finally:
        db.close()

def main():
    """Main menu"""
    print("\n" + "="*80)
    print("SMART CITY PLANNING SYSTEM - DATABASE VIEWER")
    print("="*80)
    
    while True:
        print("\nOptions:")
        print("  1. View all users")
        print("  2. View available roles")
        print("  3. View all projects")
        print("  4. View statistics")
        print("  5. View all")
        print("  0. Exit")
        
        choice = input("\nEnter your choice (0-5): ").strip()
        
        if choice == "1":
            view_users()
        elif choice == "2":
            view_roles()
        elif choice == "3":
            view_projects()
        elif choice == "4":
            view_statistics()
        elif choice == "5":
            view_statistics()
            view_roles()
            view_users()
            view_projects()
        elif choice == "0":
            print("\nGoodbye!")
            break
        else:
            print("\nInvalid choice. Please try again.")

if __name__ == "__main__":
    main()
