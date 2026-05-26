"""
Message templates for the Telegram bot.
All messages match the specification requirements.
"""

# Access Denied Messages
ACCESS_DENIED_USER_EXPIRED = (
    "⚠️ Acceso denegado. Tu periodo de suscripción ha expirado. "
    "Por favor, comunícate con el Owner para renovar tu acceso."
)

def access_denied_wrong_admin(email: str) -> str:
    """Message when admin tries to assign email registered by another admin."""
    return (
        f"❌ Error de asignación. No tienes permiso para asignar el correo {email} a un usuario. "
        f"Solo puedes asignar los correos que tú has registrado."
    )

# Expiration Notifications
def expiration_warning_admin(date: str) -> str:
    """Warning message for admin when access is about to expire."""
    return (
        f"🚨 Alerta de Vencimiento. Tu acceso como Admin expirará en 3 días (el {date}). "
        f"Contacta al Owner para extender tu permiso."
    )

def expiration_warning_user(date: str) -> str:
    """Warning message for user when subscription is about to expire."""
    return (
        f"🔔 Alerta de Suscripción. Tu acceso a la cuenta de streaming expira en 3 días (el {date}). "
        f"Contacta a tu Admin para renovar."
    )

# Success Messages
def command_success_assign_user(username: str, email: str, date: str) -> str:
    """Success message when user is assigned to streaming account."""
    return f"✅ Acción completada. El usuario {username} ha sido asignado a {email} hasta el {date}."

def command_success_renew_user(username: str, date: str) -> str:
    """Success message when user subscription is renewed."""
    return f"✅ Suscripción Renovada. El acceso de {username} ha sido extendido por 30 días, hasta el {date}."

def command_success_add_admin(username: str, date: str) -> str:
    """Success message when admin is added."""
    return f"✅ Admin agregado. El usuario {username} tiene acceso hasta el {date}."

def command_success_remove_admin(username: str) -> str:
    """Success message when admin is removed."""
    return f"✅ Admin removido. El acceso de {username} ha sido revocado."

def command_success_register_email(email: str) -> str:
    """Success message when email is registered."""
    return f"✅ Correo registrado. La cuenta {email} ha sido añadida a tu lista."

# Error Messages
ERROR_NOT_OWNER = "❌ Este comando solo está disponible para el Owner."
ERROR_NOT_ADMIN = "❌ Este comando solo está disponible para Admins."
ERROR_NOT_USER = "❌ Este comando solo está disponible para Usuarios."
ERROR_ADMIN_INACTIVE = "❌ Tu acceso como Admin ha expirado. Contacta al Owner."
ERROR_USER_INACTIVE = "❌ Tu acceso ha expirado. Contacta a tu Admin."
ERROR_INVALID_EMAIL = "❌ El formato del correo electrónico no es válido."
ERROR_EMAIL_EXISTS = "❌ Este correo ya está registrado en el sistema."
ERROR_EMAIL_NOT_FOUND = "❌ Este correo no existe en el sistema."
ERROR_USER_NOT_FOUND = "❌ Usuario no encontrado."
ERROR_ADMIN_NOT_FOUND = "❌ Admin no encontrado."
ERROR_INVALID_DAYS = "❌ El periodo debe ser exactamente 30 días."
ERROR_INVALID_FORMAT = "❌ Formato de comando incorrecto. Usa /help para ver la sintaxis correcta."

# Help Messages
HELP_SUPER_OWNER = """
💎 <b>PANEL DE CONTROL - DUEÑO TOTAL</b>

<b>Gestión de Jerarquía:</b>
/addowner <code>id</code> - Crear un nuevo Owner
/delowner <code>id</code> - Eliminar un Owner
/addadmin <code>id</code> - Crear Administrador
/addseller <code>id</code> - Crear Vendedor
/deladmin <code>id</code> - Eliminar Administrador
/delseller <code>id</code> - Eliminar Vendedor
/quitar <code>id</code> - Revocar TODOS los accesos

<b>Administración Global:</b>
/allemails <code>[plataforma]</code> <code>[libres/ocupados]</code>
/staff - Ver lista del equipo
/backup - Obtener respaldo de la DB
/health - Ver estado del sistema
/audit - Ver registros de actividad
/spam <code>mensaje</code> - Mensaje a todos los usuarios
/settrial <code>plat</code> <code>email</code> - Marcar cuenta para pruebas
/guia - Ver manuales
/me - Ver mi ID de Telegram

<b>Acceso rápido:</b>
/cmds - Mostrar este menú
"""

