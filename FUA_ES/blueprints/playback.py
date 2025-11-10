from flask import Blueprint, current_app, render_template, request, abort, send_file, Response
from pathlib import Path
import os

bp = Blueprint('playback', __name__)

VIDEO_EXTS = ('.mp4', '.mkv', '.avi', '.webm', '.mov', '.m4v', '.flv', '.wmv')

def has_video_files(directory_path: Path, max_depth=5, current_depth=0) -> bool:
    try:
        for item in os.listdir(directory_path):
            item_path = directory_path / item
            if item_path.is_file() and item_path.suffix.lower() in VIDEO_EXTS:
                return True
            elif item_path.is_dir() and current_depth < max_depth:
                if has_video_files(item_path, max_depth, current_depth + 1):
                    return True
    except Exception:
        pass
    return False

def get_current_directory_contents(relative_path=None):
    folders = []
    files = []
    parent_path = None
    media_folders = current_app.config['MEDIA_FOLDERS']
    from ..services.path_resolver import get_base_root_path

    if relative_path is None:
        for root in media_folders:
            root_path = Path(root)
            if root_path.is_dir() and has_video_files(root_path):
                folders.append(root_path.name)
        return {'folders': folders, 'files': [], 'current_path': None, 'parent_path': None}

    path_parts = Path(relative_path).parts
    parent_path = str(Path(*path_parts[:-1]).as_posix()) if len(path_parts) > 1 else ''

    base_root_path = get_base_root_path(relative_path, media_folders)
    if not base_root_path:
        return {'folders': [], 'files': [], 'current_path': relative_path, 'parent_path': parent_path}

    sub_path_parts = Path(relative_path).parts[1:]
    absolute_dir_to_scan = base_root_path
    for part in sub_path_parts:
        absolute_dir_to_scan = absolute_dir_to_scan / part

    if not absolute_dir_to_scan.is_dir():
        return {'folders': [], 'files': [], 'current_path': relative_path, 'parent_path': parent_path}

    for item in os.listdir(absolute_dir_to_scan):
        full_item_path = absolute_dir_to_scan / item
        next_relative_path = Path(relative_path) / item
        if full_item_path.is_dir():
            if has_video_files(full_item_path):
                folders.append(item)
        elif full_item_path.is_file() and full_item_path.suffix.lower() in VIDEO_EXTS:
            files.append({'name': item,'full_relative_path': str(next_relative_path.as_posix()),'display_name': item.replace('_', ' ').replace('.', ' ').title()})
    folders.sort()
    files.sort(key=lambda x: x['display_name'])
    return {'folders': folders, 'files': files, 'current_path': relative_path, 'parent_path': parent_path}

@bp.route('/')
def index():
    contents = get_current_directory_contents(None)
    return render_template('index.html', contents=contents, media_path=None)

@bp.route('/browse/<path:media_path>')
def browse_folder(media_path):
    contents = get_current_directory_contents(media_path)
    return render_template('index.html', contents=contents, media_path=media_path)


def is_apple_device(user_agent: str) -> bool:
    ua = user_agent.lower()
    apple_indicators = ['iphone', 'ipad', 'ipod', 'macintosh', 'safari']
    is_apple = any(ind in ua for ind in apple_indicators)
    if is_apple and ('chrome' in ua or 'firefox' in ua or 'edg' in ua):
        if 'iphone' not in ua and 'ipad' not in ua and 'ipod' not in ua:
            return False
    return is_apple

@bp.route('/video_info/<path:media_path>')
def video_info(media_path):
    """Get video metadata including duration."""
    from flask import jsonify
    duration = current_app.transcoder.get_video_duration(media_path)
    if duration is None:
        return jsonify({'status': 'error', 'message': 'Could not get video duration'}), 404
    return jsonify({'status': 'success', 'duration': duration})

