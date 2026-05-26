"""
Email monitoring system for password reset and OTP forwarding.
Monitors IMAP inbox for security emails and forwards links/codes to authorized users.
"""

import re
import time
import email
import email.utils
import asyncio
import imaplib
import ssl
import socket
from email.header import decode_header
from datetime import datetime, timedelta
from imapclient import IMAPClient
# Removed InlineKeyboardButton, InlineKeyboardMarkup as they are no longer used
import config
from database import get_db_session
from models import StreamingAccount, User, StatusEnum, Owner, CodeHistory
from utils.messages import ACCESS_DENIED_USER_EXPIRED
from utils.ai_parser import AIEmailParser
from platform_config import get_platform_config, is_security_email, get_supported_platforms
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EmailMonitor:
    """Monitors email inbox for security messages (password resets and OTP codes)."""
    
    def __init__(self, bot_instance=None, loop=None):
        """
        Initialize email monitor.
        
        Args:
            bot_instance: Telegram bot instance for sending messages
            loop: Asyncio event loop of the bot
        """
        self.bot = bot_instance
        self.loop = loop
        self.imap_client = None
        self.running = False
        self.processed_ids = set()
        self.ai_parser = AIEmailParser()
        self.last_check = datetime.utcnow()
    
    def connect(self):
        """Establish IMAP connection."""
        try:
            self.imap_client = IMAPClient(config.EMAIL_HOST, port=config.EMAIL_PORT, ssl=True)
            self.imap_client.login(config.EMAIL_USERNAME, config.EMAIL_PASSWORD)
            self.imap_client.select_folder('INBOX')
            logger.info("✅ Connected to email server")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to connect to email server: {e}")
            return False
    
    def disconnect(self):
        """Close IMAP connection."""
        if self.imap_client:
            try:
                self.imap_client.logout()
                logger.info("📧 Disconnected from email server")
            except:
                pass
            self.imap_client = None

    def extract_security_content(self, email_body: str, platform_name: str, sender: str = "", subject: str = "") -> dict:
        """
        Extract security content (links and OTP codes) from email body.
        Uses AI if available, falls back to Regex.
        
        Args:
            email_body: Email body text
            platform_name: Platform name for specific patterns
            sender: Email sender (for AI context)
            subject: Email subject (for AI context)
            
        Returns:
            Dictionary with 'link' and 'otp' keys
        """
        import html
        
        # 1. Try AI Parsing first
        if self.ai_parser.model:
            logger.info("🤖 Attempting AI extraction...")
            ai_result = self.ai_parser.parse_email(sender, subject, email_body)
            
            if ai_result.get('type') != 'ERROR':
                # Check for Email Change (Security Risk)
                if ai_result.get('type') == 'EMAIL_CHANGE':
                    logger.warning("⛔ AI detected Email Change request - IGNORING")
                    return {'link': '', 'otp': ''}
                
                # Check if we got useful content
                if ai_result.get('code') or ai_result.get('link'):
                    logger.info(f"✅ AI Success: Type={ai_result['type']}, Code={ai_result['code']}")
                    return {
                        'link': ai_result.get('link', ''),
                        'otp': ai_result.get('code', '')
                    }
            
            logger.info("⚠️ AI could not extract content, falling back to Regex")

        # 2. Fallback to Regex (Original Logic)
        platform_config = get_platform_config(platform_name)
        result = {'link': '', 'otp': ''}
        
        # Strip HTML tags for cleaner regex matching (EXCEPT for Netflix, which uses tags for isolation)
        if platform_name == 'netflix':
            clean_body = email_body
        else:
            clean_body = re.sub(r'<[^>]+>', ' ', email_body)
        
        # Extract reset link
        link_matches = re.findall(platform_config['link_pattern'], email_body, re.IGNORECASE)
        if link_matches:
            clean_link = html.unescape(link_matches[0])
            result['link'] = clean_link.rstrip('.,;)')
        
        # Extract OTP code
        otp_matches = re.findall(platform_config['otp_pattern'], clean_body, re.IGNORECASE)
        if otp_matches:
            valid_matches = [m for m in otp_matches if m not in ['000000', '123456', '232323']]
            if valid_matches:
                result['otp'] = valid_matches[0]
        
        return result

    def get_email_body(self, msg) -> str:
        """
        Extract email body from message.
        Improved to handle HTML multipart emails from HBO Max, Netflix, etc.
        
        Args:
            msg: Email message object
            
        Returns:
            Email body as string
        """
        body = ""
        html_body = ""
        
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition", ""))
                
                # Skip attachments
                if "attachment" in content_disposition:
                    continue
                
                try:
                    payload = part.get_payload(decode=True)
                    if not payload:
                        continue
                    
                    # Decode with proper charset
                    charset = part.get_content_charset() or 'utf-8'
                    try:
                        decoded = payload.decode(charset, errors='replace')
                    except (UnicodeDecodeError, LookupError):
                        # Try common encodings
                        for enc in ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252']:
                            try:
                                decoded = payload.decode(enc, errors='replace')
                                break
                            except:
                                continue
                        else:
                            decoded = payload.decode('utf-8', errors='replace')
                    
                    if content_type == "text/plain":
                        body = decoded
                    elif content_type == "text/html":
                        html_body = decoded
                except Exception as e:
                    logger.debug(f"Failed to decode part {content_type}: {e}")
                    pass
        else:
            try:
                payload = msg.get_payload(decode=True)
                if payload:
                    charset = msg.get_content_charset() or 'utf-8'
                    try:
                        body = payload.decode(charset, errors='replace')
                    except (UnicodeDecodeError, LookupError):
                        body = payload.decode('utf-8', errors='replace')
            except:
                pass
        
        # Prefer HTML if plain text is empty (common for HBO Max, Netflix security emails)
        if html_body and not body:
            logger.debug(f"Using HTML body (no plain text), length: {len(html_body)}")
            return html_body
        elif html_body and len(html_body) > len(body) * 2:
            logger.debug(f"Using HTML body (much longer than plain text)")
            return html_body
        elif body:
            logger.debug(f"Using plain text body, length: {len(body)}")
            return body
        elif html_body:
            logger.debug(f"Using HTML body as fallback, length: {len(html_body)}")
            return html_body
        
        logger.warning("⚠️  No body content found!")
        return ""
    
    def extract_original_recipient(self, msg, body: str) -> str:
        """
        Extract original recipient from forwarded email.
        Supports Gmail, Outlook, Yahoo, and other forwarding formats.
        
        Args:
            msg: Email message object
            body: Email body text
            
        Returns:
            Original recipient email address or empty string
        """
        owner_email = config.EMAIL_USERNAME.lower() if config.EMAIL_USERNAME else ""
        
        # Helper to validate email is not owner's email
        def is_valid_recipient(email_addr):
            if not email_addr:
                return False
            email_addr = email_addr.lower()
            # Ignore owner's email
            if email_addr == owner_email:
                return False
            # Ignore common system emails
            if any(x in email_addr for x in ['noreply', 'no-reply', 'info@', 'support@', 'mailer', 'google.com']):
                return False
            return True

        # Pattern 0: Check Delivered-To header
        if msg.get('Delivered-To'):
            delivered_to = msg.get('Delivered-To')
            email_match = re.search(r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', delivered_to)
            if email_match:
                candidate = email_match.group(1).lower()
                if is_valid_recipient(candidate):
                    return candidate

        # Pattern 1: Check X-Forwarded-For header (CRITICAL for Gmail auto-forwarding)
        if msg.get('X-Forwarded-For'):
            forwarded_for = msg.get('X-Forwarded-For')
            logger.info(f"📧 X-Forwarded-For: {forwarded_for}")
            # X-Forwarded-For usually has format: "original@gmail.com destination@gmail.com"
            candidates = re.findall(r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', forwarded_for)
            for candidate in candidates:
                if is_valid_recipient(candidate):
                    logger.info(f"✅ Found recipient via X-Forwarded-For: {candidate}")
                    return candidate.lower()

        # Pattern 2: Check To header
        direct_recipient = msg.get('To', '')
        if direct_recipient:
            candidates = re.findall(r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', direct_recipient)
            for candidate in candidates:
                if is_valid_recipient(candidate):
                    return candidate.lower()
        
        # Pattern 3: Gmail forward format in body
        gmail_patterns = [
            r'---------- Forwarded message ---------[\s\S]{0,500}?To:\s*<?([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})>?',
            r'---------- Mensaje reenviado ---------[\s\S]{0,500}?Para:\s*<?([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})>?',
        ]
        
        for pattern in gmail_patterns:
            matches = re.findall(pattern, body, re.IGNORECASE)
            if matches:
                for match in matches:
                    if is_valid_recipient(match):
                        return match.lower()
        
        # Pattern 4: Extract ALL emails from body and check against database
        all_emails = re.findall(r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', body)
        if all_emails:
            unique_emails = list(set([e.lower() for e in all_emails]))
            
            with get_db_session() as session:
                for email_addr in unique_emails:
                    if is_valid_recipient(email_addr):
                        # Check if this email is in our database
                        account = session.query(StreamingAccount).filter_by(
                            email_address=email_addr
                        ).first()
                        if account:
                            logger.info(f"✅ Found recipient via database match: {email_addr}")
                            return email_addr
        
        logger.warning(f"❌ Could not extract recipient. To: {msg.get('To')}, Delivered-To: {msg.get('Delivered-To')}")
        return ""
    
    def validate_and_forward(self, recipient_email: str, security_content: dict, platform_name: str):
        """
        Validate user access and forward security content.
        
        Args:
            recipient_email: Email address of the streaming account
            security_content: Dictionary with 'link' and 'otp' keys
            platform_name: Platform name
        """
        logger.info(f"🔍 VALIDATION: Email={recipient_email}, Platform={platform_name}")
        
        with get_db_session() as session:
            # Find streaming account by email AND platform
            account = session.query(StreamingAccount).filter_by(
                email_address=recipient_email,
                platform_name=platform_name
            ).first()
            
            if not account:
                # Fallback to just email if specific platform not found
                account = session.query(StreamingAccount).filter_by(
                    email_address=recipient_email
                ).first()
            
            if not account:
                logger.warning(f"❌ Account not found: {recipient_email} + {platform_name}")
                return
            
            # Check if account is assigned to a user
            if not account.assigned_to_user_id:
                logger.warning(f"❌ Account not assigned: {recipient_email}")
                return
            
            # Get user details
            user = session.query(User).filter_by(id=account.assigned_to_user_id).first()
            
            if not user:
                logger.error(f"❌ User not found for account: {account.assigned_to_user_id}")
                return
            
            # Validate user status
            if user.status != StatusEnum.ACTIVE:
                logger.warning(f"❌ User inactive: {user.user_id}")
                return
            
            # Validate account expiration (Option B)
            if account.expiration_date and account.expiration_date < datetime.utcnow():
                logger.warning(f"❌ Account expired for user {user.user_id}: {recipient_email}")
                if self.bot and self.loop:
                    asyncio.run_coroutine_threadsafe(self.send_access_denied(user.user_id), self.loop)
                return
            
            # Anti-Abuse Check (Option 6)
            from utils.validators import check_abuse
            if check_abuse(user.user_id):
                logger.warning(f"⛔ Abuse detected for user {user.user_id}")
                if self.bot and self.loop:
                    asyncio.run_coroutine_threadsafe(
                        self.bot.send_message(
                            chat_id=user.user_id, 
                            text="⚠️ **ALERTA DE SEGURIDAD**\n\nHas solicitado demasiados códigos en poco tiempo. Por seguridad, se ha bloqueado esta entrega y tu cuenta ha sido reportada para revisión."
                        ),
                        self.loop
                    )
                return

            # Update Health Info (Option 7)
            account.last_email_at = datetime.utcnow()
            session.commit()
            
            # Forward content to user
            if self.bot and self.loop:
                logger.info(f"📤 Forwarding to Telegram user {user.user_id}")
                asyncio.run_coroutine_threadsafe(self.send_security_content(user.user_id, platform_name, security_content), self.loop)
            else:
                logger.error("❌ Bot instance or loop not available!")
    
    async def send_access_denied(self, user_id: int):
        """Send access denied message with contact button."""
        with get_db_session() as session:
            owner = session.query(Owner).first()
            owner_username = owner.telegram_username if owner and owner.telegram_username else None
        
        message = ACCESS_DENIED_USER_EXPIRED
        
        await self.bot.send_message(chat_id=user_id, text=message)
    
    async def send_security_content(self, user_id: int, platform_name: str, content: dict):
        """Send security content (link and/or OTP) to user."""
        logger.info(f"📨 Sending to user {user_id}")
        
        import html
        
        parts = [f"🔐 <b>{html.escape(platform_name.title())} - Código de Seguridad</b>\n"]
        
        if content.get('otp'):
            parts.append(f"<b>Código OTP:</b> <code>{html.escape(content['otp'])}</code>")
            logger.info(f"   - OTP: {content['otp']}")
        
        if content.get('link'):
            parts.append(f"\n<b>Enlace:</b> {html.escape(content['link'])}")
            logger.info(f"   - Link included")
        
        if not content.get('otp') and not content.get('link'):
            parts.append("No se pudo extraer el código o enlace.")
        
        parts.append("\n⚠️ Este código/enlace expirará pronto. Úsalo inmediatamente.")
        
        message = "\n".join(parts)
        
        try:
            await self.bot.send_message(
                chat_id=user_id,
                text=message,
                parse_mode='HTML',
                disable_web_page_preview=True
            )
            logger.info(f"✅ Message sent to user {user_id}")
        except Exception as e:
            logger.error(f"❌ Failed to send to user {user_id}: {e}")
        
        # Save to code history
        with get_db_session() as session:
            user = session.query(User).filter_by(user_id=user_id).first()
            if user:
                account = session.query(StreamingAccount).filter_by(
                    assigned_to_user_id=user.id,
                    platform_name=platform_name
                ).first()
                
                email_address = account.email_address if account else "unknown"
                
                # Save OTP if present
                if content.get('otp'):
                    history = CodeHistory(
                        user_id=user_id,
                        platform_name=platform_name,
                        email_address=email_address,
                        code_type='otp',
                        code_value=content['otp']
                    )
                    session.add(history)
                
                # Save link if present
                if content.get('link'):
                    history = CodeHistory(
                        user_id=user_id,
                        platform_name=platform_name,
                        email_address=email_address,
                        code_type='link',
                        code_value=content['link']
                    )
                    session.add(history)
                
                session.commit()

    def process_new_emails(self):
        """Process new unread emails in inbox."""
        try:
            # Refresh connection to see new messages
            self.last_check = datetime.utcnow()
            self.imap_client.noop()
            
            # Search for emails from today AND unread
            since_date = datetime.now().date()
            messages = self.imap_client.search(['SINCE', since_date, 'UNSEEN'])
            
            if not messages:
                return
            
            # Only look at the last 20 messages to avoid processing the whole day's inbox every time
            recent_messages = messages[-20:]
            
            # Filter for messages we haven't processed yet in this session
            new_messages = [mid for mid in recent_messages if mid not in self.processed_ids]
            
            if not new_messages:
                return
            
            logger.info(f"\n{'='*60}")
            logger.info(f"📬 Processing {len(new_messages)} new/unprocessed email(s)")
            logger.info(f"{'='*60}")
            
            # Fetch email data
            for idx, msg_id in enumerate(new_messages, 1):
                # Add to processed list immediately
                self.processed_ids.add(msg_id)
                
                try:
                    logger.info(f"\n📧 Email {idx}/{len(new_messages)} (ID: {msg_id})")
                    
                    raw_message = self.imap_client.fetch([msg_id], ['RFC822'])
                    email_data = raw_message[msg_id][b'RFC822']
                    msg = email.message_from_bytes(email_data)
                    
                    # Check email date to avoid processing old emails (even if they are from today)
                    if msg['Date']:
                        try:
                            email_date = email.utils.parsedate_to_datetime(msg['Date'])
                            # Convert to offset-naive UTC for comparison if needed, or just compare timestamps
                            if email_date.tzinfo:
                                email_date = email_date.astimezone(datetime.now().astimezone().tzinfo).replace(tzinfo=None)
                            
                            now = datetime.now()
                            # If email is older than 10 minutes, skip it
                            if now - email_date > timedelta(minutes=10):
                                logger.info(f"⏳ Email is too old ({email_date}), skipping...")
                                continue
                        except Exception as e:
                            logger.warning(f"⚠️ Could not parse date: {e}")
                    
                    # Get subject
                    subject = ""
                    if msg['Subject']:
                        decoded_subject = decode_header(msg['Subject'])[0]
                        if isinstance(decoded_subject[0], bytes):
                            subject = decoded_subject[0].decode(decoded_subject[1] or 'utf-8')
                        else:
                            subject = decoded_subject[0]
                    
                    sender = msg.get('From', '')
                    
                    logger.info(f"From: {sender}")
                    logger.info(f"Subject: {subject}")
                    
                    # Extract email body
                    body = self.get_email_body(msg)
                    logger.info(f"Body length: {len(body)} chars")
                    
                    # Get recipient
                    recipient = self.extract_original_recipient(msg, body)
                    
                    if not recipient:
                        logger.warning(f"⚠️  Could not extract recipient")
                        continue
                    
                    logger.info(f"✅ Recipient: {recipient}")
                    
                    # 1. Detect platform from email content first
                    detected_platform = None
                    supported_platforms = get_supported_platforms()
                    
                    for platform in supported_platforms:
                        if is_security_email(sender, subject, platform):
                            detected_platform = platform
                            logger.info(f"🎯 Detected platform from content: {detected_platform}")
                            break
                    
                    # 2. Find account in database
                    with get_db_session() as session:
                        account = None
                        
                        if detected_platform:
                            # If we detected the platform, look for that specific account
                            account = session.query(StreamingAccount).filter_by(
                                email_address=recipient,
                                platform_name=detected_platform
                            ).first()
                        
                        # Fallback: If no platform detected or account not found for detected platform,
                        # try to find ANY account with this email (legacy behavior)
                        if not account:
                            account = session.query(StreamingAccount).filter_by(
                                email_address=recipient
                            ).first()
                            
                            if account and not detected_platform:
                                # If we found an account but didn't detect platform, assume it's the account's platform
                                detected_platform = account.platform_name
                                logger.info(f"⚠️ Platform not detected from content, assuming: {detected_platform}")

                        if not account:
                            logger.info(f"❌ No account found for email: {recipient}")
                            continue
                            
                        platform_name = account.platform_name
                        
                        # Double check if the email matches the platform (if we fell back to account lookup)
                        if not is_security_email(sender, subject, platform_name):
                            logger.info(f"📋 Not a security email for {platform_name}, ignoring")
                            continue
                            
                        logger.info(f"✅ Security email confirmed for {platform_name}!")
                        
                        # Extract content

                        # Extract content
                        security_content = self.extract_security_content(body, platform_name, sender, subject)
                        
                        if not security_content['link'] and not security_content['otp']:
                            logger.warning("⚠️  No security content found")
                            continue
                            
                        logger.info("✅ Content extracted")
                        
                        # Validate and forward
                        self.validate_and_forward(recipient, security_content, platform_name)

                except Exception as e:
                    logger.error(f"❌ Error processing email {msg_id}: {e}")
                    import traceback
                    logger.error(traceback.format_exc())
            
            logger.info(f"\n{'='*60}")
            logger.info(f"✅ Completed processing {len(messages)} email(s)")
            logger.info(f"{'='*60}\n")
        
        except (imaplib.IMAP4.abort, ssl.SSLEOFError, socket.error) as e:
            # Re-raise connection errors so the main loop can reconnect
            logger.error(f"🔌 Connection lost: {e}")
            raise e
        except Exception as e:
            logger.error(f"❌ Error fetching emails: {e}")
            import traceback
            logger.error(traceback.format_exc())
    
    def start_monitoring(self):
        """Start monitoring email inbox."""
        self.running = True
        logger.info("🚀 Starting email monitoring...")
        
        while self.running:
            try:
                if not self.imap_client:
                    if not self.connect():
                        logger.error("❌ Failed to connect, retrying in 60 seconds...")
                        time.sleep(60)
                        continue
                
                # Process new emails
                self.process_new_emails()
                
                # Wait before next check
                time.sleep(config.EMAIL_CHECK_INTERVAL)
                
            except (imaplib.IMAP4.abort, ssl.SSLEOFError, socket.error) as e:
                logger.error(f"🔌 Connection lost: {e}. Reconnecting in 30 seconds...")
                self.disconnect()
                self.imap_client = None
                time.sleep(30)
            except Exception as e:
                logger.error(f"❌ Error in monitoring loop: {e}")
                import traceback
                logger.debug(traceback.format_exc())
                self.disconnect()
                self.imap_client = None
                time.sleep(60)
    
    def stop_monitoring(self):
        """Stop monitoring email inbox."""
        self.running = False
        self.disconnect()
        logger.info("🛑 Email monitoring stopped")
