"""
Debug script for department by ID functionality
"""
import sys
import os
import time

# Add the project root to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from models import DepartmentRepository

def debug_get_department_by_id():
    """Debug getting a department by ID"""
    print("Debugging get department by ID...")
    # Initialize repository
    dept_repo = DepartmentRepository()
    
    # Create a test department with unique name
    unique_name = f"Finance Department {int(time.time())}"
    print(f"Creating department: {unique_name}")
    department = dept_repo.create_department(
        name=unique_name,
        description="Financial Management"
    )
    
    print(f"Created department with ID: {department.id}")
    
    # Get the department by ID
    print(f"Retrieving department by ID: {department.id}")
    retrieved_dept = dept_repo.get_department_by_id(department.id)
    
    print(f"Retrieved department: {retrieved_dept}")
    
    if retrieved_dept:
        print(f"Retrieved department details - ID: {retrieved_dept.id}, Name: {retrieved_dept.name}")
    
    # Clean up
    dept_repo.delete_department(department.id)
    print("Cleaned up test department")

if __name__ == "__main__":
    debug_get_department_by_id()