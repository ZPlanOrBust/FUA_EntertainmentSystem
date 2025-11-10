from flask import Blueprint, current_app, jsonify, request, send_file, Response
from pathlib import Path
import os
import re

bp = Blueprint('subtitles', __name__)

def srt_to_vtt(srt_content):
    """Convert SRT subtitle format to WebVTT format."""
    vtt_content = "WEBVTT\n\n"
    # Replace SRT timestamp format (00:00:00,000) with VTT format (00:00:00.000)
    vtt_content += srt_content.replace(',', '.')
    return vtt_content

@bp.route('/find_subs/<path:media_path>', methods=['POST'])
def find_subs(media_path):
    data = request.get_json() or {}
    imdb_id = data.get('imdb_id')
    language = data.get('language', 'en')
    results, error = current_app.subtitles.find_subtitles(media_path, language_code=language, imdb_id=imdb_id)
    if error:
        return jsonify({'status': 'error', 'message': error, 'results': []}), 500
    language_name = 'Arabic' if language == 'ar' else 'English'
    if not results:
        return jsonify({'status': 'warning','message': f'No {language_name} subtitles found matching the query.','results': []}), 200
    return jsonify({'status': 'success','message': f'Found {len(results)} {language_name} subtitle candidates via Subliminal.','results': results}), 200

@bp.route('/download_sub/<path:media_path>', methods=['POST'])
def download_sub(media_path):
    data = request.get_json() or {}
    subtitle_data = data.get('subtitle_data', {})
    encoded = subtitle_data.get('file_id')
    title = subtitle_data.get('title', 'subtitle')
    msg = current_app.subtitles.download_subtitle(media_path, encoded, title)
    if msg.startswith('Successfully'):
        return jsonify({'status': 'success', 'message': msg}), 200
    return jsonify({'status': 'error', 'message': msg}), 500

