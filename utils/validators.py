"""
Validation utilities for the Telegram bot.
"""

import re
from database import get_db_session
from models import Owner, Admin, Seller, User, StatusEnum
from email_validator import validate_email as validate_email_format, EmailNotValidError


def is_super_owner(user_id: int) -> bool:
    """
    Check if a user is one of the absolute SuperOwners (defined in .env).
    """
    import config
    return user_id in config.OWNER_TELEGRAM_IDS


def is_owner(user_id: int) -> bool:
    """
    Check if a user is an Owner (SuperOwner OR in owners table) and has active access.
    """
    if is_super_owner(user_id):
        return True
        
    from datetime import datetime
    with get_db_session() as session:
        owner = session.query(Owner).filter_by(user_id=user_id, status=StatusEnum.ACTIVE).first()
        if owner:
            if owner.access_end_date and owner.access_end_date < datetime.utcnow():
                return False
            return True
        return False


def is_admin(user_id: int, check_active: bool = True) -> bool:
    """
    Check if a user is an Admin and has active access.
    """
    if is_owner(user_id):
        return True
        
    from datetime import datetime
    with get_db_session() as session:
        query = session.query(Admin).filter_by(user_id=user_id)
        if check_active:
            query = query.filter_by(status=StatusEnum.ACTIVE)
        admin = query.first()
        if admin:
            if admin.access_end_date < datetime.utcnow():
                return False
            return True
        return False


def has_any_management_role(user_id: int) -> bool:
    """
    Check if user is SuperOwner, Owner, Seller or Admin.
    """
    return is_super_owner(user_id) or is_owner(user_id) or is_seller(user_id) or is_admin(user_id)


def is_seller(user_id: int, check_active: bool = True) -> bool:
    """
    Check if a user is a Seller and has active access.
    """
    if is_owner(user_id):
        return True
        
    from datetime import datetime
    with get_db_session() as session:
        query = session.query(Seller).filter_by(user_id=user_id)
        if check_active:
            query = query.filter_by(status=StatusEnum.ACTIVE)
        seller = query.first()
        if seller:
            if seller.access_end_date < datetime.utcnow():
                return False
            return True
        return False


def is_user(user_id: int, check_active: bool = True) -> bool:
    """
    Check if a user is a User.
    """
    if is_owner(user_id):
        return True
        
    with get_db_session() as session:
        query = session.query(User).filter_by(user_id=user_id)
        if check_active:
            query = query.filter_by(status=StatusEnum.ACTIVE)
        user = query.first()
        return user is not None


def get_admin_by_user_id(user_id: int):
    """
    Get Admin record by Telegram user ID.
    """
    with get_db_session() as session:
        admin = session.query(Admin).filter_by(user_id=user_id).first()
        if admin:
            session.expunge(admin)
        return admin


def get_user_by_user_id(user_id: int):
    """
    Get User record by Telegram user ID.
    """
    with get_db_session() as session:
        user = session.query(User).filter_by(user_id=user_id).first()
        if user:
            session.expunge(user)
        return user


def validate_email(email: str) -> bool:
    """
    Validate email format.
    """
    try:
        validate_email_format(email)
        return True
    except EmailNotValidError:
        return False


def extract_user_id_from_mention(mention: str) -> int:
    """
    Extract Telegram user ID from a mention.
    """
    username = mention.lstrip('@')
    return 0  # Placeholder


def parse_days_parameter(days_str: str) -> int:
    """
    Parse and validate the days parameter.
    """
    try:
        days = int(days_str)
        if days != 30:
            raise ValueError("Days must be exactly 30")
        return days
    except ValueError:
        raise ValueError("Invalid days parameter")


def get_user_role(user_id: int) -> str:
    """
    Determine the role of a user.
    """
    if is_super_owner(user_id):
        return "superowner"
    elif is_owner(user_id):
        return "owner"
    elif is_seller(user_id):
        return "seller"
    elif is_admin(user_id):
        return "admin"
    elif is_user(user_id):
        return "user"
    else:
        return "unknown"


def get_expiration_info(user_id: int) -> str:
    """
    Get the expiration date as a formatted string for a given user.
    """
    from database import get_db_session
    from models import Owner, Seller, Admin
    from datetime import datetime
    import config
    
    if user_id == config.OWNER_TELEGRAM_ID:
        return "Infinito (SuperOwner)"
        
    with get_db_session() as session:
        # Check Owner
        owner = session.query(Owner).filter_by(user_id=user_id).first()
        if owner and owner.access_end_date:
            days = (owner.access_end_date - datetime.utcnow()).days
            return f"{owner.access_end_date.strftime('%Y-%m-%d')} ({days} días)"
            
        # Check Seller
        seller = session.query(Seller).filter_by(user_id=user_id).first()
        if seller and seller.access_end_date:
            days = (seller.access_end_date - datetime.utcnow()).days
            return f"{seller.access_end_date.strftime('%Y-%m-%d')} ({days} días)"
            
        # Check Admin
        admin = session.query(Admin).filter_by(user_id=user_id).first()
        if admin and admin.access_end_date:
            days = (admin.access_end_date - datetime.utcnow()).days
            return f"{admin.access_end_date.strftime('%Y-%m-%d')} ({days} días)"
            
    return "N/A"


def get_owner_username() -> str:
    """
    Get the username of the system owner.
    
    Returns:
        Owner username or empty string
    """
    with get_db_session() as session:
        owner = session.query(Owner).first()
        return owner.telegram_username if owner else ""


# Anti-Spam / Rate Limiting
from datetime import datetime, timedelta
_last_execution = {}

def rate_limit(user_id: int, command: str, seconds: int = 15) -> bool:
    """
    Checks if a user is allowed to run a command based on time window.
    
    Returns:
        True if allowed, False if rate limited.
    """
    # SuperOwner is immune
    if is_super_owner(user_id):
        return True
        
    key = f"{user_id}:{command}"
    now = datetime.utcnow()
    
    if key in _last_execution:
        elapsed = (now - _last_execution[key]).total_seconds()
        if elapsed < seconds:
            return False
            
    _last_execution[key] = now
    return True


def check_abuse(user_id: int, limit: int = 5, window_minutes: int = 60) -> bool:
    """
    Check if a user is requesting too many codes (Option 6).
    Returns True if abuse detected, False otherwise.
    """
    if is_super_owner(user_id):
        return False
        
    from models import CodeHistory
    from datetime import datetime, timedelta
    
    with get_db_session() as session:
        since = datetime.utcnow() - timedelta(minutes=window_minutes)
        count = session.query(CodeHistory).filter(
            CodeHistory.user_id == user_id,
            CodeHistory.sent_at >= since
        ).count()
        
        return count >= limit
