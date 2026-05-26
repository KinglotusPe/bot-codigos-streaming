from telegram import Update
from telegram.ext import ContextTypes
from utils.validators import is_admin
import config

async def guia(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Send the admin guide to the user.
    Command: /guia
    """
    user_id = update.effective_user.id
    
    # Check if user is admin (or owner)
    if not is_admin(user_id):
        await update.message.reply_text("❌ Este comando es solo para administradores.")
        return

    guide_text = f"""
📚 **GUÍA RÁPIDA PARA ADMINS**

**1. Configuración OBLIGATORIA (Solo una vez por cuenta):**
Para cada cuenta de streaming que vendas (ej: `netflix1@gmail.com`), debes configurar el reenvío de correos hacia:
👉 `{config.EMAIL_USERNAME}`

1. Entra al Gmail de la cuenta.
2. Configuración > Reenvío y correo POP/IMAP.
3. Añadir dirección de reenvío: `{config.EMAIL_USERNAME}`
4. Pide el código de confirmación al Owner (@{config.OWNER_TELEGRAM_USERNAME} | ID: `{config.OWNER_TELEGRAM_ID}`).
5. **ACTIVA** la opción "Reenviar una copia...".

---

**2. Comandos Diarios:**

🔹 **Registrar cuenta nueva:**
`/reg <plataforma> <correo>`
Ej: `/reg netflix netflix1@gmail.com`

🔹 **Vender/Asignar a cliente:**
`/asig <id_cliente> <plataforma> <correo>`
Ej: `/asig 123456789 netflix netflix1@gmail.com`
_(El cliente obtiene su ID con @userinfobot)_

🔹 **Ver mis cuentas:**
`/miscorreos`

🔹 **Renovar cliente (30 días más):**
`/renov <id_cliente>`

🔹 **Ver vencimientos próximos:**
`/venc`
"""
    from utils.keyboards import get_back_button
    if update.callback_query:
        await update.callback_query.edit_message_text(guide_text, parse_mode='Markdown', reply_markup=get_back_button())
    else:
        await update.message.reply_text(guide_text, parse_mode='Markdown', reply_markup=get_back_button())
