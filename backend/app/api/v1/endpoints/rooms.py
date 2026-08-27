import random
import string
from datetime import datetime
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import require_authenticated_user, require_teacher, require_learner
from app.models.models import User, Teacher, Learner, Room, RoomMembership
from app.schemas.schemas import RoomCreate, RoomUpdate, RoomOut, RoomMembershipOut, RoomMembershipCreate

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
    # Fallback random
    suffix = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f"ROOM-{year}-{suffix}"

@router.post("", response_model=RoomOut, status_code=status.HTTP_201_CREATED)
def create_room(
    room_in: RoomCreate,
    current_user: User = Depends(require_teacher),
    db: Session = Depends(get_db)
):
    teacher = db.query(Teacher).filter(Teacher.user_id == current_user.id).first()
    if not teacher:
        # Auto-create teacher profile if missing
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

    # Archive / soft deactivate
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
