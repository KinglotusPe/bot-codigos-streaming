"""
Seller commands for the Telegram bot.
Commands: /addadmin, /deladmin (Restricted for Sellers)
"""

from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import ContextTypes
from database import get_db_session
from models import Seller, Admin, User, StatusEnum
from utils.validators import is_seller
from utils.messages import (
    ERROR_INVALID_FORMAT,
    command_success_add_admin,
    command_success_remove_admin
)
from utils.logger import log_action
import config
import logging

logger = logging.getLogger(__name__)

async def seller_addadmin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Seller: Add a new admin with 30-day access.
    Command: /addadmin <user_id>
    """
    user_id = update.effective_user.id
    
    # Check if sender is seller
    if not is_seller(user_id):
        # This handler should only be called if is_seller is true, 
        # but double check or just return if not.
        # Note: In bot_manager we will route /addadmin to this if user is seller,
        # or to owner_addadmin if user is owner.
        return
    
    if len(context.args) != 1:
        await update.message.reply_text(f"{ERROR_INVALID_FORMAT}\n\nUso: /addadmin <user_id>")
        return
    
    try:
        new_admin_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text(ERROR_INVALID_FORMAT)
        return
    
    days = config.SUBSCRIPTION_DAYS
    
    with get_db_session() as session:
        # Get the seller record
        seller = session.query(Seller).filter_by(user_id=user_id).first()
        if not seller or seller.status != StatusEnum.ACTIVE:
            await update.message.reply_text("❌ Tu cuenta de Seller no está activa.")
            return

        # Check if admin already exists
        existing_admin = session.query(Admin).filter_by(user_id=new_admin_id).first()
        
        if existing_admin:
            # Seller can only renew THEIR OWN admins
            if existing_admin.seller_id != seller.id:
                await update.message.reply_text("❌ Este admin ya existe y no te pertenece.")
                return
                
            # Update existing admin
            existing_admin.access_end_date = datetime.utcnow() + timedelta(days=days)
            existing_admin.status = StatusEnum.ACTIVE
            session.commit()
            
            end_date = existing_admin.access_end_date.strftime('%Y-%m-%d')
            log_action(user_id, 'RENEW_ADMIN_BY_SELLER', new_admin_id, f"Nueva exp: {end_date}")
            await update.message.reply_text(
                command_success_add_admin(f"ID:{new_admin_id}", end_date)
            )
        else:
            # Create new admin linked to this seller
            admin = Admin(
                user_id=new_admin_id,
                owner_id=None, # Not directly linked to owner
                seller_id=seller.id, # Linked to seller
                access_end_date=datetime.utcnow() + timedelta(days=days),
                status=StatusEnum.ACTIVE
            )
            session.add(admin)
            session.commit()
            
            end_date = admin.access_end_date.strftime('%Y-%m-%d')
            log_action(user_id, 'ADD_ADMIN_BY_SELLER', new_admin_id, f"Exp: {end_date}")
            await update.message.reply_text(
                command_success_add_admin(f"ID:{new_admin_id}", end_date)
            )
    
    logger.info(f"✅ Seller {user_id} added admin {new_admin_id}")


async def seller_deladmin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Seller: Remove an admin's access (DISABLED - Only SuperOwner).
    Command: /deladmin <user_id>
    """
    await update.message.reply_text("❌ Solo el Dueño Total puede quitar suscripciones o rangos.")
