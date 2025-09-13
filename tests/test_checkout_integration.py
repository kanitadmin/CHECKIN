"""
Integration tests for check-out functionality
Tests the check-out business logic and AttendanceRepository integration
"""
import unittest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from models import AttendanceRepository
from database import DatabaseQueryError


class TestCheckoutIntegration(unittest.TestCase):
    """Integration tests for check-out logic"""
    
    def setUp(self):
        """Set up test environment"""
        self.mock_db_manager = Mock()
        self.attendance_repo = AttendanceRepository(self.mock_db_manager)
        
        # Mock attendance data
        self.mock_checked_in_attendance = {
            'id': 1,
            'employee_id': 1,
            'check_in_time': datetime(2023, 12, 1, 9, 0, 0),
            'check_out_time': None,
            'work_date': '2023-12-01',
            'created_at': datetime(2023, 12, 1, 9, 0, 0)
        }
        
        self.mock_completed_attendance = {
            'id': 1,
            'employee_id': 1,
            'check_in_time': datetime(2023, 12, 1, 9, 0, 0),
            'check_out_time': datetime(2023, 12, 1, 17, 0, 0),
            'work_date': '2023-12-01',
            'created_at': datetime(2023, 12, 1, 9, 0, 0)
        }
    
    def test_successful_checkout_updates_record(self):
        """Test successful check-out updates attendance record with check_out_time"""
        # Setup: Employee has checked in today
        self.mock_db_manager.execute_query.side_effect = [
            [self.mock_checked_in_attendance],  # get_today_attendance call
            None,  # update query call
            [self.mock_completed_attendance]  # get_today_attendance call after update
        ]
        
        # Execute check-out
        result = self.attendance_repo.update_checkout(1)
        
        # Verify result
        self.assertEqual(result['id'], 1)
        self.assertEqual(result['employee_id'], 1)
        self.assertIsNotNone(result['check_out_time'])
        
        # Verify database calls
        self.assertEqual(self.mock_db_manager.execute_query.call_count, 3)
        
        # Verify update query was called with correct parameters
        update_call = self.mock_db_manager.execute_query.call_args_list[1]
        self.assertIn('UPDATE attendances', update_call[0][0])
        self.assertIn('SET check_out_time = NOW()', update_call[0][0])
        self.assertEqual(update_call[0][1], (1,))
    
    def test_checkout_fails_when_not_checked_in(self):
        """Test check-out fails when employee hasn't checked in today"""
        # Setup: No attendance record for today
        self.mock_db_manager.execute_query.return_value = []
        
        # Execute and verify exception
        with self.assertRaises(DatabaseQueryError) as context:
            self.attendance_repo.update_checkout(1)
        
        self.assertIn("has not checked in today", str(context.exception))
    
    def test_checkout_fails_when_already_checked_out(self):
        """Test check-out fails when employee has already checked out"""
        # Setup: Employee has already completed attendance
        self.mock_db_manager.execute_query.return_value = [self.mock_completed_attendance]
        
        # Execute and verify exception
        with self.assertRaises(DatabaseQueryError) as context:
            self.attendance_repo.update_checkout(1)
        
        self.assertIn("has already checked out today", str(context.exception))
    
    def test_checkout_handles_database_errors(self):
        """Test check-out handles database connection errors"""
        # Setup: Database error on get_today_attendance
        self.mock_db_manager.execute_query.side_effect = DatabaseQueryError("Connection failed")
        
        # Execute and verify exception propagation
        with self.assertRaises(DatabaseQueryError):
            self.attendance_repo.update_checkout(1)
    
    def test_checkout_validates_employee_id(self):
        """Test check-out validates employee_id parameter"""
        # Setup: Valid attendance record
        self.mock_db_manager.execute_query.side_effect = [
            [self.mock_checked_in_attendance],  # get_today_attendance call
            None,  # update query call
            [self.mock_completed_attendance]  # get_today_attendance call after update
        ]
        
        # Execute with different employee IDs
        result = self.attendance_repo.update_checkout(123)
        
        # Verify correct employee_id was used in queries
        get_call = self.mock_db_manager.execute_query.call_args_list[0]
        self.assertEqual(get_call[0][1], (123,))
        
        update_call = self.mock_db_manager.execute_query.call_args_list[1]
        self.assertEqual(update_call[0][1], (123,))


