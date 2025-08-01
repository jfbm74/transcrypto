# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

**Setup**:
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
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
- `modules/auth/`: User authentication, registration, profile management
- `modules/transcription/`: Core transcription functionality with dual AI provider support
- `modules/subscription/`: Future subscription features
- `modules/utils/`: Audio processing utilities

**AI Integration**:
- **Primary**: OpenAI Whisper (transcription) + GPT-4 (document generation)
- **Secondary**: Google AI Gemini (alternative/fallback provider)
- Both providers configurable per user via API settings

**Database**: SQLite with SQLAlchemy ORM
- User model: Authentication, transcription limits (10 free per user)
- Transcription model: File metadata, processing results, generated documents

**File Processing**:
- Supported formats: MP3, WAV, M4A, OGG, MP4
- Large file handling: Automatic splitting for files >25MB using PyDub
- Storage: `uploads/` for audio, `transcripciones/` for text output

## Configuration

**Environment Variables** (`.env`):
- `SECRET_KEY`: Flask secret key
- `OPENAI_API_KEY`: OpenAI API access
- `GOOGLE_AI_API_KEY`: Google AI API access

**Key Config Values**:
- Database: SQLite at `app.db`
- Upload limits and folders defined in `config.py`
- Free transcription limit: 10 per user

## Important Patterns

**Blueprint Registration**: All routes organized in modules with blueprints
**Factory Pattern**: `create_app()` function for application initialization
**Dual AI Providers**: Services support both OpenAI and Google AI with graceful fallback
**File Security**: Werkzeug secure_filename for upload sanitization
**Session Management**: Flask-Login for user authentication

## Document Generation Features

The application generates structured documents from transcriptions:
- Meeting minutes with participant identification
- Software requirements documentation
- Custom document formatting using AI prompts

## Database Schema

Key relationships:
- User -> Transcription (one-to-many)
- Transcription stores: filename, original text, generated documents, timestamps
- User tracks: transcription count for freemium model