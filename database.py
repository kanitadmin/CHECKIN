"""
Database connection and schema management for Employee Check-in System
"""
import pymysql
import os
import logging
from contextlib import contextmanager
from typing import Optional, Dict, Any, List, Tuple
from dotenv import load_dotenv
from security_utils import validate_database_query, SecurityValidator

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DatabaseManager:
    """Database connection utility class with proper error handling and connection pooling"""
    
    def __init__(self):
        self.connection_config = {
            'host': os.getenv('DB_HOST'),
            'port': int(os.getenv('DB_PORT', 3306)),
            'user': os.getenv('DB_USER'),
            'password': os.getenv('DB_PASSWORD'),
            'database': os.getenv('DB_NAME'),
            'charset': 'utf8mb4',
            'autocommit': False,
            'connect_timeout': 10,
            'read_timeout': 10,
            'write_timeout': 10
        }
        
        # Validate required environment variables
        required_vars = ['DB_HOST', 'DB_USER', 'DB_PASSWORD', 'DB_NAME']
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
    
    def get_connection(self) -> pymysql.Connection:
        """
        Create a new database connection with enhanced retry logic and exponential backoff
        Returns: PyMySQL connection object
        Raises: DatabaseConnectionError on failure
        """
        max_retries = 3
        retry_count = 0
        base_delay = 1  # Base delay in seconds
        
        while retry_count < max_retries:
            try:
                connection = pymysql.connect(**self.connection_config)
                logger.info("Database connection established successfully")
                return connection
            except pymysql.OperationalError as e:
                retry_count += 1
                error_code = e.args[0] if e.args else 0
                
                # Handle specific MySQL error codes
                if error_code in (2003, 2006, 2013):  # Connection refused, lost, lost during query
                    logger.warning(f"Database connection attempt {retry_count}/{max_retries} failed (connection issue): {e}")
                elif error_code == 1045:  # Access denied
                    logger.error(f"Database authentication failed: {e}")
                    raise DatabaseConnectionError(f"Database authentication failed: {e}")
                elif error_code == 1049:  # Unknown database
                    logger.error(f"Database does not exist: {e}")
                    raise DatabaseConnectionError(f"Database '{self.connection_config['database']}' does not exist: {e}")
                else:
                    logger.warning(f"Database connection attempt {retry_count}/{max_retries} failed: {e}")
                
                if retry_count >= max_retries:
                    logger.error(f"Failed to connect to database after {max_retries} attempts")
                    raise DatabaseConnectionError(f"Could not connect to database after {max_retries} attempts: {e}")
                
                # Exponential backoff with jitter
                import random
                delay = base_delay * (2 ** (retry_count - 1)) + random.uniform(0, 1)
                logger.info(f"Retrying database connection in {delay:.2f} seconds...")
                import time
                time.sleep(delay)
                
            except pymysql.Error as e:
                retry_count += 1
                logger.warning(f"Database connection attempt {retry_count}/{max_retries} failed: {e}")
                if retry_count >= max_retries:
                    logger.error(f"Failed to connect to database after {max_retries} attempts")
                    raise DatabaseConnectionError(f"Could not connect to database: {e}")
        
        raise DatabaseConnectionError("Unexpected error in connection retry logic")
    
    @contextmanager
    def get_db_connection(self):
        """
        Context manager for database connections with automatic cleanup
        """
        connection = None
        try:
            connection = self.get_connection()
            yield connection
        except Exception as e:
            if connection:
                connection.rollback()
            logger.error(f"Database operation failed: {e}")
            raise
        finally:
            if connection:
                connection.close()
    
    def execute_query(self, query: str, params: Optional[Tuple] = None, fetch_results: bool = False) -> Optional[List[Dict[str, Any]]]:
        """
        Execute a SQL query with proper error handling and security validation
        
        Args:
            query: SQL query string with parameter placeholders
            params: Query parameters tuple
            fetch_results: Whether to fetch and return results
            
        Returns:
            List of dictionaries for SELECT queries, None for other queries
        """
        # Security validation
        if not validate_database_query(query, params):
            SecurityValidator.log_security_event(
                "INVALID_SQL_QUERY", 
                f"Blocked potentially dangerous query: {query[:100]}..."
            )
            raise DatabaseQueryError("Query failed security validation")
        
        with self.get_db_connection() as connection:
            try:
                with connection.cursor(pymysql.cursors.DictCursor) as cursor:
                    cursor.execute(query, params or ())
                    
                    if fetch_results:
                        results = cursor.fetchall()
                        connection.commit()
                        return results
                    else:
                        connection.commit()
                        return None
                        
            except pymysql.Error as e:
                connection.rollback()
                logger.error(f"Query execution failed: {e}")
                logger.error(f"Query: {query}")
                logger.error(f"Params: {params}")
                raise DatabaseQueryError(f"Query execution failed: {e}")
    
    def execute_script(self, script: str) -> None:
        """
        Execute a multi-statement SQL script
        
        Args:
            script: SQL script with multiple statements
        """
        with self.get_db_connection() as connection:
            try:
                # Split script into individual statements
                statements = [stmt.strip() for stmt in script.split(';') if stmt.strip()]
                
                with connection.cursor() as cursor:
                    for statement in statements:
                        if statement:
                            cursor.execute(statement)
                            logger.info(f"Executed: {statement[:50]}...")
                
                connection.commit()
                logger.info("Script execution completed successfully")
                
            except pymysql.Error as e:
                connection.rollback()
                logger.error(f"Script execution failed: {e}")
                raise DatabaseQueryError(f"Script execution failed: {e}")


