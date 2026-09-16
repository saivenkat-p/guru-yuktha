import random
import string
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import require_authenticated_user, get_optional_current_user
from app.models.models import User, Teacher, Learner, Room, RoomMembership, Folder, Resource, Follow
from app.schemas.schemas import (
    RoomCreate, RoomUpdate, RoomOut, RoomMembershipOut, RoomMembershipCreate,
    FolderCreate, FolderUpdate, FolderOut, ResourceCreate, ResourceUpdate, ResourceOut,
    RoomPreviewOut, RoomPreviewFolderOut, RoomPreviewResourceOut, JoinRequestOut, JoinRequestAction
)

VALID_RESOURCE_TYPES = {"PDF", "PPT", "DOC", "VIDEO", "LINK", "IMAGE", "OTHER"}
VALID_VISIBILITIES = {"PUBLIC", "ROOM_ONLY"}
VALID_ACCESS_TYPES = {"PUBLIC_FREE", "PRIVATE_FREE", "PRIVATE_PAID"}

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

def is_room_owner(room: Room, user: User) -> bool:
    if room.owner_id == user.id:
        return True
    if room.teacher and room.teacher.user_id == user.id:
        return True
    return False

def get_room_owner_info(room: Room, db: Session):
    owner_user = room.owner_user
    if not owner_user and room.teacher and room.teacher.user:
        owner_user = room.teacher.user
    if owner_user:
        return (
            owner_user.full_name,
            owner_user.guru_id or f"GY-{owner_user.id:04d}",
            owner_user.username or f"user_{owner_user.id}",
            owner_user.avatar_url
        )
    return ("Guru", f"GY-{room.id:04d}", "guru", None)

def format_room_out(room: Room, current_user: Optional[User], db: Session) -> RoomOut:
    count = db.query(RoomMembership).filter(
        RoomMembership.room_id == room.id,
        RoomMembership.status == "ACTIVE",
        RoomMembership.role != "OWNER"
    ).count()

    owner_name, owner_guru_id, owner_username, owner_avatar = get_room_owner_info(room, db)

    user_role = None
    membership_status = None
    if current_user:
        if is_room_owner(room, current_user):
            user_role = "OWNER"
            membership_status = "ACTIVE"
        else:
            membership = db.query(RoomMembership).filter(
                RoomMembership.room_id == room.id,
                RoomMembership.user_id == current_user.id
            ).first()
            if membership:
                user_role = membership.role
                membership_status = membership.status

    return RoomOut(
        id=room.id,
        owner_id=room.owner_id,
        teacher_id=room.teacher_id,
        name=room.name,
        description=room.description,
        code=room.code,
        visibility=room.visibility,
        access_type=room.access_type or ("PUBLIC_FREE" if room.visibility == "PUBLIC" else "PRIVATE_FREE"),
        price=room.price or 0.0,
        currency=room.currency or "INR",
        is_active=room.is_active,
        active_members_count=count,
        created_at=room.created_at,
        updated_at=room.updated_at,
        owner_name=owner_name,
        owner_guru_id=owner_guru_id,
        owner_username=owner_username,
        owner_avatar_url=owner_avatar,
        user_role=user_role,
        membership_status=membership_status
    )

# ================= ROOM CRUD ENDPOINTS =================

@router.post("", response_model=RoomOut, status_code=status.HTTP_201_CREATED)
def create_room(
    room_in: RoomCreate,
    current_user: User = Depends(require_authenticated_user),
    db: Session = Depends(get_db)
):
    code = generate_room_code(room_in.name, db)
    visibility = (room_in.visibility or "PUBLIC").upper()
    access_type = (room_in.access_type or "PUBLIC_FREE").upper()
    if access_type not in VALID_ACCESS_TYPES:
        access_type = "PUBLIC_FREE" if visibility == "PUBLIC" else "PRIVATE_FREE"

    teacher = db.query(Teacher).filter(Teacher.user_id == current_user.id).first()
    teacher_id = teacher.id if teacher else None

    room = Room(
        owner_id=current_user.id,
        teacher_id=teacher_id,
        name=room_in.name.strip(),
        description=room_in.description.strip() if room_in.description else None,
        code=code,
        visibility=visibility,
        access_type=access_type,
        price=max(0.0, float(room_in.price or 0.0)),
        currency=(room_in.currency or "INR").upper(),
        is_active=True
    )
    db.add(room)
    db.commit()
    db.refresh(room)

    # Create RoomMembership for owner
    membership = RoomMembership(
        room_id=room.id,
        user_id=current_user.id,
        role="OWNER",
        status="ACTIVE",
        access_source="OWNER"
    )
    db.add(membership)
    db.commit()

    return format_room_out(room, current_user, db)

