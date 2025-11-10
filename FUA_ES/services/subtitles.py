"""Subtitle Service using OpenSubtitles.com REST API"""

from pathlib import Path
import json
from base64 import b64encode, b64decode
import struct
import os
import requests
from typing import Optional, Tuple, List, Dict

def compute_hash(filename, filesize):
    """Compute OpenSubtitles hash for video file."""
    try:
        longlongformat = 'q'  # long long
        bytesize = struct.calcsize(longlongformat)
        with open(filename, "rb") as f:
            filesize = filesize
            hash_value = filesize
            if filesize < 65536 * 2:
                return None
            for _ in range(65536 // bytesize):
                buffer = f.read(bytesize)
                (l_value,) = struct.unpack(longlongformat, buffer)
                hash_value += l_value
                hash_value &= 0xFFFFFFFFFFFFFFFF
            f.seek(max(0, filesize - 65536), 0)
            for _ in range(65536 // bytesize):
                buffer = f.read(bytesize)
                (l_value,) = struct.unpack(longlongformat, buffer)
                hash_value += l_value
                hash_value &= 0xFFFFFFFFFFFFFFFF
        return "%016x" % hash_value
    except:
        return None

class SubtitleService:
    """Service for searching and downloading subtitles using OpenSubtitles.com API."""
    
    API_BASE_URL = "https://api.opensubtitles.com/api/v1"
    
    def __init__(self, api_key: str = "", username: str = "", password: str = "", user_agent: str = "FUA_Entertainment_System v1.0.0"):
        self.resolve_absolute_path = None
        self.MEDIA_FOLDERS = None
        self.api_key = api_key
        self.username = username
        self.password = password
        self.user_agent = user_agent
        self.auth_token = None
        
        if api_key:
            # Try to login if username/password provided
            if username and password:
                self._login()
    
    def _get_headers(self) -> Dict[str, str]:
        """Get request headers with authentication."""
        headers = {
            "Content-Type": "application/json",
            "User-Agent": self.user_agent,
            "Accept": "application/json"
        }
        
        if self.api_key:
            headers["Api-Key"] = self.api_key
        
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"
        
        return headers
    
    def _login(self) -> bool:
        """Login to OpenSubtitles API to get auth token (optional, improves rate limits)."""
        if not self.username or not self.password:
            return False
        
        try:
            response = requests.post(
                f"{self.API_BASE_URL}/login",
                headers=self._get_headers(),
                json={"username": self.username, "password": self.password},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get("token")
                print("[OpenSubtitles] Successfully authenticated")
                return True
            else:
                print(f"[OpenSubtitles] Login failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"[OpenSubtitles] Login error: {e}")
            return False

    def _serialize_subtitle(self, subtitle_data: dict) -> str:
        """Serialize subtitle data for passing to download."""
        return b64encode(json.dumps(subtitle_data).encode('utf-8')).decode('utf-8')
    
    def _deserialize_subtitle(self, encoded_string: str) -> dict:
        """Deserialize subtitle data."""
        json_string = b64decode(encoded_string.encode('utf-8')).decode('utf-8')
        return json.loads(json_string)

    def find_subtitles_by_hash(self, media_path: str, language_code: str = 'en') -> Tuple[List[dict], Optional[str]]:
        """Find subtitles using hash-based search (most accurate)."""
        if not self.resolve_absolute_path or not self.MEDIA_FOLDERS:
            return [], 'Subtitle service not initialized'
        
        if not self.api_key:
            return [], 'OpenSubtitles API key not configured. Please set OPENSUBTITLES_API_KEY in config.'
        
        absolute_path = self.resolve_absolute_path(media_path, self.MEDIA_FOLDERS)
        if not absolute_path or not absolute_path.is_file():
            return [], 'Video file not found'
        
        try:
            # Compute file hash and size
            filesize = os.path.getsize(absolute_path)
            file_hash = compute_hash(str(absolute_path), filesize)
            
            if not file_hash:
                return [], 'Could not compute video hash'
            
            print(f"[OpenSubtitles] Searching by hash: {file_hash}, size: {filesize}")
            
            # Search by hash
            params = {
                "moviehash": file_hash,
                "languages": language_code,
            }
            
            response = requests.get(
                f"{self.API_BASE_URL}/subtitles",
                headers=self._get_headers(),
                params=params,
                timeout=30
            )
            
            if response.status_code != 200:
                return [], f'OpenSubtitles API error: {response.status_code} - {response.text}'
            
            data = response.json()
            subtitles_data = data.get('data', [])
            
            if not subtitles_data:
                return [], 'No subtitles found for this video'
            
            print(f"[OpenSubtitles] Found {len(subtitles_data)} subtitles by hash")
            
            return self._format_subtitle_results(subtitles_data), None
            
        except Exception as e:
            return [], f'Error searching subtitles by hash: {str(e)}'

    def find_subtitles(self, media_path: str, language_code: str = 'en', imdb_id: Optional[str] = None) -> Tuple[List[dict], Optional[str]]:
        """Find subtitles by filename or IMDB ID."""
        if not self.api_key:
            return [], 'OpenSubtitles API key not configured. Please set OPENSUBTITLES_API_KEY in config.'
        
        # First, try hash-based search (most accurate)
        results, error = self.find_subtitles_by_hash(media_path, language_code)
        if results:
            return results, None
        
        # Fallback to query search
        if not self.resolve_absolute_path or not self.MEDIA_FOLDERS:
            return [], 'Subtitle service not initialized'
        
        absolute_path = self.resolve_absolute_path(media_path, self.MEDIA_FOLDERS)
        if not absolute_path or not absolute_path.is_file():
            return [], 'Video file not found'
        
        try:
            # Extract movie/show name from filename
            query = absolute_path.stem
            
            print(f"[OpenSubtitles] Hash search failed, trying query: {query}")
            
            params = {
                "query": query,
                "languages": language_code,
            }
            
            if imdb_id:
                params["imdb_id"] = imdb_id.replace('tt', '')  # Remove 'tt' prefix if present
            
            response = requests.get(
                f"{self.API_BASE_URL}/subtitles",
                headers=self._get_headers(),
                params=params,
                timeout=30
            )
            
            if response.status_code != 200:
                return [], f'OpenSubtitles API error: {response.status_code} - {response.text}'
            
            data = response.json()
            subtitles_data = data.get('data', [])
            
            if not subtitles_data:
                return [], 'No subtitles found'
            
            print(f"[OpenSubtitles] Found {len(subtitles_data)} subtitles by query")
            
            return self._format_subtitle_results(subtitles_data), None
            
        except Exception as e:
            return [], f'Error searching subtitles: {str(e)}'
    
    def _format_subtitle_results(self, subtitles_data: List[dict]) -> List[dict]:
        """Format OpenSubtitles API results into our expected format."""
        results = []
        
        for item in subtitles_data:
            attributes = item.get('attributes', {})
            
            # Extract relevant info
            file_id = item.get('id')
            files = attributes.get('files', [])
            if not files:
                continue
            
            file_info = files[0]  # Get first file
            file_id_internal = file_info.get('file_id')
            
            # Language info
            language = attributes.get('language', 'en').upper()
            
            # Release info
            release_info = attributes.get('release', '')
            feature_details = attributes.get('feature_details', {})
            movie_name = feature_details.get('movie_name', '')
            
            # Uploader info
            uploader_info = attributes.get('uploader', {})
            uploader = uploader_info.get('name', 'Unknown')
            
            # Format title
            if release_info:
                clean_name = release_info.replace('.', ' ').replace('_', ' ').strip()
                title = f"OpenSubtitles - {language} - {clean_name}"
            elif movie_name:
                title = f"OpenSubtitles - {language} - {movie_name}"
            else:
                title = f"OpenSubtitles - {language} - Sub {str(file_id)[:8]}"
            
            # Serialize for download
            subtitle_data = {
                'file_id': file_id_internal,
                'language': language.lower(),
                'release_info': release_info,
                'movie_name': movie_name
            }
            serialized = self._serialize_subtitle(subtitle_data)
            
            results.append({
                'provider_name': 'OpenSubtitles',
                'id': str(file_id),
                'file_id': serialized,
                'score': attributes.get('ratings', 0),
                'is_hearing_impaired': attributes.get('hearing_impaired', False),
                'title': title,
                'language': language,
                'uploader': uploader,
                'release_info': release_info
            })
        
        return results

    def download_subtitle(self, media_path: str, encoded_sub_data: str, sub_title: str = 'subtitle') -> str:
        """Download subtitle using OpenSubtitles API."""
        if not self.api_key:
            return 'OpenSubtitles API key not configured. Please set OPENSUBTITLES_API_KEY in config.'
        
        if not self.resolve_absolute_path or not self.MEDIA_FOLDERS:
            return 'Subtitle service not initialized.'
        
        absolute_path = self.resolve_absolute_path(media_path, self.MEDIA_FOLDERS)
        if not absolute_path or not absolute_path.is_file():
            return 'Video file not found for download.'
        
        try:
            # Deserialize subtitle data
            sub_data = self._deserialize_subtitle(encoded_sub_data)
            file_id = sub_data.get('file_id')
            language = sub_data.get('language', 'en')
            release_info = sub_data.get('release_info', '')
            
            if not file_id:
                return 'Invalid subtitle data.'
            
            print(f"[OpenSubtitles] Downloading subtitle file_id: {file_id}")
            
            # Request download link
            response = requests.post(
                f"{self.API_BASE_URL}/download",
                headers=self._get_headers(),
                json={"file_id": file_id},
                timeout=30
            )
            
            if response.status_code != 200:
                return f'Failed to get download link: {response.status_code} - {response.text}'
            
            data = response.json()
            download_link = data.get('link')
            
            if not download_link:
                return 'No download link provided by API.'
            
            # Download subtitle content
            print(f"[OpenSubtitles] Downloading from: {download_link}")
            download_response = requests.get(download_link, timeout=30)
            
            if download_response.status_code != 200:
                return f'Failed to download subtitle content: {download_response.status_code}'
            
            content = download_response.content
            
            # Determine filename
            video_dir = absolute_path.parent
            
            if release_info:
                base_name = Path(release_info).stem
                sub_filename = f"{base_name}.{language}.srt"
            else:
                sub_filename = f"{absolute_path.stem}.{language}.srt"
            
            # Sanitize filename
            sub_filename = "".join(c for c in sub_filename if c.isalnum() or c in ' .-_')
            sub_save_path = video_dir / sub_filename
            
            # Save subtitle
            try:
                content_str = content.decode('utf-8')
            except UnicodeDecodeError:
                try:
                    content_str = content.decode('utf-8-sig')
                except UnicodeDecodeError:
                    content_str = content.decode('latin-1', errors='replace')
            
            with open(sub_save_path, 'w', encoding='utf-8-sig') as f:
                f.write(content_str)
            
            print(f"[OpenSubtitles] Saved subtitle to: {sub_save_path}")
            return f'Successfully downloaded and saved subtitle: "{sub_title}" as {sub_filename}.'
            
        except Exception as e:
            return f'Error downloading subtitle: {str(e)}'
