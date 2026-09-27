"""
Database models for Shapir Recordings System
"""
from sqlalchemy import Column, String, DateTime, Integer, Float, Enum, ForeignKey, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
from uuid import uuid4
import enum

Base = declarative_base()


class UserRole(str, enum.Enum):
    """User roles in the system"""
    VIEWER = "viewer"
    EDITOR = "editor"
    ADMIN = "admin"


class TranscriptionStatus(str, enum.Enum):
    """Status of transcription processing"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class User(Base):
    """User model - represents Shapir employees with AD auth"""
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    email = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    ad_username = Column(String(255), nullable=True)
    ad_domain = Column(String(255), nullable=True)
    role = Column(Enum(UserRole), default=UserRole.VIEWER)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)

    # Relationships
    recordings = relationship("Recording", back_populates="user", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User {self.email}>"


class Recording(Base):
    """Recording model - uploaded audio files"""
    __tablename__ = "recordings"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    file_name = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size_mb = Column(Float, nullable=False)
    file_format = Column(String(10), nullable=False)  # mp3, m4a, wav, ogg

    # Transcription metadata
    language = Column(String(10), nullable=True)  # he, ar, en
    transcription_status = Column(Enum(TranscriptionStatus), default=TranscriptionStatus.PENDING)
    duration_seconds = Column(Integer, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    transcribed_at = Column(DateTime, nullable=True)
    deleted_at = Column(DateTime, nullable=True)  # Soft delete

    # Relationships
    user = relationship("User", back_populates="recordings")
    transcript = relationship("Transcript", back_populates="recording", uselist=False, cascade="all, delete-orphan")
    summaries = relationship("Summary", back_populates="recording", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Recording {self.file_name}>"


class Transcript(Base):
    """Transcript model - output from Whisper API"""
    __tablename__ = "transcripts"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    recording_id = Column(String(36), ForeignKey("recordings.id"), nullable=False, unique=True, index=True)

    # Transcript content
    text = Column(Text, nullable=False)
    language = Column(String(10), nullable=True)

    # API metadata
    api_cost = Column(Float, default=0.0)  # USD cost of Whisper API call
    processing_time_seconds = Column(Integer, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    recording = relationship("Recording", back_populates="transcript")

    def __repr__(self):
        return f"<Transcript {self.recording_id}>"


class Template(Base):
    """Template model - summarization templates"""
    __tablename__ = "templates"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    name = Column(String(255), nullable=False, unique=True)
    description = Column(Text, nullable=True)

    # GPT Configuration
    system_prompt = Column(Text, nullable=False)  # System instructions for GPT
    user_prompt_template = Column(Text, nullable=False)  # User prompt with {transcript} placeholder

    # Output configuration
    output_format = Column(String(20), nullable=False)  # txt, pdf, docx, xlsx

    # Status
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    summaries = relationship("Summary", back_populates="template")

    def __repr__(self):
        return f"<Template {self.name}>"


class Summary(Base):
    """Summary model - generated summaries from GPT"""
    __tablename__ = "summaries"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    recording_id = Column(String(36), ForeignKey("recordings.id"), nullable=False, index=True)
    template_id = Column(String(36), ForeignKey("templates.id"), nullable=False)

    # Summary content
    summary_text = Column(Text, nullable=False)

    # API metadata
    api_cost = Column(Float, default=0.0)  # USD cost of GPT API call
    processing_time_seconds = Column(Integer, nullable=True)
    model_used = Column(String(50), default="gpt-4-turbo-preview")

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Relationships
    recording = relationship("Recording", back_populates="summaries")
    template = relationship("Template", back_populates="summaries")

    def __repr__(self):
        return f"<Summary {self.id}>"


class AuditLog(Base):
    """AuditLog model - track all user actions"""
    __tablename__ = "audit_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)

    # Action details
    action = Column(String(50), nullable=False)  # upload, transcribe, summarize, download, delete
    resource_type = Column(String(50), nullable=False)  # recording, summary, template
    resource_id = Column(String(36), nullable=True, index=True)

    # Additional details
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    details = Column(Text, nullable=True)  # JSON or text details

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Relationships
    user = relationship("User", back_populates="audit_logs")

    def __repr__(self):
        return f"<AuditLog {self.action} {self.resource_type}>"
