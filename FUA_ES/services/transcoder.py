import os
import time
import shutil
import tempfile
import subprocess
import threading
from pathlib import Path
import json

class TranscoderService:
    def __init__(self, media_folders: list[str], device: str = "gpu", 
                 cleanup_interval: int = 1800, inactive_timeout: int = 14400, 
                 active_threshold: int = 300):
        self.MEDIA_FOLDERS = media_folders
        self.device = device.lower() if device in ("gpu", "cpu") else "gpu"
        self.resolve_absolute_path = None
        self.hls_streams: dict[str, dict] = {}
        self.cleanup_interval = cleanup_interval
        self.inactive_timeout = inactive_timeout
        self.active_threshold = active_threshold
        self._cleanup_old_hls_directories()
        self._start_cleanup_thread()

    def _cleanup_old_hls_directories(self):
        try:
            hls_root = os.path.join(tempfile.gettempdir(), 'hls_streams')
            if not os.path.exists(hls_root):
                return
            for dir_name in os.listdir(hls_root):
                dir_path = os.path.join(hls_root, dir_name)
                if os.path.isdir(dir_path):
                    shutil.rmtree(dir_path, ignore_errors=True)
        except Exception:
            pass

    def _start_cleanup_thread(self):
        def _loop():
            while True:
                time.sleep(self.cleanup_interval)
                print(f"[HLS Cleanup] Running scheduled cleanup...")
                removed = self.cleanup_old_streams()
                print(f"[HLS Cleanup] Removed {removed} inactive stream(s)")
        t = threading.Thread(target=_loop, daemon=True)
        t.start()
        print(f"[HLS Cleanup] Background cleanup thread started (interval: {self.cleanup_interval}s)")

    def _cleanup_inactive_streams(self):
        to_remove = []
        for key, info in list(self.hls_streams.items()):
            proc = info.get('process')
            if proc and proc.poll() is not None:
                to_remove.append(key)
        for key in to_remove:
            self.cleanup_stream(key)

    def cleanup_stream(self, stream_key: str):
        info = self.hls_streams.pop(stream_key, None)
        if not info:
            return
        proc = info.get('process')
        if proc and proc.poll() is None:
            proc.terminate()
        temp_dir = info.get('temp_dir')
        if temp_dir and os.path.exists(temp_dir):
            shutil.rmtree(temp_dir, ignore_errors=True)

    def start_hls_stream(self, media_path: str, session_id: str | None = None, start_time: int = 0) -> str:
        stream_key = str(Path(media_path).as_posix())
        print(f"[HLS] Starting stream for: {media_path}")
        print(f"[HLS] Stream key: {stream_key}")
        print(f"[HLS] Active streams: {list(self.hls_streams.keys())}")
        
        existing = self.hls_streams.get(stream_key)
        if existing and self._is_stream_valid(existing):
            print(f"[HLS] Reusing existing valid stream: {stream_key}")
            if session_id:
                existing.setdefault('active_sessions', set()).add(session_id)
            existing['last_accessed'] = time.time()
            return stream_key
        elif existing:
            print(f"[HLS] Existing stream invalid, cleaning up: {stream_key}")
            self.cleanup_stream(stream_key)

        if not self.resolve_absolute_path:
            raise RuntimeError("Path resolver not set")
        absolute_path = self.resolve_absolute_path(media_path, self.MEDIA_FOLDERS)
        if not absolute_path or not os.path.exists(absolute_path):
            raise FileNotFoundError(media_path)

        import re
        safe_name = re.sub(r'[^\w\-_\.]', '_', Path(media_path).stem)
        stream_id = f"{safe_name}_{int(time.time())}"
        temp_dir = os.path.join(tempfile.gettempdir(), 'hls_streams', stream_id)
        os.makedirs(temp_dir, exist_ok=True)

        # For full-duration seeking support, always start from 0 (ignore start_time for HLS)
        # The player will handle seeking via the generated segments
        cmd = [
            'ffmpeg', '-hide_banner', '-loglevel', 'warning',
            '-i', str(absolute_path),
            '-map', '0:v:0', '-map', '0:a:0?',
            ('-c:v','h264_nvenc') if self.device=='gpu' else ('-c:v','libx264'),
            '-preset', 'p4' if self.device=='gpu' else 'veryfast',
            '-b:v', '3M', '-maxrate', '5M', '-bufsize', '10M',
            '-profile:v', 'main', '-level', '4.0', '-pix_fmt', 'yuv420p', '-vsync', 'cfr',
            '-c:a', 'aac', '-b:a', '128k', '-ac', '2', '-ar', '44100', '-af', 'aresample=async=1',
            '-sn', '-hls_time', '6', '-hls_list_size', '0', '-hls_flags', 'independent_segments',
            '-hls_segment_type', 'mpegts', '-start_number', '0',
            '-hls_segment_filename', os.path.join(temp_dir, 'segment_%03d.ts'),
            '-f', 'hls', os.path.join(temp_dir, 'playlist.m3u8')
        ]
        flat_cmd = []
        for part in cmd:
            if isinstance(part, tuple):
                flat_cmd.extend(list(part))
            else:
                flat_cmd.append(part)
        process = subprocess.Popen(flat_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        time.sleep(5)
        playlist_path = os.path.join(temp_dir, 'playlist.m3u8')
        if not os.path.exists(playlist_path):
            try:
                _, stderr = process.communicate(timeout=5)
            except Exception:
                pass
            self.cleanup_stream(stream_key)
            raise RuntimeError('Failed to create playlist')

        self.hls_streams[stream_key] = {
            'process': process,
            'temp_dir': temp_dir,
            'stream_id': stream_id,
            'start_time': time.time(),
            'last_accessed': time.time(),
            'media_path': str(absolute_path),
            'active_sessions': set([session_id]) if session_id else set()
        }
        print(f"[HLS] Created new stream: {stream_key} -> {stream_id}")
        print(f"[HLS] Temp dir: {temp_dir}")
        print(f"[HLS] Total active streams: {len(self.hls_streams)}")
        return stream_key

    def _is_stream_valid(self, info: dict) -> bool:
        temp_dir = info.get('temp_dir')
        playlist = os.path.join(temp_dir, 'playlist.m3u8') if temp_dir else None
        proc = info.get('process')
        return bool(temp_dir and os.path.exists(temp_dir) and os.path.exists(playlist) and proc and proc.poll() is None)

    def get_hls_playlist(self, stream_id: str, session_id: str | None = None) -> str | None:
        stream_key = str(Path(stream_id).as_posix())
        info = self.hls_streams.get(stream_key)
        if not info:
            return None
        info['last_accessed'] = time.time()
        if session_id:
            info.setdefault('active_sessions', set()).add(session_id)
        return os.path.join(info['temp_dir'], 'playlist.m3u8')

    def get_hls_segment(self, stream_id: str, segment_name: str, session_id: str | None = None) -> str | None:
        stream_key = str(Path(stream_id).as_posix())
        info = self.hls_streams.get(stream_key)
        if not info:
            return None
        info['last_accessed'] = time.time()
        if session_id:
            info.setdefault('active_sessions', set()).add(session_id)
        seg_path = os.path.join(info['temp_dir'], segment_name)
        return seg_path if os.path.exists(seg_path) else None

    def get_video_duration(self, media_path: str) -> float | None:
        """Get video duration in seconds using ffprobe."""
        if not self.resolve_absolute_path:
            return None
        absolute_path = self.resolve_absolute_path(media_path, self.MEDIA_FOLDERS)
        if not absolute_path or not os.path.exists(absolute_path):
            return None
        try:
            cmd = ['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'json', str(absolute_path)]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            data = json.loads(result.stdout)
            return float(data.get('format', {}).get('duration', 0))
        except Exception:
            return None

    def should_transcode_video(self, absolute_path: Path) -> bool:
        """Check if a video should be transcoded based on its format and codec."""
        try:
            ext = absolute_path.suffix.lower()
            if ext not in ['.mp4', '.mkv', '.avi', '.mov']:
                return True
            # MKV and AVI always need transcoding because browsers don't support these containers
            if ext in ['.mkv', '.avi']:
                return True
            # Check for HEVC/H.265 codec
            cmd = ['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=codec_name', '-of', 'json', str(absolute_path)]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                return True
            info = json.loads(result.stdout)
            if 'streams' not in info or not info['streams']:
                return True
            codec = info['streams'][0].get('codec_name', '').lower()
            # Always transcode HEVC/H.265
            if codec in ['hevc', 'h265']:
                return True
            # Check for unsupported codecs
            if codec not in ['h264', 'vp8', 'vp9', 'av1']:
                return True
            return False
        except Exception:
            return True

    def stream_video_pipe(self, media_path: str, start_time: int = 0):
        """Generator that transcodes video on-the-fly via FFmpeg pipe."""
        if not self.resolve_absolute_path:
            raise RuntimeError("Path resolver not set")
        absolute_path = self.resolve_absolute_path(media_path, self.MEDIA_FOLDERS)
        if not absolute_path or not absolute_path.is_file():
            raise FileNotFoundError(media_path)
        process = None
        try:
            cmd = ['ffmpeg', '-y', '-loglevel', 'error', '-hide_banner']
            if start_time > 0:
                cmd.extend(['-ss', str(start_time)])
            cmd.extend(['-i', str(absolute_path)])
            if self.device == 'gpu':
                cmd.extend(['-map', '0:v:0', '-c:v', 'h264_nvenc', '-preset', 'p4', '-b:v', '5M', '-maxrate', '7M', '-bufsize', '10M', '-profile:v', 'main', '-level', '4.1', '-pix_fmt', 'yuv420p', '-vsync', 'cfr'])
            else:
                cmd.extend(['-map', '0:v:0', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '23', '-maxrate', '5M', '-bufsize', '10M', '-profile:v', 'main', '-level', '4.1', '-pix_fmt', 'yuv420p', '-vsync', 'cfr'])
            cmd.extend(['-map', '0:a:0?', '-c:a', 'aac', '-b:a', '128k', '-ac', '2', '-ar', '44100', '-af', 'aresample=async=1'])
            cmd.extend(['-sn', '-f', 'mp4', '-movflags', 'frag_keyframe+empty_moov+default_base_moof', 'pipe:1'])
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=10*1024*1024)
            chunk_size = 8192 * 8
            try:
                while True:
                    chunk = process.stdout.read(chunk_size)
                    if not chunk:
                        break
                    yield chunk
                _, stderr = process.communicate()
                if process.returncode != 0:
                    raise RuntimeError(f"FFmpeg failed: {stderr.decode('utf-8', errors='replace')}")
            except GeneratorExit:
                if process and process.poll() is None:
                    process.terminate()
                raise
        except Exception as e:
            if process and process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
            raise RuntimeError(f"Transcoding error: {str(e)}") from e

    # ---- HLS Cleanup ----
    def _cleanup_old_hls_directories(self):
        """Clean up any existing HLS stream directories on startup."""
        try:
            import tempfile
            hls_root = os.path.join(tempfile.gettempdir(), 'hls_streams')
            if not os.path.exists(hls_root):
                return
            print(f"[HLS Startup] Cleaning up old HLS directories in {hls_root}")
            for dir_name in os.listdir(hls_root):
                dir_path = os.path.join(hls_root, dir_name)
                if os.path.isdir(dir_path):
                    try:
                        shutil.rmtree(dir_path, ignore_errors=True)
                        print(f"[HLS Startup] Removed old stream directory: {dir_path}")
                    except Exception as e:
                        print(f"[HLS Startup] Error removing {dir_path}: {e}")
        except Exception as e:
            print(f"[HLS Startup] Error during cleanup: {e}")

    def _start_cleanup_thread(self):
        """Start a background thread to periodically clean up old streams."""
        import threading
        def cleanup_loop():
            while True:
                try:
                    time.sleep(self.cleanup_interval)
                    self.cleanup_old_streams()
                except Exception as e:
                    print(f"[HLS Cleanup] Error in cleanup thread: {e}")
        cleanup_thread = threading.Thread(target=cleanup_loop, daemon=True)
        cleanup_thread.start()
        print(f"[HLS] Started background cleanup thread (runs every {self.cleanup_interval/60:.0f} minutes)")

    def cleanup_old_streams(self):
        """Clean up streams based on inactivity."""
        if not self.hls_streams:
            return 0
        current_time = time.time()
        streams_to_remove = []
        for stream_key, stream_info in list(self.hls_streams.items()):
            time_since_creation = current_time - stream_info['start_time']
            time_since_access = current_time - stream_info.get('last_accessed', stream_info['start_time'])
            is_active = time_since_access < self.active_threshold
            if not is_active and time_since_creation > self.inactive_timeout:
                print(f"[HLS Cleanup] Removing inactive stream: {stream_key}")
                self.cleanup_stream(stream_key)
                streams_to_remove.append(stream_key)
        for stream_key in streams_to_remove:
            self.hls_streams.pop(stream_key, None)
        return len(streams_to_remove)

    def cleanup_stream(self, stream_id):
        """Clean up a specific HLS stream."""
        if stream_id not in self.hls_streams:
            return
        stream_info = self.hls_streams[stream_id]
        # Terminate FFmpeg process
        if stream_info['process'].poll() is None:
            try:
                stream_info['process'].terminate()
                stream_info['process'].wait(timeout=5)
            except:
                try:
                    stream_info['process'].kill()
                except:
                    pass
        # Clean up temporary files
        try:
            if os.path.exists(stream_info['temp_dir']):
                shutil.rmtree(stream_info['temp_dir'], ignore_errors=True)
        except Exception as e:
            print(f"[HLS Cleanup] Error cleaning up {stream_info['temp_dir']}: {e}")

    def flush_all_hls_streams(self):
        """Flush all HLS streams and temporary directories."""
        import tempfile
        # Clean up all active streams
        for stream_key in list(self.hls_streams.keys()):
            self.cleanup_stream(stream_key)
        self.hls_streams.clear()
        # Remove all HLS directories
        hls_root = os.path.join(tempfile.gettempdir(), 'hls_streams')
        if os.path.exists(hls_root):
            try:
                shutil.rmtree(hls_root, ignore_errors=True)
                print(f"[HLS Flush] Removed all HLS directories from {hls_root}")
            except Exception as e:
                print(f"[HLS Flush] Error removing HLS root: {e}")

    def kill_all_ffmpeg(self):
        """Kill all active FFmpeg processes."""
        import psutil
        killed = 0
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    if 'ffmpeg' in proc.info['name'].lower():
                        proc.terminate()
                        killed += 1
                        print(f"[Kill FFmpeg] Terminated process {proc.info['pid']}")
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            # Also terminate all processes in hls_streams
            for stream_info in self.hls_streams.values():
                if stream_info['process'].poll() is None:
                    try:
                        stream_info['process'].kill()
                    except:
                        pass
            return killed
        except ImportError:
            # psutil not available, just kill processes in hls_streams
            for stream_info in self.hls_streams.values():
                if stream_info['process'].poll() is None:
                    try:
                        stream_info['process'].kill()
                        killed += 1
                    except:
                        pass
            return killed

    # ---- Embedded subtitle extraction ----
    def _ffprobe_streams(self, file_path: str) -> dict | None:
        try:
            cmd = [
                'ffprobe','-v','error','-show_entries',
                'stream=index,codec_type,codec_name,disposition:stream_tags=language,title',
                '-of','json', str(file_path)
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                return json.loads(result.stdout)
            return None
        except Exception:
            return None

    def _subtitle_streams(self, file_path: str) -> list[dict]:
        meta = self._ffprobe_streams(file_path)
        if not meta or 'streams' not in meta:
            return []
        out = []
        for s in meta['streams']:
            if s.get('codec_type') == 'subtitle':
                out.append({
                    'index': s.get('index', 0),
                    'codec': s.get('codec_name','unknown'),
                    'language': (s.get('tags', {}) or {}).get('language','und'),
                    'title': (s.get('tags', {}) or {}).get('title','')
                })
        return out

    def extract_embedded_subtitles(self, media_path: str) -> dict:
        try:
            if not self.resolve_absolute_path:
                return {'status':'error','message':'Path resolver not set'}
            absolute = self.resolve_absolute_path(media_path, self.MEDIA_FOLDERS)
            if not absolute or not absolute.exists():
                return {'status':'error','message':f'Media file not found: {media_path}'}
            output_dir = absolute.parent
            streams = self._subtitle_streams(str(absolute))
            if not streams:
                return {'status':'success','message':'No embedded subtitles found','subtitles':[]}
            extracted = []
            for s in streams:
                idx = s['index']; lang = s.get('language','und'); codec = s.get('codec','unknown'); title = (s.get('title') or '').strip()
                base = absolute.stem
                if title:
                    safe = ''.join(c for c in title if c.isalnum() or c in (' ','-','_')).strip().replace(' ','_')
                    out_name = f"{base}.{lang}.{safe}.srt"
                else:
                    out_name = f"{base}.{lang}.{idx}.srt"
                out_path = output_dir / out_name
                # Try extraction with re-encoding to srt
                cmd = ['ffmpeg','-v','warning','-i', str(absolute), '-map', f'0:s:{idx}','-c:s','srt','-f','srt','-y', str(out_path)]
                res = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace')
                if (res.returncode != 0 or not out_path.exists()) and codec.lower() == 'subrip':
                    # fallback copy if already subrip
                    cmd2 = ['ffmpeg','-v','warning','-i', str(absolute), '-map', f'0:s:{idx}?','-c:s','copy','-y', str(out_path)]
                    subprocess.run(cmd2, capture_output=True, text=True, encoding='utf-8', errors='replace')
                if out_path.exists():
                    extracted.append({'filename': out_path.name,'path': str(out_path.relative_to(output_dir)),'language': lang,'stream_index': idx})
            if extracted:
                return {'status':'success','message':f'Successfully extracted {len(extracted)} subtitle(s)','subtitles':extracted}
            return {'status':'error','message':'Failed to extract embedded subtitles','subtitles':[]}
        except Exception as e:
            return {'status':'error','message':str(e)}
