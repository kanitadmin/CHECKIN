"""
Quick test for department functionality
"""
import os
import sys

# Add the project root to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def test_department_imports():
    """Test that we can import the department classes"""
    try:
        from models import DepartmentRepository, Department
        print("✓ Successfully imported Department classes")
        return True
    except Exception as e:
        print(f"✗ Failed to import Department classes: {e}")
        return False

def test_database_imports():
    """Test that we can import the database classes"""
    try:
        from database import DatabaseManager
        print("✓ Successfully imported DatabaseManager")
        return True
    except Exception as e:
        print(f"✗ Failed to import DatabaseManager: {e}")
        return False

if __name__ == "__main__":
    print("Running quick department tests...")
    
    success = True
    success &= test_department_imports()
    success &= test_database_imports()
    
    if success:
        print("\n✓ All quick tests passed!")
    else:
        print("\n✗ Some tests failed!")
        sys.exit(1)