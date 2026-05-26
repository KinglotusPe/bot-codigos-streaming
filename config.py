"""
Configuration management for the Telegram Streaming Account Manager Bot.
Loads settings from environment variables.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
_owner_ids_str = os.getenv('OWNER_TELEGRAM_ID', '0')
OWNER_TELEGRAM_IDS = [int(i.strip()) for i in _owner_ids_str.split(',') if i.strip()]
OWNER_TELEGRAM_ID = OWNER_TELEGRAM_IDS[0] if OWNER_TELEGRAM_IDS else 0
OWNER_TELEGRAM_USERNAME = os.getenv('OWNER_TELEGRAM_USERNAME', '')

# Email Configuration
EMAIL_HOST = os.getenv('EMAIL_HOST', 'imap.gmail.com')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', 993))
EMAIL_USERNAME = os.getenv('EMAIL_USERNAME')
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')

# Database Configuration
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///bot_database.db')

# Subscription Settings
SUBSCRIPTION_DAYS = 30  # STRICT: Max 1 month per user/role

# Email Monitoring Settings
EMAIL_CHECK_INTERVAL = int(os.getenv('EMAIL_CHECK_INTERVAL', '5'))
PASSWORD_RESET_KEYWORDS = [
    'reset password',
    'password reset',
    'recuperar contraseña',
    'restablecer contraseña',
    'cambiar contraseña',
    'change password'
]

# AI Configuration
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

# Validation
def validate_config():
    """Validate that all required configuration is present."""
    errors = []
    
    if not TELEGRAM_BOT_TOKEN:
        errors.append("TELEGRAM_BOT_TOKEN is required")
    
    if not OWNER_TELEGRAM_ID or OWNER_TELEGRAM_ID == 0:
        errors.append("OWNER_TELEGRAM_ID is required")
    
    if not EMAIL_USERNAME:
        errors.append("EMAIL_USERNAME is required")
    
    if not EMAIL_PASSWORD:
        errors.append("EMAIL_PASSWORD is required")
    
    if errors:
        raise ValueError(f"Configuration errors:\n" + "\n".join(f"  - {e}" for e in errors))
    
    return True
