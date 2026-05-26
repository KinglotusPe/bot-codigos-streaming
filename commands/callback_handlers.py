"""
Callback query handlers for the Telegram bot.
Maps button clicks to their respective functions.
"""

from telegram import Update
from telegram.ext import ContextTypes
from commands.admin_commands import miscorreos, venc, asig, renov
from commands.user_commands import user_list, user_historial
from commands.owner_commands import allemails, stats, spam, staff, health, backup
from commands.guide_command import guia
from utils.keyboards import get_main_menu_keyboard, get_back_button, get_guides_keyboard
from utils.validators import get_user_role
import logging

logger = logging.getLogger(__name__)

async def universal_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Router for all inline button clicks."""
    query = update.callback_query
    data = query.data
    user_id = update.effective_user.id
    
    # Required for Telegram to stop the "loading" animation on the button
    await query.answer()
    
    # Map callback data to functions
    if data == "main_menu":
        from commands.help_command import cmds
        # Instead of calling cmds directly (which sends a new message), 
        # we try to edit the current one if possible
        role = get_user_role(user_id)
        from utils.validators import get_expiration_info
        exp_info = get_expiration_info(user_id)
        welcome_msg = f"<b>🌟 MENÚ PRINCIPAL 🌟</b>\n\n"
        
        # Determine text based on role (similar to cmds)
        if role == "superowner": help_text = welcome_msg + f"👤 <b>Rol:</b> Super Owner 💎\n⏳ <b>Suscripción:</b> {exp_info}"
        elif role == "owner": help_text = welcome_msg + f"👤 <b>Rol:</b> Owner 👑\n⏳ <b>Suscripción:</b> {exp_info}"
        elif role == "seller": help_text = welcome_msg + f"👤 <b>Rol:</b> Seller 💼\n⏳ <b>Suscripción:</b> {exp_info}"
        elif role == "admin": help_text = welcome_msg + f"👤 <b>Rol:</b> Admin 🛡️\n⏳ <b>Suscripción:</b> {exp_info}"
        elif role == "user": help_text = welcome_msg + f"👤 <b>Rol:</b> Usuario 🎬"
        else: help_text = welcome_msg + "❌ Acceso Restringido"
        
        keyboard = get_main_menu_keyboard(role)
        try:
            if query.message.caption:
                await query.edit_message_caption(caption=help_text, parse_mode='HTML', reply_markup=keyboard)
            else:
                await query.edit_message_text(text=help_text, parse_mode='HTML', reply_markup=keyboard)
        except Exception:
            await context.bot.send_message(chat_id=user_id, text=help_text, parse_mode='HTML', reply_markup=keyboard)

    elif data == "miscorreos":
        await miscorreos(update, context)
    elif data == "venc":
        await venc(update, context)
    elif data == "list":
        await user_list(update, context)
    elif data == "historial":
        await user_historial(update, context)
    elif data == "all_emails" or data == "all_emails_list":
        await allemails(update, context)
    elif data.startswith("inv_plat_"):
        await allemails(update, context)
    elif data == "stats":
        await stats(update, context)
    elif data == "staff_list":
        await staff(update, context)
    elif data == "health":
        await health(update, context)
    elif data == "backup_db":
        await backup(update, context)
    elif data == "prueba":
        from commands.user_commands import user_prueba
        await user_prueba(update, context)
    elif data == "my_profile":
        from commands.user_commands import user_me
        await user_me(update, context)
    elif data == "view_guides":
        keyboard = get_guides_keyboard()
        text = "<b>📘 CENTRO DE AYUDA Y GUÍAS</b>\n\nSelecciona el manual que deseas consultar:"
        try:
            if query.message.caption:
                await query.edit_message_caption(caption=text, parse_mode='HTML', reply_markup=keyboard)
            else:
                await query.edit_message_text(text=text, parse_mode='HTML', reply_markup=keyboard)
        except Exception:
            await query.message.reply_text(text, parse_mode='HTML', reply_markup=keyboard)

    elif data == "guide_user":
        # Simulate /guia command for users
        context.args = [] # No specific guide, just general
        await guia(update, context)
    elif data == "guide_admin":
        # In a real scenario, we'd pass a parameter or have a specific guide text
        await query.message.reply_text("🛡️ <b>Guía para Administradores:</b>\n\n1. Registra cuentas con /reg\n2. Asigna usuarios con /asig\n3. Controla vencimientos con /venc", parse_mode='HTML')
        
    elif data == "spam_prompt":
        await query.message.reply_text("📢 <b>Modo Difusión:</b>\n\nPara enviar un mensaje a todos los usuarios, usa el comando:\n<code>/spam tu mensaje aquí</code>", parse_mode='HTML', reply_markup=get_back_button())
    elif data == "owner_tools":
        text = "<b>🛠️ HERRAMIENTAS DE DUEÑO</b>\n\nUtiliza los siguientes comandos en el chat:\n\n" \
               "/addowner <code>id</code>\n/delowner <code>id</code>\n/addseller <code>id</code>\n" \
               "/delseller <code>id</code>\n/quitar <code>id</code>"
        await query.message.reply_text(text, parse_mode='HTML', reply_markup=get_back_button())
    elif data == "asig_prompt":
        await query.message.reply_text("➕ <b>Asignar Cuenta:</b>\n\nUsa el formato:\n<code>/asig id plataforma correo</code>", parse_mode='HTML', reply_markup=get_back_button())
    elif data == "renov_prompt":
        await query.message.reply_text("🔄 <b>Renovar Suscripción:</b>\n\nUsa el formato:\n<code>/renov id</code>", parse_mode='HTML', reply_markup=get_back_button())
    
    # Feature 3: Support / Tickets
    elif data == "ticket_create":
        context.user_data['waiting_for_ticket'] = True
        text = "🆘 **REPORTE DE PROBLEMA**\n\nPor favor, describe el problema detalladamente (ej: 'La cuenta netflix@gmail.com no me da el código').\n\nEscribe tu mensaje a continuación:"
        await query.edit_message_text(text, parse_mode='Markdown', reply_markup=get_back_button())

    elif data == "ticket_confirm":
        # This will be handled after the user sends the text
        pass

    else:
        logger.warning(f"Unhandled callback data: {data}")
