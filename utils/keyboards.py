"""
Keyboard templates for the Telegram bot.
Centralizes all button generation for a professional UI.
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def get_main_menu_keyboard(role: str) -> InlineKeyboardMarkup:
    """Generate the main menu keyboard based on user role."""
    keyboard = []
    
    if role == "superowner":
        keyboard = [
            [
                InlineKeyboardButton("👥 Staff", callback_data="staff_list"),
                InlineKeyboardButton("📊 Estadísticas", callback_data="stats")
            ],
            [
                InlineKeyboardButton("📧 Todos los Correos", callback_data="all_emails"),
                InlineKeyboardButton("🛠️ Herramientas", callback_data="owner_tools")
            ],
            [
                InlineKeyboardButton("📢 Enviar Spam", callback_data="spam_prompt"),
                InlineKeyboardButton("💾 Backup", callback_data="backup_db")
            ],
            [
                InlineKeyboardButton("🆘 Reportar Problema", callback_data="ticket_create"),
                InlineKeyboardButton("📘 Guías de Uso", callback_data="view_guides")
            ]
        ]
    elif role == "owner":
        keyboard = [
            [
                InlineKeyboardButton("👥 Staff", callback_data="staff_list"),
                InlineKeyboardButton("📊 Estadísticas", callback_data="stats")
            ],
            [
                InlineKeyboardButton("🩺 Salud Sistema", callback_data="health"),
                InlineKeyboardButton("🛠️ Herramientas", callback_data="owner_tools")
            ],
            [
                InlineKeyboardButton("📢 Mensaje Global", callback_data="spam_prompt"),
                InlineKeyboardButton("🆘 Reportar Problema", callback_data="ticket_create")
            ],
            [InlineKeyboardButton("📘 Guías", callback_data="view_guides")]
        ]
    elif role == "seller":
        keyboard = [
            [
                InlineKeyboardButton("➕ Agregar Admin", callback_data="add_admin_prompt"),
                InlineKeyboardButton("🛡️ Mis Admins", callback_data="staff_list")
            ],
            [
                InlineKeyboardButton("🆘 Reportar Problema", callback_data="ticket_create"),
                InlineKeyboardButton("👤 Mi Perfil", callback_data="my_profile")
            ],
            [InlineKeyboardButton("📘 Guías", callback_data="view_guides")]
        ]
    elif role == "admin":
        keyboard = [
            [
                InlineKeyboardButton("✉️ Mis Correos", callback_data="miscorreos"),
                InlineKeyboardButton("⏰ Por Vencer", callback_data="venc")
            ],
            [
                InlineKeyboardButton("➕ Asignar Usuario", callback_data="asig_prompt"),
                InlineKeyboardButton("🔄 Renovar", callback_data="renov_prompt")
            ],
            [
                InlineKeyboardButton("🆘 Reportar Problema", callback_data="ticket_create"),
                InlineKeyboardButton("👤 Mi Perfil", callback_data="my_profile")
            ],
            [InlineKeyboardButton("📘 Guías", callback_data="view_guides")]
        ]
    elif role == "user":
        keyboard = [
            [
                InlineKeyboardButton("📺 Mis Cuentas", callback_data="list"),
                InlineKeyboardButton("📜 Historial", callback_data="historial")
            ],
            [
                InlineKeyboardButton("🎁 Prueba Gratis", callback_data="prueba"),
                InlineKeyboardButton("👤 Mi Perfil", callback_data="my_profile")
            ],
            [
                InlineKeyboardButton("🆘 Reportar Problema", callback_data="ticket_create"),
                InlineKeyboardButton("❓ Ayuda", callback_data="view_guides")
            ]
        ]
    else:  # unknown
        keyboard = [
            [InlineKeyboardButton("🎁 Probar 2 Horas", callback_data="prueba")],
            [InlineKeyboardButton("🆔 Ver mi ID", callback_data="my_profile")],
            [InlineKeyboardButton("👨‍💻 Contactar Soporte", url="https://t.me/Kinglotusp")] # Replace with dynamic if possible
        ]
        
    return InlineKeyboardMarkup(keyboard)

def get_back_button(target: str = "main_menu") -> InlineKeyboardMarkup:
    """Return a keyboard with a single 'Back' button."""
    return InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Volver", callback_data=target)]])

def get_guides_keyboard() -> InlineKeyboardMarkup:
    """Keyboard for selecting guides."""
    keyboard = [
        [InlineKeyboardButton("📖 Manual de Usuario", callback_data="guide_user")],
        [InlineKeyboardButton("🛡️ Manual Admin", callback_data="guide_admin")],
        [InlineKeyboardButton("⬅️ Volver al Menú", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_inventory_platforms_keyboard() -> InlineKeyboardMarkup:
    """Keyboard for selecting a platform to view inventory (Option 2)."""
    from platform_config import get_supported_platforms
    platforms = get_supported_platforms()
    
    keyboard = []
    # Create buttons in pairs
    for i in range(0, len(platforms), 2):
        row = [InlineKeyboardButton(platforms[i].upper(), callback_data=f"inv_plat_{platforms[i]}")]
        if i + 1 < len(platforms):
            row.append(InlineKeyboardButton(platforms[i+1].upper(), callback_data=f"inv_plat_{platforms[i+1]}"))
        keyboard.append(row)
    
    keyboard.append([InlineKeyboardButton("📦 Ver Todo el Inventario", callback_data="all_emails_list")])
    keyboard.append([InlineKeyboardButton("⬅️ Volver", callback_data="main_menu")])
    return InlineKeyboardMarkup(keyboard)

def get_ticket_confirm_keyboard() -> InlineKeyboardMarkup:
    """Keyboard to confirm ticket creation."""
    keyboard = [
        [InlineKeyboardButton("✅ Confirmar Envío", callback_data="ticket_confirm")],
        [InlineKeyboardButton("❌ Cancelar", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)
