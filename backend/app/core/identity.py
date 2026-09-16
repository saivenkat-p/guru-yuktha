import re
import random
import string
from typing import Optional
from sqlalchemy.orm import Session

def clean_name_prefix(name: str) -> str:
    # Filter out common titles like Md., Dr., Prof., etc.
    words = [w for w in re.split(r'[\s._-]+', name or "") if w]
    meaningful = [w for w in words if w.lower() not in ("md", "dr", "prof", "mr", "mrs", "ms")]
    target = meaningful[0] if meaningful else (words[0] if words else "GURU")
    clean = re.sub(r'[^A-Za-z0-9]', '', target).upper()
    return clean[:8] if len(clean) >= 2 else "GURU"

def generate_guru_id(name: str, user_id: Optional[int] = None, db: Optional[Session] = None) -> str:
    from app.models.models import User
    prefix = clean_name_prefix(name)
    
    for _ in range(50):
        rand_chars = "".join(random.choices(string.ascii_uppercase + string.digits, k=4))
        if user_id:
            uid_str = f"{user_id % 100:02d}"
            candidate = f"GY-{prefix}{uid_str}{rand_chars[:2]}"
        else:
            candidate = f"GY-{prefix}{rand_chars}"
        
        if db:
            exists = db.query(User).filter(User.guru_id == candidate).first()
            if not exists:
                return candidate
        else:
            return candidate
            
    # Fallback
    rand_suffix = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f"GY-{prefix}{rand_suffix}"

def generate_username(name: str, email: Optional[str] = None, user_id: Optional[int] = None, db: Optional[Session] = None) -> str:
    from app.models.models import User
    base = ""
    if name:
        base = re.sub(r'[^a-zA-Z0-9_]', '', name.strip().lower().replace(' ', '_'))
    if not base and email:
        base = email.split('@')[0]
        base = re.sub(r'[^a-zA-Z0-9_]', '', base.lower())
    if not base:
        base = "member"

    candidate = base[:30]
    if db:
        exists = db.query(User).filter(User.username == candidate).first()
        if not exists:
            return candidate
        suffix = f"_{user_id}" if user_id else f"_{random.randint(100, 9999)}"
        return f"{candidate[:24]}{suffix}"
    return candidate
