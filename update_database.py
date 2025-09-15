"""
Script to update the database schema by running migrations
"""
import os
import sys
import logging

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import migrate_database

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    try:
        logger.info("Starting database migration...")
        migrate_database()
        logger.info("Database migration completed successfully!")
    except Exception as e:
        logger.error(f"Database migration failed: {e}")
        sys.exit(1)