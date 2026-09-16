from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.core.database import get_db
from app.models.models import User, Room, Resource, Follow
from app.schemas.schemas import UniversalSearchResult, SearchMemberResult, SearchRoomResult, SearchResourceResult

router = APIRouter()

@router.get("", response_model=UniversalSearchResult)
def universal_search(
    q: str = Query(..., min_length=1, description="Search query for Gurus, Rooms, or Public Resources"),
    db: Session = Depends(get_db)
):
    query_str = q.strip().lstrip('@')
    wildcard = f"%{query_str}%"

    # 1. Members Search
    members_found = db.query(User).filter(
        or_(
            User.guru_id.ilike(wildcard),
            User.username.ilike(wildcard),
            User.full_name.ilike(wildcard),
            User.skills.ilike(wildcard)
        )
    ).limit(15).all()

    member_results = []
    for m in members_found:
        f_count = db.query(Follow).filter(Follow.following_id == m.id).count()
        r_count = db.query(Room).filter(Room.owner_id == m.id, Room.is_active == True).count()
        member_results.append(
            SearchMemberResult(
                id=m.id,
                guru_id=m.guru_id or f"GY-{m.id:04d}",
                username=m.username or f"user_{m.id}",
                full_name=m.full_name,
                avatar_url=m.avatar_url,
                bio=m.bio,
                followers_count=f_count,
                rooms_owned_count=r_count
            )
        )

    # 2. Rooms Search
    rooms_found = db.query(Room).filter(
        Room.is_active == True,
        or_(
            Room.code.ilike(wildcard),
            Room.name.ilike(wildcard),
            Room.description.ilike(wildcard)
        )
    ).limit(15).all()

    room_results = []
    for r in rooms_found:
        owner_name = r.owner_user.full_name if r.owner_user else (r.owner.user.full_name if r.owner and r.owner.user else "Guru")
        owner_guru_id = r.owner_user.guru_id if r.owner_user else (r.owner.user.guru_id if r.owner and r.owner.user else None)
        room_results.append(
            SearchRoomResult(
                id=r.id,
                code=r.code,
                name=r.name,
                description=r.description,
                access_type=r.access_type or ("PUBLIC_FREE" if r.visibility == "PUBLIC" else "PRIVATE_FREE"),
                price=r.price or 0.0,
                owner_name=owner_name,
                owner_guru_id=owner_guru_id
            )
        )

    # 3. Public Resources Search
    resources_found = db.query(Resource).filter(
        Resource.is_active == True,
        Resource.visibility == "PUBLIC",
        or_(
            Resource.title.ilike(wildcard),
            Resource.description.ilike(wildcard)
        )
    ).limit(15).all()

    resource_results = []
    for res in resources_found:
        r_name = res.room.name if res.room else "Open Resource"
        resource_results.append(
            SearchResourceResult(
                id=res.id,
                room_id=res.room_id,
                room_name=r_name,
                title=res.title,
                description=res.description,
                resource_type=res.resource_type,
                file_url=res.file_url,
                external_url=res.external_url
            )
        )

    return UniversalSearchResult(
        query=q,
        members=member_results,
        rooms=room_results,
        resources=resource_results
    )
