# Configuration Guide

This document explains all available configuration options for the FUA Entertainment System.

## Quick Start

1. Copy `.env.example` to `.env`
2. Edit `.env` with your settings
3. Restart the application

```bash
copy .env.example .env
# Edit .env with your settings
py run.py
```

## Configuration Methods

Settings can be configured in three ways (in order of precedence):

1. **Environment Variables** - Highest priority
2. **`.env` file** - Loaded automatically
3. **`config.py` defaults** - Fallback values

---

## Media Library Settings

### `MEDIA_FOLDERS`
**Type:** String (semicolon-separated paths)  
**Default:** `D:\Movies`  
**Example:** `D:\Movies;E:\TV Shows;F:\Anime`

Root directories containing your video files. The application will scan these folders and their subdirectories.

### `VIDEO_EXTENSIONS`
**Type:** List (hardcoded in config.py)  
**Default:** `.mkv, .mp4, .avi, .mov, .wmv, .flv, .webm, .m4v`

File extensions recognized as video files.

### `SUBTITLE_EXTENSIONS`
**Type:** List (hardcoded in config.py)  
**Default:** `.srt, .vtt, .sub, .ass, .ssa`

File extensions recognized as subtitle files.

---

## Transcoding Settings

### `TRANSCODING_DEVICE`
**Type:** String (`gpu` or `cpu`)  
**Default:** `gpu`

Transcoding method:
- **`gpu`** - NVIDIA hardware acceleration (NVENC)
  - ✅ Much faster (10-20x)
  - ⚠️ Requires NVIDIA GPU with NVENC support
  - Recommended for real-time streaming
- **`cpu`** - Software encoding (libx264)
  - ✅ Works on any system
  - ❌ Slower, may struggle with 4K
  - Use if no NVIDIA GPU available

### `VIDEO_BITRATE`
**Type:** Integer (kbps)  
**Default:** `2500`  
**Range:** `500` - `10000`

Video quality in kilobits per second:
- **500-1000** - Low quality (mobile)
- **1500-2500** - Good quality (1080p)
- **3000-5000** - High quality (1080p)
- **6000+** - Very high quality (4K)

Higher = better quality but larger file size and more bandwidth.

### `AUDIO_BITRATE`
**Type:** Integer (kbps)  
**Default:** `192`  
**Range:** `96` - `320`

Audio quality:
- **96-128** - Acceptable
- **192** - Good (recommended)
- **256-320** - Excellent

### `VIDEO_RESOLUTION`
**Type:** String  
**Default:** `original`  
**Options:** `original`, `1080p`, `720p`, `480p`

Force video resolution during transcoding:
- **`original`** - Keep source resolution (recommended)
- **`1080p`** - Scale to 1920x1080
- **`720p`** - Scale to 1280x720 (saves bandwidth)
- **`480p`** - Scale to 854x480 (mobile/slow connections)

### `FFMPEG_PRESET`
**Type:** String  
**Default:** `veryfast`  
**Options:** `ultrafast`, `superfast`, `veryfast`, `faster`, `fast`, `medium`, `slow`, `slower`, `veryslow`

Encoding speed vs quality tradeoff:

| Preset      | Speed | Quality | CPU Usage | Use Case                    |
|-------------|-------|---------|-----------|------------------------------|
| ultrafast   | ⚡⚡⚡  | ⭐      | Low       | Testing only                 |
| superfast   | ⚡⚡   | ⭐⭐    | Low       | Very weak CPUs               |
| **veryfast**| ⚡⚡   | ⭐⭐⭐  | Medium    | **Recommended (default)**    |
| faster      | ⚡    | ⭐⭐⭐  | Medium    | Good balance                 |
| fast        | ⚡    | ⭐⭐⭐⭐ | High      | Better quality               |
| medium      | 🐌    | ⭐⭐⭐⭐ | High      | Offline encoding             |
| slow        | 🐌    | ⭐⭐⭐⭐⭐| Very High | Archive quality              |

---

## HLS Streaming Settings

### `HLS_SEGMENT_DURATION`
**Type:** Integer (seconds)  
**Default:** `4`  
**Range:** `2` - `10`

