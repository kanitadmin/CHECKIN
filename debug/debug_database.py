#!/usr/bin/env python3
"""
Debug script to test database connection and identify issues
"""

import os
import pymysql
from dotenv import load_dotenv
import time

# Load environment variables
load_dotenv()

def test_database_connection():
    """Test database connection with detailed error reporting"""
    
    print("🔍 Database Connection Debug")
    print("=" * 50)
    
    # Check environment variables
    print("1. Checking environment variables...")
    required_vars = ['DB_HOST', 'DB_USER', 'DB_PASSWORD', 'DB_NAME', 'DB_PORT']
    
    for var in required_vars:
        value = os.getenv(var)
        if value:
            if var == 'DB_PASSWORD':
                print(f"   ✅ {var}: {'*' * len(value)}")
            else:
                print(f"   ✅ {var}: {value}")
        else:
            print(f"   ❌ {var}: Not set")
    
    # Test connection
    print("\n2. Testing database connection...")
    
    try:
        connection_config = {
            'host': os.getenv('DB_HOST'),
            'port': int(os.getenv('DB_PORT', 3306)),
            'user': os.getenv('DB_USER'),
            'password': os.getenv('DB_PASSWORD'),
            'database': os.getenv('DB_NAME'),
            'charset': 'utf8mb4',
            'connect_timeout': 10,
            'read_timeout': 10,
            'write_timeout': 10
        }
        
        print(f"   Connecting to: {connection_config['host']}:{connection_config['port']}")
        print(f"   Database: {connection_config['database']}")
        print(f"   User: {connection_config['user']}")
        
        start_time = time.time()
        connection = pymysql.connect(**connection_config)
        end_time = time.time()
        
        print(f"   ✅ Connection successful! ({end_time - start_time:.2f}s)")
        
        # Test query
        with connection.cursor() as cursor:
            cursor.execute("SELECT VERSION()")
            version = cursor.fetchone()
            print(f"   ✅ MySQL Version: {version[0]}")
            
        connection.close()
        return True
        
    except pymysql.Error as e:
        print(f"   ❌ Database Error: {e}")
        return False
    except Exception as e:
        print(f"   ❌ Connection Error: {e}")
        return False

def test_tables():
    """Test if required tables exist"""
    
    print("\n3. Testing table structure...")
    
    try:
        connection_config = {
            'host': os.getenv('DB_HOST'),
            'port': int(os.getenv('DB_PORT', 3306)),
            'user': os.getenv('DB_USER'),
            'password': os.getenv('DB_PASSWORD'),
            'database': os.getenv('DB_NAME'),
            'charset': 'utf8mb4',
            'connect_timeout': 10
        }
        
        connection = pymysql.connect(**connection_config)
        
        required_tables = ['employees', 'attendances', 'location_settings']
        
        with connection.cursor() as cursor:
            cursor.execute("SHOW TABLES")
            existing_tables = [row[0] for row in cursor.fetchall()]
            
            for table in required_tables:
                if table in existing_tables:
                    print(f"   ✅ Table '{table}' exists")
                    
                    # Check table structure
                    cursor.execute(f"DESCRIBE {table}")
                    columns = cursor.fetchall()
                    print(f"      Columns: {len(columns)}")
                    
                else:
                    print(f"   ❌ Table '{table}' missing")
        
        connection.close()
        return True
        
    except Exception as e:
        print(f"   ❌ Error checking tables: {e}")
        return False

def suggest_solutions():
    """Suggest solutions for common database issues"""
    
    print("\n💡 Common Solutions")
    print("=" * 50)
    
    print("1. Network/Connection Issues:")
    print("   - Check if MySQL server is running")
    print("   - Verify firewall settings")
    print("   - Test network connectivity: ping 10.5.23.62")
    print("   - Try connecting from MySQL client")
    print()
    
    print("2. Authentication Issues:")
    print("   - Verify username and password")
    print("   - Check user permissions in MySQL")
    print("   - Ensure user can connect from your IP")
    print()
    
    print("3. Database Issues:")
    print("   - Verify database name exists")
    print("   - Check database permissions")
    print("   - Run: python database.py to create tables")
    print()
    
    print("4. Alternative Solutions:")
    print("   - Use local MySQL server")
    print("   - Use SQLite for development")
    print("   - Check with database administrator")
    print()

def create_local_config():
    """Create configuration for local development"""
    
    print("\n🔧 Local Development Setup")
    print("=" * 50)
    
    local_env = """
# Local Development Database Configuration
DB_HOST=localhost
DB_PORT=3306
DB_NAME=checkin_local
DB_USER=root
DB_PASSWORD=your_local_password

# Keep other settings the same
FLASK_SECRET_KEY=your-secret-key-here
FLASK_ENV=development

# Google OAuth Configuration (same as before)
GOOGLE_CLIENT_ID=1064430917847-ivi433ia0catrflerfvoq188topm8v7h.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=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
HOSTED_DOMAIN=go.buu.ac.th

# Application Configuration
REDIRECT_URI=http://localhost:5000/auth/callback
"""
    
    print("To use local MySQL:")
    print("1. Install MySQL locally")
    print("2. Create database: CREATE DATABASE checkin_local;")
    print("3. Update .env file with local settings:")
    print(local_env)
    print("4. Run: python database.py")

if __name__ == "__main__":
    success = test_database_connection()
    
    if success:
        test_tables()
        print("\n🎉 Database connection is working!")
    else:
        suggest_solutions()
        create_local_config()
    
    print("\n📞 Need Help?")
    print("- Check MySQL server status")
    print("- Contact database administrator")
    print("- Try local MySQL setup for development")