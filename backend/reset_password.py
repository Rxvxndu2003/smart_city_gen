"""
Script to reset a user's password.
Usage: python reset_password.py <email> <new_password>
"""
import sys
from sqlalchemy.orm import Session
from app.database import get_db_session
from app.models.user import User
from app.utils.password import hash_password

def reset_password(email: str, new_password: str):
    """Reset password for a user."""
    db = next(get_db_session())
    
    try:
        user = db.query(User).filter(User.email == email).first()
        
        if not user:
            print(f"❌ User with email '{email}' not found.")
            return False
        
        # Hash the new password
        hashed = hash_password(new_password)
        user.password_hash = hashed
        
        db.commit()
        print(f"✅ Password for '{email}' has been reset successfully!")
        print(f"   New password: {new_password}")
        return True
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error resetting password: {str(e)}")
        return False
    finally:
        db.close()

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python reset_password.py <email> <new_password>")
        print("\nExample:")
        print("  python reset_password.py admin@smartcity.lk newpassword123")
        sys.exit(1)
    
    email = sys.argv[1]
    new_password = sys.argv[2]
    
    reset_password(email, new_password)
