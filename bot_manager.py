"""
Main Telegram bot application.
"""

import asyncio
import logging
import threading
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
import config
from database import init_db
from email_monitor import EmailMonitor
from scheduler import BotScheduler
from commands.owner_commands import addadmin as owner_addadmin, deladmin as owner_deladmin, spam, allemails, addseller, delseller, addowner, delowner, stats, quitar as owner_quitar, staff, backup, health, audit
from commands.seller_commands import seller_addadmin, seller_deladmin
from commands.admin_commands import reg, miscorreos, asig, renov, venc, settrial, cerrar_ticket
from commands.user_commands import user_list, user_historial, user_prueba, user_me, handle_ticket_message
from commands.help_command import cmds
from commands.guide_command import guia
from commands.callback_handlers import universal_callback_handler

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


class StreamingAccountBot:
    """Main bot application."""
    
    def __init__(self):
        """Initialize the bot."""
        self.application = None
        self.email_monitor = None
        self.scheduler = None
        self.email_thread = None

    async def post_init(self, application: Application):
        """Post-initialization hook."""
        # Initialize email monitor with bot instance and loop
        self.email_monitor = EmailMonitor(bot_instance=application.bot, loop=asyncio.get_running_loop())
        
        # Initialize scheduler with bot instance and email monitor
        self.scheduler = BotScheduler(bot_instance=application.bot, email_monitor=self.email_monitor)
        
        # Start email monitoring in background thread
        self.email_thread = threading.Thread(
            target=self.email_monitor.start_monitoring,
            daemon=True
        )
        self.email_thread.start()
        logger.info("✅ Email monitoring started in background")
        
        # Start scheduler
        self.scheduler.start()
        logger.info("✅ Scheduler started")
        
        # Notify owners
        await self.notify_owners()
    
    async def post_shutdown(self, application: Application):
        """Post-shutdown hook."""
        # Stop email monitoring
        if self.email_monitor:
            self.email_monitor.stop_monitoring()
        
        # Stop scheduler
        if self.scheduler:
            self.scheduler.stop()
        
        logger.info("✅ Bot shutdown complete")
    
    def setup_handlers(self):
        """Register command handlers."""
        # Owner commands
        self.application.add_handler(CommandHandler("addadmin", self.route_addadmin))
        self.application.add_handler(CommandHandler("deladmin", self.route_deladmin))
        self.application.add_handler(CommandHandler("addseller", addseller))
        self.application.add_handler(CommandHandler("delseller", delseller))
        self.application.add_handler(CommandHandler("addowner", addowner))
        self.application.add_handler(CommandHandler("delowner", delowner))
        self.application.add_handler(CommandHandler("spam", spam))
        self.application.add_handler(CommandHandler("allemails", allemails))
        self.application.add_handler(CommandHandler("stats", stats))
        self.application.add_handler(CommandHandler("quitar", owner_quitar))
        self.application.add_handler(CommandHandler("staff", staff))
        self.application.add_handler(CommandHandler("backup", backup))
        self.application.add_handler(CommandHandler("health", health))
        self.application.add_handler(CommandHandler("audit", audit))
        
        # Admin commands
        self.application.add_handler(CommandHandler("reg", reg))
        self.application.add_handler(CommandHandler("miscorreos", miscorreos))
        self.application.add_handler(CommandHandler("asig", asig))
        self.application.add_handler(CommandHandler("renov", renov))
        self.application.add_handler(CommandHandler("venc", venc))
        self.application.add_handler(CommandHandler("settrial", settrial))
        self.application.add_handler(CommandHandler("guia", guia))
        self.application.add_handler(CommandHandler("cerrar", cerrar_ticket))
        
        # User commands
        self.application.add_handler(CommandHandler("list", user_list))
        self.application.add_handler(CommandHandler("historial", user_historial))
        self.application.add_handler(CommandHandler("prueba", user_prueba))
        self.application.add_handler(CommandHandler("me", user_me))
        # Callback Handlers (Buttons)
        self.application.add_handler(CallbackQueryHandler(universal_callback_handler))
        
        # Help command
        self.application.add_handler(CommandHandler("cmds", cmds))
        self.application.add_handler(CommandHandler("start", cmds))
        
        # Message Handlers
        from telegram.ext import MessageHandler, filters
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_ticket_message))
        
        logger.info("✅ Command handlers registered")
    
    def run(self):
        """Run the bot."""
        # Validate configuration
        try:
            config.validate_config()
        except ValueError as e:
            logger.error(f"❌ Configuration error: {e}")
            return
        
        # Initialize database
        logger.info("🔧 Initializing database...")
        init_db()
        
        # Create application
        self.application = Application.builder().token(config.TELEGRAM_BOT_TOKEN).build()
        
        # Register post-init and post-shutdown hooks
        self.application.post_init = self.post_init
        self.application.post_shutdown = self.post_shutdown
        
        # Setup command handlers
        self.setup_handlers()
        
        # Start bot
        logger.info("🚀 Starting bot...")
        self.application.run_polling(allowed_updates=Update.ALL_TYPES)

    async def route_addadmin(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Route /addadmin to owner or seller handler."""
        from utils.validators import is_owner, is_seller
        user_id = update.effective_user.id
        if is_owner(user_id):
            await owner_addadmin(update, context)
        elif is_seller(user_id):
            await seller_addadmin(update, context)
        else:
            # Default to owner handler which shows error
            await owner_addadmin(update, context)

    async def route_deladmin(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Route /deladmin to owner or seller handler."""
        from utils.validators import is_owner, is_seller
        user_id = update.effective_user.id
        if is_owner(user_id):
            await owner_deladmin(update, context)
        elif is_seller(user_id):
            await seller_deladmin(update, context)
        else:
            # Default to owner handler which shows error
            await owner_deladmin(update, context)

    async def notify_owners(self):
        """Notify all owners that the bot is online."""
        from database import get_db_session
        from models import Owner, StatusEnum
        import config
        
        # Get all active owners from DB
        owners_to_notify = []
        try:
            with get_db_session() as session:
                owners = session.query(Owner).filter_by(status=StatusEnum.ACTIVE).all()
                for o in owners:
                    owners_to_notify.append(o.user_id)
            
            # Add all super owners
            for super_id in config.OWNER_TELEGRAM_IDS:
                if super_id not in owners_to_notify:
                    owners_to_notify.append(super_id)
                
            import platform
            env_type = "PRODUCCIÓN (VPS)" if platform.system() == "Linux" else "entorno local"
            
            for owner_id in owners_to_notify:
                try:
                    await self.application.bot.send_message(
                        chat_id=owner_id,
                        text=f"🚀 **Sistema Iniciado**\n\nEl bot de streaming se ha encendido en **{env_type}** y está operativo.",
                        parse_mode='Markdown'
                    )
                    logger.info(f"🔔 Notification sent to owner {owner_id}")
                except Exception as e:
                    logger.warning(f"Could not notify owner {owner_id}: {e}")
        except Exception as e:
            logger.error(f"Error notifying owners: {e}")


def main():
    """Main entry point."""
    logger.info("=" * 60)
    logger.info("🤖 Telegram Streaming Account Manager Bot")
    logger.info("=" * 60)
    
    bot = StreamingAccountBot()
    bot.run()


if __name__ == '__main__':
    main()
