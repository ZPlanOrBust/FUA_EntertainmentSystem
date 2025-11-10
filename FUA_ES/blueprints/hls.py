from flask import Blueprint, current_app, request, Response, send_file, session, jsonify
import os

bp = Blueprint('hls', __name__)

@bp.route('/api/flush-hls', methods=['POST'])
def flush_hls_streams():
    """Flush all HLS streams and temporary directories."""
    try:
        current_app.transcoder.flush_all_hls_streams()
        return jsonify({'status': 'success', 'message': 'HLS cache cleared successfully'})
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500

@bp.route('/api/kill-ffmpeg', methods=['POST'])
def kill_ffmpeg():
    """Kill all active FFmpeg processes."""
    try:
        count = current_app.transcoder.kill_all_ffmpeg()
        return jsonify({'status': 'success', 'message': f'Terminated {count} FFmpeg process(es)'})
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500

@bp.route('/hls/<path:stream_id>/<filename>')
def hls_playlist(stream_id, filename):
    transcoder = current_app.transcoder
    from urllib.parse import unquote
    stream_id = unquote(stream_id)
    response_headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type',
        'Cache-Control': 'no-cache, no-store, must-revalidate',
        'Pragma': 'no-cache',
        'Expires': '0'
    }
    if request.method == 'OPTIONS':
        return ('', 204, response_headers)
    if filename == 'playlist.m3u8':
        session_id = session.get('session_id') if 'session_id' in session else None
        playlist_path = transcoder.get_hls_playlist(stream_id, session_id=session_id)
        if not playlist_path or not os.path.exists(playlist_path):
            return ("Playlist not found", 404, response_headers)
        with open(playlist_path, 'r') as f:
            content = f.read()
        resp = Response(content, mimetype='application/vnd.apple.mpegurl', headers=response_headers)
        resp.headers['Content-Disposition'] = 'inline; filename=playlist.m3u8'
        return resp
    else:
        session_id = session.get('session_id') if 'session_id' in session else None
        segment_path = transcoder.get_hls_segment(stream_id, filename, session_id=session_id)
        if not segment_path or not os.path.exists(segment_path):
            return ("Segment not found", 404, response_headers)
        response = send_file(segment_path, mimetype='video/MP2T', conditional=True, download_name=filename)
        for k, v in response_headers.items():
            response.headers[k] = v
        return response