@router.get("", response_model=List[RoomOut])
def get_rooms(
    filter: Optional[str] = Query("owned", description="'owned', 'joined', or 'all'"),
    current_user: User = Depends(require_authenticated_user),
    db: Session = Depends(get_db)
):
    if filter == "joined":
        memberships = db.query(RoomMembership).filter(
            RoomMembership.user_id == current_user.id,
            RoomMembership.status == "ACTIVE",
            RoomMembership.role != "OWNER"
        ).all()
        room_ids = [m.room_id for m in memberships]
        rooms = db.query(Room).filter(Room.id.in_(room_ids), Room.is_active == True).order_by(Room.created_at.desc()).all()
    elif filter == "all":
        # All rooms where user is either owner or active member
        owned_rooms = db.query(Room).filter(
            (Room.owner_id == current_user.id) | 
            (Room.teacher_id.in_(db.query(Teacher.id).filter(Teacher.user_id == current_user.id))),
            Room.is_active == True
        ).all()
        member_room_ids = db.query(RoomMembership.room_id).filter(
            RoomMembership.user_id == current_user.id,
            RoomMembership.status == "ACTIVE"
        ).all()
        ids = list(set([r.id for r in owned_rooms] + [m[0] for m in member_room_ids]))
        rooms = db.query(Room).filter(Room.id.in_(ids), Room.is_active == True).order_by(Room.created_at.desc()).all()
    else:
        # Default: owned rooms
        rooms = db.query(Room).filter(
            (Room.owner_id == current_user.id) | 
            (Room.teacher_id.in_(db.query(Teacher.id).filter(Teacher.user_id == current_user.id))),
            Room.is_active == True
        ).order_by(Room.created_at.desc()).all()

    return [format_room_out(r, current_user, db) for r in rooms]

@router.get("/my/memberships", response_model=List[RoomMembershipOut])
def get_user_memberships(
    current_user: User = Depends(require_authenticated_user),
    db: Session = Depends(get_db)
):
    memberships = db.query(RoomMembership).filter(
        RoomMembership.user_id == current_user.id,
        RoomMembership.status == "ACTIVE"
    ).all()

    result = []
    for m in memberships:
        room_out = format_room_out(m.room, current_user, db) if m.room else None
        result.append(RoomMembershipOut(
            id=m.id,
            room_id=m.room_id,
            user_id=m.user_id,
            learner_id=m.learner_id,
            role=m.role,
            status=m.status,
            access_source=m.access_source or "FREE_JOIN",
            joined_at=m.joined_at,
            created_at=m.created_at,
            room=room_out
        ))
    return result

@router.get("/discover", response_model=List[RoomOut])
def discover_public_rooms(
    current_user: User = Depends(require_authenticated_user),
    db: Session = Depends(get_db)
):
    rooms = db.query(Room).filter(
        Room.is_active == True,
        Room.visibility == "PUBLIC"
    ).order_by(Room.created_at.desc()).limit(30).all()

    return [format_room_out(r, current_user, db) for r in rooms]

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

    is_owner = is_room_owner(room, current_user)
    membership = db.query(RoomMembership).filter(
        RoomMembership.room_id == room.id,
        RoomMembership.user_id == current_user.id,
        RoomMembership.status == "ACTIVE"
    ).first()
    is_member = membership is not None

    if not is_owner and not is_member and room.visibility != "PUBLIC":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: You do not have permission to view this private room. View the preview instead."
        )

    return format_room_out(room, current_user, db)

