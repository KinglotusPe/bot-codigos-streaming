"""
Owner commands for the Telegram bot (Enhanced Version).
Commands: /o_add, /o_del
"""

import os
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import ContextTypes
from database import get_db_session
from models import Owner, Admin, Seller, User, StatusEnum
from utils.validators import is_owner, is_super_owner
from utils.messages import (
    ERROR_NOT_OWNER,
    ERROR_INVALID_DAYS,
    ERROR_INVALID_FORMAT,
    ERROR_ADMIN_NOT_FOUND,
    command_success_add_admin,
    command_success_remove_admin
)
from utils.logger import log_action


async def addowner(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Add a new secondary owner.
    Command: /addowner <user_id>
    Only SuperOwner can use this.
    """
    user_id = update.effective_user.id
    if not is_super_owner(user_id):
        await update.message.reply_text("❌ Solo el Dueño Total puede crear otros Owners.")
        return
        
    if len(context.args) != 1:
        await update.message.reply_text("Uso: /addowner <user_id>")
        return
        
    try:
        new_owner_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("ID inválido.")
        return
        
    with get_db_session() as session:
        existing = session.query(Owner).filter_by(user_id=new_owner_id).first()
        if existing:
            await update.message.reply_text(f"Ese ID ya es Owner.")
            return
            
        owner = Owner(
            user_id=new_owner_id,
            access_end_date=datetime.utcnow() + timedelta(days=30),
            status=StatusEnum.ACTIVE
        )
        session.add(owner)
        session.commit()
        log_action(user_id, 'ADD_OWNER', new_owner_id, "Agregado por 30 días")
        await update.message.reply_text(f"✅ Nuevo Owner agregado por 30 días: {new_owner_id}")


async def delowner(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Remove a secondary owner.
    Command: /delowner <user_id>
    Only SuperOwner can use this.
    """
    user_id = update.effective_user.id
    if not is_super_owner(user_id):
        await update.message.reply_text("❌ Solo el Dueño Total puede eliminar otros Owners.")
        return
        
    if len(context.args) != 1:
        await update.message.reply_text("Uso: /delowner <user_id>")
        return
        
    try:
        target_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("ID inválido.")
        return
        
    if target_id in config.OWNER_TELEGRAM_IDS:
        await update.message.reply_text("❌ No puedes eliminar a un Dueño Total.")
        return
        
    with get_db_session() as session:
        owner = session.query(Owner).filter_by(user_id=target_id).first()
        if not owner:
            await update.message.reply_text("Owner no encontrado.")
            return
            
        session.delete(owner)
        session.commit()
        log_action(user_id, 'DEL_OWNER', target_id)
        await update.message.reply_text(f"✅ Owner eliminado: {target_id}")
import config
import logging

logger = logging.getLogger(__name__)


async def addadmin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Add a new admin with 30-day access.
    Command: /addadmin <user_id>
    """
    user_id = update.effective_user.id
    
    # Check if sender is owner
    if not is_owner(user_id):
        await update.message.reply_text(ERROR_NOT_OWNER)
        return
    
    # Parse arguments
    if len(context.args) != 1:
        await update.message.reply_text(f"{ERROR_INVALID_FORMAT}\n\nUso: /addadmin <user_id>")
        return
    
    try:
        new_admin_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text(ERROR_INVALID_FORMAT)
        return
    
    # Create admin with 30 days
    days = config.SUBSCRIPTION_DAYS
    
    with get_db_session() as session:
        # Check if admin already exists
        existing_admin = session.query(Admin).filter_by(user_id=new_admin_id).first()
        
        if existing_admin:
            # Update existing admin
            existing_admin.access_end_date = datetime.utcnow() + timedelta(days=days)
            existing_admin.status = StatusEnum.ACTIVE
            session.commit()
            
            end_date = existing_admin.access_end_date.strftime('%Y-%m-%d')
            await update.message.reply_text(
                command_success_add_admin(f"ID:{new_admin_id}", end_date)
            )
        else:
            # Create new admin
            admin = Admin(
                user_id=new_admin_id,
                owner_id=user_id,
                access_end_date=datetime.utcnow() + timedelta(days=days),
                status=StatusEnum.ACTIVE
            )
            session.add(admin)
            session.commit()
            
            end_date = admin.access_end_date.strftime('%Y-%m-%d')
            await update.message.reply_text(
                command_success_add_admin(f"ID:{new_admin_id}", end_date)
            )
    
    logger.info(f"✅ Owner {user_id} added admin {new_admin_id}")


async def deladmin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Remove an admin's access.
    Command: /deladmin <user_id>
    Only SuperOwner can do this.
    """
    user_id = update.effective_user.id
    if not is_super_owner(user_id):
        await update.message.reply_text("❌ Solo el Dueño Total puede quitar suscripciones o rangos.")
        return
    
    if len(context.args) != 1:
        await update.message.reply_text("Uso: /deladmin <user_id>")
        return
    
    try:
        admin_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("ID inválido.")
        return
    
    with get_db_session() as session:
        admin = session.query(Admin).filter_by(user_id=admin_id).first()
        if not admin:
            await update.message.reply_text("Admin no encontrado.")
            return
        
        admin.status = StatusEnum.INACTIVE
        session.commit()
        await update.message.reply_text(f"✅ Admin {admin_id} desactivado.")


async def quitar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Universal command to remove access from anyone.
    Command: /quitar <user_id>
    Only SuperOwner can do this.
    """
    user_id = update.effective_user.id
    if not is_super_owner(user_id):
        await update.message.reply_text("❌ Solo el Dueño Total tiene el poder de revocar accesos.")
        return
        
    if len(context.args) != 1:
        await update.message.reply_text("Uso: /quitar <id_telegram>")
        return
        
    try:
        target_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("ID inválido.")
        return
        
    with get_db_session() as session:
        # Check all roles
        owner = session.query(Owner).filter_by(user_id=target_id).first()
        seller = session.query(Seller).filter_by(user_id=target_id).first()
        admin = session.query(Admin).filter_by(user_id=target_id).first()
        user = session.query(User).filter_by(user_id=target_id).first()
        
        found = False
        if owner and target_id not in config.OWNER_TELEGRAM_IDS:
            owner.status = StatusEnum.INACTIVE
            found = True
        if seller:
            seller.status = StatusEnum.INACTIVE
            found = True
        if admin:
            admin.status = StatusEnum.INACTIVE
            found = True
        if user:
            user.status = StatusEnum.INACTIVE
            found = True
            
        if not found:
            await update.message.reply_text("❌ No se encontró a nadie con ese ID en el sistema.")
            return
            
        session.commit()
        await update.message.reply_text(f"✅ Todos los accesos de {target_id} han sido revocados.")


async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Show system statistics.
    Command: /stats
    Only SuperOwner can use this.
    """
    user_id = update.effective_user.id
    if not is_super_owner(user_id):
        await update.message.reply_text("❌ Solo el Dueño Total puede ver las estadísticas globales.")
        return
        
    with get_db_session() as session:
        # User counts
        total_users = session.query(User).count()
        active_users = session.query(User).filter_by(status=StatusEnum.ACTIVE).count()
        
        # Management counts
        total_admins = session.query(Admin).count()
        total_sellers = session.query(Seller).count()
        total_owners = session.query(Owner).count()
        
        # Account counts
        from models import StreamingAccount
        total_accounts = session.query(StreamingAccount).count()
        assigned_accounts = session.query(StreamingAccount).filter(StreamingAccount.assigned_to_user_id != None).count()
        free_accounts = total_accounts - assigned_accounts
        
        # Last codes
        from models import CodeHistory
        total_codes = session.query(CodeHistory).count()
        
        report = [
            "📊 **ESTADÍSTICAS GLOBALES**\n",
            f"👤 **Usuarios:** {active_users} activos / {total_users} total",
            f"💼 **Equipo:** {total_owners} Owners | {total_sellers} Sellers | {total_admins} Admins",
            f"🎬 **Cuentas:** {total_accounts} registradas",
            f"   ├ ✅ Asignadas: {assigned_accounts}",
            f"   └ 🟢 Disponibles: {free_accounts}\n",
            f"📨 **Tráfico:** {total_codes} códigos procesados",
            f"\n📅 _Reporte generado el: {datetime.now().strftime('%Y-%m-%d %H:%M')}_"
        ]
        
        from utils.keyboards import get_back_button
        if update.callback_query:
            await update.callback_query.edit_message_text("\n".join(report), parse_mode='Markdown', reply_markup=get_back_button())
        else:
            await update.message.reply_text("\n".join(report), parse_mode='Markdown', reply_markup=get_back_button())


async def addadmin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Add a new admin with STRICT 30-day access.
    Command: /addadmin <user_id>
    """
    user_id = update.effective_user.id
    if not is_owner(user_id):
        await update.message.reply_text(ERROR_NOT_OWNER)
        return
    
    if len(context.args) != 1:
        await update.message.reply_text(f"{ERROR_INVALID_FORMAT}\n\nUso: /addadmin <user_id>")
        return
    
    try:
        new_admin_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text(ERROR_INVALID_FORMAT)
        return
    
    # FORCED 30 DAYS
    days = 30
    
    with get_db_session() as session:
        existing_admin = session.query(Admin).filter_by(user_id=new_admin_id).first()
        
        if existing_admin:
            existing_admin.access_end_date = datetime.utcnow() + timedelta(days=days)
            existing_admin.status = StatusEnum.ACTIVE
            session.commit()
            end_date = existing_admin.access_end_date.strftime('%Y-%m-%d')
            await update.message.reply_text(f"✅ Admin {new_admin_id} renovado por 30 días hasta el {end_date}.")
        else:
            admin = Admin(
                user_id=new_admin_id,
                owner_id=user_id if is_super_owner(user_id) else None,
                access_end_date=datetime.utcnow() + timedelta(days=days),
                status=StatusEnum.ACTIVE
            )
            session.add(admin)
            session.commit()
            end_date = admin.access_end_date.strftime('%Y-%m-%d')
            log_action(user_id, 'ADD_ADMIN', new_admin_id, f"Expiración: {end_date}")
            await update.message.reply_text(f"✅ Admin {new_admin_id} agregado por 30 días hasta el {end_date}.")
    
    logger.info(f"✅ Management added admin {new_admin_id}")


async def addseller(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Add a new seller with STRICT 30-day access.
    Command: /addseller <user_id>
    """
    user_id = update.effective_user.id
    if not is_owner(user_id):
        await update.message.reply_text(ERROR_NOT_OWNER)
        return
    
    if len(context.args) != 1:
        await update.message.reply_text(f"{ERROR_INVALID_FORMAT}\n\nUso: /addseller <user_id>")
        return
    
    try:
        new_seller_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text(ERROR_INVALID_FORMAT)
        return
    
    # FORCED 30 DAYS
    days = 30
    
    with get_db_session() as session:
        existing_seller = session.query(Seller).filter_by(user_id=new_seller_id).first()
        
        if existing_seller:
            existing_seller.access_end_date = datetime.utcnow() + timedelta(days=days)
            existing_seller.status = StatusEnum.ACTIVE
            session.commit()
            end_date = existing_seller.access_end_date.strftime('%Y-%m-%d')
            await update.message.reply_text(f"✅ Seller {new_seller_id} renovado por 30 días hasta el {end_date}.")
        else:
            seller = Seller(
                user_id=new_seller_id,
                owner_id=user_id if is_super_owner(user_id) else config.OWNER_TELEGRAM_ID, # Fallback to superowner
                access_end_date=datetime.utcnow() + timedelta(days=days),
                status=StatusEnum.ACTIVE
            )
            session.add(seller)
            session.commit()
            end_date = seller.access_end_date.strftime('%Y-%m-%d')
            log_action(user_id, 'ADD_SELLER', new_seller_id, f"Expiración: {end_date}")
            await update.message.reply_text(f"✅ Seller {new_seller_id} agregado por 30 días hasta el {end_date}.")


async def delseller(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Remove a seller's access.
    Command: /delseller <user_id>
    """
    user_id = update.effective_user.id
    
    if not is_super_owner(user_id):
        await update.message.reply_text(ERROR_NOT_OWNER)
        return
    
    if len(context.args) != 1:
        await update.message.reply_text(f"{ERROR_INVALID_FORMAT}\n\nUso: /delseller <user_id>")
        return
    
    try:
        seller_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text(ERROR_INVALID_FORMAT)
        return
    
    with get_db_session() as session:
        seller = session.query(Seller).filter_by(user_id=seller_id).first()
        
        if not seller:
            await update.message.reply_text("❌ Seller no encontrado.")
            return
        
        seller.status = StatusEnum.INACTIVE
        session.commit()
        log_action(user_id, 'DEL_SELLER', seller_id)
        await update.message.reply_text(f"✅ Seller {seller_id} eliminado (sus admins/usuarios permanecen activos).")
    
    logger.info(f"✅ Owner {user_id} removed seller {seller_id}")


async def spam(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Send a message to all registered users.
    Command: /spam <mensaje>
    """
    user_id = update.effective_user.id
    
    # Check if sender is owner
    if not is_owner(user_id):
        await update.message.reply_text(ERROR_NOT_OWNER)
        return
    
    # Parse message
    if not context.args:
        await update.message.reply_text(
            f"{ERROR_INVALID_FORMAT}\n\n"
            f"Uso: /spam <mensaje>\n"
            f"Ejemplo: /spam Hola a todos! El sistema estará en mantenimiento mañana."
        )
        return
    
    # Join all arguments as the message
    message = " ".join(context.args)
    
    # Get all targets (Users + Admins + Sellers)
    with get_db_session() as session:
        users = session.query(User).all()
        admins = session.query(Admin).all()
        sellers = session.query(Seller).all()
        
        targets = set()
        for u in users: targets.add(u.user_id)
        for a in admins: targets.add(a.user_id)
        for s in sellers: targets.add(s.user_id)
        
        if not targets:
            await update.message.reply_text("ℹ️ No hay nadie registrado en el sistema.")
            return
        
        # Send message to all
        sent_count = 0
        failed_count = 0
        
        for target_id in targets:
            try:
                await context.bot.send_message(
                    chat_id=target_id,
                    text=f"📢 **Mensaje del Owner:**\n\n{message}",
                    parse_mode='Markdown'
                )
                sent_count += 1
            except Exception as e:
                logger.warning(f"Failed to send to {target_id}: {e}")
                failed_count += 1
        
        # Send confirmation to owner
        await update.message.reply_text(
            f"✅ Mensaje enviado a {sent_count} personas (Users/Admins/Sellers).\n"
            f"❌ Fallos: {failed_count}"
        )
    
    logger.info(f"✅ Owner {user_id} sent broadcast message to {sent_count} targets")


async def allemails(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Show all emails registered in the system (SuperOwner Only).
    Command: /allemails [plataforma]
    """
    user_id = update.effective_user.id
    
    # If called from button without specific platform, show platform selector (Dashboard)
    if not context.args and (not update.callback_query or update.callback_query.data == "all_emails"):
        if not is_super_owner(user_id):
            await (update.callback_query.answer("⛔ Acceso Denegado. Solo el Dueño Total puede ver el inventario global.", show_alert=True) if update.callback_query else update.message.reply_text("⛔ Acceso Denegado."))
            return
            
        from utils.keyboards import get_inventory_platforms_keyboard
        text = "📊 **DASHBOARD DE INVENTARIO**\n\nSelecciona una plataforma para ver el estado de las cuentas:"
        if update.callback_query:
            await update.callback_query.edit_message_text(text, parse_mode='Markdown', reply_markup=get_inventory_platforms_keyboard())
        else:
            await update.message.reply_text(text, parse_mode='Markdown', reply_markup=get_inventory_platforms_keyboard())
        return

    # STRICT: Only SuperOwner can see global inventory list
    if not is_super_owner(user_id):
        if update.callback_query:
            await update.callback_query.answer("⛔ Acceso Denegado.", show_alert=True)
        else:
            await update.message.reply_text("⛔ Acceso Denegado. Solo el Dueño Total puede ver el inventario global.")
        return

    # Check for platform filter and status filter
    platform_filter = None
    status_filter = None
    
    if update.callback_query and update.callback_query.data.startswith("inv_plat_"):
        platform_filter = update.callback_query.data.replace("inv_plat_", "")
    
    for arg in context.args:
        arg_lower = arg.lower()
        if arg_lower in ['libres', 'libre', 'free', '🟢']:
            status_filter = 'free'
        elif arg_lower in ['ocupados', 'ocupado', 'busy', '🔴']:
            status_filter = 'busy'
        else:
            platform_filter = arg_lower
    
    with get_db_session() as session:
        query = session.query(StreamingAccount)
        
        if platform_filter:
            query = query.filter(StreamingAccount.platform_name.ilike(f"%{platform_filter}%"))
            
        if status_filter == 'free':
            query = query.filter(StreamingAccount.assigned_to_user_id == None)
        elif status_filter == 'busy':
            query = query.filter(StreamingAccount.assigned_to_user_id != None)
            
        accounts = query.all()
        
        if not accounts:
            filter_msg = []
            if platform_filter: filter_msg.append(f"plataforma {platform_filter.upper()}")
            if status_filter: filter_msg.append(f"estado {status_filter}")
            
            msg = f"ℹ️ No hay correos registrados{' con ' + ' y '.join(filter_msg) if filter_msg else ''}."
            await update.message.reply_text(msg)
            return
        
        # Build message
        title = f"🌍 **INVENTARIO GLOBAL{' (' + platform_filter.upper() + ')' if platform_filter else ''}**\n"
        lines = [title]
        
        # Group by platform for better view
        by_platform = {}
        for acc in accounts:
            p = acc.platform_name.upper()
            if p not in by_platform: by_platform[p] = []
            by_platform[p].append(acc)
            
        for platform, accs in by_platform.items():
            lines.append(f"📦 **{platform}**")
            for acc in accs:
                status = "🟢 Libre"
                assigned = ""
                if acc.assigned_to_user_id:
                    status = "🔴 Ocupado"
                    user = session.query(User).filter_by(id=acc.assigned_to_user_id).first()
                    assigned = f" (Asig a: {user.user_id if user else '?'})"
                
                lines.append(f"  ├ {acc.email_address}")
                lines.append(f"  └ Estado: {status}{assigned}")
            lines.append("")
            
        full_message = "\n".join(lines)
        from utils.keyboards import get_back_button
        # Handle long messages
        if len(full_message) > 4000:
            parts = [full_message[i:i+4000] for i in range(0, len(full_message), 4000)]
            for i, part in enumerate(parts):
                markup = get_back_button() if i == len(parts) - 1 else None
                await context.bot.send_message(chat_id=user_id, text=part, parse_mode='Markdown', reply_markup=markup)
        else:
            if update.callback_query:
                await update.callback_query.edit_message_text(full_message, parse_mode='Markdown', reply_markup=get_back_button())
            else:
                await update.message.reply_text(full_message, parse_mode='Markdown', reply_markup=get_back_button())
    
    logger.info(f"✅ Owner {user_id} requested global email report")


async def staff(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    List all Owners and Sellers (SuperOwner Only).
    Command: /staff
    """
    user_id = update.effective_user.id
    
    if not is_super_owner(user_id):
        await update.message.reply_text("⛔ Acceso Denegado. Solo el Dueño Total puede ver la lista del equipo.")
        return
        
    with get_db_session() as session:
        owners = session.query(Owner).all()
        sellers = session.query(Seller).all()
        from models import Admin
        admins = session.query(Admin).all()
        
        new_lines = ["👥 **EQUIPO DE GESTIÓN**\n"]
        
        # Section: Owners
        new_lines.append("💎 **Owners (Dueños):**")
        for o in owners:
            status_icon = "🟢" if o.status == StatusEnum.ACTIVE else "🔴"
            is_total = " [DUEÑO TOTAL]" if o.user_id == config.OWNER_TELEGRAM_ID else ""
            new_lines.append(f"  ├ ID: [{o.user_id}](tg://user?id={o.user_id}){is_total}")
            new_lines.append(f"  └ Estado: {status_icon} {o.status.value}")
        
        # Section: Sellers
        new_lines.append("\n💼 **Sellers (Vendedores):**")
        if not sellers:
            new_lines.append("  (No hay sellers registrados)")
        else:
            for s in sellers:
                status_icon = "🟢" if s.status == StatusEnum.ACTIVE else "🔴"
                exp = s.access_end_date.strftime('%Y-%m-%d') if s.access_end_date else "N/A"
                new_lines.append(f"  ├ ID: [{s.user_id}](tg://user?id={s.user_id})")
                new_lines.append(f"  └ Estado: {status_icon} {s.status.value} | Exp: {exp} | Por: [Owner {s.owner_id}](tg://user?id={s.owner_id})")

        # Section: Admins
        new_lines.append("\n🛡️ **Admins (Operadores):**")
        if not admins:
            new_lines.append("  (No hay admins registrados)")
        else:
            for a in admins:
                status_icon = "🟢" if a.status == StatusEnum.ACTIVE else "🔴"
                if a.owner_id:
                    creator_link = f"[Owner {a.owner_id}](tg://user?id={a.owner_id})"
                elif a.seller_id:
                    seller_record = session.query(Seller).filter_by(id=a.seller_id).first()
                    creator_link = f"[Seller {seller_record.user_id}](tg://user?id={seller_record.user_id})" if seller_record else "Seller"
                else:
                    creator_link = "Sistema"
                new_lines.append(f"  ├ ID: [{a.user_id}](tg://user?id={a.user_id})")
                new_lines.append(f"  └ Estado: {status_icon} {a.status.value} | Por: {creator_link}")

        from utils.keyboards import get_back_button
        if update.callback_query:
            await update.callback_query.edit_message_text("\n".join(new_lines), parse_mode='Markdown', reply_markup=get_back_button())
        else:
            await update.message.reply_text("\n".join(new_lines), parse_mode='Markdown', reply_markup=get_back_button())
    
    logger.info(f"✅ Owner {user_id} requested staff list")


async def backup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Send the database file as a backup (SuperOwner Only).
    Command: /backup
    """
    user_id = update.effective_user.id
    if not is_super_owner(user_id):
        msg = "⛔ Solo el Dueño Total puede solicitar respaldos."
        if update.callback_query:
            await update.callback_query.answer(msg, show_alert=True)
        else:
            await update.message.reply_text(msg)
        return
        
    db_path = 'bot_database.db'
    if not os.path.exists(db_path):
        await update.message.reply_text("❌ Base de datos no encontrada.")
        return
        
    try:
        with open(db_path, 'rb') as f:
            await context.bot.send_document(
                chat_id=user_id,
                document=f,
                filename=f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db",
                caption="📁 **Respaldo de Base de Datos**\nConsérvalo en un lugar seguro."
            )
        log_action(user_id, 'BACKUP_REQUESTED')
    except Exception as e:
        logger.error(f"Error sending backup: {e}")
        await update.message.reply_text("❌ Error al enviar el respaldo.")


async def health(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Check system health status (Owner Only).
    Command: /health
    """
    user_id = update.effective_user.id
    if not is_owner(user_id):
        await update.message.reply_text(ERROR_NOT_OWNER)
        return
        
    import psutil
    import os
    
    # Process info
    process = psutil.Process(os.getpid())
    memory_mb = process.memory_info().rss / 1024 / 1024
    
    # DB status
    db_size_kb = os.path.getsize('bot_database.db') / 1024 if os.path.exists('bot_database.db') else 0
    
    # Audit stats
    from models import AuditLog
    with get_db_session() as session:
        recent_logs = session.query(AuditLog).count()
        
    lines = [
        "🏥 **ESTADO DEL SISTEMA**\n",
        f"⏱ **Memoria RAM:** {memory_mb:.2f} MB",
        f"💾 **Base de Datos:** {db_size_kb:.2f} KB",
        f"📝 **Registros Auditoría:** {recent_logs}",
        f"🤖 **Status:** Operativo ✅",
        f"\n📅 _Reporte: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}_"
    ]
    
    from utils.keyboards import get_back_button
    if update.callback_query:
        await update.callback_query.edit_message_text("\n".join(lines), parse_mode='Markdown', reply_markup=get_back_button())
    else:
        await update.message.reply_text("\n".join(lines), parse_mode='Markdown', reply_markup=get_back_button())


async def audit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Show recent audit logs (SuperOwner Only).
    Command: /audit
    """
    user_id = update.effective_user.id
    if not is_super_owner(user_id):
        await update.message.reply_text("⛔ Acceso denegado.")
        return
        
    from models import AuditLog
    with get_db_session() as session:
        logs = session.query(AuditLog).order_by(AuditLog.timestamp.desc()).limit(20).all()
        
        if not logs:
            await update.message.reply_text("ℹ️ No hay registros de auditoría aún.")
            return
            
        lines = ["📝 **ÚLTIMOS REGISTROS DE AUDITORÍA**\n"]
        for log in logs:
            date_str = (log.timestamp - timedelta(hours=5)).strftime('%d/%m %H:%M')
            details = f" - {log.details}" if log.details else ""
            lines.append(f"⏱ `{date_str}` | `{log.performed_by_id}`")
            lines.append(f"└ **{log.action}** ➔ `{log.target_id or 'N/A'}`{details}\n")
            
        full_message = "\n".join(lines)
        from utils.keyboards import get_back_button
        if len(full_message) > 4000:
            parts = [full_message[i:i+4000] for i in range(0, len(full_message), 4000)]
            for i, part in enumerate(parts):
                markup = get_back_button() if i == len(parts) - 1 else None
                await context.bot.send_message(chat_id=user_id, text=part, parse_mode='Markdown', reply_markup=markup)
        else:
            if update.callback_query:
                await update.callback_query.edit_message_text(full_message, parse_mode='Markdown', reply_markup=get_back_button())
            else:
                await update.message.reply_text(full_message, parse_mode='Markdown', reply_markup=get_back_button())
