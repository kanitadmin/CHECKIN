"""
Integration tests for AttendanceRepository with database
"""
import unittest
import os
import sys
from datetime import datetime, date

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models import AttendanceRepository, EmployeeRepository
from database import DatabaseManager, DatabaseQueryError, initialize_database


class TestAttendanceRepositoryIntegration(unittest.TestCase):
    """Integration test cases for AttendanceRepository with real database"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test database once for all tests"""
        # Skip integration tests if database environment variables are not set
        required_vars = ['DB_HOST', 'DB_USER', 'DB_PASSWORD', 'DB_NAME']
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        
        if missing_vars:
            raise unittest.SkipTest(f"Skipping integration tests - missing environment variables: {', '.join(missing_vars)}")
        
        try:
            # Initialize database schema
            initialize_database()
            cls.db_manager = DatabaseManager()
        except Exception as e:
            raise unittest.SkipTest(f"Skipping integration tests - database setup failed: {e}")
    
    def setUp(self):
        """Set up test fixtures before each test method"""
        self.attendance_repo = AttendanceRepository()
        self.employee_repo = EmployeeRepository()
        
        # Clean up any existing test data
        self._cleanup_test_data()
        
        # Create a test employee
        self.test_employee = self._create_test_employee()
    
    def tearDown(self):
        """Clean up after each test"""
        self._cleanup_test_data()
    
    def _create_test_employee(self):
        """Create a test employee for use in attendance tests"""
        google_user_info = {
            'sub': 'test_google_id_123',
            'email': 'test.employee@company.com',
            'name': 'Test Employee',
            'picture': 'https://example.com/picture.jpg'
        }
        return self.employee_repo.create_or_update(google_user_info)
    
    def _cleanup_test_data(self):
        """Remove any test data from database"""
        try:
            # Delete test attendance records
            self.db_manager.execute_query(
                "DELETE FROM attendances WHERE employee_id IN (SELECT id FROM employees WHERE email LIKE 'test.%@company.com')"
            )
            # Delete test employees
            self.db_manager.execute_query(
                "DELETE FROM employees WHERE email LIKE 'test.%@company.com'"
            )
        except Exception:
            # Ignore cleanup errors
            pass
    
    def test_get_today_attendance_no_record(self):
        """Test get_today_attendance when no attendance record exists"""
        result = self.attendance_repo.get_today_attendance(self.test_employee.id)
        self.assertIsNone(result)
    
    def test_create_checkin_success(self):
        """Test successful check-in creation"""
        # Create check-in
        result = self.attendance_repo.create_checkin(self.test_employee.id)
        
        # Verify result structure
        self.assertIsNotNone(result)
        self.assertEqual(result['employee_id'], self.test_employee.id)
        self.assertIsNotNone(result['check_in_time'])
        self.assertIsNone(result['check_out_time'])
        self.assertEqual(result['work_date'], date.today())
    
    def test_create_checkin_duplicate_prevention(self):
        """Test that duplicate check-in is prevented"""
        # Create first check-in
        self.attendance_repo.create_checkin(self.test_employee.id)
        
        # Attempt duplicate check-in
        with self.assertRaises(DatabaseQueryError) as context:
            self.attendance_repo.create_checkin(self.test_employee.id)
        
        self.assertIn("already checked in today", str(context.exception))
    
    def test_update_checkout_success(self):
        """Test successful check-out update"""
        # Create check-in first
        checkin_result = self.attendance_repo.create_checkin(self.test_employee.id)
        
        # Update with check-out
        checkout_result = self.attendance_repo.update_checkout(self.test_employee.id)
        
        # Verify result
        self.assertIsNotNone(checkout_result)
        self.assertEqual(checkout_result['id'], checkin_result['id'])
        self.assertEqual(checkout_result['employee_id'], self.test_employee.id)
        self.assertIsNotNone(checkout_result['check_in_time'])
        self.assertIsNotNone(checkout_result['check_out_time'])
        self.assertEqual(checkout_result['work_date'], date.today())
    
    def test_update_checkout_no_checkin(self):
        """Test update_checkout when no check-in exists"""
        with self.assertRaises(DatabaseQueryError) as context:
            self.attendance_repo.update_checkout(self.test_employee.id)
        
        self.assertIn("has not checked in today", str(context.exception))
    
    def test_update_checkout_already_checked_out(self):
        """Test update_checkout when already checked out"""
        # Create check-in and check-out
        self.attendance_repo.create_checkin(self.test_employee.id)
        self.attendance_repo.update_checkout(self.test_employee.id)
        
        # Attempt second check-out
        with self.assertRaises(DatabaseQueryError) as context:
            self.attendance_repo.update_checkout(self.test_employee.id)
        
        self.assertIn("has already checked out today", str(context.exception))
    
    def test_get_recent_history_empty(self):
        """Test get_recent_history when no records exist"""
        result = self.attendance_repo.get_recent_history(self.test_employee.id)
        self.assertEqual(result, [])
    
    def test_get_recent_history_with_records(self):
        """Test get_recent_history with attendance records"""
        # Create a check-in/check-out record
        self.attendance_repo.create_checkin(self.test_employee.id)
        self.attendance_repo.update_checkout(self.test_employee.id)
        
        # Get history
        result = self.attendance_repo.get_recent_history(self.test_employee.id)
        
        # Verify result
        self.assertEqual(len(result), 1)
        record = result[0]
        self.assertEqual(record['employee_id'], self.test_employee.id)
        self.assertIsNotNone(record['check_in_time'])
        self.assertIsNotNone(record['check_out_time'])
        self.assertEqual(record['work_date'], date.today())
    
    def test_get_recent_history_custom_days(self):
        """Test get_recent_history with custom number of days"""
        # Create a record
        self.attendance_repo.create_checkin(self.test_employee.id)
        
        # Test with different day ranges
        result_7_days = self.attendance_repo.get_recent_history(self.test_employee.id, 7)
        result_30_days = self.attendance_repo.get_recent_history(self.test_employee.id, 30)
        
        # Both should contain the same record since it's from today
        self.assertEqual(len(result_7_days), 1)
        self.assertEqual(len(result_30_days), 1)
        self.assertEqual(result_7_days[0]['id'], result_30_days[0]['id'])


if __name__ == '__main__':
    unittest.main()