class DatabaseConnectionError(Exception):
    """Custom exception for database connection errors"""
    pass


class DatabaseQueryError(Exception):
    """Custom exception for database query errors"""
    pass


# SQL Scripts for table creation
EMPLOYEES_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS employees (
    id INT AUTO_INCREMENT PRIMARY KEY,
    google_id VARCHAR(255) NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL UNIQUE,
    name VARCHAR(255),
    picture_url VARCHAR(255),
    role ENUM('employee', 'admin') DEFAULT 'employee',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_google_id (google_id),
    INDEX idx_email (email),
    INDEX idx_role (role)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
"""

ATTENDANCES_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS attendances (
    id INT AUTO_INCREMENT PRIMARY KEY,
    employee_id INT NOT NULL,
    check_in_time DATETIME NOT NULL,
    check_out_time DATETIME NULL,
    work_date DATE NOT NULL,
    latitude DECIMAL(10, 8) NULL,
    longitude DECIMAL(11, 8) NULL,
    location_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE,
    UNIQUE KEY unique_daily_checkin (employee_id, work_date),
    INDEX idx_employee_date (employee_id, work_date),
    INDEX idx_work_date (work_date),
    INDEX idx_location (latitude, longitude)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
"""

LOCATION_SETTINGS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS location_settings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    latitude DECIMAL(10, 8) NOT NULL,
    longitude DECIMAL(11, 8) NOT NULL,
    radius_meters INT NOT NULL DEFAULT 100,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_active (is_active),
    INDEX idx_location (latitude, longitude)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
"""

WORK_TIME_SETTINGS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS work_time_settings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    break_duration_minutes INT NOT NULL DEFAULT 60,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
"""


def initialize_database() -> None:
    """
    Initialize database by creating all required tables and indexes
    This function sets up the complete database schema
    """
    logger.info("Starting database initialization...")
    
    try:
        db_manager = DatabaseManager()
        
        # Create employees table
        logger.info("Creating employees table...")
        db_manager.execute_query(EMPLOYEES_TABLE_SQL)
        logger.info("Employees table created successfully")
        
        # Create attendances table
        logger.info("Creating attendances table...")
        db_manager.execute_query(ATTENDANCES_TABLE_SQL)
        logger.info("Attendances table created successfully")
        
        # Create location settings table
        logger.info("Creating location settings table...")
        db_manager.execute_query(LOCATION_SETTINGS_TABLE_SQL)
        logger.info("Location settings table created successfully")
        
        # Create work time settings table
        logger.info("Creating work time settings table...")
        db_manager.execute_query(WORK_TIME_SETTINGS_TABLE_SQL)
        logger.info("Work time settings table created successfully")
        
        # Run migrations for existing databases
        migrate_database()
        
        logger.info("Database initialization completed successfully")
        
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise


def migrate_database() -> None:
    """
    Run database migrations for existing installations
    """
    logger.info("Running database migrations...")
    
    try:
        db_manager = DatabaseManager()
        
        # Check if role column exists
        check_role_column_query = """
            SELECT COUNT(*) as count
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = %s 
            AND TABLE_NAME = 'employees' 
            AND COLUMN_NAME = 'role'
        """
        
        result = db_manager.execute_query(
            check_role_column_query, 
            (os.getenv('DB_NAME'),), 
            fetch_results=True
        )
        
        if result and result[0]['count'] == 0:
            logger.info("Adding role column to employees table...")
            add_role_column_query = """
                ALTER TABLE employees 
                ADD COLUMN role ENUM('employee', 'admin') DEFAULT 'employee' AFTER picture_url,
                ADD INDEX idx_role (role)
            """
            db_manager.execute_query(add_role_column_query)
            logger.info("Role column added successfully")
        else:
            logger.info("Role column already exists, skipping migration")
        
        logger.info("Database migrations completed successfully")
        
    except Exception as e:
        logger.error(f"Database migration failed: {e}")
        raise


def verify_database_schema() -> bool:
    """
    Verify that all required tables and indexes exist
    Returns: True if schema is valid, False otherwise
    """
    try:
        db_manager = DatabaseManager()
        
        # Check if employees table exists
        employees_check = db_manager.execute_query(
            "SHOW TABLES LIKE 'employees'", 
            fetch_results=True
        )
        
        # Check if attendances table exists
        attendances_check = db_manager.execute_query(
            "SHOW TABLES LIKE 'attendances'", 
            fetch_results=True
        )
        
        if not employees_check or not attendances_check:
            logger.error("Required tables are missing")
            return False
        
        # Verify foreign key constraint exists
        fk_check = db_manager.execute_query(
            """
            SELECT CONSTRAINT_NAME 
            FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE 
            WHERE TABLE_NAME = 'attendances' 
            AND REFERENCED_TABLE_NAME = 'employees'
            """,
            fetch_results=True
        )
        
        if not fk_check:
            logger.error("Foreign key constraint is missing")
            return False
        
        logger.info("Database schema verification passed")
        return True
        
    except Exception as e:
        logger.error(f"Schema verification failed: {e}")
        return False


if __name__ == "__main__":
    """
    Script entry point for database initialization
    """
    try:
        initialize_database()
        if verify_database_schema():
            print("Database schema setup completed successfully!")
        else:
            print("Database schema verification failed!")
    except Exception as e:
        print(f"Database setup failed: {e}")