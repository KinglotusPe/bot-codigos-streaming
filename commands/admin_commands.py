"""
Admin commands for the Telegram bot (Enhanced Version).
Now supports individual account expiration (Option B).
"""

from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import ContextTypes
from database import get_db_session
from models import Admin, User, StreamingAccount, StatusEnum
from utils.validators import is_admin, has_any_management_role, validate_email, get_admin_by_user_id
from utils.messages import (
    ERROR_NOT_ADMIN,
    ERROR_ADMIN_INACTIVE,
    ERROR_INVALID_EMAIL,
    ERROR_INVALID_FORMAT,
    NO_EMAILS_REGISTERED
)
from utils.logger import log_action
from platform_config import get_supported_platforms
import config
import logging

logger = logging.getLogger(__name__)


async def reg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Register a new streaming account.
    Command: /reg <plataforma> <email>
    """
    user_id = update.effective_user.id
    if not has_any_management_role(user_id):
        await update.message.reply_text("❌ No tienes rango suficiente para registrar correos.")
        return
    
    if len(context.args) != 2:
        platforms = ", ".join(get_supported_platforms())
        await update.message.reply_text(
            f"❌ Formato inválido.\n\n"
            f"Uso: /reg <plataforma> <correo>\n"
            f"Plataformas soportadas: {platforms}"
        )
        return
    
    platform_name = context.args[0].lower()
    email = context.args[1].lower()
    
    if not validate_email(email):
        await update.message.reply_text(ERROR_INVALID_EMAIL)
        return
    
    with get_db_session() as session:
        # Check if admin record exists (for owners/sellers it might not exist yet)
        admin = session.query(Admin).filter_by(user_id=user_id).first()
        if not admin:
            # Create a virtual admin record for the management role if it doesn't exist
            # This is just for the foreign key link
            pass # Actually, for owners/sellers, we might need to handle this differently
            # For now, let's assume SuperOwner/Owner/Seller are already in their tables.
            # But StreamingAccount needs registered_by_admin_id.
            # I'll use a system admin (ID 1) as fallback or create one.
            admin = session.query(Admin).first()
        
        existing = session.query(StreamingAccount).filter_by(
            email_address=email,
            platform_name=platform_name
        ).first()
        
        if existing:
            await update.message.reply_text(f"❌ La cuenta {email} ({platform_name.upper()}) ya existe.")
            return
        
        account = StreamingAccount(
            email_address=email,
            platform_name=platform_name,
            registered_by_admin_id=admin.id if admin else 1,
            last_email_at=datetime.utcnow() # Initialize health tracking
        )
        session.add(account)
        session.commit()
        
        log_action(user_id, 'REGISTER_ACCOUNT', f"{platform_name}:{email}")
        from utils.keyboards import get_back_button
        await update.message.reply_text(f"✅ Cuenta {email} ({platform_name.upper()}) registrada con éxito.", reply_markup=get_back_button())

async def miscorreos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """List all emails registered by the sender."""
    user_id = update.effective_user.id
    if not has_any_management_role(user_id):
        await update.message.reply_text("❌ No tienes rango para ver correos.")
        return
    
    with get_db_session() as session:
        admin = session.query(Admin).filter_by(user_id=user_id).first()
        admin_id = admin.id if admin else 1
        
        accounts = session.query(StreamingAccount).filter_by(registered_by_admin_id=admin_id).all()
        
        if not accounts:
            await update.message.reply_text(NO_EMAILS_REGISTERED)
            return
            
        lines = ["📧 **Tus Correos Registrados:**\n"]
        for acc in accounts:
            status = "🟢 Libre"
            assigned = ""
            if acc.assigned_to_user_id:
                user = session.query(User).get(acc.assigned_to_user_id)
                status = "🔴 Ocupado"
                assigned = f" (ID:{user.user_id if user else '?'})"
                if acc.expiration_date:
                    assigned += f" [Vence: {acc.expiration_date.strftime('%Y-%m-%d')}]"
            
        from utils.keyboards import get_back_button
        if update.callback_query:
            await update.callback_query.edit_message_text("\n".join(lines), parse_mode='Markdown', reply_markup=get_back_button())
        else:
            await update.message.reply_text("\n".join(lines), parse_mode='Markdown', reply_markup=get_back_button())

async def asig(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Assign a streaming account to a user for 30 days.
    Command: /asig <user_id> <plataforma> <correo>
    """
    user_id = update.effective_user.id
    if not has_any_management_role(user_id):
        await update.message.reply_text("❌ No tienes rango para asignar.")
        return
    
    if len(context.args) < 3:
        await update.message.reply_text("❌ Uso: /asig <user_id> <plataforma> <correo>")
        return
        
    try:
        target_user_id = int(context.args[0])
        platform = context.args[1].lower()
        email = context.args[2].lower()
    except ValueError:
        await update.message.reply_text("❌ ID de usuario inválido.")
        return

    with get_db_session() as session:
        account = session.query(StreamingAccount).filter_by(
            platform_name=platform,
            email_address=email
        ).first()
        
        if not account:
            await update.message.reply_text("❌ Cuenta no encontrada.")
            return
            
        user = session.query(User).filter_by(user_id=target_user_id).first()
        if not user:
            # Create user if doesn't exist
            admin = session.query(Admin).filter_by(user_id=user_id).first()
            user = User(user_id=target_user_id, admin_id=admin.id if admin else 1)
            session.add(user)
            session.flush()
            
        account.assigned_to_user_id = user.id
        account.expiration_date = datetime.utcnow() + timedelta(days=30)
        session.commit()
        
        date_str = account.expiration_date.strftime('%Y-%m-%d')
        log_action(user_id, 'ASSIGN_ACCOUNT', target_user_id, f"{platform}:{email} hasta {date_str}")
        await update.message.reply_text(f"✅ Asignado: {email} ({platform.upper()}) para {target_user_id} hasta {date_str}.")
        
        try:
            await context.bot.send_message(
                chat_id=target_user_id,
                text=f"🎉 Se te ha asignado **{platform.upper()}** ({email})\n📅 Vence: {date_str}\nUsa /historial para ver tus códigos."
            )
        except: pass

