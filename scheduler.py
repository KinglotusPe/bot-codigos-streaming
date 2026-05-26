from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from database import get_db_session
from models import Owner, Seller, Admin, User, StreamingAccount, StatusEnum
from utils.messages import expiration_warning_admin, expiration_warning_user
import config
import logging
import os

logger = logging.getLogger(__name__)


class BotScheduler:
    """Manages scheduled tasks for the bot."""
    
    def __init__(self, bot_instance=None, email_monitor=None):
        self.bot = bot_instance
        self.email_monitor = email_monitor
        self.scheduler = AsyncIOScheduler()
    
    async def health_check(self):
        """Check if email monitor is active."""
        if not self.email_monitor or not self.bot: return
        
        # If last check was more than 10 minutes ago, something might be wrong
        time_diff = datetime.utcnow() - self.email_monitor.last_check
        if time_diff > timedelta(minutes=10):
            logger.warning(f"🚨 Heartbeat Alert: No activity for {time_diff.seconds // 60} minutes!")
            try:
                await self.bot.send_message(
                    chat_id=config.OWNER_TELEGRAM_ID,
                    text=f"⚠️ **ALERTA DE SALUD**\n\nEl monitor de correos no ha reportado actividad en {time_diff.seconds // 60} minutos.\n\nVerifica el estado del VPS."
                )
            except:
                pass
    
    async def check_owner_expirations(self):
        """Check for secondary owners expiring in 3 days."""
        logger.info("🔍 Checking owner expirations...")
        with get_db_session() as session:
            target_date = datetime.utcnow() + timedelta(days=3)
            start_of_day = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
            end_of_day = target_date.replace(hour=23, minute=59, second=59, microsecond=999999)
            
            owners = session.query(Owner).filter(
                Owner.status == StatusEnum.ACTIVE,
                Owner.access_end_date >= start_of_day,
                Owner.access_end_date <= end_of_day
            ).all()
            
            for owner in owners:
                if owner.user_id == config.OWNER_TELEGRAM_ID: continue # Skip SuperOwner
                
                date_str = owner.access_end_date.strftime('%Y-%m-%d')
                msg = f"⚠️ **Aviso de Vencimiento OWNER**\n\nTu acceso como Owner expira en 3 días ({date_str})."
                
                if self.bot:
                    try:
                        await self.bot.send_message(chat_id=owner.user_id, text=msg, parse_mode='Markdown')
                        await self.bot.send_message(
                            chat_id=config.OWNER_TELEGRAM_ID,
                            text=f"📢 OWNER ID:{owner.user_id} expira en 3 días."
                        )
                    except Exception as e:
                        logger.error(f"Error notifying owner {owner.user_id}: {e}")

    async def check_seller_expirations(self):
        """Check for sellers expiring in 3 days."""
        logger.info("🔍 Checking seller expirations...")
        with get_db_session() as session:
            target_date = datetime.utcnow() + timedelta(days=3)
            start_of_day = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
            end_of_day = target_date.replace(hour=23, minute=59, second=59, microsecond=999999)
            
            sellers = session.query(Seller).filter(
                Seller.status == StatusEnum.ACTIVE,
                Seller.access_end_date >= start_of_day,
                Seller.access_end_date <= end_of_day
            ).all()
            
            for seller in sellers:
                date_str = seller.access_end_date.strftime('%Y-%m-%d')
                msg = f"⚠️ **Aviso de Vencimiento SELLER**\n\nTu acceso expira en 3 días ({date_str})."
                
                if self.bot:
                    try:
                        await self.bot.send_message(chat_id=seller.user_id, text=msg, parse_mode='Markdown')
                        await self.bot.send_message(
                            chat_id=config.OWNER_TELEGRAM_ID,
                            text=f"📢 SELLER ID:{seller.user_id} expira en 3 días."
                        )
                    except Exception as e:
                        logger.error(f"Error notifying seller {seller.user_id}: {e}")

    async def check_admin_expirations(self):
        """Check for admins expiring in 3 days."""
        logger.info("🔍 Checking admin expirations...")
        with get_db_session() as session:
            target_date = datetime.utcnow() + timedelta(days=3)
            start_of_day = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
            end_of_day = target_date.replace(hour=23, minute=59, second=59, microsecond=999999)
            
            admins = session.query(Admin).filter(
                Admin.status == StatusEnum.ACTIVE,
                Admin.access_end_date >= start_of_day,
                Admin.access_end_date <= end_of_day
            ).all()
            
            for admin in admins:
                date_str = admin.access_end_date.strftime('%Y-%m-%d')
                message = expiration_warning_admin(date_str)
                
                if self.bot:
                    try:
                        await self.bot.send_message(chat_id=admin.user_id, text=message, parse_mode='HTML')
                        if admin.seller_id:
                            seller = session.query(Seller).get(admin.seller_id)
                            if seller:
                                await self.bot.send_message(chat_id=seller.user_id, text=f"⚠️ Tu Admin ID:{admin.user_id} expira en 3 días.")
                        else:
                            await self.bot.send_message(chat_id=config.OWNER_TELEGRAM_ID, text=f"⚠️ Admin ID:{admin.user_id} expira en 3 días.")
                    except Exception as e:
                        logger.error(f"Error notifying admin {admin.user_id}: {e}")

    async def check_account_expirations(self):
        """Check for accounts expiring in 3 days."""
        logger.info("🔍 Checking account expirations...")
        with get_db_session() as session:
            target_date = datetime.utcnow() + timedelta(days=3)
            start_of_day = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
            end_of_day = target_date.replace(hour=23, minute=59, second=59, microsecond=999999)
            
            accounts = session.query(StreamingAccount).filter(
                StreamingAccount.assigned_to_user_id != None,
                StreamingAccount.expiration_date >= start_of_day,
                StreamingAccount.expiration_date <= end_of_day
            ).all()
            
            for acc in accounts:
                user = session.query(User).get(acc.assigned_to_user_id)
                if not user: continue
                
                date_str = acc.expiration_date.strftime('%Y-%m-%d')
                msg = f"⚠️ **Aviso de Vencimiento**\n\nTu acceso a **{acc.platform_name.upper()}** ({acc.email_address}) expira en 3 días ({date_str})."
                
                if self.bot:
                    try:
                        await self.bot.send_message(chat_id=user.user_id, text=msg, parse_mode='Markdown')
                    except Exception as e:
                        logger.error(f"Error notifying user {user.user_id}: {e}")

    async def check_account_health(self):
        """Check for accounts with no email activity in 7 days (Option 7)."""
        logger.info("🔍 Checking account health (email activity)...")
        with get_db_session() as session:
            # 7 days limit
            limit = datetime.utcnow() - timedelta(days=7)
            
            # Find accounts assigned and active, but with no email in 7 days
            unhealthy_accounts = session.query(StreamingAccount).filter(
                StreamingAccount.assigned_to_user_id != None,
                StreamingAccount.last_email_at < limit
            ).all()
            
            if unhealthy_accounts:
                summary = [f"🚨 **REPORTE DE SALUD DE CUENTAS**\n\nLas siguientes cuentas no han enviado correos en >7 días:"]
                for acc in unhealthy_accounts:
                    summary.append(f"• {acc.platform_name.upper()} - {acc.email_address}")
                
                if self.bot:
                    try:
                        await self.bot.send_message(
                            chat_id=config.OWNER_TELEGRAM_ID,
                            text="\n".join(summary),
                            parse_mode='Markdown'
                        )
                    except: pass

    async def deactivate_expired_owners(self):
        """Deactivate expired secondary owners."""
        with get_db_session() as session:
            expired_owners = session.query(Owner).filter(
                Owner.status == StatusEnum.ACTIVE,
                Owner.access_end_date < datetime.utcnow()
            ).all()
            
            for owner in expired_owners:
                if owner.user_id == config.OWNER_TELEGRAM_ID: continue
                owner.status = StatusEnum.INACTIVE
                # Cascade to sellers
                sellers = session.query(Seller).filter_by(owner_id=owner.user_id).all()
                for seller in sellers:
                    seller.status = StatusEnum.INACTIVE
                    # ... more cascade logic can be added here
                logger.info(f"🛑 Deactivated Owner {owner.user_id}")
            session.commit()

    async def deactivate_expired_sellers(self):
        """Deactivate expired sellers."""
        with get_db_session() as session:
            expired_sellers = session.query(Seller).filter(
                Seller.status == StatusEnum.ACTIVE,
                Seller.access_end_date < datetime.utcnow()
            ).all()
            
            for seller in expired_sellers:
                seller.status = StatusEnum.INACTIVE
                admins = session.query(Admin).filter_by(seller_id=seller.id).all()
                for admin in admins:
                    admin.status = StatusEnum.INACTIVE
                    users = session.query(User).filter_by(admin_id=admin.id).all()
                    for user in users:
                        user.status = StatusEnum.INACTIVE
                logger.info(f"🛑 Deactivated Seller {seller.user_id}")
            session.commit()

    async def deactivate_expired_admins(self):
        """Deactivate expired admins."""
        with get_db_session() as session:
            expired_admins = session.query(Admin).filter(
                Admin.status == StatusEnum.ACTIVE,
                Admin.access_end_date < datetime.utcnow()
            ).all()
            
            for admin in expired_admins:
                admin.status = StatusEnum.INACTIVE
                users = session.query(User).filter_by(admin_id=admin.id).all()
                for user in users:
                    user.status = StatusEnum.INACTIVE
                logger.info(f"🛑 Deactivated Admin {admin.user_id}")
            session.commit()

    async def backup_db(self):
        """Send a backup of the database to the SuperOwner."""
        logger.info("📦 Creating database backup...")
        if not self.bot: return
        
        db_path = config.DATABASE_URL.replace('sqlite:///', '')
        if os.path.exists(db_path):
            try:
                with open(db_path, 'rb') as f:
                    await self.bot.send_document(
                        chat_id=config.OWNER_TELEGRAM_ID,
                        document=f,
                        filename=f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db",
                        caption=f"📦 **Backup Diario Automático**\n📅 {datetime.now().strftime('%Y-%m-%d %H:%M')}"
                    )
                logger.info("✅ Backup sent to SuperOwner")
            except Exception as e:
                logger.error(f"❌ Failed to send backup: {e}")
        else:
            logger.error(f"❌ DB file not found for backup: {db_path}")

    async def daily_maintenance(self):
        """Run all maintenance tasks."""
        logger.info("🔧 Running daily maintenance...")
        await self.check_owner_expirations()
        await self.check_seller_expirations()
        await self.check_admin_expirations()
        await self.check_account_expirations()
        await self.check_account_health()
        await self.deactivate_expired_owners()
        await self.deactivate_expired_sellers()
        await self.deactivate_expired_admins()
        await self.backup_db()
        logger.info("✅ Daily maintenance complete")

    def start(self):
        self.scheduler.add_job(self.daily_maintenance, 'cron', hour=9, minute=0, id='daily_maintenance')
        self.scheduler.add_job(self.health_check, 'interval', minutes=5, id='health_check')
        # Add a quick health check every hour to notify if things are alive
        self.scheduler.add_job(lambda: logger.info("💓 Heartbeat: Scheduler is alive"), 'interval', hours=1)
        self.scheduler.start()
        logger.info("✅ Scheduler started")

    def stop(self):
        self.scheduler.shutdown()
        logger.info("🛑 Scheduler stopped")