@bp.route('/list_subtitles/<path:media_path>')
def list_subtitles(media_path):
    try:
        from urllib.parse import unquote
        media_path = unquote(media_path)
        
        print(f"[List Subtitles] media_path: {media_path}")
        
        # Use same path resolver as get_subtitle and delete_subtitle
        video_path = current_app.transcoder.resolve_absolute_path(media_path)
        
        print(f"[List Subtitles] video_path: {video_path}")
        
        if not video_path or not video_path.exists() or not video_path.is_file():
            return jsonify({'status': 'error', 'message': 'Video file not found'}), 404
        video_dir = video_path.parent
        
        print(f"[List Subtitles] video_dir: {video_dir}")
        
        subtitles = []
        for srt_file in video_dir.rglob('*.srt'):
            try:
                relative_to_video_dir = srt_file.relative_to(video_dir)
                filename = srt_file.name
                lang_match = re.search(r'[._]([a-z]{2,3})(?:[._]|$)', filename, re.IGNORECASE)
                language = lang_match.group(1).lower() if lang_match else 'und'
                if srt_file.parent == video_dir:
                    label = f"{srt_file.stem}"
                    source = 'same_dir'
                else:
                    folder_name = srt_file.parent.name
                    label = f"{folder_name}/{srt_file.stem}"
                    source = 'subfolder'
                
                subtitle_path = str(relative_to_video_dir.as_posix())
                print(f"[List Subtitles] Found subtitle: {subtitle_path}")
                
                subtitles.append({
                    'type': 'external',
                    'path': subtitle_path,
                    'filename': filename,
                    'label': label,
                    'language': language,
                    'source': source,
                    'size': os.path.getsize(srt_file)
                })
            except Exception as e:
                print(f"[List Subtitles] Error processing {srt_file}: {e}")
                continue
        
        print(f"[List Subtitles] Total subtitles found: {len(subtitles)}")
        return jsonify({'status': 'success', 'subtitles': subtitles}), 200
    except Exception as e:
        print(f"[List Subtitles] Error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@bp.route('/extract_subtitles/<path:media_path>', methods=['POST'])
def extract_subtitles(media_path):
    try:
        result = current_app.transcoder.extract_embedded_subtitles(media_path)
        status = 200 if result.get('status') == 'success' else 500
        return jsonify(result), status
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@bp.route('/get_subtitle')
def get_subtitle():
    """Serve subtitle files."""
    try:
        from urllib.parse import unquote
        from flask import request
        media_path = request.args.get('media_path', '')
        subtitle_path = request.args.get('subtitle_path', '')
        
        if not media_path or not subtitle_path:
            return jsonify({'status': 'error', 'message': 'Missing parameters'}), 400
        
        print(f"[Get Subtitle] media_path: {media_path}")
        print(f"[Get Subtitle] subtitle_path: {subtitle_path}")
        
        # Use path resolver to find video file
        video_path = current_app.transcoder.resolve_absolute_path(media_path)
        
        if not video_path or not video_path.exists():
            print(f"[Get Subtitle] Video file not found: {media_path}")
            return jsonify({'status': 'error', 'message': 'Video file not found'}), 404
        
        print(f"[Get Subtitle] video_path: {video_path}")
        
        # Subtitle path is relative to video directory
        video_dir = video_path.parent
        abs_subtitle_path = video_dir / subtitle_path
        
        print(f"[Get Subtitle] video_dir: {video_dir}")
        print(f"[Get Subtitle] abs_subtitle_path: {abs_subtitle_path}")
        print(f"[Get Subtitle] exists: {abs_subtitle_path.exists()}")
        
        if not abs_subtitle_path.exists() or not abs_subtitle_path.is_file():
            print(f"[Get Subtitle] File not found: {abs_subtitle_path}")
            return jsonify({'status': 'error', 'message': 'Subtitle file not found', 'path': str(abs_subtitle_path)}), 404
        
        # Read subtitle file with encoding fallback
        try:
            with open(abs_subtitle_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            # Try with different encoding if UTF-8 fails
            try:
                with open(abs_subtitle_path, 'r', encoding='cp1252') as f:
                    content = f.read()
            except Exception as e:
                print(f"[Get Subtitle] Encoding error: {e}")
                return jsonify({'status': 'error', 'message': 'Unsupported subtitle encoding'}), 400
        
        # Convert SRT to VTT if needed (browsers require VTT format)
        if abs_subtitle_path.suffix.lower() == '.srt':
            print(f"[Get Subtitle] Converting SRT to VTT")
            content = srt_to_vtt(content)
        
        # Return as VTT with proper headers
        response = Response(content, mimetype='text/vtt; charset=utf-8')
        response.headers['Content-Disposition'] = f'inline; filename="{abs_subtitle_path.stem}.vtt"'
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        print(f"[Get Subtitle] Serving subtitle successfully")
        return response
        
    except Exception as e:
        print(f"[Get Subtitle] Error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@bp.route('/delete_subtitle', methods=['DELETE'])
def delete_subtitle():
    try:
        from urllib.parse import unquote
        from flask import request
        media_path = request.args.get('media_path', '')
        subtitle_path = request.args.get('subtitle_path', '')
        
        if not media_path or not subtitle_path:
            return jsonify({'status': 'error', 'message': 'Missing parameters'}), 400
        
        print(f"[Delete Sub] media_path: {media_path}")
        print(f"[Delete Sub] subtitle_path: {subtitle_path}")
        
        # Use path resolver to find video file
        video_path = current_app.transcoder.resolve_absolute_path(media_path)
        
        if not video_path or not video_path.exists():
            print(f"[Delete Sub] Video file not found: {media_path}")
            return jsonify({'status': 'error', 'message': 'Video file not found', 'media_path': media_path}), 404
        
        print(f"[Delete Sub] video_path: {video_path}")
        
        # Subtitle path is relative to video directory
        video_dir = video_path.parent
        abs_subtitle_path = video_dir / subtitle_path
        
        print(f"[Delete Sub] video_dir: {video_dir}")
        print(f"[Delete Sub] abs_subtitle_path: {abs_subtitle_path}")
        print(f"[Delete Sub] exists: {abs_subtitle_path.exists()}")
        
        if not abs_subtitle_path.exists() or not abs_subtitle_path.is_file():
            return jsonify({'status': 'error', 'message': 'Subtitle file not found', 'path': str(abs_subtitle_path), 'video_dir': str(video_dir)}), 404
        
        if not str(abs_subtitle_path).lower().endswith(('.srt', '.vtt')):
            return jsonify({'status': 'error', 'message': 'Not a valid subtitle file'}), 400
        
        # Delete the file
        abs_subtitle_path.unlink()
        
        return jsonify({
            'status': 'success',
            'message': f'Deleted {abs_subtitle_path.name}'
        })
        
    except Exception as e:
        import traceback
        return jsonify({
            'status': 'error',
            'message': f'Error deleting subtitle: {str(e)}',
            'traceback': traceback.format_exc()
        }), 500
