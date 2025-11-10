import os
from flask import Flask

from .config import Config
from .services.transcoder import TranscoderService
from .services.path_resolver import resolve_absolute_path
from .services.subtitles import SubtitleService
from .blueprints.playback import bp as playback_bp
from .blueprints.hls import bp as hls_bp
from .blueprints.subtitles import bp as subs_bp

def create_app(config_object: type | None = None) -> Flask:
    app = Flask(__name__, static_folder="static", template_folder="templates")
    app.config.from_object(config_object or Config)

    transcoder = TranscoderService(
        media_folders=app.config["MEDIA_FOLDERS"], 
        device=app.config["TRANSCODING_DEVICE"],
        cleanup_interval=app.config["HLS_CLEANUP_INTERVAL"],
        inactive_timeout=app.config["HLS_INACTIVE_TIMEOUT"],
        active_threshold=app.config["HLS_ACTIVE_THRESHOLD"]
    ) 
    transcoder.resolve_absolute_path = lambda media_path, _=None: resolve_absolute_path(media_path, app.config["MEDIA_FOLDERS"]) 

    subtitles = SubtitleService(
        api_key=app.config["OPENSUBTITLES_API_KEY"],
        username=app.config["OPENSUBTITLES_USERNAME"],
        password=app.config["OPENSUBTITLES_PASSWORD"],
        user_agent=app.config["OPENSUBTITLES_USER_AGENT"]
    )
    subtitles.resolve_absolute_path = lambda media_path, _=None: resolve_absolute_path(media_path, app.config["MEDIA_FOLDERS"]) 
    subtitles.MEDIA_FOLDERS = app.config["MEDIA_FOLDERS"]

    app.transcoder = transcoder
    app.subtitles = subtitles

    app.register_blueprint(playback_bp)
    app.register_blueprint(hls_bp)
    app.register_blueprint(subs_bp)

    return app