Length of each HLS segment (.ts file):
- **2-3** - Lower latency, more seeking precision, more files
- **4-6** - Good balance (recommended)
- **8-10** - Less overhead, less seeking precision

### `HLS_PLAYLIST_SIZE`
**Type:** Integer  
**Default:** `5`  
**Range:** `3` - `10`

Number of segments kept in the playlist:
- **3-5** - Less memory, faster startup (recommended)
- **6-10** - Better buffering, more memory

### `HLS_CLEANUP_INTERVAL`
**Type:** Integer (seconds)  
**Default:** `1800` (30 minutes)

How often to check for inactive streams and clean them up:
- **300** (5 min) - Aggressive cleanup, less disk usage
- **1800** (30 min) - Balanced (recommended)
- **3600** (1 hour) - Relaxed cleanup

### `HLS_INACTIVE_TIMEOUT`
**Type:** Integer (seconds)  
**Default:** `14400` (4 hours)

Remove streams that have been inactive for this long:
- **3600** (1 hour) - Aggressive
- **14400** (4 hours) - Balanced (recommended)
- **86400** (24 hours) - Very relaxed

### `HLS_ACTIVE_THRESHOLD`
**Type:** Integer (seconds)  
**Default:** `300` (5 minutes)

Consider a stream "active" if accessed within this time:
- **60** (1 min) - Very aggressive
- **300** (5 min) - Balanced (recommended)
- **600** (10 min) - Relaxed

### `HLS_TEMP_DIR`
**Type:** String (path)  
**Default:** `temp_hls`

Directory for HLS temporary files. Will be created if it doesn't exist.

---

## Subtitle Settings

### `SUPPORTED_LANGUAGES`
**Type:** Dictionary (language_code: display_name)  
**Default:** 
```python
{
    'en': 'English',
    'ar': 'العربية',  # Arabic
    'es': 'Español'   # Spanish
}
```

List of supported subtitle languages with their display names. 
- Keys are ISO 639-1 language codes
- Values are the display names in their native language
- Can be extended by adding more language codes and names

### `DEFAULT_LANGUAGE`
**Type:** String (language code)  
**Default:** `'en'`

The default language code used for subtitle search. Must be one of the keys in `SUPPORTED_LANGUAGES`.

### `SUBTITLE_SEARCH_TIMEOUT`
**Type:** Integer (seconds)  
**Default:** `30`

Maximum time to wait for subtitle search results.

### `SUBTITLE_HASH_SEARCH`
**Type:** Boolean (`true`/`false`)  
**Default:** `true`

Enable hash-based subtitle search:
- **`true`** - More accurate matching, slower
- **`false`** - Faster but less accurate

---

## Player Settings

### `DEFAULT_PLAYBACK_MODE`
**Type:** String  
**Default:** `auto`  
**Options:** `auto`, `direct`, `hls`

Default player mode:
- **`auto`** - Choose based on browser/file (recommended)
- **`direct`** - Always use direct streaming
- **`hls`** - Always use HLS streaming

### `PLAYER_MAX_VIDEO_HEIGHT`
**Type:** Integer (vh units)  
**Default:** `60`  
**Range:** `40` - `90`

Maximum video player height as percentage of viewport:
- **40-50** - Small player, more UI visible
- **60** - Balanced (recommended)
- **70-90** - Large player, less UI visible

### `DIRECT_TRANSCODE_SEEK`
**Type:** Boolean (`true`/`false`)  
**Default:** `false`

Enable seeking in transcoded direct streams:
- **`false`** - Disabled (recommended, seeking unreliable)
- **`true`** - Enabled (experimental, may cause issues)

---

## Server Settings

### `SECRET_KEY`
**Type:** String  
**Default:** Random (generated)

Flask secret key for sessions. **Set this in production!**

```bash
# Generate a secure key:
python -c "import secrets; print(secrets.token_hex(32))"
```

### `HOST`
**Type:** String (IP address)  
**Default:** `0.0.0.0`

Server binding address:
- **`0.0.0.0`** - All interfaces (accessible from network)
- **`127.0.0.1`** - Localhost only (secure, local access only)

### `PORT`
**Type:** Integer  
**Default:** `5000`

