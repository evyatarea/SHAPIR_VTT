"""
Recording routes - Upload, list, transcribe
"""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from pathlib import Path
import shutil
import logging
from datetime import datetime

from database import get_db
from routes_auth import get_current_user
from services.whisper_service import whisper_service
from schemas import RecordingCreate, RecordingResponse, RecordingListResponse, FileUploadResponse, TranscriptResponse
from models import User, Recording, TranscriptionStatus, AuditLog
from config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/recordings", tags=["recordings"])


def validate_file(file: UploadFile) -> str:
    """
    Validate uploaded file

    Returns:
        File format (extension)
    """
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No filename provided"
        )

    # Get file extension
    file_ext = Path(file.filename).suffix.lower().lstrip(".")

    # Check if format is allowed
    if file_ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File format '.{file_ext}' not allowed. Allowed: {', '.join(settings.ALLOWED_EXTENSIONS)}"
        )

    return file_ext


@router.post("/upload", response_model=FileUploadResponse)
async def upload_recording(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Upload audio file for transcription

    Accepts: MP3, M4A, WAV, OGG
    Max size: 100MB
    """
    logger.info(f"Upload started by user {current_user.email} for file {file.filename}")

    try:
        # Validate file
        file_format = validate_file(file)

        # Create upload directory if needed
        upload_dir = Path(settings.UPLOAD_DIR)
        upload_dir.mkdir(parents=True, exist_ok=True)

        # Read file content
        file_content = await file.read()
        file_size_mb = len(file_content) / (1024 * 1024)

        # Check file size
        if file_size_mb > settings.MAX_FILE_SIZE_MB:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File size {file_size_mb:.2f}MB exceeds maximum {settings.MAX_FILE_SIZE_MB}MB"
            )

        # Create recording record
        recording = Recording(
            user_id=current_user.id,
            file_name=file.filename,
            file_size_mb=file_size_mb,
            file_format=file_format,
            transcription_status=TranscriptionStatus.PENDING,
            language=None
        )

        db.add(recording)
        db.commit()
        db.refresh(recording)

        # Save file to disk
        file_path = upload_dir / f"{recording.id}.{file_format}"
        recording.file_path = str(file_path)

        with open(file_path, "wb") as f:
            f.write(file_content)

        db.commit()

        # Log audit
        audit_log = AuditLog(
            user_id=current_user.id,
            action="upload",
            resource_type="recording",
            resource_id=recording.id,
            details=f"Uploaded file: {file.filename}"
        )
        db.add(audit_log)
        db.commit()

        logger.info(f"File uploaded successfully: {recording.id} by {current_user.email}")

        return FileUploadResponse(
            recording_id=recording.id,
            file_name=file.filename,
            file_size_mb=file_size_mb,
            message="File uploaded successfully",
            transcription_status=TranscriptionStatus.PENDING
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload file"
        )


@router.get("", response_model=RecordingListResponse)
async def list_recordings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 50
):
    """
    List user's recordings (paginated)

    Returns latest recordings first
    """
    query = db.query(Recording).filter(
        Recording.user_id == current_user.id,
        Recording.deleted_at == None  # Exclude soft-deleted
    ).order_by(Recording.created_at.desc())

    total = query.count()
    recordings = query.offset(skip).limit(limit).all()

    return RecordingListResponse(
        total=total,
        recordings=[RecordingResponse.model_validate(r) for r in recordings]
    )


@router.get("/{recording_id}", response_model=RecordingResponse)
async def get_recording(
    recording_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get recording details
    """
    recording = db.query(Recording).filter(
        Recording.id == recording_id,
        Recording.user_id == current_user.id,
        Recording.deleted_at == None
    ).first()

    if not recording:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recording not found"
        )

    return RecordingResponse.model_validate(recording)


@router.get("/{recording_id}/transcript", response_model=TranscriptResponse)
async def get_transcript(
    recording_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get transcript of a recording

    Transcription must be completed
    """
    recording = db.query(Recording).filter(
        Recording.id == recording_id,
        Recording.user_id == current_user.id
    ).first()

    if not recording:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recording not found"
        )

    if recording.transcription_status != TranscriptionStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Transcription status: {recording.transcription_status}. Not ready."
        )

    transcript = recording.transcript
    if not transcript:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transcript not found"
        )

    return TranscriptResponse.model_validate(transcript)


@router.post("/{recording_id}/transcribe")
async def transcribe_recording(
    recording_id: str,
    language: str = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Manually trigger transcription for a recording

    Can be called asynchronously or via background task
    """
    recording = db.query(Recording).filter(
        Recording.id == recording_id,
        Recording.user_id == current_user.id
    ).first()

    if not recording:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recording not found"
        )

    if not Path(recording.file_path).exists():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Recording file not found on disk"
        )

    try:
        logger.info(f"Starting transcription for recording {recording_id}")

        # Call Whisper service
        transcript = whisper_service.process_recording(
            db,
            recording_id,
            recording.file_path,
            language
        )

        if not transcript:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Transcription failed"
            )

        # Log audit
        audit_log = AuditLog(
            user_id=current_user.id,
            action="transcribe",
            resource_type="recording",
            resource_id=recording_id,
            details=f"Transcribed: {language or 'auto-detect'}"
        )
        db.add(audit_log)
        db.commit()

        logger.info(f"Transcription completed for recording {recording_id}")

        return {
            "recording_id": recording_id,
            "status": "completed",
            "language": transcript.language,
            "cost": transcript.api_cost,
            "processing_time_seconds": transcript.processing_time_seconds
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Transcription error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Transcription failed"
        )


@router.delete("/{recording_id}")
async def delete_recording(
    recording_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Soft delete a recording (mark as deleted but keep in database)
    """
    recording = db.query(Recording).filter(
        Recording.id == recording_id,
        Recording.user_id == current_user.id
    ).first()

    if not recording:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recording not found"
        )

    # Soft delete
    recording.deleted_at = datetime.utcnow()

    # Log audit
    audit_log = AuditLog(
        user_id=current_user.id,
        action="delete",
        resource_type="recording",
        resource_id=recording_id
    )
    db.add(audit_log)
    db.commit()

    logger.info(f"Recording {recording_id} deleted by {current_user.email}")

    return {
        "message": "Recording deleted successfully",
        "recording_id": recording_id
    }
