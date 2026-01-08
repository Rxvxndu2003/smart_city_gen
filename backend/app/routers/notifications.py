"""
Notifications router - Manage user notifications and alerts.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.models.project import Project
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

router = APIRouter()

# In-memory notifications (replace with database in production)
notifications_store = {}

class Notification(BaseModel):
    id: int
    user_id: int
    title: str
    message: str
    type: str  # 'info', 'success', 'warning', 'error'
    read: bool
    created_at: datetime
    project_id: Optional[int] = None

@router.get("")
async def get_notifications(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user notifications."""
    user_notifications = notifications_store.get(current_user.id, [])
    
    # If no notifications, create some sample ones
    if not user_notifications:
        user_notifications = [
            {
                "id": 1,
                "user_id": current_user.id,
                "title": "Welcome to Smart City!",
                "message": "Your account has been created successfully.",
                "type": "success",
                "read": False,
                "created_at": datetime.now().isoformat(),
                "project_id": None
            }
        ]
        notifications_store[current_user.id] = user_notifications
    
    return {
        "notifications": user_notifications,
        "unread_count": len([n for n in user_notifications if not n.get('read', False)])
    }

@router.post("")
async def create_notification(
    title: str,
    message: str,
    type: str = "info",
    project_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new notification."""
    if current_user.id not in notifications_store:
        notifications_store[current_user.id] = []
    
    notification = {
        "id": len(notifications_store[current_user.id]) + 1,
        "user_id": current_user.id,
        "title": title,
        "message": message,
        "type": type,
        "read": False,
        "created_at": datetime.now().isoformat(),
        "project_id": project_id
    }
    
    notifications_store[current_user.id].append(notification)
    
    return {"success": True, "notification": notification}

@router.put("/{notification_id}/read")
async def mark_as_read(
    notification_id: int,
    current_user: User = Depends(get_current_user)
):
    """Mark a notification as read."""
    user_notifications = notifications_store.get(current_user.id, [])
    
    for notification in user_notifications:
        if notification['id'] == notification_id:
            notification['read'] = True
            return {"success": True, "notification": notification}
    
    raise HTTPException(status_code=404, detail="Notification not found")

@router.put("/read-all")
async def mark_all_as_read(
    current_user: User = Depends(get_current_user)
):
    """Mark all notifications as read."""
    user_notifications = notifications_store.get(current_user.id, [])
    
    for notification in user_notifications:
        notification['read'] = True
    
    return {
        "success": True,
        "message": f"Marked {len(user_notifications)} notifications as read"
    }

@router.delete("/{notification_id}")
async def delete_notification(
    notification_id: int,
    current_user: User = Depends(get_current_user)
):
    """Delete a notification."""
    user_notifications = notifications_store.get(current_user.id, [])
    
    notifications_store[current_user.id] = [
        n for n in user_notifications if n['id'] != notification_id
    ]
    
    return {"success": True, "message": "Notification deleted"}

@router.get("/unread-count")
async def get_unread_count(
    current_user: User = Depends(get_current_user)
):
    """Get count of unread notifications."""
    user_notifications = notifications_store.get(current_user.id, [])
    unread_count = len([n for n in user_notifications if not n.get('read', False)])
    
    return {"unread_count": unread_count}

# Utility function to send notification (can be called from other routers)
def send_notification(
    user_id: int,
    title: str,
    message: str,
    type: str = "info",
    project_id: Optional[int] = None
):
    """Send a notification to a user."""
    if user_id not in notifications_store:
        notifications_store[user_id] = []
    
    notification = {
        "id": len(notifications_store[user_id]) + 1,
        "user_id": user_id,
        "title": title,
        "message": message,
        "type": type,
        "read": False,
        "created_at": datetime.now().isoformat(),
        "project_id": project_id
    }
    
    notifications_store[user_id].append(notification)
    return notification