@bp.route('/play/<path:media_path>')
def play_video(media_path):
    """Route for video playback page."""
    from ..services.path_resolver import resolve_absolute_path
    
    # Check if the file exists in any of the media folders
    absolute_path = resolve_absolute_path(media_path, current_app.config['MEDIA_FOLDERS'])
    if not absolute_path or not absolute_path.exists():
        return f"File not found: {media_path}", 404
        
    # Check if the file is a video
    if absolute_path.suffix.lower() not in ('.mp4', '.mkv', '.avi', '.webm', '.mov', '.m4v', '.flv', '.wmv'):
        return f"Unsupported file type: {absolute_path.suffix}", 400
    
    # Get video info for duration
    video_info = {}
    try:
        import subprocess
        import json
        
        # Use ffprobe to get video duration
        cmd = [
            'ffprobe',
            '-v', 'error',
            '-show_entries', 'format=duration',
            '-of', 'json',
            str(absolute_path)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
        if result.returncode == 0:
            data = json.loads(result.stdout)
            duration = float(data['format']['duration'])
            video_info['duration'] = duration
    except Exception as e:
        current_app.logger.error(f"Error getting video info: {e}")
    
    # Check if we need to transcode
    needs_transcoding = absolute_path.suffix.lower() not in ('.mp4', '.m4v')
    
    # For HLS mode, we need to check if the client is an Apple device
    user_agent = request.headers.get('User-Agent', '').lower()
    is_apple = any(device in user_agent for device in ['iphone', 'ipad', 'mac os x', 'safari'])
    
    # Default to HLS for Apple devices or if explicitly requested
    use_hls = 'hls' in request.args or is_apple
    
    # Get supported languages from config
    supported_languages = current_app.config.get('SUPPORTED_LANGUAGES', {'en': 'English'})
    
    if use_hls:
        return render_template('player_hls.html', 
                            media_path=media_path,
                            stream_url=f"/hls/playlist/{media_path}",
                            duration=video_info.get('duration', 0),
                            supported_languages=supported_languages,
                            default_language=current_app.config.get('DEFAULT_LANGUAGE', 'en'))
    else:
        return render_template('player_direct.html', 
                            media_path=media_path,
                            needs_transcoding=needs_transcoding,
                            duration=video_info.get('duration', 0),
                            supported_languages=supported_languages,
                            default_language=current_app.config.get('DEFAULT_LANGUAGE', 'en'))

@bp.route('/video/<path:media_path>')
def serve_video(media_path):
    absolute_path = current_app.transcoder.resolve_absolute_path(media_path, current_app.config['MEDIA_FOLDERS'])
    if not absolute_path or not absolute_path.exists() or not absolute_path.is_file():
        abort(404)
    
    # Check if transcoding is needed
    if current_app.transcoder.should_transcode_video(absolute_path):
        # Transcode on the fly
        start_time = request.args.get('start_time', type=int, default=0)
        print(f"[Transcode] {absolute_path.name} (codec requires transcoding)")
        generator = current_app.transcoder.stream_video_pipe(media_path, start_time=start_time)
        return Response(
            generator,
            mimetype='video/mp4',
            headers={
                'Content-Disposition': f'inline; filename="{absolute_path.stem}.mp4"',
                'Accept-Ranges': 'none',
                'Cache-Control': 'no-cache',
                'X-Content-Type-Options': 'nosniff',
                'Connection': 'keep-alive'
            }
        )
    
    # Direct streaming for compatible formats
    range_header = request.headers.get('Range', None)
    if not range_header:
        return send_file(absolute_path, mimetype=f"video/{absolute_path.suffix.lstrip('.').lower()}", conditional=True)
    size = absolute_path.stat().st_size
    byte1, byte2 = 0, None
    import re
    m = re.search(r'bytes=(\d+)-(\d*)', range_header)
    if m:
        g1 = m.group(1); g2 = m.group(2)
        byte1 = int(g1)
        if g2:
            byte2 = int(g2)
    length = size - byte1 if byte2 is None else byte2 - byte1 + 1
    with open(absolute_path, 'rb') as f:
        f.seek(byte1)
        data = f.read(length)
    rv = Response(data, 206, mimetype=f"video/{absolute_path.suffix.lstrip('.').lower()}", direct_passthrough=True)
    rv.headers.add('Content-Range', f'bytes {byte1}-{byte1 + length - 1}/{size}')
    rv.headers.add('Accept-Ranges', 'bytes')
    rv.headers.add('Content-Length', str(length))
    return rv
