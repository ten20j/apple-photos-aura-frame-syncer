from github import Github, InputFileContent
import json
import os
from datetime import datetime
from typing import List, Optional
from dotenv import load_dotenv
from .logger import setup_logger

load_dotenv()

logger = setup_logger(__name__)

class SyncTracker:
    def __init__(self):
        """Initialize sync tracker with GitHub token and Gist ID from environment."""
        logger.info("Initializing...")
        self.github_token = os.getenv("GITHUB_TOKEN")
        self.gist_id = os.getenv("SYNC_GIST_ID")
        
        if not self.github_token or not self.gist_id:
            raise ValueError("GITHUB_TOKEN and SYNC_GIST_ID must be set in .env")
        
        self.gh = Github(self.github_token)
        self.gist = self.gh.get_gist(self.gist_id)
        logger.info(f"Connected to Gist: {self.gist_id[:8]}...")
    
    def _load_synced_photos(self) -> dict:
        """Load the current state of synced photos from Gist."""
        try:
            content = self.gist.files["synced_photos.json"].content
            data = json.loads(content)
            logger.info(f"Loaded sync data: {len(data.get('synced_photos', {}))} photos tracked")
            return data
        except (KeyError, json.JSONDecodeError):
            logger.info("No existing sync data found, starting fresh")
            return {"synced_photos": {}}
        except Exception as e:
            logger.error(f"Error loading sync data: {e}")
            return {"synced_photos": {}}
    
    def _save_synced_photos(self, data: dict):
        """Save the updated state back to Gist."""
        try:
            self.gist.edit(
                files={
                    "synced_photos.json": InputFileContent(
                        json.dumps(data, indent=2)
                    )
                }
            )
            logger.info("Successfully saved sync data to Gist")
        except Exception as e:
            logger.error(f"Error saving sync data: {e}")
            raise
    
    def mark_synced(self, photo_uuid: str, album_name: str):
        """Mark a photo as synced with its album context."""
        logger.info(f"Marking photo as synced: {photo_uuid[:8]}... from album: {album_name}")
        data = self._load_synced_photos()
        data["synced_photos"][photo_uuid] = {
            "album": album_name,
            "synced_at": datetime.utcnow().isoformat(),
        }
        self._save_synced_photos(data)
    
    def is_synced(self, photo_uuid: str, album_name: str) -> bool:
        """Check if a photo has been synced from a specific album."""
        data = self._load_synced_photos()
        is_synced = (
            photo_uuid in data["synced_photos"] and
            data["synced_photos"][photo_uuid]["album"] == album_name
        )
        if is_synced:
            sync_time = data["synced_photos"][photo_uuid]["synced_at"]
            logger.debug(f"Photo {photo_uuid[:8]}... was synced at {sync_time}")
        return is_synced
    
    def get_synced_photos(self, album_name: Optional[str] = None) -> List[str]:
        """Get all synced photo UUIDs, optionally filtered by album."""
        data = self._load_synced_photos()
        if album_name:
            photos = [
                uuid for uuid, info in data["synced_photos"].items()
                if info["album"] == album_name
            ]
            logger.info(f"Found {len(photos)} synced photos in album: {album_name}")
            return photos
        
        photos = list(data["synced_photos"].keys())
        logger.info(f"Found {len(photos)} total synced photos")
        return photos
    
    def clear_album_history(self, album_name: str):
        """Clear sync history for a specific album."""
        logger.info(f"Clearing sync history for album: {album_name}")
        data = self._load_synced_photos()
        before_count = len(data["synced_photos"])
        data["synced_photos"] = {
            uuid: info for uuid, info in data["synced_photos"].items()
            if info["album"] != album_name
        }
        after_count = len(data["synced_photos"])
        removed = before_count - after_count
        logger.info(f"Removed {removed} photos from sync history")
        self._save_synced_photos(data) 