"""
Pydantic schemas for request/response validation
"""
from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime

from models import UserRole, TranscriptionStatus


# --- Auth ---

class LoginRequest(BaseModel):
    username: str
    password: str


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    email: str
    name: str
    role: UserRole
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime] = None


class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse


# --- Recordings ---

class RecordingCreate(BaseModel):
    file_name: str
    file_format: str


class RecordingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    file_name: str
    file_size_mb: float
    file_format: str
    language: Optional[str] = None
    transcription_status: TranscriptionStatus
    duration_seconds: Optional[int] = None
    created_at: datetime
    transcribed_at: Optional[datetime] = None


class RecordingListResponse(BaseModel):
    total: int
    recordings: List[RecordingResponse]


class FileUploadResponse(BaseModel):
    recording_id: str
    file_name: str
    file_size_mb: float
    message: str
    transcription_status: TranscriptionStatus


class TranscriptResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    recording_id: str
    text: str
    language: Optional[str] = None
    api_cost: float
    processing_time_seconds: Optional[int] = None
    created_at: datetime


# --- Templates ---

class TemplateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    description: Optional[str] = None
    output_format: str
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None


# --- Errors ---

class ErrorResponse(BaseModel):
    detail: str