class TestCheckoutBusinessLogic(unittest.TestCase):
    """Test check-out business logic functions"""
    
    @patch('app.attendance_repo')
    def test_attendance_status_detection(self, mock_attendance_repo):
        """Test attendance status detection for different states"""
        from app import get_attendance_status, AttendanceStatus
        
        # Test NOT_CHECKED_IN status
        mock_attendance_repo.get_today_attendance.return_value = None
        status = get_attendance_status(1)
        self.assertEqual(status, AttendanceStatus.NOT_CHECKED_IN)
        
        # Test CHECKED_IN status
        mock_attendance_repo.get_today_attendance.return_value = {
            'check_in_time': datetime.now(),
            'check_out_time': None
        }
        status = get_attendance_status(1)
        self.assertEqual(status, AttendanceStatus.CHECKED_IN)
        
        # Test COMPLETED status
        mock_attendance_repo.get_today_attendance.return_value = {
            'check_in_time': datetime.now(),
            'check_out_time': datetime.now()
        }
        status = get_attendance_status(1)
        self.assertEqual(status, AttendanceStatus.COMPLETED)
    
    @patch('app.attendance_repo')
    def test_attendance_status_handles_errors(self, mock_attendance_repo):
        """Test attendance status detection handles database errors gracefully"""
        from app import get_attendance_status, AttendanceStatus
        
        # Setup: Database error
        mock_attendance_repo.get_today_attendance.side_effect = Exception("Database error")
        
        # Should default to NOT_CHECKED_IN on error
        status = get_attendance_status(1)
        self.assertEqual(status, AttendanceStatus.NOT_CHECKED_IN)


class TestCheckoutValidationScenarios(unittest.TestCase):
    """Test various check-out validation scenarios"""
    
    def setUp(self):
        """Set up test environment"""
        self.mock_db_manager = Mock()
        self.attendance_repo = AttendanceRepository(self.mock_db_manager)
    
    def test_checkout_with_valid_attendance_record(self):
        """Test check-out with a valid attendance record structure"""
        # Setup valid attendance record
        valid_attendance = {
            'id': 42,
            'employee_id': 5,
            'check_in_time': datetime(2023, 12, 1, 8, 30, 15),
            'check_out_time': None,
            'work_date': '2023-12-01',
            'created_at': datetime(2023, 12, 1, 8, 30, 15)
        }
        
        updated_attendance = valid_attendance.copy()
        updated_attendance['check_out_time'] = datetime(2023, 12, 1, 17, 45, 30)
        
        self.mock_db_manager.execute_query.side_effect = [
            [valid_attendance],  # get_today_attendance call
            None,  # update query call
            [updated_attendance]  # get_today_attendance call after update
        ]
        
        # Execute check-out
        result = self.attendance_repo.update_checkout(5)
        
        # Verify result structure
        self.assertEqual(result['id'], 42)
        self.assertEqual(result['employee_id'], 5)
        self.assertIsNotNone(result['check_out_time'])
        self.assertEqual(result['work_date'], '2023-12-01')
    
    def test_checkout_error_messages_are_descriptive(self):
        """Test that error messages provide clear information"""
        # Test not checked in error
        self.mock_db_manager.execute_query.return_value = []
        
        with self.assertRaises(DatabaseQueryError) as context:
            self.attendance_repo.update_checkout(1)
        
        error_message = str(context.exception)
        self.assertIn("Employee 1", error_message)
        self.assertIn("has not checked in today", error_message)
        
        # Test already checked out error
        completed_attendance = {
            'id': 1,
            'employee_id': 1,
            'check_in_time': datetime.now(),
            'check_out_time': datetime.now(),
            'work_date': '2023-12-01'
        }
        self.mock_db_manager.execute_query.return_value = [completed_attendance]
        
        with self.assertRaises(DatabaseQueryError) as context:
            self.attendance_repo.update_checkout(1)
        
        error_message = str(context.exception)
        self.assertIn("Employee 1", error_message)
        self.assertIn("has already checked out today", error_message)


if __name__ == '__main__':
    unittest.main()