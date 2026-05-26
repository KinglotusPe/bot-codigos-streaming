"""
Utility for auditing management actions.
"""
import logging
from database import get_db_session
from models import AuditLog

logger = logging.getLogger(__name__)

def log_action(performed_by_id: int, action: str, target_id: int = None, details: str = None):
    """
    Log a management action to the database.
    
    Args:
        performed_by_id: Telegram ID of the person performing the action
        action: String identifier of the action (e.g., 'ADD_ADMIN')
        target_id: Optional Telegram ID of the person affected
        details: Optional additional text information
    """
    try:
        with get_db_session() as session:
            log_entry = AuditLog(
                performed_by_id=performed_by_id,
                action=action,
                target_id=target_id,
                details=details
            )
            session.add(log_entry)
            session.commit()
            logger.info(f"📝 AUDIT: {action} by {performed_by_id} on {target_id}")
    except Exception as e:
        logger.error(f"❌ Failed to log audit action: {e}")
