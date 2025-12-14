"""
Announcements endpoints for the High School Management System API
"""

from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any, Optional
from datetime import datetime
from bson import ObjectId

from ..database import announcements_collection

router = APIRouter(
    prefix="/announcements",
    tags=["announcements"]
)


@router.get("")
def get_announcements() -> List[Dict[str, Any]]:
    """Get all active announcements (not expired)"""
    now = datetime.utcnow().isoformat()
    
    # Find announcements that are currently active
    announcements = list(announcements_collection.find({
        "$or": [
            {"start_date": {"$exists": False}},
            {"start_date": {"$lte": now}}
        ],
        "expiration_date": {"$gte": now}
    }))
    
    # Convert ObjectId to string for JSON serialization
    for announcement in announcements:
        announcement["_id"] = str(announcement["_id"])
    
    return announcements


@router.get("/all")
def get_all_announcements() -> List[Dict[str, Any]]:
    """Get all announcements (including expired ones) - for management UI"""
    announcements = list(announcements_collection.find({}))
    
    # Convert ObjectId to string for JSON serialization
    for announcement in announcements:
        announcement["_id"] = str(announcement["_id"])
    
    return announcements


@router.post("")
def create_announcement(
    message: str,
    expiration_date: str,
    created_by: str,
    start_date: Optional[str] = None
) -> Dict[str, Any]:
    """Create a new announcement - requires authentication"""
    
    # Validate expiration_date
    try:
        exp_date = datetime.fromisoformat(expiration_date.replace('Z', '+00:00'))
        if exp_date < datetime.utcnow():
            raise HTTPException(
                status_code=400,
                detail="Expiration date must be in the future"
            )
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid expiration date format. Use ISO 8601 format."
        )
    
    # Validate start_date if provided
    if start_date:
        try:
            datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Invalid start date format. Use ISO 8601 format."
            )
    
    announcement = {
        "message": message,
        "expiration_date": expiration_date,
        "created_by": created_by
    }
    
    if start_date:
        announcement["start_date"] = start_date
    
    result = announcements_collection.insert_one(announcement)
    announcement["_id"] = str(result.inserted_id)
    
    return announcement


@router.put("/{announcement_id}")
def update_announcement(
    announcement_id: str,
    message: str,
    expiration_date: str,
    start_date: Optional[str] = None
) -> Dict[str, Any]:
    """Update an existing announcement - requires authentication"""
    
    # Validate ObjectId format
    try:
        obj_id = ObjectId(announcement_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid announcement ID")
    
    # Validate expiration_date
    try:
        datetime.fromisoformat(expiration_date.replace('Z', '+00:00'))
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid expiration date format. Use ISO 8601 format."
        )
    
    # Validate start_date if provided
    if start_date:
        try:
            datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Invalid start date format. Use ISO 8601 format."
            )
    
    update_data = {
        "message": message,
        "expiration_date": expiration_date
    }
    
    if start_date:
        update_data["start_date"] = start_date
    else:
        # Remove start_date if not provided
        announcements_collection.update_one(
            {"_id": obj_id},
            {"$unset": {"start_date": ""}}
        )
    
    result = announcements_collection.update_one(
        {"_id": obj_id},
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Announcement not found")
    
    # Return updated announcement
    updated = announcements_collection.find_one({"_id": obj_id})
    updated["_id"] = str(updated["_id"])
    
    return updated


@router.delete("/{announcement_id}")
def delete_announcement(announcement_id: str) -> Dict[str, str]:
    """Delete an announcement - requires authentication"""
    
    # Validate ObjectId format
    try:
        obj_id = ObjectId(announcement_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid announcement ID")
    
    result = announcements_collection.delete_one({"_id": obj_id})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Announcement not found")
    
    return {"message": "Announcement deleted successfully"}
