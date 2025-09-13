"""
Integration tests for Employee model and repository with actual database
"""
import unittest
import os
from models import Employee, EmployeeRepository
from database import DatabaseManager, initialize_database, verify_database_schema


class TestEmployeeIntegration(unittest.TestCase):
    """Integration tests for Employee model with real database operations"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test database before running integration tests"""
        # Only run if we have database configuration
        required_env_vars = ['DB_HOST', 'DB_USER', 'DB_PASSWORD', 'DB_NAME']
        if not all(os.getenv(var) for var in required_env_vars):
            raise unittest.SkipTest("Database environment variables not configured")
        
        try:
            # Initialize database schema
            initialize_database()
            if not verify_database_schema():
                raise unittest.SkipTest("Database schema verification failed")
        except Exception as e:
            raise unittest.SkipTest(f"Database setup failed: {e}")
    
    def setUp(self):
        """Set up test data before each test"""
        self.repo = EmployeeRepository()
        self.test_google_info = {
            'sub': 'test_google_id_12345',
            'email': 'test.employee@company.com',
            'name': 'Test Employee',
            'picture': 'https://example.com/test.jpg'
        }
        
        # Clean up any existing test data
        self._cleanup_test_data()
    
    def tearDown(self):
        """Clean up test data after each test"""
        self._cleanup_test_data()
    
    def _cleanup_test_data(self):
        """Remove test employee data from database"""
        try:
            db_manager = DatabaseManager()
            db_manager.execute_query(
                "DELETE FROM employees WHERE google_id = %s OR email = %s",
                (self.test_google_info['sub'], self.test_google_info['email'])
            )
        except Exception:
            # Ignore cleanup errors
            pass
    
    def test_create_new_employee_integration(self):
        """Test creating a new employee with real database"""
        # Create employee
        employee = self.repo.create_or_update(self.test_google_info)
        
        # Verify employee was created
        self.assertIsInstance(employee, Employee)
        self.assertEqual(employee.google_id, self.test_google_info['sub'])
        self.assertEqual(employee.email, self.test_google_info['email'])
        self.assertEqual(employee.name, self.test_google_info['name'])
        self.assertEqual(employee.picture_url, self.test_google_info['picture'])
        self.assertIsNotNone(employee.id)
        self.assertIsNotNone(employee.created_at)
    
    def test_find_by_google_id_integration(self):
        """Test finding employee by Google ID with real database"""
        # Create employee first
        created_employee = self.repo.create_or_update(self.test_google_info)
        
        # Find by Google ID
        found_employee = self.repo.find_by_google_id(self.test_google_info['sub'])
        
        # Verify found employee matches created employee
        self.assertIsNotNone(found_employee)
        self.assertEqual(found_employee.id, created_employee.id)
        self.assertEqual(found_employee.google_id, created_employee.google_id)
        self.assertEqual(found_employee.email, created_employee.email)
    
    def test_find_by_email_integration(self):
        """Test finding employee by email with real database"""
        # Create employee first
        created_employee = self.repo.create_or_update(self.test_google_info)
        
        # Find by email
        found_employee = self.repo.find_by_email(self.test_google_info['email'])
        
        # Verify found employee matches created employee
        self.assertIsNotNone(found_employee)
        self.assertEqual(found_employee.id, created_employee.id)
        self.assertEqual(found_employee.email, created_employee.email)
        self.assertEqual(found_employee.google_id, created_employee.google_id)
    
    def test_find_by_id_integration(self):
        """Test finding employee by ID with real database (Flask-Login integration)"""
        # Create employee first
        created_employee = self.repo.create_or_update(self.test_google_info)
        
        # Find by ID
        found_employee = self.repo.find_by_id(created_employee.id)
        
        # Verify found employee matches created employee
        self.assertIsNotNone(found_employee)
        self.assertEqual(found_employee.id, created_employee.id)
        self.assertEqual(found_employee.email, created_employee.email)
        self.assertEqual(found_employee.google_id, created_employee.google_id)
    
    def test_update_existing_employee_integration(self):
        """Test updating existing employee with real database"""
        # Create employee first
        original_employee = self.repo.create_or_update(self.test_google_info)
        
        # Update employee info
        updated_google_info = self.test_google_info.copy()
        updated_google_info['name'] = 'Updated Test Employee'
        updated_google_info['picture'] = 'https://example.com/updated.jpg'
        
        # Update employee
        updated_employee = self.repo.create_or_update(updated_google_info)
        
        # Verify update
        self.assertEqual(updated_employee.id, original_employee.id)  # Same ID
        self.assertEqual(updated_employee.google_id, original_employee.google_id)  # Same Google ID
        self.assertEqual(updated_employee.name, 'Updated Test Employee')  # Updated name
        self.assertEqual(updated_employee.picture_url, 'https://example.com/updated.jpg')  # Updated picture
    
    def test_flask_login_integration(self):
        """Test Flask-Login UserMixin methods with real employee data"""
        # Create employee
        employee = self.repo.create_or_update(self.test_google_info)
        
        # Test Flask-Login methods
        self.assertTrue(employee.is_authenticated)
        self.assertTrue(employee.is_active)
        self.assertFalse(employee.is_anonymous)
        self.assertEqual(employee.get_id(), str(employee.id))
        
        # Test that get_id returns a string (required by Flask-Login)
        self.assertIsInstance(employee.get_id(), str)


if __name__ == '__main__':
    unittest.main()