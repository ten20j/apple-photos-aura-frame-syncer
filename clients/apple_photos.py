import osxphotos
from osxphotos import PhotoExporter, ExportOptions, QueryOptions
import tempfile
import os
import random
import traceback
from typing import List, Optional, Tuple
from datetime import datetime, timedelta
from .logger import setup_logger

logger = setup_logger(__name__)

def export_photo_as_jpeg(photo, dest_dir):
    """Helper function to export a single photo as JPEG using PhotoExporter."""
    try:
        # Debug photo info
        logger.debug("Photo details:")
        logger.debug(f"- Filename: {getattr(photo, 'filename', 'unknown')}")
        logger.debug(f"- Path: {getattr(photo, 'path', 'unknown')}")
        logger.debug(f"- UUID: {getattr(photo, 'uuid', 'unknown')}")
        logger.debug(f"- Is in iCloud: {getattr(photo, 'incloud', 'unknown')}")
        logger.debug(f"- Is missing: {getattr(photo, 'ismissing', 'unknown')}")
        logger.debug(f"- Has adjustments: {getattr(photo, 'hasadjustments', 'unknown')}")
        
        # Try different paths that might exist
        possible_paths = [
            getattr(photo, 'path', None),  # Original path
            getattr(photo, 'path_edited', None),  # Edited version
            getattr(photo, 'path_original', None),  # Original version
        ]
        logger.debug("Available paths:")
        for path in possible_paths:
            if path:
                exists = os.path.exists(path)
                logger.debug(f"- {path} (exists: {exists})")
        
        logger.debug("Creating exporter for photo")
        exporter = PhotoExporter(photo)
        
        logger.debug("Setting up export options...")
        options = ExportOptions()
        options.convert_to_jpeg = True
        # Try to force local copy if in iCloud
        if getattr(photo, 'incloud', False):
            logger.info("Photo is in iCloud, attempting to download...")
            options.download_missing = True
        
        logger.debug(f"Exporting to directory: {dest_dir}")
        results = exporter.export(dest_dir, options=options)
        
        logger.debug(f"Export results type: {type(results)}")
        
        if hasattr(results, 'exported'):
            # Check for errors and issues
            if hasattr(results, 'error') and results.error:
                logger.error(f"Error during export: {results.error}")
            
            if hasattr(results, 'missing') and results.missing:
                logger.warning(f"Missing files: {results.missing}")
            
            if hasattr(results, 'skipped') and results.skipped:
                logger.warning(f"Skipped files: {results.skipped}")
            
            # Check conversion status
            if hasattr(results, 'converted_to_jpeg'):
                logger.debug(f"Converted to JPEG: {results.converted_to_jpeg}")
            
            paths = results.exported
            logger.debug("ExportResults details:")
            logger.debug(f"- Exported paths: {paths}")
            
            if not paths:
                logger.warning("ExportResults.exported is empty")
                # Try alternative export method if available
                try:
                    logger.info("Attempting alternative export method...")
                    if hasattr(photo, 'export2'):
                        alt_result = photo.export2(dest_dir, convert_to_jpeg=True)
                        logger.debug(f"Alternative export result: {alt_result}")
                        if alt_result and os.path.exists(alt_result):
                            return [alt_result]
                except Exception as e:
                    logger.error(f"Alternative export failed: {e}")
                
                # Check directory contents
                import glob
                actual_files = glob.glob(os.path.join(dest_dir, '*'))
                logger.debug(f"Files actually in directory: {actual_files}")
            
            return paths
        elif isinstance(results, (str, list)):
            paths = results if isinstance(results, list) else [results]
            logger.debug(f"Direct results paths: {paths}")
            return paths
        else:
            logger.warning(f"Unexpected export result type: {type(results)}")
            logger.warning(f"Result value: {results}")
            return []
    except Exception as e:
        logger.error(f"Error during export: {e}")
        logger.error(f"Traceback:\n{traceback.format_exc()}")
        return []

def list_albums() -> List[dict]:
    """
    Return a list of album information from the Photos library.
    Each album is represented as a dict with 'title', 'photo_count', and 'type'.
    """
    try:
        photosdb = osxphotos.PhotosDB()
        albums_dict = {}  # Use dict to deduplicate albums
        
        # Debug: Print all available attributes and methods
        logger.debug("Available PhotosDB attributes:")
        for attr in dir(photosdb):
            if not attr.startswith('_'):  # Skip private attributes
                logger.debug(f"- {attr}")
        
        # Process regular albums
        logger.info("Processing regular albums...")
        for album in photosdb.album_info:
            try:
                photos = album.photos
                title = str(album.title)
                # Debug: Print album details
                logger.debug(f"Album details for {title}:")
                for attr in dir(album):
                    if not attr.startswith('_'):
                        try:
                            value = getattr(album, attr)
                            # logger.debug(f"- {attr}: {value}")
                        except Exception as e:
                            logger.error(f"- {attr}: Error accessing ({e})")
                
                # Use album UUID as key to prevent duplicates
                album_uuid = getattr(album, 'uuid', title)
                albums_dict[album_uuid] = {
                    'title': title,
                    'photo_count': len(photos) if photos else 0,
                    'type': 'album' if not getattr(album, 'smart', False) else 'smart'
                }
                logger.info(f"Found album: {title} with {len(photos) if photos else 0} photos (UUID: {album_uuid})")
            except Exception as e:
                logger.error(f"Error processing album {getattr(album, 'title', 'Unknown')}: {e}")
                continue
        
        # Convert dict to list and sort
        albums = list(albums_dict.values())
        # Sort: Regular albums alphabetically first, then smart albums alphabetically
        albums.sort(key=lambda x: (x['type'] != 'album', x['title'].lower()))
        
        logger.info(f"Found {len(albums)} unique albums")
        logger.info("Final album list:")
        for album in albums:
            logger.info(f"- {album['title']} ({album['type']}, {album['photo_count']} photos)")
        
        return albums
    except Exception as e:
        logger.error(f"Error listing albums: {e}")
        return []

