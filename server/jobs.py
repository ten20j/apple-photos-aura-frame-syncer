from clients.apple_photos import export_random_photo, get_album_photos
from clients.email_uploader import send_photos_via_email
from clients.sync_tracker import SyncTracker
from clients.logger import setup_logger

logger = setup_logger(__name__)

def sync_photos_to_aura(album_name=None):
    """
    Sync photos to Aura frame.
    If album_name is provided, syncs unsynced photos from that album.
    Otherwise, sends a random photo for testing.
    """
    try:
        if album_name:
            logger.info(f"Starting sync for album: {album_name}")
            
            # Initialize sync tracker
            try:
                sync_tracker = SyncTracker()
            except Exception as e:
                logger.error(f"Error initializing sync tracker: {e}")
                return False
            
            # Get unsynced photos from album
            try:
                photo_results = get_album_photos(album_name, sync_tracker)
                if not photo_results:
                    logger.info(f"No new photos to sync from album '{album_name}'")
                    return True  # Return success when there are no new photos to sync
            except Exception as e:
                logger.error(f"Error getting album photos: {e}")
                return False
            
            # Upload photos
            success = True
            total = len(photo_results)
            logger.info(f"Starting upload of {total} photos...")
            
            for i, (photo_uuid, photo_paths) in enumerate(photo_results, 1):
                try:
                    if send_photos_via_email(photo_paths):
                        sync_tracker.mark_synced(photo_uuid, album_name)
                        logger.info(f"Progress: {i}/{total} photos uploaded")
                    else:
                        logger.error(f"Failed to upload photo {i}/{total}")
                        success = False
                except Exception as e:
                    logger.error(f"Error uploading photo {i}/{total}: {e}")
                    success = False
            
            logger.info(f"Album sync completed. Success: {success}")
            return success
        else:
            # Test mode: just send a random photo
            logger.info("Starting random photo test sync")
            photo_paths = export_random_photo()
            if not photo_paths:
                logger.warning("No photos found in library.")
                return False
            success = send_photos_via_email(photo_paths)
            logger.info(f"Random photo sync completed. Success: {success}")
            return success
    except Exception as e:
        logger.error(f"Error during sync: {e}")
        return False 