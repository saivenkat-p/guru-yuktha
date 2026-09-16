from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.models import User, Follow, Room
from app.schemas.schemas import MemberProfileOut, RoomOut

router = APIRouter()

def resolve_member(identifier: str, db: Session) -> User:
    ident = identifier.strip().lstrip('@').lower()
    user = db.query(User).filter(
        (User.guru_id.ilike(ident)) |
        (User.username.ilike(ident))
    ).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Member '{identifier}' not found"
        )
    return user

def build_profile_out(target: User, current_user: Optional[User], db: Session) -> MemberProfileOut:
    followers_count = db.query(Follow).filter(Follow.following_id == target.id).count()
    following_count = db.query(Follow).filter(Follow.follower_id == target.id).count()
    rooms_owned_count = db.query(Room).filter(Room.owner_id == target.id, Room.is_active == True).count()
    is_eligible = followers_count >= 100

    is_following = False
    if current_user and current_user.id != target.id:
        existing = db.query(Follow).filter(
            Follow.follower_id == current_user.id,
            Follow.following_id == target.id
        ).first()
        is_following = existing is not None

    return MemberProfileOut(
        id=target.id,
        guru_id=target.guru_id or f"GY-{target.id:04d}",
        username=target.username or f"user_{target.id}",
        full_name=target.full_name,
        avatar_url=target.avatar_url,
        bio=target.bio,
        skills=target.skills,
        followers_count=followers_count,
        following_count=following_count,
        rooms_owned_count=rooms_owned_count,
        is_guru_eligible=is_eligible,
        is_following=is_following,
        created_at=target.created_at
    )

@router.get("/{identifier}", response_model=MemberProfileOut)
def get_member_profile(
    identifier: str,
    db: Session = Depends(get_db)
):
    target = resolve_member(identifier, db)
    return build_profile_out(target, None, db)

@router.post("/{identifier}/follow", response_model=MemberProfileOut)
def follow_member(
    identifier: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    target = resolve_member(identifier, db)
    if target.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot follow your own profile."
        )

    existing = db.query(Follow).filter(
        Follow.follower_id == current_user.id,
        Follow.following_id == target.id
    ).first()

    if not existing:
        follow = Follow(follower_id=current_user.id, following_id=target.id)
        db.add(follow)
        db.commit()

    return build_profile_out(target, current_user, db)

@router.delete("/{identifier}/follow", response_model=MemberProfileOut)
def unfollow_member(
    identifier: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    target = resolve_member(identifier, db)
    existing = db.query(Follow).filter(
        Follow.follower_id == current_user.id,
        Follow.following_id == target.id
    ).first()

    if existing:
        db.delete(existing)
        db.commit()

    return build_profile_out(target, current_user, db)

@router.get("/{identifier}/followers", response_model=List[MemberProfileOut])
def get_member_followers(
    identifier: str,
    db: Session = Depends(get_db)
):
    target = resolve_member(identifier, db)
    follows = db.query(Follow).filter(Follow.following_id == target.id).all()
    results = []
    for f in follows:
        if f.follower:
            results.append(build_profile_out(f.follower, None, db))
    return results

@router.get("/{identifier}/following", response_model=List[MemberProfileOut])
def get_member_following(
    identifier: str,
    db: Session = Depends(get_db)
):
    target = resolve_member(identifier, db)
    follows = db.query(Follow).filter(Follow.follower_id == target.id).all()
    results = []
    for f in follows:
        if f.following_user:
            results.append(build_profile_out(f.following_user, None, db))
    return results

@router.get("/{identifier}/rooms", response_model=List[RoomOut])
def get_member_public_rooms(
    identifier: str,
    db: Session = Depends(get_db)
):
    target = resolve_member(identifier, db)
    rooms = db.query(Room).filter(
        Room.owner_id == target.id,
        Room.visibility == "PUBLIC",
        Room.is_active == True
    ).order_by(Room.created_at.desc()).all()

    return [
        RoomOut(
            id=r.id,
            owner_id=r.owner_id,
            teacher_id=r.teacher_id,
            name=r.name,
            description=r.description,
            code=r.code,
            visibility=r.visibility,
            access_type=r.access_type or "PUBLIC_FREE",
            price=r.price or 0.0,
            currency=r.currency or "INR",
            is_active=r.is_active,
            active_members_count=len(r.memberships) if r.memberships else 0,
            created_at=r.created_at,
            updated_at=r.updated_at,
            owner_name=target.full_name,
            owner_guru_id=target.guru_id,
            owner_username=target.username,
            owner_avatar_url=target.avatar_url
        )
        for r in rooms
    ]
