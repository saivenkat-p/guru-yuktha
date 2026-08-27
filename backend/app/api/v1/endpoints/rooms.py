import random
import string
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import require_authenticated_user, require_teacher, require_learner
from app.models.models import User, Teacher, Learner, Room, RoomMembership, Folder, Resource
from app.schemas.schemas import (
    RoomCreate, RoomUpdate, RoomOut, RoomMembershipOut, RoomMembershipCreate,
    FolderCreate, FolderUpdate, FolderOut, ResourceCreate, ResourceUpdate, ResourceOut
)

VALID_RESOURCE_TYPES = {"PDF", "PPT", "DOC", "VIDEO", "LINK", "IMAGE", "OTHER"}
VALID_VISIBILITIES = {"PUBLIC", "ROOM_ONLY"}

router = APIRouter()

def generate_room_code(name: str, db: Session) -> str:
    words = [w for w in name.replace("-", " ").replace("_", " ").split() if w]
    prefix = words[0][:3].upper() if words else "RM"
    year = datetime.utcnow().year
    
    for _ in range(20):
        suffix = "".join(random.choices(string.ascii_uppercase + string.digits, k=4))
        code = f"{prefix}-{year}-{suffix}"
        exists = db.query(Room).filter(Room.code == code).first()
        if not exists:
            return code
    suffix = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f"ROOM-{year}-{suffix}"

# ================= ROOM ENDPOINTS =================

@router.post("", response_model=RoomOut, status_code=status.HTTP_201_CREATED)
def create_room(
    room_in: RoomCreate,
    current_user: User = Depends(require_teacher),
    db: Session = Depends(get_db)
):
    teacher = db.query(Teacher).filter(Teacher.user_id == current_user.id).first()
    if not teacher:
        teacher = Teacher(
            user_id=current_user.id,
            employee_code=f"EMP-{current_user.id:04d}",
            department="Academic",
            designation="Faculty",
            college_name="Institution"
        )
        db.add(teacher)
        db.commit()
        db.refresh(teacher)

    code = generate_room_code(room_in.name, db)
    room = Room(
        teacher_id=teacher.id,
        name=room_in.name.strip(),
        description=room_in.description.strip() if room_in.description else None,
        code=code,
        visibility=(room_in.visibility or "PRIVATE").upper(),
        is_active=True
    )
    db.add(room)
    db.commit()
    db.refresh(room)

    return RoomOut(
        id=room.id,
        teacher_id=room.teacher_id,
        name=room.name,
        description=room.description,
        code=room.code,
        visibility=room.visibility,
        is_active=room.is_active,
        active_members_count=0,
        created_at=room.created_at,
        updated_at=room.updated_at
    )

@router.get("", response_model=List[RoomOut])
def get_teacher_rooms(
    current_user: User = Depends(require_teacher),
    db: Session = Depends(get_db)
):
    teacher = db.query(Teacher).filter(Teacher.user_id == current_user.id).first()
    if not teacher:
        return []

    rooms = db.query(Room).filter(
        Room.teacher_id == teacher.id,
        Room.is_active == True
    ).order_by(Room.created_at.desc()).all()

    result = []
    for r in rooms:
        count = db.query(RoomMembership).filter(
            RoomMembership.room_id == r.id,
            RoomMembership.status == "ACTIVE"
        ).count()
        result.append(RoomOut(
            id=r.id,
            teacher_id=r.teacher_id,
            name=r.name,
            description=r.description,
            code=r.code,
            visibility=r.visibility,
            is_active=r.is_active,
            active_members_count=count,
            created_at=r.created_at,
            updated_at=r.updated_at
        ))
    return result

@router.get("/my/memberships", response_model=List[RoomMembershipOut])
def get_learner_memberships(
    current_user: User = Depends(require_learner),
    db: Session = Depends(get_db)
):
    memberships = db.query(RoomMembership).filter(
        RoomMembership.user_id == current_user.id,
        RoomMembership.status == "ACTIVE"
    ).all()
    
    result = []
    for m in memberships:
        room_out = None
        if m.room:
            count = db.query(RoomMembership).filter(
                RoomMembership.room_id == m.room.id,
                RoomMembership.status == "ACTIVE"
            ).count()
            room_out = RoomOut(
                id=m.room.id,
                teacher_id=m.room.teacher_id,
                name=m.room.name,
                description=m.room.description,
                code=m.room.code,
                visibility=m.room.visibility,
                is_active=m.room.is_active,
                active_members_count=count,
                created_at=m.room.created_at,
                updated_at=m.room.updated_at
            )
        result.append(RoomMembershipOut(
            id=m.id,
            room_id=m.room_id,
            user_id=m.user_id,
            learner_id=m.learner_id,
            role=m.role,
            status=m.status,
            joined_at=m.joined_at,
            created_at=m.created_at,
            room=room_out
        ))
    return result