@router.get("/{room_id}/preview", response_model=RoomPreviewOut)
def get_room_preview(
    room_id: int,
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: Session = Depends(get_db)
):
    room = db.query(Room).filter(Room.id == room_id, Room.is_active == True).first()
    if not room:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Room not found")

    owner_user = room.owner_user
    if not owner_user and room.teacher and room.teacher.user:
        owner_user = room.teacher.user

    owner_name = owner_user.full_name if owner_user else "Guru"
    owner_guru_id = owner_user.guru_id if owner_user else f"GY-{room.id:04d}"
    owner_username = owner_user.username if owner_user else "guru"
    owner_avatar = owner_user.avatar_url if owner_user else None
    owner_followers = db.query(Follow).filter(Follow.following_id == owner_user.id).count() if owner_user else 0

    active_members = db.query(RoomMembership).filter(
        RoomMembership.room_id == room.id,
        RoomMembership.status == "ACTIVE"
    ).count()

    total_resources = db.query(Resource).filter(Resource.room_id == room.id, Resource.is_active == True).count()

    folders = db.query(Folder).filter(Folder.room_id == room.id, Folder.is_active == True).all()
    folder_outs = []
    for f in folders:
        r_cnt = db.query(Resource).filter(Resource.folder_id == f.id, Resource.is_active == True).count()
        folder_outs.append(RoomPreviewFolderOut(id=f.id, name=f.name, resources_count=r_cnt))

    # Safe preview resources: only show title, type, and preview allowance, NEVER file_url
    resources = db.query(Resource).filter(Resource.room_id == room.id, Resource.is_active == True).limit(10).all()
    preview_res = [
        RoomPreviewResourceOut(
            id=r.id,
            title=r.title,
            resource_type=r.resource_type,
            is_preview_allowed=r.is_preview_allowed or (r.visibility == "PUBLIC")
        )
        for r in resources
    ]

    membership_status = None
    if current_user:
        if is_room_owner(room, current_user):
            membership_status = "OWNER"
        else:
            m = db.query(RoomMembership).filter(
                RoomMembership.room_id == room.id,
                RoomMembership.user_id == current_user.id
            ).first()
            if m:
                membership_status = m.status

    return RoomPreviewOut(
        id=room.id,
        code=room.code,
        name=room.name,
        description=room.description,
        visibility=room.visibility,
        access_type=room.access_type or "PRIVATE_FREE",
        price=room.price or 0.0,
        currency=room.currency or "INR",
        owner_name=owner_name,
        owner_guru_id=owner_guru_id,
        owner_username=owner_username,
        owner_avatar_url=owner_avatar,
        owner_followers_count=owner_followers,
        active_members_count=active_members,
        total_resources_count=total_resources,
        folders=folder_outs,
        preview_resources=preview_res,
        user_membership_status=membership_status
    )

