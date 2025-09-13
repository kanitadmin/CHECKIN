"""
Unit tests for Employee data model and EmployeeRepository
"""
import unittest
from unittest.mock import Mock, patch, MagicMock
from models import Employee, EmployeeRepository
from database import DatabaseQueryError
import os


class TestEmployee(unittest.TestCase):
    """Test cases for Employee class and Flask-Login integration"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.employee_data = {
            'id': 1,
            'google_id': 'google_123456789',
            'email': 'john.doe@company.com',
            'name': 'John Doe',
            'picture_url': 'https://example.com/picture.jpg',
            'created_at': '2024-01-01 10:00:00'
        }
        self.employee = Employee(**self.employee_data)
    
    def test_employee_initialization(self):
        """Test Employee object initialization with all fields"""
        self.assertEqual(self.employee.id, 1)
        self.assertEqual(self.employee.google_id, 'google_123456789')
        self.assertEqual(self.employee.email, 'john.doe@company.com')
        self.assertEqual(self.employee.name, 'John Doe')
        self.assertEqual(self.employee.picture_url, 'https://example.com/picture.jpg')
        self.assertEqual(self.employee.created_at, '2024-01-01 10:00:00')
    
    def test_employee_initialization_minimal(self):
        """Test Employee object initialization with minimal required fields"""
        minimal_employee = Employee(
            id=2,
            google_id='google_987654321',
            email='jane.doe@company.com'
        )
        
        self.assertEqual(minimal_employee.id, 2)
        self.assertEqual(minimal_employee.google_id, 'google_987654321')
        self.assertEqual(minimal_employee.email, 'jane.doe@company.com')
        self.assertIsNone(minimal_employee.name)
        self.assertIsNone(minimal_employee.picture_url)
        self.assertIsNone(minimal_employee.created_at)
    
    def test_flask_login_get_id(self):
        """Test Flask-Login UserMixin get_id method returns string ID"""
        user_id = self.employee.get_id()
        self.assertEqual(user_id, '1')
        self.assertIsInstance(user_id, str)
    
    def test_flask_login_is_authenticated(self):
        """Test Flask-Login UserMixin is_authenticated property"""
        self.assertTrue(self.employee.is_authenticated)
    
    def test_flask_login_is_active(self):
        """Test Flask-Login UserMixin is_active property"""
        self.assertTrue(self.employee.is_active)
    
    def test_flask_login_is_anonymous(self):
        """Test Flask-Login UserMixin is_anonymous property"""
        self.assertFalse(self.employee.is_anonymous)
    
    def test_to_dict(self):
        """Test Employee to_dict method returns correct dictionary"""
        result = self.employee.to_dict()
        expected = {
            'id': 1,
            'google_id': 'google_123456789',
            'email': 'john.doe@company.com',
            'name': 'John Doe',
            'picture_url': 'https://example.com/picture.jpg',
            'created_at': '2024-01-01 10:00:00'
        }
        self.assertEqual(result, expected)
    
    def test_repr(self):
        """Test Employee string representation"""
        result = repr(self.employee)
        expected = "<Employee john.doe@company.com (ID: 1)>"
        self.assertEqual(result, expected)


class TestEmployeeRepository(unittest.TestCase):
    """Test cases for EmployeeRepository class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_db_manager = Mock()
        
        # Sample database row data
        self.sample_db_row = {
            'id': 1,
            'google_id': 'google_123456789',
            'email': 'john.doe@company.com',
            'name': 'John Doe',
            'picture_url': 'https://example.com/picture.jpg',
            'created_at': '2024-01-01 10:00:00'
        }
        
        # Sample Google OAuth user info
        self.google_user_info = {
            'sub': 'google_123456789',
            'email': 'john.doe@company.com',
            'name': 'John Doe',
            'picture': 'https://example.com/picture.jpg'
        }
    
    @patch('models.DatabaseManager')
    def test_repository_initialization(self, mock_db_manager_class):
        """Test EmployeeRepository initialization"""
        repo = EmployeeRepository()
        mock_db_manager_class.assert_called_once()
        self.assertIsNotNone(repo.db_manager)
    
    @patch('models.DatabaseManager')
    def test_find_by_google_id_success(self, mock_db_manager_class):
        """Test successful find_by_google_id operation"""
        # Setup mock
        mock_db_manager_class.return_value = self.mock_db_manager
        self.mock_db_manager.execute_query.return_value = [self.sample_db_row]
        
        # Execute
        repo = EmployeeRepository()
        result = repo.find_by_google_id('google_123456789')
        
        # Verify
        self.assertIsInstance(result, Employee)
        self.assertEqual(result.google_id, 'google_123456789')
        self.assertEqual(result.email, 'john.doe@company.com')
        
        # Verify database call
        expected_query = """
                SELECT id, google_id, email, name, picture_url, created_at
                FROM employees 
                WHERE google_id = %s
            """
        self.mock_db_manager.execute_query.assert_called_once()
        call_args = self.mock_db_manager.execute_query.call_args
        self.assertIn('google_id = %s', call_args[0][0])
        self.assertEqual(call_args[0][1], ('google_123456789',))
        self.assertTrue(call_args[1]['fetch_results'])
    
    @patch('models.DatabaseManager')
    def test_find_by_google_id_not_found(self, mock_db_manager_class):
        """Test find_by_google_id when employee not found"""
        # Setup mock
        mock_db_manager_class.return_value = self.mock_db_manager
        self.mock_db_manager.execute_query.return_value = []
        
        # Execute
        repo = EmployeeRepository()
        result = repo.find_by_google_id('nonexistent_google_id')
        
        # Verify
        self.assertIsNone(result)
    
    @patch('models.DatabaseManager')
    def test_find_by_google_id_database_error(self, mock_db_manager_class):
        """Test find_by_google_id with database error"""
        # Setup mock
        mock_db_manager_class.return_value = self.mock_db_manager
        self.mock_db_manager.execute_query.side_effect = DatabaseQueryError("Database connection failed")
        
        # Execute and verify exception
        repo = EmployeeRepository()
        with self.assertRaises(DatabaseQueryError):
            repo.find_by_google_id('google_123456789')
    
    @patch('models.DatabaseManager')
    def test_find_by_email_success(self, mock_db_manager_class):
        """Test successful find_by_email operation"""
        # Setup mock
        mock_db_manager_class.return_value = self.mock_db_manager
        self.mock_db_manager.execute_query.return_value = [self.sample_db_row]
        
        # Execute
        repo = EmployeeRepository()
        result = repo.find_by_email('john.doe@company.com')
        
        # Verify
        self.assertIsInstance(result, Employee)
        self.assertEqual(result.email, 'john.doe@company.com')
        self.assertEqual(result.google_id, 'google_123456789')
        
        # Verify database call
        self.mock_db_manager.execute_query.assert_called_once()
        call_args = self.mock_db_manager.execute_query.call_args
        self.assertIn('email = %s', call_args[0][0])
        self.assertEqual(call_args[0][1], ('john.doe@company.com',))
    
    @patch('models.DatabaseManager')
    def test_find_by_email_not_found(self, mock_db_manager_class):
        """Test find_by_email when employee not found"""
        # Setup mock
        mock_db_manager_class.return_value = self.mock_db_manager
        self.mock_db_manager.execute_query.return_value = []
        
        # Execute
        repo = EmployeeRepository()
        result = repo.find_by_email('nonexistent@company.com')
        
        # Verify
        self.assertIsNone(result)
    
    @patch('models.DatabaseManager')
    def test_find_by_id_success(self, mock_db_manager_class):
        """Test successful find_by_id operation (used by Flask-Login)"""
        # Setup mock
        mock_db_manager_class.return_value = self.mock_db_manager
        self.mock_db_manager.execute_query.return_value = [self.sample_db_row]
        
        # Execute
        repo = EmployeeRepository()
        result = repo.find_by_id(1)
        
        # Verify
        self.assertIsInstance(result, Employee)
        self.assertEqual(result.id, 1)
        self.assertEqual(result.email, 'john.doe@company.com')
        
        # Verify database call
        self.mock_db_manager.execute_query.assert_called_once()
        call_args = self.mock_db_manager.execute_query.call_args
        self.assertIn('id = %s', call_args[0][0])
        self.assertEqual(call_args[0][1], (1,))
    
    @patch('models.DatabaseManager')
    def test_create_or_update_new_employee(self, mock_db_manager_class):
        """Test create_or_update with new employee (creation path)"""
        # Setup mock
        mock_db_manager_class.return_value = self.mock_db_manager
        
        # Mock find_by_google_id to return None (employee doesn't exist)
        self.mock_db_manager.execute_query.side_effect = [
            [],  # find_by_google_id returns empty (not found)
            None,  # INSERT operation
            [self.sample_db_row]  # find_by_google_id after creation
        ]
        
        # Execute
        repo = EmployeeRepository()
        result = repo.create_or_update(self.google_user_info)
        
        # Verify
        self.assertIsInstance(result, Employee)
        self.assertEqual(result.google_id, 'google_123456789')
        self.assertEqual(result.email, 'john.doe@company.com')
        
        # Verify database calls
        self.assertEqual(self.mock_db_manager.execute_query.call_count, 3)
        
        # Check INSERT call
        insert_call = self.mock_db_manager.execute_query.call_args_list[1]
        self.assertIn('INSERT INTO employees', insert_call[0][0])
        self.assertEqual(insert_call[0][1], ('google_123456789', 'john.doe@company.com', 'John Doe', 'https://example.com/picture.jpg'))
    
    @patch('models.DatabaseManager')
    def test_create_or_update_existing_employee(self, mock_db_manager_class):
        """Test create_or_update with existing employee (update path)"""
        # Setup mock
        mock_db_manager_class.return_value = self.mock_db_manager
        
        # Mock find_by_google_id to return existing employee
        updated_row = self.sample_db_row.copy()
        updated_row['name'] = 'John Updated Doe'
        
        self.mock_db_manager.execute_query.side_effect = [
            [self.sample_db_row],  # find_by_google_id returns existing employee
            None,  # UPDATE operation
            [updated_row]  # find_by_id after update
        ]
        
        # Execute with updated info
        updated_google_info = self.google_user_info.copy()
        updated_google_info['name'] = 'John Updated Doe'
        
        repo = EmployeeRepository()
        result = repo.create_or_update(updated_google_info)
        
        # Verify
        self.assertIsInstance(result, Employee)
        self.assertEqual(result.name, 'John Updated Doe')
        
        # Verify UPDATE call
        update_call = self.mock_db_manager.execute_query.call_args_list[1]
        self.assertIn('UPDATE employees', update_call[0][0])
        self.assertEqual(update_call[0][1], ('john.doe@company.com', 'John Updated Doe', 'https://example.com/picture.jpg', 1))
    
    @patch('models.DatabaseManager')
    def test_create_or_update_missing_required_fields(self, mock_db_manager_class):
        """Test create_or_update with missing required fields"""
        # Setup
        mock_db_manager_class.return_value = self.mock_db_manager
        repo = EmployeeRepository()
        
        # Test missing 'sub' field
        invalid_info = {'email': 'test@company.com'}
        with self.assertRaises(ValueError) as context:
            repo.create_or_update(invalid_info)
        self.assertIn('Missing required fields', str(context.exception))
        self.assertIn('sub', str(context.exception))
        
        # Test missing 'email' field
        invalid_info = {'sub': 'google_123'}
        with self.assertRaises(ValueError) as context:
            repo.create_or_update(invalid_info)
        self.assertIn('Missing required fields', str(context.exception))
        self.assertIn('email', str(context.exception))
    
    @patch('models.DatabaseManager')
    def test_create_or_update_minimal_google_info(self, mock_db_manager_class):
        """Test create_or_update with minimal Google OAuth info (no name/picture)"""
        # Setup mock
        mock_db_manager_class.return_value = self.mock_db_manager
        
        minimal_row = {
            'id': 2,
            'google_id': 'google_minimal',
            'email': 'minimal@company.com',
            'name': None,
            'picture_url': None,
            'created_at': '2024-01-01 10:00:00'
        }
        
        self.mock_db_manager.execute_query.side_effect = [
            [],  # find_by_google_id returns empty (not found)
            None,  # INSERT operation
            [minimal_row]  # find_by_google_id after creation
        ]
        
        # Execute with minimal info
        minimal_google_info = {
            'sub': 'google_minimal',
            'email': 'minimal@company.com'
        }
        
        repo = EmployeeRepository()
        result = repo.create_or_update(minimal_google_info)
        
        # Verify
        self.assertIsInstance(result, Employee)
        self.assertEqual(result.google_id, 'google_minimal')
        self.assertEqual(result.email, 'minimal@company.com')
        self.assertIsNone(result.name)
        self.assertIsNone(result.picture_url)
        
        # Check INSERT call with None values
        insert_call = self.mock_db_manager.execute_query.call_args_list[1]
        self.assertEqual(insert_call[0][1], ('google_minimal', 'minimal@company.com', None, None))


if __name__ == '__main__':
    # Run tests
    unittest.main()