@router.get("/{room_id}", response_model=RoomOut)
def get_room_details(
    room_id: int,
    current_user: User = Depends(require_authenticated_user),
    db: Session = Depends(get_db)
):
    room = db.query(Room).filter(Room.id == room_id).first()
    if not room or not room.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Room not found or no longer active"
        )

    teacher = db.query(Teacher).filter(Teacher.user_id == current_user.id).first()
    is_owner = teacher and room.teacher_id == teacher.id

    is_member = False
    if not is_owner:
        membership = db.query(RoomMembership).filter(
            RoomMembership.room_id == room.id,
            RoomMembership.user_id == current_user.id,
            RoomMembership.status == "ACTIVE"
        ).first()
        is_member = membership is not None

    if not is_owner and not is_member and room.visibility != "PUBLIC":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: You do not have permission to view this room."
        )

    count = db.query(RoomMembership).filter(
        RoomMembership.room_id == room.id,
        RoomMembership.status == "ACTIVE"
    ).count()

    return RoomOut(
        id=room.id,
        teacher_id=room.teacher_id,
        name=room.name,
        description=room.description,
        code=room.code,
        visibility=room.visibility,
        is_active=room.is_active,
        active_members_count=count,
        created_at=room.created_at,
        updated_at=room.updated_at
    )

@router.put("/{room_id}", response_model=RoomOut)
def update_room(
    room_id: int,
    room_in: RoomUpdate,
    current_user: User = Depends(require_teacher),
    db: Session = Depends(get_db)
):
    teacher = db.query(Teacher).filter(Teacher.user_id == current_user.id).first()
    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Room not found")

    if not teacher or room.teacher_id != teacher.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: You do not own this room."
        )

    if room_in.name is not None:
        room.name = room_in.name.strip()
    if room_in.description is not None:
        room.description = room_in.description.strip()
    if room_in.visibility is not None:
        room.visibility = room_in.visibility.upper()
    if room_in.is_active is not None:
        room.is_active = room_in.is_active

    db.commit()
    db.refresh(room)

    count = db.query(RoomMembership).filter(
        RoomMembership.room_id == room.id,
        RoomMembership.status == "ACTIVE"
    ).count()

    return RoomOut(
        id=room.id,
        teacher_id=room.teacher_id,
        name=room.name,
        description=room.description,
        code=room.code,
        visibility=room.visibility,
        is_active=room.is_active,
        active_members_count=count,
        created_at=room.created_at,
        updated_at=room.updated_at
    )

@router.delete("/{room_id}")
def archive_room(
    room_id: int,
    current_user: User = Depends(require_teacher),
    db: Session = Depends(get_db)
):
    teacher = db.query(Teacher).filter(Teacher.user_id == current_user.id).first()
    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Room not found")

    if not teacher or room.teacher_id != teacher.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: You do not own this room."
        )

    room.is_active = False
    db.commit()

    return {"message": "Room archived successfully", "id": room.id}

@router.get("/{room_id}/members", response_model=List[RoomMembershipOut])
def get_room_members(
    room_id: int,
    current_user: User = Depends(require_teacher),
    db: Session = Depends(get_db)
):
    teacher = db.query(Teacher).filter(Teacher.user_id == current_user.id).first()
    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Room not found")

    if not teacher or room.teacher_id != teacher.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: You can only inspect members of your own room."
        )

    memberships = db.query(RoomMembership).filter(RoomMembership.room_id == room.id).all()
    return memberships

# ================= FOLDERS ENDPOINTS (Phase 3) =================

