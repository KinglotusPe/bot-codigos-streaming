import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, BigInteger, DateTime, ForeignKey, Enum, UniqueConstraint, Boolean
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()

class StatusEnum(enum.Enum):
    """Status enumeration for Admin and User models."""
    ACTIVE = "Active"
    INACTIVE = "Inactive"


class Owner(Base):
    """Owner model - highest permission level."""
    __tablename__ = 'owners'
    
    user_id = Column(BigInteger, primary_key=True)  # Telegram User ID
    telegram_username = Column(String(255), nullable=True)  # For contact button
    access_end_date = Column(DateTime, nullable=True)  # Null for SuperOwner
    status = Column(Enum(StatusEnum), default=StatusEnum.ACTIVE, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    admins = relationship("Admin", back_populates="owner", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Owner(user_id={self.user_id}, username={self.telegram_username})>"


class Seller(Base):
    """Seller model - intermediate permission level."""
    __tablename__ = 'sellers'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, unique=True, nullable=False)  # Telegram User ID
    owner_id = Column(BigInteger, ForeignKey('owners.user_id'), nullable=False)
    access_end_date = Column(DateTime, nullable=False)
    status = Column(Enum(StatusEnum), default=StatusEnum.ACTIVE, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    owner = relationship("Owner", backref="sellers")
    admins = relationship("Admin", back_populates="seller", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Seller(user_id={self.user_id}, status={self.status.value})>"


class Admin(Base):
    """Admin model - manages streaming accounts and users."""
    __tablename__ = 'admins'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, unique=True, nullable=False)  # Telegram User ID
    owner_id = Column(BigInteger, ForeignKey('owners.user_id'), nullable=True) # Made nullable to allow Seller parent
    seller_id = Column(Integer, ForeignKey('sellers.id'), nullable=True) # Parent Seller
    access_end_date = Column(DateTime, nullable=False)
    status = Column(Enum(StatusEnum), default=StatusEnum.ACTIVE, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    owner = relationship("Owner", back_populates="admins")
    seller = relationship("Seller", back_populates="admins")
    streaming_accounts = relationship("StreamingAccount", back_populates="admin", cascade="all, delete-orphan")
    users = relationship("User", back_populates="admin", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Admin(user_id={self.user_id}, status={self.status.value})>"


class User(Base):
    """User model - has access to assigned streaming accounts."""
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, unique=True, nullable=False)  # Telegram User ID
    admin_id = Column(Integer, ForeignKey('admins.id'), nullable=False)
    has_used_trial = Column(Boolean, default=False, nullable=False)
    status = Column(Enum(StatusEnum), default=StatusEnum.ACTIVE, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    admin = relationship("Admin", back_populates="users")
    streaming_accounts = relationship("StreamingAccount", back_populates="assigned_user")
    
    def __repr__(self):
        return f"<User(user_id={self.user_id}, status={self.status.value})>"


class StreamingAccount(Base):
    """StreamingAccount model - represents a streaming service email account."""
    __tablename__ = 'streaming_accounts'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    email_address = Column(String(255), nullable=False)  # Removed unique=True
    platform_name = Column(String(100), nullable=False)  # Netflix, HBO, Disney+, etc.
    registered_by_admin_id = Column(Integer, ForeignKey('admins.id'), nullable=False)
    assigned_to_user_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    expiration_date = Column(DateTime, nullable=True) # Expiration per assignment
    is_trial = Column(Boolean, default=False, nullable=False) # Marked for trials
    last_email_at = Column(DateTime, nullable=True) # For health tracking (Option 7)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Composite unique constraint: same email can be registered for different platforms
    __table_args__ = (
        UniqueConstraint('email_address', 'platform_name', name='uq_email_platform'),
    )
    
    # Relationships
    admin = relationship("Admin", back_populates="streaming_accounts")
    assigned_user = relationship("User", back_populates="streaming_accounts")
    
    def __repr__(self):
        return f"<StreamingAccount(platform={self.platform_name}, email={self.email_address}, assigned={self.assigned_to_user_id is not None})>"


class CodeHistory(Base):
    """CodeHistory model - tracks all security codes/links sent to users."""
    __tablename__ = 'code_history'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey('users.user_id'), nullable=False)
    platform_name = Column(String(100), nullable=False)
    email_address = Column(String(255), nullable=False)
    code_type = Column(String(20), nullable=False)  # 'otp' or 'link'
    code_value = Column(String(500), nullable=False)  # The actual code or link
    sent_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f"<CodeHistory(user_id={self.user_id}, platform={self.platform_name}, type={self.code_type})>"


class AuditLog(Base):
    """AuditLog model - tracks management actions for security and accountability."""
    __tablename__ = 'audit_logs'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    performed_by_id = Column(BigInteger, nullable=False)  # Telegram ID of the person who did it
    action = Column(String(50), nullable=False)  # 'ADD_ADMIN', 'DEL_OWNER', etc.
    target_id = Column(BigInteger, nullable=True)  # ID of the person affected
    details = Column(String(500), nullable=True)  # Additional info (JSON or text)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f"<AuditLog(action={self.action}, by={self.performed_by_id}, target={self.target_id})>"


class Ticket(Base):
    """Ticket model - tracks user reports and support issues (Option 3)."""
    __tablename__ = 'tickets'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=False)
    platform_name = Column(String(100), nullable=True)
    email_address = Column(String(255), nullable=True)
    description = Column(String(1000), nullable=False)
    status = Column(String(20), default="OPEN") # OPEN, CLOSED
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    closed_at = Column(DateTime, nullable=True)
    
    def __repr__(self):
        return f"<Ticket(id={self.id}, user={self.user_id}, status={self.status})>"