async def renov(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Renew a specific account for 30 days.
    Command: /renov <user_id> <plataforma> <correo>
    """
    user_id = update.effective_user.id
    if not has_any_management_role(user_id):
        await update.message.reply_text("❌ No tienes rango para renovar.")
        return
        
    if len(context.args) < 3:
        await update.message.reply_text("❌ Uso: /renov <user_id> <plataforma> <correo>")
        return
        
    target_user_id = int(context.args[0])
    platform = context.args[1].lower()
    email = context.args[2].lower()
    
    with get_db_session() as session:
        user = session.query(User).filter_by(user_id=target_user_id).first()
        if not user:
            await update.message.reply_text("❌ Usuario no encontrado.")
            return
            
        account = session.query(StreamingAccount).filter_by(
            assigned_to_user_id=user.id,
            platform_name=platform,
            email_address=email
        ).first()
        
        if not account:
            await update.message.reply_text("❌ Esa cuenta no está asignada a ese usuario.")
            return
            
        now = datetime.utcnow()
        if account.expiration_date and account.expiration_date > now:
            account.expiration_date += timedelta(days=30)
        else:
            account.expiration_date = now + timedelta(days=30)
            
        session.commit()
        date_str = account.expiration_date.strftime('%Y-%m-%d')
        log_action(user_id, 'RENEW_ACCOUNT', target_user_id, f"{platform}:{email} hasta {date_str}")
        await update.message.reply_text(f"✅ Renovado: {platform.upper()} ({email}) hasta {date_str}")
        
        try:
            await context.bot.send_message(
                chat_id=target_user_id,
                text=f"🎉 Renovado: **{platform.upper()}** ({email}) hasta {date_str}"
            )
        except: pass

async def venc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """List all accounts expiring in 7 days."""
    user_id = update.effective_user.id
    if not has_any_management_role(user_id):
        await update.message.reply_text("❌ No tienes rango.")
        return
        
    with get_db_session() as session:
        now = datetime.utcnow()
        limit = now + timedelta(days=7)
        
        accounts = session.query(StreamingAccount).filter(
            StreamingAccount.assigned_to_user_id != None,
            StreamingAccount.expiration_date <= limit,
            StreamingAccount.expiration_date > now
        ).all()
        
        if not accounts:
            await update.message.reply_text("✅ No hay vencimientos próximos (7 días).")
            return
            
        lines = ["⚠️ **Próximos Vencimientos:**\n"]
        for acc in accounts:
            user = session.query(User).get(acc.assigned_to_user_id)
            days = (acc.expiration_date - now).days
            lines.append(f"🔴 ID:{user.user_id if user else '?'} | {acc.platform_name.upper()} | {acc.email_address} | {days} días")
            
        from utils.keyboards import get_back_button
        if update.callback_query:
            await update.callback_query.edit_message_text("\n".join(lines), parse_mode='Markdown', reply_markup=get_back_button())
        else:
            await update.message.reply_text("\n".join(lines), parse_mode='Markdown', reply_markup=get_back_button())


async def settrial(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Mark an account as a Trial account.
    Command: /settrial <plataforma> <correo>
    """
    user_id = update.effective_user.id
    if not has_any_management_role(user_id):
        await update.message.reply_text("❌ No tienes rango para esto.")
        return
        
    if len(context.args) < 2:
        await update.message.reply_text("❌ Uso: /settrial <plataforma> <correo>")
        return
        
    platform = context.args[0].lower()
    email = context.args[1].lower()
    
    with get_db_session() as session:
        account = session.query(StreamingAccount).filter_by(
            platform_name=platform,
            email_address=email
        ).first()
        
        if not account:
            await update.message.reply_text("❌ Cuenta no encontrada.")
            return
            
        account.is_trial = True
        session.commit()
        
        log_action(user_id, 'SET_TRIAL_ACCOUNT', f"{platform}:{email}")
        await update.message.reply_text(f"✅ La cuenta {email} ({platform.upper()}) ahora es una CUENTA DE PRUEBA.")


async def cerrar_ticket(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Close an open support ticket.
    Command: /cerrar <ticket_id>
    """
    user_id = update.effective_user.id
    if not has_any_management_role(user_id):
        await update.message.reply_text("❌ No tienes rango para cerrar tickets.")
        return
        
    if not context.args:
        await update.message.reply_text("❌ Uso: /cerrar <ticket_id>")
        return
        
    try:
        ticket_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("❌ ID de ticket inválido.")
        return
        
    from models import Ticket
    with get_db_session() as session:
        ticket = session.query(Ticket).get(ticket_id)
        if not ticket:
            await update.message.reply_text("❌ Ticket no encontrado.")
            return
            
        if ticket.status == "CLOSED":
            await update.message.reply_text("ℹ️ Este ticket ya está cerrado.")
            return
            
        ticket.status = "CLOSED"
        ticket.closed_at = datetime.utcnow()
        session.commit()
        
        log_action(user_id, 'CLOSE_TICKET', ticket_id)
        
        # Notify user
        try:
            await context.bot.send_message(
                chat_id=ticket.user_id,
                text=f"✅ **Ticket #{ticket_id} Cerrado**\n\nTu reporte ha sido resuelto por nuestro equipo técnico. ¡Gracias por tu paciencia!"
            )
        except: pass
        
        await update.message.reply_text(f"✅ Ticket #{ticket_id} marcado como RESUELTO y usuario notificado.")