@router.post("/{room_id}/folders", response_model=FolderOut, status_code=status.HTTP_201_CREATED)
def create_folder(
    room_id: int,
    folder_in: FolderCreate,
    current_user: User = Depends(require_teacher),
    db: Session = Depends(get_db)
):
    teacher = db.query(Teacher).filter(Teacher.user_id == current_user.id).first()
    room = db.query(Room).filter(Room.id == room_id, Room.is_active == True).first()
    if not room:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Room not found")

    if not teacher or room.teacher_id != teacher.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access forbidden: You do not own this room.")

    folder = Folder(
        room_id=room.id,
        name=folder_in.name.strip(),
        description=folder_in.description.strip() if folder_in.description else None,
        created_by=current_user.id,
        is_active=True
    )
    db.add(folder)
    db.commit()
    db.refresh(folder)

    return FolderOut(
        id=folder.id,
        room_id=folder.room_id,
        name=folder.name,
        description=folder.description,
        is_active=folder.is_active,
        resources_count=0,
        created_at=folder.created_at,
        updated_at=folder.updated_at
    )

@router.get("/{room_id}/folders", response_model=List[FolderOut])
def get_room_folders(
    room_id: int,
    current_user: User = Depends(require_authenticated_user),
    db: Session = Depends(get_db)
):
    room = db.query(Room).filter(Room.id == room_id, Room.is_active == True).first()
    if not room:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Room not found")

    teacher = db.query(Teacher).filter(Teacher.user_id == current_user.id).first()
    is_owner = teacher and room.teacher_id == teacher.id

    is_member = False
    if not is_owner:
        membership = db.query(RoomMembership).filter(
            RoomMembership.room_id == room.id,
            RoomMembership.user_id == current_user.id,
            RoomMembership.status == "ACTIVE"
        ).first()
        is_member = membership is not None

    if not is_owner and not is_member and room.visibility != "PUBLIC":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access forbidden: You cannot view folders in this private room.")

    folders = db.query(Folder).filter(Folder.room_id == room.id, Folder.is_active == True).order_by(Folder.name.asc()).all()
    result = []
    for f in folders:
        r_count = db.query(Resource).filter(Resource.folder_id == f.id, Resource.is_active == True).count()
        result.append(FolderOut(
            id=f.id,
            room_id=f.room_id,
            name=f.name,
            description=f.description,
            is_active=f.is_active,
            resources_count=r_count,
            created_at=f.created_at,
            updated_at=f.updated_at
        ))
    return result

@router.put("/{room_id}/folders/{folder_id}", response_model=FolderOut)
def update_folder(
    room_id: int,
    folder_id: int,
    folder_in: FolderUpdate,
    current_user: User = Depends(require_teacher),
    db: Session = Depends(get_db)
):
    teacher = db.query(Teacher).filter(Teacher.user_id == current_user.id).first()
    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Room not found")

    if not teacher or room.teacher_id != teacher.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access forbidden: You do not own this room.")

    folder = db.query(Folder).filter(Folder.id == folder_id, Folder.room_id == room.id).first()
    if not folder:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Folder not found")

    if folder_in.name is not None:
        folder.name = folder_in.name.strip()
    if folder_in.description is not None:
        folder.description = folder_in.description.strip()
    if folder_in.is_active is not None:
        folder.is_active = folder_in.is_active

    db.commit()
    db.refresh(folder)

    r_count = db.query(Resource).filter(Resource.folder_id == folder.id, Resource.is_active == True).count()
    return FolderOut(
        id=folder.id,
        room_id=folder.room_id,
        name=folder.name,
        description=folder.description,
        is_active=folder.is_active,
        resources_count=r_count,
        created_at=folder.created_at,
        updated_at=folder.updated_at
    )

@router.delete("/{room_id}/folders/{folder_id}")
def archive_folder(
    room_id: int,
    folder_id: int,
    current_user: User = Depends(require_teacher),
    db: Session = Depends(get_db)
):
    teacher = db.query(Teacher).filter(Teacher.user_id == current_user.id).first()
    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Room not found")

    if not teacher or room.teacher_id != teacher.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access forbidden: You do not own this room.")

    folder = db.query(Folder).filter(Folder.id == folder_id, Folder.room_id == room.id).first()
    if not folder:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Folder not found")

    folder.is_active = False
    db.commit()
    return {"message": "Folder archived successfully", "id": folder.id}

