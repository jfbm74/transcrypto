# Video-to-Audio Conversion Feature

## Overview
This feature automatically detects video files and extracts their audio track before transcription, allowing users to transcribe video files (MP4, AVI, MOV, etc.) without manual conversion.

## Implementation Details

### Files Modified
1. **modules/utils/audio_processing.py**
   - Added `detect_file_type()`: Detects if uploaded file is audio or video using ffprobe
   - Added `convert_video_to_audio()`: Converts video files to MP3 format using ffmpeg

2. **modules/transcription/services.py**
   - Modified `process_audio_file()`: Now detects file type and converts videos to audio before transcription
   - Automatic cleanup of temporary audio files after transcription

3. **modules/transcription/routes.py**
   - Updated `allowed_extensions` to include video formats: MP4, AVI, MOV, MKV, FLV, WMV, WEBM

4. **CLAUDE.md**
   - Added FFmpeg as system dependency
   - Updated documentation for supported formats

### Workflow
1. User uploads a file (audio or video)
2. File is saved to `uploads/` folder
3. System detects file type using ffprobe
4. If video:
   - Audio track is extracted to MP3 using ffmpeg
   - Temporary MP3 file is created
   - Transcription is performed on the MP3
   - Temporary MP3 file is deleted after transcription
5. If audio:
   - Transcription proceeds normally
6. Transcription result is saved and displayed

### System Requirements
- **FFmpeg**: Required for video processing
  - Ubuntu/Debian: `sudo apt-get install ffmpeg`
  - macOS: `brew install ffmpeg`
  - Windows: Download from https://ffmpeg.org/download.html

### Supported Formats
**Audio**: MP3, WAV, M4A, OGG, FLAC, AAC, WMA
**Video**: MP4, AVI, MOV, MKV, FLV, WMV, WEBM

### Error Handling
- If video conversion fails, user receives clear error message
- Temporary files are always cleaned up, even if errors occur
- Detailed logging for debugging conversion issues

### Benefits
1. **User Experience**: Users can upload videos directly without external conversion tools
2. **Flexibility**: Supports meeting recordings, webinars, video conferences in native format
3. **Efficiency**: Automatic detection and conversion with no user intervention
4. **Resource Management**: Temporary files are cleaned up automatically

## Testing Checklist
- [ ] Upload MP4 video file and verify transcription
- [ ] Upload MP3 audio file and verify normal processing
- [ ] Verify temporary audio files are deleted after conversion
- [ ] Test with large video files (>25MB) to ensure splitting works
- [ ] Verify error handling when FFmpeg is not installed
- [ ] Check logs for proper detection and conversion messages

## Future Enhancements
- Support for more video formats
- Option to preserve audio quality settings
- Batch video processing
- Progress indicator for video conversion