def get_children_photos(face_names):
    """
    Exports only the first photo for given face names to a temp directory and returns exported file paths (for testing).
    """
    photosdb = osxphotos.PhotosDB()
    all_photos = photosdb.photos()
    filtered_photos = [p for p in all_photos if any(name in (p.persons or []) for name in face_names)]
    if not filtered_photos:
        return []
    temp_dir = tempfile.mkdtemp(prefix="aura_photos_")
    # Only export the first matching photo
    photo = filtered_photos[0]
    return export_photo_as_jpeg(photo, temp_dir)

def list_all_person_names():
    photosdb = osxphotos.PhotosDB()
    return photosdb.persons

def get_sample_photos_for_person(person_name, max_samples=10):
    photosdb = osxphotos.PhotosDB()
    all_photos = photosdb.photos()
    logger.info(f"get_sample_photos_for_person: Found {len(all_photos)} total photos in library")
    filtered_photos = [p for p in all_photos if person_name in (p.persons or [])]
    if not filtered_photos:
        return []
    temp_dir = tempfile.mkdtemp(prefix="face_sample_")
    exported_paths = []
    for photo in filtered_photos[:max_samples]:
        paths = export_photo_as_jpeg(photo, temp_dir)
        exported_paths.extend(paths)
    return exported_paths

def export_random_photo():
    """
    Export a random photo from the Photos library to a temp directory and return its path (for testing email upload).
    """
    photosdb = osxphotos.PhotosDB()
    all_photos = photosdb.photos()
    logger.info(f"export_random_photo: Found {len(all_photos)} total photos in library")
    if not all_photos:
        return []
    photo = random.choice(all_photos)
    temp_dir = tempfile.mkdtemp(prefix="random_photo_")
    return export_photo_as_jpeg(photo, temp_dir)

def get_album_photos(album_name: str, sync_tracker=None) -> List[Tuple[str, List[str]]]:
    """
    Get photos from a specific album that haven't been synced yet.
    Returns a list of tuples: (photo_uuid, exported_paths)
    """
    logger.info(f"Looking for album: {album_name}")
    photosdb = osxphotos.PhotosDB()
    
    # Try regular albums first
    album = next((a for a in photosdb.album_info if str(a.title) == album_name), None)
    
    # If not found in regular albums, try smart albums
    if not album and hasattr(photosdb, 'albums'):
        album = next((a for a in photosdb.albums if str(a.title) == album_name), None)
    
    if not album:
        logger.warning(f"Album '{album_name}' not found")
        return []
    
    # Get photos from the album
    try:
        photos = album.photos
        if not photos:
            logger.warning(f"No photos found in album '{album_name}'")
            return []
        
        logger.info(f"Found {len(photos)} photos in album '{album_name}'")
    except Exception as e:
        logger.error(f"Error accessing album photos: {e}")
        return []
    
    # Create temp directory for exports
    try:
        temp_dir = tempfile.mkdtemp(prefix=f"album_{album_name}_")
    except Exception as e:
        logger.error(f"Error creating temp directory: {e}")
        return []
    
    # Export photos that haven't been synced
    results = []
    skipped_count = 0
    for i, photo in enumerate(photos, 1):
        try:
            # Get photo UUID
            photo_uuid = getattr(photo, 'uuid', None)
            if not photo_uuid:
                skipped_count += 1
                continue
            
            # Check if already synced
            if sync_tracker and sync_tracker.is_synced(photo_uuid, album_name):
                skipped_count += 1
                continue
            
            # Export the photo
            exported_paths = export_photo_as_jpeg(photo, temp_dir)
            if exported_paths:
                results.append((photo_uuid, exported_paths))
            else:
                logger.error(f"Failed to export photo {i}/{len(photos)}")
        except Exception as e:
            logger.error(f"Error processing photo {i}/{len(photos)}: {e}")
            continue
    
    logger.info("Export summary:")
    logger.info(f"- Total photos in album: {len(photos)}")
    logger.info(f"- Skipped (already synced/no UUID): {skipped_count}")
    logger.info(f"- Successfully exported: {len(results)}")
    return results 