"""
Platform-specific email detection configuration.
Defines patterns for different streaming platforms to detect security emails.
"""

# Platform detection patterns
PLATFORM_PATTERNS = {
    'netflix': {
        'senders': ['info@account.netflix.com', 'info@mailer.netflix.com', 'noreply@netflix.com'],
        'subject_keywords': ['reset password', 'password reset', 'verification code', 'security code', 'código', 'codigo', 'restablecer', 'recuperar'],
        'otp_pattern': r'>\s*(\d{4,6})\s*<',  # Match isolated number between tags
        'link_pattern': r'https://www\.netflix\.com/(?:password|reset|restablecer|verify)[^\s<>"]*'
    },
    'hbo': {
        'senders': ['noreply@hbomax.com', 'info@hbomax.com', 'hbo@email.hbomax.com', 'max@max.com', 'noreply@max.com', 'alerts.hbomax.com'],
        'subject_keywords': ['reset password', 'password reset', 'verification', 'código de verificación', 'código de un solo uso', 'codigo', 'código', 'urgente', 'tu codigo', 'tu código'],
        'otp_pattern': r'\b(\d{6})\b',  # 6-digit code
        'link_pattern': r'https://[^\s<>"]*(?:hbomax|max)\.com[^\s<>"]+(?:reset|verify|password)[^\s<>"]*'
    },
    'disney': {
        'senders': ['DisneyPlus@email.disneyplus.com', 'noreply@disneyplus.com'],
        'subject_keywords': ['reset password', 'password reset', 'verification code', 'security', 'código', 'codigo'],
        'otp_pattern': r'\b(\d{6})\b',
        'link_pattern': r'https://[^\s<>"]*disneyplus\.com[^\s<>"]+(?:reset|verify|password)[^\s<>"]*'
    },
    'prime': {
        'senders': ['primevideo@amazon.com', 'no-reply@amazon.com', 'account-update@amazon.com'],
        'subject_keywords': ['reset password', 'password reset', 'verification code', 'one-time password', 'código', 'codigo'],
        'otp_pattern': r'\b(\d{6})\b',
        'link_pattern': r'https://[^\s<>"]*amazon\.com[^\s<>"]+(?:reset|verify|password|ap/signin)[^\s<>"]*'
    },
    'spotify': {
        'senders': ['no-reply@spotify.com', 'noreply@spotify.com'],
        'subject_keywords': ['reset password', 'password reset', 'verification', 'security code', 'código', 'codigo'],
        'otp_pattern': r'\b(\d{6})\b',
        'link_pattern': r'https://[^\s<>"]*spotify\.com[^\s<>"]+(?:reset|verify|password)[^\s<>"]*'
    },
    'youtube': {
        'senders': ['noreply@youtube.com', 'noreply-youtube@google.com'],
        'subject_keywords': ['reset password', 'password reset', 'verification code', 'google verification', 'código', 'codigo'],
        'otp_pattern': r'\b([A-Z0-9]{6})\b',
        'link_pattern': r'https://[^\s<>"]*(?:youtube|google)\.com[^\s<>"]+(?:reset|verify|password)[^\s<>"]*'
    },
    'apple': {
        'senders': ['appleid@id.apple.com', 'noreply@email.apple.com'],
        'subject_keywords': ['reset password', 'password reset', 'verification code', 'apple id', 'código', 'codigo'],
        'otp_pattern': r'\b(\d{6})\b',
        'link_pattern': r'https://[^\s<>"]*apple\.com[^\s<>"]+(?:reset|verify|password|iforgot)[^\s<>"]*'
    },
    'crunchyroll': {
        'senders': ['noreply@crunchyroll.com', 'support@crunchyroll.com'],
        'subject_keywords': ['reset password', 'password reset', 'verification', 'código', 'codigo'],
        'otp_pattern': r'\b([A-Z0-9]{6})\b',
        'link_pattern': r'https://[^\s<>"]*crunchyroll\.com[^\s<>"]+(?:reset|verify|password)[^\s<>"]*'
    },
    'paramount': {
        'senders': ['noreply@paramountplus.com', 'info@paramountplus.com'],
        'subject_keywords': ['reset password', 'password reset', 'verification code', 'código', 'codigo'],
        'otp_pattern': r'\b(\d{6})\b',
        'link_pattern': r'https://[^\s<>"]*paramountplus\.com[^\s<>"]+(?:reset|verify|password)[^\s<>"]*'
    },
    'other': {
        # Generic fallback for unlisted platforms
        'senders': [],
        'subject_keywords': [
            'reset password', 'password reset', 'verification code', 'security code', 'otp', 
            'código', 'codigo', 'confirm', 'confirmar', 'access', 'acceso', 'login', 
            'inicio de sesión', 'verify', 'verificar', 'one-time', 'un solo uso'
        ],
        'otp_pattern': r'\b([A-Z0-9]{4,8})\b',  # 4-8 character code
        'link_pattern': r'https?://[^\s<>"]+(?:reset|password|verify|recuperar|restablecer|confirm)[^\s<>"]*'
    }
}


GLOBAL_EXCLUSIONS = [
    'cambio de correo', 'change email', 'update email', 'actualizar correo',
    'cambio de email', 'email change', 'nuevo correo', 'new email'
]


def get_platform_config(platform_name: str) -> dict:
    """
    Get platform-specific configuration.
    
    Args:
        platform_name: Name of the platform (case-insensitive)
        
    Returns:
        Dictionary with platform patterns
    """
    platform_key = platform_name.lower()
    return PLATFORM_PATTERNS.get(platform_key, PLATFORM_PATTERNS['other'])


def is_security_email(sender: str, subject: str, platform_name: str) -> bool:
    """
    Check if email is a security-related email for the platform.
    
    Args:
        sender: Email sender address
        subject: Email subject line
        platform_name: Platform name
        
    Returns:
        True if security email, False otherwise
    """
    config = get_platform_config(platform_name)
    subject_lower = subject.lower()
    
    # 1. Check exclusions first
    if any(ex in subject_lower for ex in GLOBAL_EXCLUSIONS):
        return False
    
    # 2. Check sender (if platform has specific senders)
    if config['senders']:
        sender_match = any(allowed_sender.lower() in sender.lower() for allowed_sender in config['senders'])
        if sender_match:
            # If sender matches, we accept it (unless it was excluded above)
            # This fulfills "recognize any email from registered platforms"
            return True
    
    # 3. Fallback: Check subject keywords (for 'other' platform or if sender check failed/skipped)
    keyword_match = any(keyword in subject_lower for keyword in config['subject_keywords'])
    
    return keyword_match


def get_supported_platforms() -> list:
    """Get list of supported platform names."""
    return [p for p in PLATFORM_PATTERNS.keys() if p != 'other']
