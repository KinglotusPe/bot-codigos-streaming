"""
Database initialization script.
Creates all tables and seeds the initial Owner record.
"""

import sys
from database import init_db, drop_db, get_db_session
from models import Owner
import config


def seed_owner():
    """Create the initial Owner record from config."""
    with get_db_session() as session:
        # Check if owner already exists
        existing_owner = session.query(Owner).filter_by(user_id=config.OWNER_TELEGRAM_ID).first()
        
        if existing_owner:
            print(f"ℹ️ Owner already exists with Telegram ID: {config.OWNER_TELEGRAM_ID}")
            # Update username if provided
            if config.OWNER_TELEGRAM_USERNAME and not existing_owner.telegram_username:
                existing_owner.telegram_username = config.OWNER_TELEGRAM_USERNAME
                session.commit()
                print(f"✅ Owner username updated to: {config.OWNER_TELEGRAM_USERNAME}")
        else:
            owner = Owner(
                user_id=config.OWNER_TELEGRAM_ID,
                telegram_username=config.OWNER_TELEGRAM_USERNAME or None
            )
            session.add(owner)
            session.commit()
            print(f"✅ Owner created with Telegram ID: {config.OWNER_TELEGRAM_ID}")

        # Ensure Owner is also an Admin (Super Admin)
        from models import Admin, StatusEnum
        from datetime import datetime, timedelta
        
        existing_admin = session.query(Admin).filter_by(user_id=config.OWNER_TELEGRAM_ID).first()
        
        if not existing_admin:
            # Create admin record for owner with long expiry (10 years)
            admin = Admin(
                user_id=config.OWNER_TELEGRAM_ID,
                owner_id=config.OWNER_TELEGRAM_ID,
                access_end_date=datetime.utcnow() + timedelta(days=3650),
                status=StatusEnum.ACTIVE
            )
            session.add(admin)
            session.commit()
            print(f"✅ Owner registered as Admin (Super Admin) with ID: {config.OWNER_TELEGRAM_ID}")
        else:
            # Ensure it's active
            if existing_admin.status != StatusEnum.ACTIVE:
                existing_admin.status = StatusEnum.ACTIVE
                session.commit()
                print(f"✅ Owner Admin status reactivated")


def main():
    """Main initialization function."""
    print("🚀 Initializing database...")
    
    # Validate configuration
    try:
        config.validate_config()
    except ValueError as e:
        print(f"❌ Configuration error: {e}")
        sys.exit(1)
    
    # Ask for confirmation if resetting
    if len(sys.argv) > 1 and sys.argv[1] == '--reset':
        response = input("⚠️ This will delete all data. Are you sure? (yes/no): ")
        if response.lower() == 'yes':
            drop_db()
        else:
            print("❌ Reset cancelled")
            sys.exit(0)
    
    # Initialize database
    init_db()
    
    # Seed owner
    seed_owner()
    
    print("✅ Database setup complete!")


if __name__ == '__main__':
    main()
