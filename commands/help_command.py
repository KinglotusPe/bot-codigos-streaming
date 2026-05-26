"""
Help command for the Telegram bot (Enhanced Version).
Command: /cmds
"""

from telegram import Update
from telegram.ext import ContextTypes
from utils.validators import get_user_role, get_owner_username
from utils.messages import HELP_SUPER_OWNER, HELP_OWNER, HELP_ADMIN, HELP_USER, HELP_UNKNOWN, HELP_SELLER


async def cmds(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Show help message based on user role with professional buttons.
    Command: /cmds or /start
    """
    from utils.keyboards import get_main_menu_keyboard
    import os
    
    user_id = update.effective_user.id
    role = get_user_role(user_id)
    from utils.validators import get_expiration_info
    exp_info = get_expiration_info(user_id)
    
    # Header for the menu
    welcome_msg = f"<b>🌟 BIENVENIDO AL SISTEMA DE STREAMING 🌟</b>\n\n"
    
    if role == "superowner":
        help_text = welcome_msg + f"👤 <b>Rol:</b> Super Owner 💎\n⏳ <b>Suscripción:</b> {exp_info}\n\nSelecciona una opción del panel de control:"
    elif role == "owner":
        help_text = welcome_msg + f"👤 <b>Rol:</b> Owner 👑\n⏳ <b>Suscripción:</b> {exp_info}\n\nSelecciona una opción del panel de control:"
    elif role == "seller":
        help_text = welcome_msg + f"👤 <b>Rol:</b> Seller 💼\n⏳ <b>Suscripción:</b> {exp_info}\n\nSelecciona una opción para gestionar:"
    elif role == "admin":
        help_text = welcome_msg + f"👤 <b>Rol:</b> Admin 🛡️\n⏳ <b>Suscripción:</b> {exp_info}\n\nSelecciona una acción:"
    elif role == "user":
        help_text = welcome_msg + f"👤 <b>Rol:</b> Usuario 🎬\n\nAccede a tus servicios desde los botones:"
    else:
        help_text = HELP_UNKNOWN
    
    keyboard = get_main_menu_keyboard(role)
    
    # Try to send with photo for extra professionalism
    photo_path = "bot_profile.png"
    if os.path.exists(photo_path):
        try:
            with open(photo_path, 'rb') as photo:
                await update.message.reply_photo(
                    photo=photo,
                    caption=help_text,
                    parse_mode='HTML',
                    reply_markup=keyboard
                )
            return
        except Exception:
            pass # Fallback to text message if photo fails
            
    await update.message.reply_text(
        help_text, 
        parse_mode='HTML',
        reply_markup=keyboard
    )