Server port number.

### `DEBUG`
**Type:** Boolean (`true`/`false`)  
**Default:** `false`

⚠️ **DO NOT enable in production!**
- **`false`** - Production mode (recommended)
- **`true`** - Debug mode (development only)

### `AUTO_RELOAD`
**Type:** Boolean (`true`/`false`)  
**Default:** `true`

Auto-restart server on code changes:
- **`true`** - Development (recommended)
- **`false`** - Production

---

## Logging Settings

### `VERBOSE_LOGGING`
**Type:** Boolean (`true`/`false`)  
**Default:** `false`

Enable detailed logging:
- **`false`** - Normal logging (recommended)
- **`true`** - Verbose logging (debugging)

### `LOG_FILE`
**Type:** String (path) or empty  
**Default:** Empty (console only)

Path to log file. Leave empty for console-only logging.

---

## Performance Settings

### `MAX_CONCURRENT_STREAMS`
**Type:** Integer  
**Default:** `10`

Maximum number of simultaneous HLS streams:
- **5** - Low-end systems
- **10** - Balanced (recommended)
- **20+** - High-end systems

### `STREAM_BUFFER_SIZE`
**Type:** Integer (bytes)  
**Default:** `1048576` (1MB)

Buffer size for video streaming:
- **524288** (512KB) - Low memory
- **1048576** (1MB) - Balanced (recommended)
- **2097152** (2MB) - High performance

### `ENABLE_FILE_CACHE`
**Type:** Boolean (`true`/`false`)  
**Default:** `true`

Cache file listings for faster browsing:
- **`true`** - Faster (recommended)
- **`false`** - Always scan (for rapidly changing libraries)

### `FILE_CACHE_DURATION`
**Type:** Integer (seconds)  
**Default:** `300` (5 minutes)

How long to cache file listings.

---

## Configuration Profiles

### Development
```python
from new_app.config import DevelopmentConfig
app = create_app(DevelopmentConfig)
```

- Debug enabled
- Verbose logging
- Auto-reload enabled

### Production
```python
from new_app.config import ProductionConfig
app = create_app(ProductionConfig)
```

- Debug disabled
- Normal logging
- Auto-reload disabled

---

## Recommended Configurations

### Home Network (Default)
```env
TRANSCODING_DEVICE=gpu
VIDEO_BITRATE=2500
FFMPEG_PRESET=veryfast
HLS_CLEANUP_INTERVAL=1800
```

### Low-End System / CPU Only
```env
TRANSCODING_DEVICE=cpu
VIDEO_BITRATE=1500
VIDEO_RESOLUTION=720p
FFMPEG_PRESET=veryfast
MAX_CONCURRENT_STREAMS=3
```

### High-End System / 4K Content
```env
TRANSCODING_DEVICE=gpu
VIDEO_BITRATE=5000
VIDEO_RESOLUTION=original
FFMPEG_PRESET=fast
MAX_CONCURRENT_STREAMS=20
```

### Remote Access / Slow Connection
```env
VIDEO_BITRATE=1500
VIDEO_RESOLUTION=720p
FFMPEG_PRESET=veryfast
HLS_SEGMENT_DURATION=6
```

---

## Troubleshooting

### Video won't play / stuttering
- Lower `VIDEO_BITRATE` (try 1500)
- Change to `TRANSCODING_DEVICE=cpu`
- Use `VIDEO_RESOLUTION=720p`

### Slow transcoding
- Change to `TRANSCODING_DEVICE=gpu`
- Use faster `FFMPEG_PRESET` (veryfast or superfast)
- Lower `VIDEO_BITRATE`

### High disk usage
- Lower `HLS_CLEANUP_INTERVAL` (600 = 10 min)
- Lower `HLS_INACTIVE_TIMEOUT` (1800 = 30 min)
- Lower `HLS_SEGMENT_DURATION`

### Seeking issues in HLS
- Lower `HLS_SEGMENT_DURATION` (2-3 seconds)
- Check `HLS_PLAYLIST_SIZE` (5-6 segments)

---

## Need Help?

Check the logs for detailed error messages:
```bash
VERBOSE_LOGGING=true py run.py
```
