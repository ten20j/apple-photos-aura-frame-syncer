import schedule
import time
import os
from datetime import datetime
from dotenv import load_dotenv
from server.jobs import sync_photos_to_aura
from clients.logger import setup_logger

# Set up logging
logger = setup_logger(__name__)

def sync_job():
    """Run the sync job for configured albums."""
    try:
        logger.info("Starting scheduled sync job")
        
        # Get album names from environment
        album_names = os.getenv("SYNC_ALBUMS", "").split(",")
        album_names = [name.strip() for name in album_names if name.strip()]
        
        if not album_names:
            logger.warning("No albums configured for sync. Set SYNC_ALBUMS in .env")
            return
        
        logger.info(f"Syncing {len(album_names)} albums: {', '.join(album_names)}")
        
        for album in album_names:
            try:
                logger.info(f"Processing album: {album}")
                success = sync_photos_to_aura(album)
                logger.info(f"Album '{album}' sync {'completed' if success else 'failed'}")
            except Exception as e:
                logger.error(f"Error syncing album '{album}': {e}")
                continue
        
        logger.info("Scheduled sync job completed")
    except Exception as e:
        logger.error(f"Error in sync job: {e}")

def main():
    """Main function to run the scheduler."""
    load_dotenv()
    
    # Log startup
    logger.info("Starting Aura Frame sync scheduler")
    logger.info("Scheduling sync job to run every 30 minutes")
    
    # Run immediately on startup
    sync_job()
    
    # Schedule to run every 30 minutes
    schedule.every(30).minutes.do(sync_job)
    
    # Keep running
    while True:
        try:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
        except KeyboardInterrupt:
            logger.info("Scheduler stopped by user")
            break
        except Exception as e:
            logger.error(f"Error in scheduler loop: {e}")
            # Wait a bit before retrying
            time.sleep(300)  # 5 minutes

if __name__ == "__main__":
    main() 