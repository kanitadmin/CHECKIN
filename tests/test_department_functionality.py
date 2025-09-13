"""
Test department functionality
"""
import sys
import os
import time

# Add the project root to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from models import DepartmentRepository, Department
from database import DatabaseManager


def test_department_creation():
    """Test creating a department"""
    print("Testing department creation...")
    # Initialize repository
    dept_repo = DepartmentRepository()
    
    # Create a test department with unique name
    unique_name = f"Test Department {int(time.time())}"
    department = dept_repo.create_department(
        name=unique_name,
        description="A test department for unit testing"
    )
    
    # Verify the department was created
    assert department is not None
    assert department.name == unique_name
    assert department.description == "A test department for unit testing"
    print("✓ Department creation test passed")
    
    # Clean up - delete the department
    dept_repo.delete_department(department.id)
    return department.id


def test_get_all_departments():
    """Test getting all departments"""
    print("Testing get all departments...")
    # Initialize repository
    dept_repo = DepartmentRepository()
    
    # Create test departments with unique names
    timestamp = int(time.time())
    dept1 = dept_repo.create_department(
        name=f"HR Department {timestamp}",
        description="Human Resources"
    )
    
    dept2 = dept_repo.create_department(
        name=f"IT Department {timestamp}",
        description="Information Technology"
    )
    
    # Get all departments
    departments = dept_repo.get_all_departments()
    
    # Verify we have at least the two departments we created
    assert len(departments) >= 2
    
    # Check that our departments are in the list
    dept_names = [dept.name for dept in departments]
    assert f"HR Department {timestamp}" in dept_names
    assert f"IT Department {timestamp}" in dept_names
    print("✓ Get all departments test passed")
    
    # Clean up
    dept_repo.delete_department(dept1.id)
    dept_repo.delete_department(dept2.id)


def test_get_department_by_id():
    """Test getting a department by ID"""
    print("Testing get department by ID...")
    # Initialize repository
    dept_repo = DepartmentRepository()
    
    # Create a test department with unique name
    unique_name = f"Finance Department {int(time.time())}"
    department = dept_repo.create_department(
        name=unique_name,
        description="Financial Management"
    )
    
    # Get the department by ID
    retrieved_dept = dept_repo.get_department_by_id(department.id)
    
    # Verify the department was retrieved correctly
    assert retrieved_dept is not None
    assert retrieved_dept.id == department.id
    assert retrieved_dept.name == unique_name
    assert retrieved_dept.description == "Financial Management"
    print("✓ Get department by ID test passed")
    
    # Clean up
    dept_repo.delete_department(department.id)
    return department.id


def test_update_department():
    """Test updating a department"""
    print("Testing update department...")
    # Initialize repository
    dept_repo = DepartmentRepository()
    
    # Create a test department with unique name
    timestamp = int(time.time())
    department = dept_repo.create_department(
        name=f"Marketing Department {timestamp}",
        description="Marketing and Promotion"
    )
    
    # Update the department
    updated_dept = dept_repo.update_department(
        department_id=department.id,
        name=f"Sales Department {timestamp}",
        description="Sales and Customer Relations"
    )
    
    # Verify the department was updated
    assert updated_dept is not None
    assert updated_dept.name == f"Sales Department {timestamp}"
    assert updated_dept.description == "Sales and Customer Relations"
    print("✓ Update department test passed")
    
    # Clean up
    dept_repo.delete_department(department.id)


def test_delete_department():
    """Test deleting a department"""
    print("Testing delete department...")
    # Initialize repository
    dept_repo = DepartmentRepository()
    
    # Create a test department with unique name
    unique_name = f"Operations Department {int(time.time())}"
    department = dept_repo.create_department(
        name=unique_name,
        description="Operations Management"
    )
    
    # Delete the department
    result = dept_repo.delete_department(department.id)
    
    # Verify the department was deleted
    assert result is True
    
    # Try to retrieve the deleted department
    retrieved_dept = dept_repo.get_department_by_id(department.id)
    
    # Verify the department no longer exists
    assert retrieved_dept is None
    print("✓ Delete department test passed")


if __name__ == "__main__":
    # Run the tests
    print("Running department functionality tests...")
    try:
        test_department_creation()
        test_get_all_departments()
        test_get_department_by_id()
        test_update_department()
        test_delete_department()
        print("\n✓ All department tests passed!")
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)