# ================= RESOURCES ENDPOINTS (Phase 3) =================

@router.post("/{room_id}/resources", response_model=ResourceOut, status_code=status.HTTP_201_CREATED)
def create_resource(
    room_id: int,
    res_in: ResourceCreate,
    current_user: User = Depends(require_teacher),
    db: Session = Depends(get_db)
):
    teacher = db.query(Teacher).filter(Teacher.user_id == current_user.id).first()
    room = db.query(Room).filter(Room.id == room_id, Room.is_active == True).first()
    if not room:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Room not found")

    if not teacher or room.teacher_id != teacher.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access forbidden: You do not own this room.")

    res_type = (res_in.resource_type or "PDF").upper()
    if res_type not in VALID_RESOURCE_TYPES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid resource type: {res_type}")

    visibility = (res_in.visibility or "ROOM_ONLY").upper()
    if visibility not in VALID_VISIBILITIES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid visibility: {visibility}")

    # Validate folder relationship
    folder_name = None
    if res_in.folder_id:
        folder = db.query(Folder).filter(Folder.id == res_in.folder_id, Folder.room_id == room.id, Folder.is_active == True).first()
        if not folder:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid folder_id: Folder does not exist in this room.")
        folder_name = folder.name

    resource = Resource(
        room_id=room.id,
        folder_id=res_in.folder_id,
        title=res_in.title.strip(),
        description=res_in.description.strip() if res_in.description else None,
        resource_type=res_type,
        file_url=res_in.file_url,
        mime_type=res_in.mime_type,
        file_size=res_in.file_size,
        visibility=visibility,
        uploaded_by=current_user.id,
        is_active=True
    )
    db.add(resource)
    db.commit()
    db.refresh(resource)

    return ResourceOut(
        id=resource.id,
        room_id=resource.room_id,
        folder_id=resource.folder_id,
        title=resource.title,
        description=resource.description,
        resource_type=resource.resource_type,
        file_url=resource.file_url,
        mime_type=resource.mime_type,
        file_size=resource.file_size,
        visibility=resource.visibility,
        is_active=resource.is_active,
        created_at=resource.created_at,
        updated_at=resource.updated_at,
        folder_name=folder_name,
        room_name=room.name,
        room_code=room.code,
        teacher_name=current_user.full_name
    )

@router.get("/{room_id}/resources", response_model=List[ResourceOut])
def get_room_resources(
    room_id: int,
    folder_id: Optional[int] = None,
    current_user: User = Depends(require_authenticated_user),
    db: Session = Depends(get_db)
):
    room = db.query(Room).filter(Room.id == room_id, Room.is_active == True).first()
    if not room:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Room not found")

    teacher = db.query(Teacher).filter(Teacher.user_id == current_user.id).first()
    is_owner = teacher and room.teacher_id == teacher.id

    is_member = False
    if not is_owner:
        membership = db.query(RoomMembership).filter(
            RoomMembership.room_id == room.id,
            RoomMembership.user_id == current_user.id,
            RoomMembership.status == "ACTIVE"
        ).first()
        is_member = membership is not None

    if not is_owner and not is_member and room.visibility != "PUBLIC":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access forbidden: You cannot access resources in this private room.")

    query = db.query(Resource).filter(Resource.room_id == room.id, Resource.is_active == True)
    if folder_id:
        query = query.filter(Resource.folder_id == folder_id)

    # Filter by visibility if user is not owner and not member
    if not is_owner and not is_member:
        query = query.filter(Resource.visibility == "PUBLIC")

    resources = query.order_by(Resource.created_at.desc()).all()
    teacher_name = room.owner.user.full_name if room.owner and room.owner.user else None

    result = []
    for r in resources:
        f_name = r.folder.name if r.folder else None
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
            room_name=room.name,
            room_code=room.code,
            teacher_name=teacher_name
        ))
    return result

