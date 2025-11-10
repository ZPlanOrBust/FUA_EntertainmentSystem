"""
Application Configuration
=========================
All configuration settings for the FUA Entertainment System.
Settings can be overridden via environment variables.
"""

import os
from pathlib import Path


def _parse_media_folders(env_value: str | None):
    """Parse semicolon-separated media folder paths from environment variable."""
    if not env_value:
        return [r"D:\Movies"]
    parts = [p.strip() for p in env_value.split(";") if p.strip()]
    return parts or [r"D:\Movies"]


class Config:
    """Base configuration class with all application settings."""
    
    # ============================================================================
    # MEDIA LIBRARY SETTINGS
    # ============================================================================
    
    # List of root media folders to scan for video files
    # Can be set via MEDIA_FOLDERS environment variable (semicolon-separated)
    # Example: MEDIA_FOLDERS="D:\Movies;E:\TV Shows;F:\Anime"
    MEDIA_FOLDERS = _parse_media_folders(os.getenv("MEDIA_FOLDERS"))
    
    # Video file extensions to recognize
    VIDEO_EXTENSIONS = ['.mkv', '.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm', '.m4v']
    
    # Subtitle file extensions to recognize
    SUBTITLE_EXTENSIONS = ['.srt', '.vtt', '.sub', '.ass', '.ssa']
    
    # ============================================================================
    # TRANSCODING SETTINGS
    # ============================================================================
    
    # Transcoding device: "gpu" for NVIDIA hardware acceleration, "cpu" for software encoding
    # GPU transcoding is significantly faster but requires NVIDIA GPU with NVENC support
    # Can be set via TRANSCODING_DEVICE environment variable
    TRANSCODING_DEVICE = os.getenv("TRANSCODING_DEVICE", "gpu").lower()
    
    # Video codec for transcoding
    # "h264_nvenc" for GPU, "libx264" for CPU
    VIDEO_CODEC = "h264_nvenc" if TRANSCODING_DEVICE == "gpu" else "libx264"
    
    # ============================================================================
    # SUBTITLE SETTINGS
    # ============================================================================
    
    # Supported subtitle languages with their ISO 639-1 codes and display names
    # Format: {'code': 'Language Name'}
    # Can be overridden via SUPPORTED_LANGUAGES environment variable as JSON
    SUPPORTED_LANGUAGES = {
        'en': 'English',
        'ar': 'العربية',  # Arabic
        'es': 'Español',  # Spanish

    }
    
    # Default language code for subtitles
    DEFAULT_LANGUAGE = 'en'
    
    # Video bitrate for transcoded streams (in kbps)
    VIDEO_BITRATE = int(os.getenv("VIDEO_BITRATE", "2500"))
    
    # Audio codec for transcoding
    AUDIO_CODEC = "aac"
    
    # Audio bitrate (in kbps)
    AUDIO_BITRATE = int(os.getenv("AUDIO_BITRATE", "192"))
    
    # Video resolution preset: "original", "1080p", "720p", "480p"
    VIDEO_RESOLUTION = os.getenv("VIDEO_RESOLUTION", "original")
    
    # FFmpeg preset for encoding speed vs quality tradeoff
    # Options: "ultrafast", "superfast", "veryfast", "faster", "fast", "medium", "slow", "slower", "veryslow"
    # Faster = lower quality/smaller file, Slower = higher quality/larger file
    FFMPEG_PRESET = os.getenv("FFMPEG_PRESET", "veryfast")
    
    # ============================================================================
    # HLS STREAMING SETTINGS
    # ============================================================================
    
    # HLS segment duration in seconds (each .ts file length)
    HLS_SEGMENT_DURATION = int(os.getenv("HLS_SEGMENT_DURATION", "4"))
    
    # Number of segments to keep in the playlist
    HLS_PLAYLIST_SIZE = int(os.getenv("HLS_PLAYLIST_SIZE", "5"))
    
    # HLS cleanup interval in seconds (how often to check for inactive streams)
    # Default: 1800 seconds (30 minutes)
    HLS_CLEANUP_INTERVAL = int(os.getenv("HLS_CLEANUP_INTERVAL", "1800"))
    
    # Stream inactive timeout in seconds (remove streams inactive for this long)
    # Default: 14400 seconds (4 hours)
    HLS_INACTIVE_TIMEOUT = int(os.getenv("HLS_INACTIVE_TIMEOUT", "14400"))
    
    # Active stream threshold in seconds (consider stream active if accessed within this time)
    # Default: 300 seconds (5 minutes)
    HLS_ACTIVE_THRESHOLD = int(os.getenv("HLS_ACTIVE_THRESHOLD", "300"))
    
    # Base directory for HLS temporary files
    HLS_TEMP_DIR = Path(os.getenv("HLS_TEMP_DIR", "temp_hls"))
    
    # ============================================================================
    # SUBTITLE SETTINGS (OpenSubtitles.com API)
    # ============================================================================
    
    # OpenSubtitles.com API Credentials
    # Register at: https://www.opensubtitles.com/en/users/newuser
    # Get API key at: https://www.opensubtitles.com/en/consumers
    OPENSUBTITLES_API_KEY = os.getenv("OPENSUBTITLES_API_KEY", "")
    
    # Optional: Your OpenSubtitles username (for better rate limits)
    OPENSUBTITLES_USERNAME = os.getenv("OPENSUBTITLES_USERNAME", "")
    OPENSUBTITLES_PASSWORD = os.getenv("OPENSUBTITLES_PASSWORD", "")
    
    # User Agent (required by OpenSubtitles API)
    # Format: AppName v1.0.0
    OPENSUBTITLES_USER_AGENT = os.getenv("OPENSUBTITLES_USER_AGENT", "FUA_Entertainment_System v1.0.0")
    
    # Default subtitle language codes (ISO 639-1)
    DEFAULT_SUBTITLE_LANGUAGES = ['en', 'ar']
    
    # Subtitle search timeout in seconds
    SUBTITLE_SEARCH_TIMEOUT = int(os.getenv("SUBTITLE_SEARCH_TIMEOUT", "30"))
    
    # Enable hash-based subtitle search (more accurate but slower)
    SUBTITLE_HASH_SEARCH = os.getenv("SUBTITLE_HASH_SEARCH", "true").lower() == "true"
    
    # Maximum number of subtitle results to return
    SUBTITLE_MAX_RESULTS = int(os.getenv("SUBTITLE_MAX_RESULTS", "20"))
    
    # ============================================================================
    # PLAYER SETTINGS
    # ============================================================================
    
    # Default playback mode: "auto", "direct", "hls"
    # "auto" = choose based on browser/file type
    # "direct" = always use direct streaming (transcoded if needed)
    # "hls" = always use HLS streaming
    DEFAULT_PLAYBACK_MODE = os.getenv("DEFAULT_PLAYBACK_MODE", "auto")
    
    # Enable seek in direct transcoded streams (experimental, may cause issues)
    DIRECT_TRANSCODE_SEEK = os.getenv("DIRECT_TRANSCODE_SEEK", "false").lower() == "true"
    
    # ============================================================================
    # FLASK/SERVER SETTINGS
    # ============================================================================
    
    # Flask secret key for sessions
    SECRET_KEY = os.getenv("SECRET_KEY", os.urandom(24).hex())
    
    # Debug mode (DO NOT enable in production!)
    DEBUG = os.getenv("DEBUG", "false").lower() == "true"
    
    # Server host
    HOST = os.getenv("HOST", "0.0.0.0")
    
    # Server port
    PORT = int(os.getenv("PORT", "5000"))
    
    # Enable/disable auto-reload on code changes
    AUTO_RELOAD = os.getenv("AUTO_RELOAD", "true").lower() == "true"
    
    # ============================================================================
    # LOGGING SETTINGS
    # ============================================================================
    
    # Enable verbose logging for debugging
    VERBOSE_LOGGING = os.getenv("VERBOSE_LOGGING", "false").lower() == "true"
    
    # Log file path (None = console only)
    LOG_FILE = os.getenv("LOG_FILE", None)
    
    # ============================================================================
    # PERFORMANCE SETTINGS
    # ============================================================================
    
    # Maximum number of concurrent HLS streams
    MAX_CONCURRENT_STREAMS = int(os.getenv("MAX_CONCURRENT_STREAMS", "10"))
    
    # Buffer size for video streaming (in bytes)
    STREAM_BUFFER_SIZE = int(os.getenv("STREAM_BUFFER_SIZE", "1048576"))  # 1MB
    
    # Enable file caching for faster library browsing
    ENABLE_FILE_CACHE = os.getenv("ENABLE_FILE_CACHE", "true").lower() == "true"
    
    # File cache duration in seconds
    FILE_CACHE_DURATION = int(os.getenv("FILE_CACHE_DURATION", "300"))  # 5 minutes


class DevelopmentConfig(Config):
    """Development configuration with debug features enabled."""
    DEBUG = True
    VERBOSE_LOGGING = True
    AUTO_RELOAD = True


class ProductionConfig(Config):
    """Production configuration with security and performance optimizations."""
    DEBUG = False
    VERBOSE_LOGGING = False
    AUTO_RELOAD = False
    # In production, you should set SECRET_KEY via environment variable
