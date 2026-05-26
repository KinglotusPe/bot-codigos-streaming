"""
User commands for the Telegram bot (Enhanced Version).
Now compatible with Option B (per-account expiration).
"""

from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import ContextTypes
from database import get_db_session
from models import User, StreamingAccount, CodeHistory, StatusEnum, Admin, Seller
from utils.validators import is_user, rate_limit, has_any_management_role
from utils.logger import log_action
from utils.messages import (
    ERROR_NOT_USER,
    NO_EMAILS_ASSIGNED
)
import config
import logging

logger = logging.getLogger(__name__)


async def user_me(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Shows the user's Telegram ID in a copyable format.
    Command: /me
    """
    user_id = update.effective_user.id
    from utils.validators import get_user_role
    role = get_user_role(user_id)
    
    if role == "unknown":
        await update.message.reply_text("❌ No tienes un rango activo en el sistema.")
        return
        
    from utils.keyboards import get_back_button
    text = (
        f"👤 **Tu Información:**\n\n"
        f"🆔 ID: <code>{user_id}</code> (Toca para copiar)\n"
        f"👤 Usuario: @{update.effective_user.username or 'N/A'}\n"
        f"🏅 Rango: {role.upper()}"
    )
    
    if update.callback_query:
        await update.callback_query.edit_message_text(text, parse_mode='HTML', reply_markup=get_back_button())
    else:
        await update.message.reply_text(text, parse_mode='HTML', reply_markup=get_back_button())


async def user_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Show all emails assigned to this user with individual expiration dates.
    Command: /list
    """
    user_id = update.effective_user.id
    
    if not rate_limit(user_id, "list", seconds=10):
        await update.message.reply_text("⏳ Por favor, espera 10 segundos antes de volver a listar tus cuentas.")
        return
    
    # We check if user exists in DB
    with get_db_session() as session:
        user = session.query(User).filter_by(user_id=user_id).first()
        if not user:
            await update.message.reply_text(ERROR_NOT_USER)
            return
        
        accounts = session.query(StreamingAccount).filter_by(
            assigned_to_user_id=user.id
        ).all()
        
        if not accounts:
            await update.message.reply_text(NO_EMAILS_ASSIGNED)
            return
        
        lines = ["📧 **Tus Cuentas Asignadas:**\n"]
        now = datetime.utcnow()
        
        for account in accounts:
            platform_emoji = "🎬"
            if "netflix" in account.platform_name.lower(): platform_emoji = "🎥"
            
            if account.expiration_date:
                days_remaining = (account.expiration_date - now).days
                date_str = account.expiration_date.strftime('%Y-%m-%d')
                
                if days_remaining >= 0:
                    lines.append(f"{platform_emoji} {account.platform_name.upper()} - `{account.email_address}`")
                    lines.append(f"   └ Expira en {days_remaining} día(s) ({date_str})")
                else:
                    lines.append(f"❌ {account.platform_name.upper()} - `{account.email_address}` (VENCIDO)")
            else:
                lines.append(f"{platform_emoji} {account.platform_name.upper()} - `{account.email_address}`")
        
        from utils.keyboards import get_back_button
        text = "\n".join(lines)
        if update.callback_query:
            await update.callback_query.edit_message_text(text, parse_mode='Markdown', reply_markup=get_back_button())
        else:
            await update.message.reply_text(text, parse_mode='Markdown', reply_markup=get_back_button())


async def user_historial(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Show code history for this user.
    Command: /historial
    """
    query = update.callback_query
    user_id = update.effective_user.id
    
    if not query and not rate_limit(user_id, "historial", seconds=20):
        await update.message.reply_text("⏳ Por favor, espera 20 segundos antes de volver a pedir el historial.")
        return
    
    if query:
        await query.answer()
        
    with get_db_session() as session:
        user = session.query(User).filter_by(user_id=user_id).first()
        if not user:
            msg = "❌ No tienes acceso al historial."
            if query: await query.edit_message_text(msg)
            else: await update.message.reply_text(msg)
            return
            
        history = session.query(CodeHistory).filter_by(
            user_id=user_id
        ).order_by(CodeHistory.sent_at.desc()).limit(10).all()
        
        if not history:
            msg = "ℹ️ No tienes historial de códigos aún."
            if query: await query.edit_message_text(msg)
            else: await update.message.reply_text(msg)
            return
        
        lines = ["📜 <b>HISTORIAL DE CÓDIGOS</b> (Últimos 10)\n"]
        
        for item in history:
            date_str = (item.sent_at - timedelta(hours=5)).strftime('%d/%m %H:%M')
            icon = "🎬"
            if "netflix" in item.platform_name.lower(): icon = "🎥"
            
            val = f"<code>{item.code_value}</code>" if item.code_type == 'otp' else f'<a href="{item.code_value}">Abrir Enlace</a>'
            lines.append(f"{icon} <b>{item.platform_name.upper()}</b>")
            lines.append(f"└ {val} | <i>{date_str}</i>\n")
        
        from utils.keyboards import get_back_button
        if query:
            await query.edit_message_text("\n".join(lines), parse_mode='HTML', disable_web_page_preview=True, reply_markup=get_back_button())
        else:
            await update.message.reply_text("\n".join(lines), parse_mode='HTML', disable_web_page_preview=True, reply_markup=get_back_button())


async def user_prueba(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Trial command: Gives 2 hours of access to a test account if available.
    One-time use per user.
    """
    user_id = update.effective_user.id
    
    if not rate_limit(user_id, "prueba", seconds=60):
        await update.message.reply_text("⏳ Por favor, espera un minuto.")
        return
        
    # Check role before opening the main session to avoid session closing issues
    if has_any_management_role(user_id) and not is_super_owner(user_id):
        with get_db_session() as session:
            admin_record = session.query(Admin).filter_by(user_id=user_id).first()
            if admin_record and admin_record.access_end_date < datetime.utcnow():
                await update.message.reply_text("❌ Tu periodo de prueba ya ha expirado.")
            else:
                await update.message.reply_text("ℹ️ Ya tienes un rango activo en el sistema.")
        return

    with get_db_session() as session:
        user = session.query(User).filter_by(user_id=user_id).first()
        admin_record = session.query(Admin).filter_by(user_id=user_id).first()

        if user and user.has_used_trial:
            await update.message.reply_text("❌ Ya has utilizado tu prueba gratuita.")
            return

        # Grant Temporary Admin Role
        expiry = datetime.utcnow() + timedelta(hours=2)
        
        # 1. Ensure User record exists and mark as used trial
        if not user:
            # Assign to SuperOwner as default admin
            from config import OWNER_TELEGRAM_ID
            owner_admin = session.query(Admin).filter_by(user_id=OWNER_TELEGRAM_ID).first()
            user = User(user_id=user_id, admin_id=owner_admin.id if owner_admin else None)
            user.has_used_trial = True
            session.add(user)
        else:
            user.has_used_trial = True
            
        # 2. Create or Update Admin record
        if not admin_record:
            from config import OWNER_TELEGRAM_ID
            admin_record = Admin(
                user_id=user_id,
                owner_id=OWNER_TELEGRAM_ID,
                access_end_date=expiry,
                status=StatusEnum.ACTIVE
            )
            session.add(admin_record)
        else:
            admin_record.access_end_date = expiry
            admin_record.status = StatusEnum.ACTIVE

        try:
            session.commit()
            
            log_action(user_id, "TRIAL_ADMIN_ACTIVATED", f"Trial admin granted until {expiry}")
            
            welcome_msg = (
                f"🎉 <b>¡BIENVENIDO A LA EXPERIENCIA PREMIUM!</b>\n\n"
                f"¡Nos alegra que quieras probar nuestro sistema! Para que veas todo el potencial del bot, "
                f"te hemos otorgado el rango de <b>ADMINISTRADOR TEMPORAL</b> por <b>2 horas</b>. 🚀\n\n"
                f"🛡️ <b>¡Ahora tienes el control!</b> Te invitamos a probar estas funciones:\n\n"
                f"1️⃣ <b>Registra tu cuenta:</b> Usa <code>/reg plataforma correo</code> (ej: /reg netflix micorreo@gmail.com).\n"
                f"2️⃣ <b>Asígnala a tu ID:</b> Usa <code>/asig {user_id} plataforma correo</code> (esto activará la extracción).\n"
                f"3️⃣ <b>¡La magia sucede!</b> Solicita un código en la plataforma y verás cómo el bot te lo entrega al instante aquí mismo.\n\n"
                f"📖 <b>¿Necesitas ayuda para configurar tu correo?</b>\n"
                f"• Usa el comando <code>/guia</code> para ver los manuales paso a paso.\n"
                f"• 💡 <i>Tip:</i> Puedes copiar la guía y pegarla en una IA (como ChatGPT) para que te guíe en el proceso.\n"
                f"• 👤 O contacta al <b>Admin, Seller o Owner</b> que te ofreció el bot para que te ayude a vincular tu cuenta.\n\n"
                f"⏰ <b>Tu prueba finaliza a las:</b> {expiry.strftime('%H:%M:%S')} UTC\n\n"
                f"Usa <code>/cmds</code> para descubrir todas tus nuevas herramientas. ¡Que disfrutes la prueba! ✨"
            )
            await update.message.reply_text(welcome_msg, parse_mode='HTML')
            
        except Exception as e:
            session.rollback()
            logger.error(f"Error activating trial admin: {e}")
            await update.message.reply_text("❌ Error al activar la prueba. Contacta al soporte.")


async def handle_ticket_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles the text input for a support ticket.
    """
    if not context.user_data.get('waiting_for_ticket'):
        return False # Not waiting for ticket, let other handlers process
        
    user_id = update.effective_user.id
    description = update.message.text
    
    if len(description) < 10:
        await update.message.reply_text("⚠️ Por favor, describe el problema con más detalle (mínimo 10 caracteres).")
        return True

    from database import get_db_session
    from models import Ticket, User, Admin, Seller
    from utils.keyboards import get_back_button
    import config

    with get_db_session() as session:
        # Create ticket
        ticket = Ticket(
            user_id=user_id,
            description=description,
            status="OPEN"
        )
        session.add(ticket)
        session.commit()
        ticket_id = ticket.id

        # Notify Owner and relevant Admin/Seller
        from utils.validators import get_user_role
        role = get_user_role(user_id)
        
        notify_msg = (
            f"🚨 **NUEVO TICKET DE SOPORTE #{ticket_id}**\n\n"
            f"👤 **Usuario:** @{update.effective_user.username or 'N/A'} (ID: <code>{user_id}</code>)\n"
            f"🏅 **Rango:** {role.upper()}\n"
            f"📝 **Problema:** {description}\n\n"
            f"<i>Usa /cerrar {ticket_id} para finalizar el caso.</i>"
        )
        
        # 1. Notify SuperOwner
        try:
            await context.bot.send_message(chat_id=config.OWNER_TELEGRAM_ID, text=notify_msg, parse_mode='HTML')
        except: pass
        
        # 2. Notify assigned Admin if exists
        user_record = session.query(User).filter_by(user_id=user_id).first()
        if user_record and user_record.admin_id:
            admin = session.query(Admin).get(user_record.admin_id)
            if admin and admin.user_id != config.OWNER_TELEGRAM_ID:
                try:
                    await context.bot.send_message(chat_id=admin.user_id, text=notify_msg, parse_mode='HTML')
                except: pass

    # Clear state
    context.user_data['waiting_for_ticket'] = False
    
    await update.message.reply_text(
        f"✅ **Ticket #{ticket_id} enviado con éxito.**\n\n"
        "Nuestro equipo técnico revisará tu caso y se pondrá en contacto contigo a la brevedad.",
        parse_mode='Markdown',
        reply_markup=get_back_button()
    )
    return True