HELP_OWNER = """
👑 <b>PANEL DE CONTROL - OWNER</b>

<b>Gestión de Usuarios:</b>
/addadmin <code>id</code> - Agregar Administrador
/addseller <code>id</code> - Agregar Vendedor

<b>Administración:</b>
/allemails - Ver todos los correos
/staff - Ver lista del equipo
/health - Ver estado del sistema
/spam <code>mensaje</code> - Mensaje global
/settrial <code>plat</code> <code>email</code> - Marcar cuenta para pruebas
/guia - Ver guías
/me - Ver mi ID de Telegram

<b>Acceso rápido:</b>
/cmds - Mostrar este menú
"""

HELP_ADMIN = """
🛡️ <b>PANEL DE CONTROL - ADMIN</b>

<b>Gestión de Cuentas:</b>
/reg <code>plataforma</code> <code>correo</code> - Registrar cuenta
/miscorreos - Ver tus cuentas registradas
/asig <code>id</code> <code>plataforma</code> <code>correo</code> - Asignar a usuario

<b>Suscripciones:</b>
/renov <code>id</code> - Renovar usuario (30 días)
/venc - Ver usuarios por vencer (7 días)

<b>Utilidades:</b>
/settrial <code>plat</code> <code>email</code> - Marcar para pruebas
/guia - Ver guías de configuración
/me - Ver mi ID de Telegram
/cmds - Mostrar este menú
"""

HELP_SELLER = """
💼 <b>PANEL DE CONTROL - SELLER</b>

<b>Gestión de Equipo:</b>
/addadmin <code>id</code> - Agregar Administrador
/deladmin <code>id</code> - Quitar Administrador

<b>Utilidades:</b>
/guia - Ver manuales
/me - Ver mi ID de Telegram
/cmds - Mostrar este menú
"""

HELP_USER = """
👤 <b>MI PORTAFOLIO - USUARIO</b>

<b>Mis Accesos:</b>
/list - Ver mis cuentas (10s limit)
/historial - Ver últimos códigos (20s limit)
/prueba - Obtener 2 horas de prueba GRATIS
/me - Ver mi ID de Telegram
/cmds - Mostrar este menú
"""

HELP_UNKNOWN = """
❌ <b>ACCESO RESTRINGIDO</b>

No tienes un rango activo en el sistema. 

<b>¿Cómo obtener acceso?</b>
1️⃣ Usa /me para ver tu ID de Telegram.
2️⃣ Envía ese ID a un Administrador o Vendedor.
3️⃣ Una vez te den de alta, usa /cmds para ver tus herramientas.

🔸 <i>También puedes usar /prueba para obtener 2 horas de acceso temporal.</i>
"""

# Email Forwarding Messages
def email_forwarded(service: str, link: str) -> str:
    """Message when password reset link is forwarded to user."""
    return (
        f"🔐 **Enlace de Restablecimiento de Contraseña**\n\n"
        f"Servicio: {service}\n"
        f"Enlace: {link}\n\n"
        f"⚠️ Este enlace expirará pronto. Úsalo inmediatamente."
    )

# List Messages
def email_list_item_assigned(email: str, username: str) -> str:
    """Format for email list item that is assigned."""
    return f"✉️ {email} - Asignado a {username}"

def email_list_item_unassigned(email: str) -> str:
    """Format for email list item that is not assigned."""
    return f"✉️ {email} - Sin asignar"

def user_email_list_item_active(email: str, days_remaining: int, date: str) -> str:
    """Format for user's email list item that is active."""
    return f"📧 {email} - Expira en {days_remaining} días ({date})"

def user_email_list_item_expired(email: str) -> str:
    """Format for user's email list item that is expired."""
    return f"⚠️ {email} - VENCIDO"

NO_EMAILS_REGISTERED = "ℹ️ No tienes correos registrados aún."
NO_EMAILS_ASSIGNED = "ℹ️ No tienes correos asignados aún."
