# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

**Setup**:
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

**System Dependencies** (Required for video/audio processing):
```bash
# Ubuntu/Debian
sudo apt-get install ffmpeg

# macOS
brew install ffmpeg

# Windows
# Download from https://ffmpeg.org/download.html
```

**Database Operations**:
```bash
flask db init          # Initialize migrations (first time only)
flask db migrate -m "Migration message"
flask db upgrade        # Apply migrations
```

**Run Application**:
```bash
python app.py          # Development server on http://localhost:5000
```

**Production Deployment**:
- Uses Gunicorn with SystemD service (zentratext.service)
- Configuration: 3 workers, port 5000, 3600s timeout

## Architecture Overview

**Framework**: Flask web application with modular Blueprint architecture

**Key Modules**:
- `modules/auth/`: User authentication, registration, profile management, AI provider preferences
- `modules/transcription/`: Core transcription functionality with dual AI provider support
- `modules/subscription/`: Future subscription features
- `modules/utils/`: Audio/video processing utilities (FFmpeg wrappers)

**AI Integration - User-Selectable Providers**:
- **OpenAI**: Whisper (transcription) + GPT-4 (document generation)
- **Google AI**: Gemini 2.5 Pro (document generation alternative)
- Users select preferred provider in profile settings (`User.ai_provider` field)
- Automatic fallback to alternative provider if preferred is unavailable
- Document generation functions accept `user_provider` parameter

**Database**: SQLite with SQLAlchemy ORM and Flask-Migrate for migrations
- Database location: `db/app.db` (note: NOT in root, in `db/` subdirectory)
- User model: Authentication, transcription limits (10 free), AI provider preference
- Transcription model: File metadata, processing results, generated documents, document type

**File Processing Pipeline**:
- Supported audio formats: MP3, WAV, M4A, OGG
- Supported video formats: MP4, AVI, MOV, MKV, FLV, WMV, WEBM
- Video-to-audio conversion: Automatic extraction using FFmpeg, creates temporary MP3
- Large file handling: Automatic splitting for files >25MB using FFmpeg
- Storage: `uploads/` for audio/video, `transcripciones/` for text output
- Cleanup: Temporary audio files from video conversion are automatically deleted

## Configuration

**Environment Variables** (`.env`):
- `SECRET_KEY`: Flask secret key
- `OPENAI_API_KEY`: OpenAI API access (required for transcription)
- `GOOGLE_AI_API_KEY`: Google AI API access (optional, for document generation)
- `FREE_TRANSCRIPTIONS_LIMIT`: Number of free transcriptions per user (default: 10)

**Database Location**:
- SQLite database path: `db/app.db` (configured in `config.py`)
- Ensure `db/` directory exists before running migrations or app

## Important Patterns

**Blueprint Registration**: All routes organized in modules with blueprints registered in `app.py`

**Factory Pattern**: `create_app()` function for application initialization, allows testing with different configs

**Dual AI Provider Architecture**:
- Services in `modules/transcription/services.py` expose functions like `generate_meeting_minutes(transcription, user_provider='openai')`
- Functions check user's preferred provider first, then fallback to alternative if unavailable
- Routes in `modules/transcription/routes.py` pass `current_user.ai_provider` to service functions

**Model Relationship Pattern**:
- Relationships defined in separate `modules/models.py` file to avoid circular imports
- Import this file in `app.py` to establish relationships after all models are defined

**File Security**: Werkzeug `secure_filename()` for upload sanitization

**Session Management**: Flask-Login with `User.is_authenticated` checks

**Audio Processing**: FFmpeg subprocess calls wrapped in `modules/utils/audio_processing.py`:
- `detect_file_type()`: Uses ffprobe to detect audio vs video
- `convert_video_to_audio()`: Extracts audio track from video files
- `split_audio_file()`: Splits large files into segments for API limits

## Document Generation Features

The application generates structured documents from transcriptions using AI:
- **Meeting minutes**: Formal actas with participant identification, agenda, agreements
- **Requirements documentation**: Software requirement specs with functional/non-functional requirements, stakeholder analysis
- Document type stored in `Transcription.document_type` field
- Generated content stored in `Transcription.acta_text` field (reused for all document types)

## Database Schema

**User Model** (`modules/auth/models.py`):
- Standard authentication fields (username, email, password_hash)
- `ai_provider`: 'openai' or 'google' (default: 'openai')
- `transcriptions`: Relationship to Transcription model (one-to-many)
- Methods: `can_transcribe()`, `get_transcription_count()`

**Transcription Model** (`modules/transcription/models.py`):
- `user_id`: Foreign key to User
- `original_filename`, `file_path`, `transcript_path`: File references
- `transcript_text`: Raw transcription text
- `acta_text`: Generated document content (for any document type)
- `document_type`: 'acta' or 'requirements'
- `processing_time`: Transcription duration in seconds
- `created_at`: Timestamp

**Key Relationships**:
- User -> Transcription (one-to-many, defined in `modules/models.py`)
- User tracks transcription count for freemium model limit enforcement

## Admin User

On first run, `app.py` creates a default admin user:
- Username: `admin`
- Email: `admin@example.com`
- Password: `adminpassword`
- Flag: `is_admin=True`

## Feature Documentation

New features should include documentation in the repository:
- `FEATURE_VIDEO_TO_AUDIO.md`: Video file processing implementation
- `FEATURE_AI_PROVIDER_SELECTION.md`: User-selectable AI provider system