@router.get("/{room_id}/resources/{resource_id}", response_model=ResourceOut)
def get_resource_detail(
    room_id: int,
    resource_id: int,
    current_user: User = Depends(require_authenticated_user),
    db: Session = Depends(get_db)
):
    resource = db.query(Resource).filter(
        Resource.id == resource_id,
        Resource.room_id == room_id,
        Resource.is_active == True
    ).first()
    if not resource:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found")

    room = resource.room
    teacher = db.query(Teacher).filter(Teacher.user_id == current_user.id).first()
    is_owner = teacher and room.teacher_id == teacher.id

    is_member = False
    if not is_owner:
        membership = db.query(RoomMembership).filter(
            RoomMembership.room_id == room.id,
            RoomMembership.user_id == current_user.id,
            RoomMembership.status == "ACTIVE"
        ).first()
        is_member = membership is not None

    if resource.visibility == "ROOM_ONLY" and not is_owner and not is_member:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access forbidden: This resource is restricted to room members.")

    teacher_name = room.owner.user.full_name if room.owner and room.owner.user else None
    folder_name = resource.folder.name if resource.folder else None

    return ResourceOut(
        id=resource.id,
        room_id=resource.room_id,
        folder_id=resource.folder_id,
        title=resource.title,
        description=resource.description,
        resource_type=resource.resource_type,
        file_url=resource.file_url,
        mime_type=resource.mime_type,
        file_size=resource.file_size,
        visibility=resource.visibility,
        is_active=resource.is_active,
        created_at=resource.created_at,
        updated_at=resource.updated_at,
        folder_name=folder_name,
        room_name=room.name,
        room_code=room.code,
        teacher_name=teacher_name
    )

@router.put("/{room_id}/resources/{resource_id}", response_model=ResourceOut)
def update_resource(
    room_id: int,
    resource_id: int,
    res_in: ResourceUpdate,
    current_user: User = Depends(require_teacher),
    db: Session = Depends(get_db)
):
    teacher = db.query(Teacher).filter(Teacher.user_id == current_user.id).first()
    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Room not found")

    if not teacher or room.teacher_id != teacher.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access forbidden: You do not own this room.")

    resource = db.query(Resource).filter(Resource.id == resource_id, Resource.room_id == room.id).first()
    if not resource:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found")

    if res_in.title is not None:
        resource.title = res_in.title.strip()
    if res_in.description is not None:
        resource.description = res_in.description.strip()
    if res_in.resource_type is not None:
        res_type = res_in.resource_type.upper()
        if res_type not in VALID_RESOURCE_TYPES:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid resource type: {res_type}")
        resource.resource_type = res_type
    if res_in.visibility is not None:
        vis = res_in.visibility.upper()
        if vis not in VALID_VISIBILITIES:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid visibility: {vis}")
        resource.visibility = vis
    if res_in.file_url is not None:
        resource.file_url = res_in.file_url
    if res_in.folder_id is not None:
        if res_in.folder_id > 0:
            folder = db.query(Folder).filter(Folder.id == res_in.folder_id, Folder.room_id == room.id).first()
            if not folder:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid folder_id: Folder does not exist in this room.")
            resource.folder_id = folder.id
        else:
            resource.folder_id = None
    if res_in.is_active is not None:
        resource.is_active = res_in.is_active

    db.commit()
    db.refresh(resource)

    folder_name = resource.folder.name if resource.folder else None
    teacher_name = room.owner.user.full_name if room.owner and room.owner.user else None

    return ResourceOut(
        id=resource.id,
        room_id=resource.room_id,
        folder_id=resource.folder_id,
        title=resource.title,
        description=resource.description,
        resource_type=resource.resource_type,
        file_url=resource.file_url,
        mime_type=resource.mime_type,
        file_size=resource.file_size,
        visibility=resource.visibility,
        is_active=resource.is_active,
        created_at=resource.created_at,
        updated_at=resource.updated_at,
        folder_name=folder_name,
        room_name=room.name,
        room_code=room.code,
        teacher_name=teacher_name
    )

@router.delete("/{room_id}/resources/{resource_id}")
def archive_resource(
    room_id: int,
    resource_id: int,
    current_user: User = Depends(require_teacher),
    db: Session = Depends(get_db)
):
    teacher = db.query(Teacher).filter(Teacher.user_id == current_user.id).first()
    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Room not found")

    if not teacher or room.teacher_id != teacher.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access forbidden: You do not own this room.")

    resource = db.query(Resource).filter(Resource.id == resource_id, Resource.room_id == room.id).first()
    if not resource:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found")

    resource.is_active = False
    db.commit()
    return {"message": "Resource archived successfully", "id": resource.id}
