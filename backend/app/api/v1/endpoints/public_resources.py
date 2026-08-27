from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.models import Resource, Room
from app.schemas.schemas import ResourceOut

router = APIRouter()

@router.get("/public", response_model=List[ResourceOut])
def get_public_resources(
    search: Optional[str] = Query(None),
    resource_type: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    query = db.query(Resource).join(Room).filter(
        Resource.visibility == "PUBLIC",
        Resource.is_active == True,
        Room.is_active == True
    )

    if search:
        query = query.filter(Resource.title.ilike(f"%{search}%") | Resource.description.ilike(f"%{search}%"))
    if resource_type and resource_type.upper() != "ALL":
        query = query.filter(Resource.resource_type == resource_type.upper())

    resources = query.order_by(Resource.created_at.desc()).all()

    result = []
    for r in resources:
        f_name = r.folder.name if r.folder else None
        teacher_name = r.room.owner.user.full_name if r.room and r.room.owner and r.room.owner.user else None
        result.append(ResourceOut(
            id=r.id,
            room_id=r.room_id,
            folder_id=r.folder_id,
            title=r.title,
            description=r.description,
            resource_type=r.resource_type,
            file_url=r.file_url,
            mime_type=r.mime_type,
            file_size=r.file_size,
            visibility=r.visibility,
            is_active=r.is_active,
            created_at=r.created_at,
            updated_at=r.updated_at,
            folder_name=f_name,
            room_name=r.room.name if r.room else None,
            room_code=r.room.code if r.room else None,
            teacher_name=teacher_name
        ))
    return result