@router.put("/{room_id}", response_model=RoomOut)
def update_room(
    room_id: int,
    room_in: RoomUpdate,
    current_user: User = Depends(require_authenticated_user),
    db: Session = Depends(get_db)
):
    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Room not found")

    if not is_room_owner(room, current_user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access forbidden: You do not own this room.")

    if room_in.name is not None:
        room.name = room_in.name.strip()
    if room_in.description is not None:
        room.description = room_in.description.strip()
    if room_in.visibility is not None:
        room.visibility = room_in.visibility.upper()
    if room_in.access_type is not None:
        vis = room_in.access_type.upper()
        if vis in VALID_ACCESS_TYPES:
            room.access_type = vis
    if room_in.price is not None:
        room.price = max(0.0, float(room_in.price))
    if room_in.currency is not None:
        room.currency = room_in.currency.upper()
    if room_in.is_active is not None:
        room.is_active = room_in.is_active

    db.commit()
    db.refresh(room)
    return format_room_out(room, current_user, db)

@router.delete("/{room_id}")
def archive_room(
    room_id: int,
    current_user: User = Depends(require_authenticated_user),
    db: Session = Depends(get_db)
):
    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Room not found")

    if not is_room_owner(room, current_user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access forbidden: You do not own this room.")

    room.is_active = False
    db.commit()
    return {"message": "Room archived successfully", "id": room.id}

@router.get("/{room_id}/members", response_model=List[RoomMembershipOut])
def get_room_members(
    room_id: int,
    current_user: User = Depends(require_authenticated_user),
    db: Session = Depends(get_db)
):
    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Room not found")

    is_owner = is_room_owner(room, current_user)
    is_active_member = db.query(RoomMembership).filter(
        RoomMembership.room_id == room.id,
        RoomMembership.user_id == current_user.id,
        RoomMembership.status == "ACTIVE"
    ).first() is not None

    if not is_owner and not is_active_member:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access forbidden: You cannot view members of this room.")

    memberships = db.query(RoomMembership).filter(RoomMembership.room_id == room.id).all()
    return memberships

# ================= ROOM JOIN & ADMISSION LIFECYCLE =================

@router.post("/{room_id}/join", response_model=RoomMembershipOut)
def join_public_room(
    room_id: int,
    current_user: User = Depends(require_authenticated_user),
    db: Session = Depends(get_db)
):
    room = db.query(Room).filter(Room.id == room_id, Room.is_active == True).first()
    if not room:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Room not found")

    if is_room_owner(room, current_user):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You are the owner of this room.")

    access = room.access_type or ("PUBLIC_FREE" if room.visibility == "PUBLIC" else "PRIVATE_FREE")
    if access not in ("PUBLIC_FREE",) and room.visibility != "PUBLIC":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This is a private room. Please submit a join request or complete enrollment."
        )

    membership = db.query(RoomMembership).filter(
        RoomMembership.room_id == room.id,
        RoomMembership.user_id == current_user.id
    ).first()

    if not membership:
        membership = RoomMembership(
            room_id=room.id,
            user_id=current_user.id,
            role="MEMBER",
            status="ACTIVE",
            access_source="FREE_JOIN"
        )
        db.add(membership)
    else:
        membership.status = "ACTIVE"
        membership.role = "MEMBER"

    db.commit()
    db.refresh(membership)
    return membership

@router.post("/{room_id}/join-requests", response_model=JoinRequestOut, status_code=status.HTTP_201_CREATED)
def request_to_join_room(
    room_id: int,
    current_user: User = Depends(require_authenticated_user),
    db: Session = Depends(get_db)
):
    room = db.query(Room).filter(Room.id == room_id, Room.is_active == True).first()
    if not room:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Room not found")

    if is_room_owner(room, current_user):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You are the owner of this room.")

    membership = db.query(RoomMembership).filter(
        RoomMembership.room_id == room.id,
        RoomMembership.user_id == current_user.id
    ).first()

    if membership:
        if membership.status == "ACTIVE":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You are already an active member of this room.")
        if membership.status == "PENDING":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You have already requested to join this room. Please wait for the owner's approval.")
        membership.status = "PENDING"
    else:
        membership = RoomMembership(
            room_id=room.id,
            user_id=current_user.id,
            role="MEMBER",
            status="PENDING",
            access_source="REQUEST_ACCEPTED"
        )
        db.add(membership)

    db.commit()
    db.refresh(membership)

    return JoinRequestOut(
        id=membership.id,
        room_id=room.id,
        room_name=room.name,
        user_id=current_user.id,
        user_name=current_user.full_name,
        user_guru_id=current_user.guru_id or f"GY-{current_user.id:04d}",
        user_username=current_user.username,
        user_avatar_url=current_user.avatar_url,
        status="PENDING",
        created_at=membership.created_at
    )

@router.get("/{room_id}/join-requests", response_model=List[JoinRequestOut])
def get_pending_join_requests(
    room_id: int,
    current_user: User = Depends(require_authenticated_user),
    db: Session = Depends(get_db)
):
    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Room not found")

    if not is_room_owner(room, current_user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access forbidden: You do not own this room.")

    requests = db.query(RoomMembership).filter(
        RoomMembership.room_id == room.id,
        RoomMembership.status == "PENDING"
    ).order_by(RoomMembership.created_at.desc()).all()

    results = []
    for req in requests:
        u = req.user
        results.append(JoinRequestOut(
            id=req.id,
            room_id=room.id,
            room_name=room.name,
            user_id=req.user_id,
            user_name=u.full_name if u else "Member",
            user_guru_id=u.guru_id if u else f"GY-{req.user_id:04d}",
            user_username=u.username if u else None,
            user_avatar_url=u.avatar_url if u else None,
            status=req.status,
            created_at=req.created_at
        ))
    return results

@router.post("/{room_id}/join-requests/{membership_id}/action", response_model=JoinRequestOut)
def process_join_request(
    room_id: int,
    membership_id: int,
    action_in: JoinRequestAction,
    current_user: User = Depends(require_authenticated_user),
    db: Session = Depends(get_db)
):
    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Room not found")

    if not is_room_owner(room, current_user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access forbidden: You do not own this room.")

    membership = db.query(RoomMembership).filter(
        RoomMembership.id == membership_id,
        RoomMembership.room_id == room.id
    ).first()
    if not membership:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Join request not found")

    action = action_in.action.upper().strip()
    if action == "ACCEPT":
        membership.status = "ACTIVE"
    elif action == "REJECT":
        membership.status = "REJECTED"
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Action must be ACCEPT or REJECT")

    db.commit()
    db.refresh(membership)

    u = membership.user
    return JoinRequestOut(
        id=membership.id,
        room_id=room.id,
        room_name=room.name,
        user_id=membership.user_id,
        user_name=u.full_name if u else "Member",
        user_guru_id=u.guru_id if u else f"GY-{membership.user_id:04d}",
        user_username=u.username if u else None,
        user_avatar_url=u.avatar_url if u else None,
        status=membership.status,
        created_at=membership.created_at
    )

@router.delete("/{room_id}/join-requests")
def cancel_my_join_request(
    room_id: int,
    current_user: User = Depends(require_authenticated_user),
    db: Session = Depends(get_db)
):
    membership = db.query(RoomMembership).filter(
        RoomMembership.room_id == room_id,
        RoomMembership.user_id == current_user.id,
        RoomMembership.status == "PENDING"
    ).first()
    if not membership:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No pending join request found")

    db.delete(membership)
    db.commit()
    return {"message": "Join request cancelled successfully"}

# ================= FOLDERS ENDPOINTS (Phase 3) =================

@router.post("/{room_id}/folders", response_model=FolderOut, status_code=status.HTTP_201_CREATED)
def create_folder(
    room_id: int,
    folder_in: FolderCreate,
    current_user: User = Depends(require_authenticated_user),
    db: Session = Depends(get_db)
):
    room = db.query(Room).filter(Room.id == room_id, Room.is_active == True).first()
    if not room:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Room not found")

    if not is_room_owner(room, current_user):
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

    is_owner = is_room_owner(room, current_user)
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
    current_user: User = Depends(require_authenticated_user),
    db: Session = Depends(get_db)
):
    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Room not found")

    if not is_room_owner(room, current_user):
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
    current_user: User = Depends(require_authenticated_user),
    db: Session = Depends(get_db)
):
    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Room not found")

    if not is_room_owner(room, current_user):
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
    current_user: User = Depends(require_authenticated_user),
    db: Session = Depends(get_db)
):
    room = db.query(Room).filter(Room.id == room_id, Room.is_active == True).first()
    if not room:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Room not found")

    if not is_room_owner(room, current_user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access forbidden: You do not own this room.")

    res_type = (res_in.resource_type or "PDF").upper()
    if res_type not in VALID_RESOURCE_TYPES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid resource type: {res_type}")

    visibility = (res_in.visibility or "ROOM_ONLY").upper()
    if visibility not in VALID_VISIBILITIES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid visibility: {visibility}")

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
        external_url=res_in.external_url,
        mime_type=res_in.mime_type,
        file_size=res_in.file_size,
        visibility=visibility,
        is_preview_allowed=bool(res_in.is_preview_allowed),
        uploaded_by=current_user.id,
        is_active=True
    )
    db.add(resource)
    db.commit()
    db.refresh(resource)

    owner_name, _, _, _ = get_room_owner_info(room, db)

    return ResourceOut(
        id=resource.id,
        room_id=resource.room_id,
        folder_id=resource.folder_id,
        title=resource.title,
        description=resource.description,
        resource_type=resource.resource_type,
        file_url=resource.file_url,
        external_url=resource.external_url,
        mime_type=resource.mime_type,
        file_size=resource.file_size,
        visibility=resource.visibility,
        is_preview_allowed=resource.is_preview_allowed or False,
        is_active=resource.is_active,
        created_at=resource.created_at,
        updated_at=resource.updated_at,
        folder_name=folder_name,
        room_name=room.name,
        room_code=room.code,
        teacher_name=owner_name
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

    is_owner = is_room_owner(room, current_user)
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

    if not is_owner and not is_member:
        query = query.filter(Resource.visibility == "PUBLIC")

    resources = query.order_by(Resource.created_at.desc()).all()
    owner_name, _, _, _ = get_room_owner_info(room, db)

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
            external_url=r.external_url,
            mime_type=r.mime_type,
            file_size=r.file_size,
            visibility=r.visibility,
            is_preview_allowed=r.is_preview_allowed or False,
            is_active=r.is_active,
            created_at=r.created_at,
            updated_at=r.updated_at,
            folder_name=f_name,
            room_name=room.name,
            room_code=room.code,
            teacher_name=owner_name
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
    is_owner = is_room_owner(room, current_user)
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

    owner_name, _, _, _ = get_room_owner_info(room, db)
    folder_name = resource.folder.name if resource.folder else None

    return ResourceOut(
        id=resource.id,
        room_id=resource.room_id,
        folder_id=resource.folder_id,
        title=resource.title,
        description=resource.description,
        resource_type=resource.resource_type,
        file_url=resource.file_url,
        external_url=resource.external_url,
        mime_type=resource.mime_type,
        file_size=resource.file_size,
        visibility=resource.visibility,
        is_preview_allowed=resource.is_preview_allowed or False,
        is_active=resource.is_active,
        created_at=resource.created_at,
        updated_at=resource.updated_at,
        folder_name=folder_name,
        room_name=room.name,
        room_code=room.code,
        teacher_name=owner_name
    )

@router.put("/{room_id}/resources/{resource_id}", response_model=ResourceOut)
def update_resource(
    room_id: int,
    resource_id: int,
    res_in: ResourceUpdate,
    current_user: User = Depends(require_authenticated_user),
    db: Session = Depends(get_db)
):
    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Room not found")

    if not is_room_owner(room, current_user):
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
    if res_in.external_url is not None:
        resource.external_url = res_in.external_url
    if res_in.is_preview_allowed is not None:
        resource.is_preview_allowed = res_in.is_preview_allowed
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
    owner_name, _, _, _ = get_room_owner_info(room, db)

    return ResourceOut(
        id=resource.id,
        room_id=resource.room_id,
        folder_id=resource.folder_id,
        title=resource.title,
        description=resource.description,
        resource_type=resource.resource_type,
        file_url=resource.file_url,
        external_url=resource.external_url,
        mime_type=resource.mime_type,
        file_size=resource.file_size,
        visibility=resource.visibility,
        is_preview_allowed=resource.is_preview_allowed or False,
        is_active=resource.is_active,
        created_at=resource.created_at,
        updated_at=resource.updated_at,
        folder_name=folder_name,
        room_name=room.name,
        room_code=room.code,
        teacher_name=owner_name
    )

@router.delete("/{room_id}/resources/{resource_id}")
def archive_resource(
    room_id: int,
    resource_id: int,
    current_user: User = Depends(require_authenticated_user),
    db: Session = Depends(get_db)
):
    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Room not found")

    if not is_room_owner(room, current_user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access forbidden: You do not own this room.")

    resource = db.query(Resource).filter(Resource.id == resource_id, Resource.room_id == room.id).first()
    if not resource:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found")

    resource.is_active = False
    db.commit()
    return {"message": "Resource archived successfully", "id": resource.id}
