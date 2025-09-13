"""
Script to check if the departments table was created correctly
"""
import sys
import os
import time

# Add the project root to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database import DatabaseManager

def check_departments_table():
    """Check if the departments table exists and show its structure"""
    try:
        db_manager = DatabaseManager()
        
        # Check if departments table exists
        print("Checking if departments table exists...")
        result = db_manager.execute_query(
            "SHOW TABLES LIKE 'departments'", 
            fetch_results=True
        )
        
        if result:
            print("✓ Departments table exists")
        else:
            print("✗ Departments table does not exist")
            return False
        
        # Show table structure
        print("\nDepartments table structure:")
        result = db_manager.execute_query(
            "DESCRIBE departments", 
            fetch_results=True
        )
        
        if result:
            for row in result:
                print(f"  {row['Field']}: {row['Type']} {row['Null'] if row['Null'] == 'YES' else 'NOT NULL'} {row['Key'] if row['Key'] else ''} {row['Extra'] if row['Extra'] else ''}")
        else:
            print("✗ Could not retrieve table structure")
            return False
            
        # Check if we can insert a record
        print("\nTesting insert operation...")
        # Use a unique name with timestamp to avoid duplicates
        unique_name = f"Test Department {int(time.time())}"
        try:
            db_manager.execute_query(
                "INSERT INTO departments (name, description) VALUES (%s, %s)",
                (unique_name, "A test department")
            )
            print("✓ Insert operation successful")
            
            # Check if we can select the record
            result = db_manager.execute_query(
                "SELECT * FROM departments WHERE name = %s",
                (unique_name,),
                fetch_results=True
            )
            
            if result:
                print("✓ Select operation successful")
                print(f"  Retrieved: {result[0]['name']} - {result[0]['description']}")
                
                # Clean up - delete the test record
                db_manager.execute_query(
                    "DELETE FROM departments WHERE name = %s",
                    (unique_name,)
                )
                print("✓ Cleaned up test record")
            else:
                print("✗ Select operation failed")
                return False
                
        except Exception as e:
            print(f"✗ Insert operation failed: {e}")
            return False
            
        return True
        
    except Exception as e:
        print(f"✗ Error checking departments table: {e}")
        return False

if __name__ == "__main__":
    print("Checking departments table...")
    if check_departments_table():
        print("\n✓ All checks passed!")
    else:
        print("\n✗ Some checks failed!")
        sys.exit(1)