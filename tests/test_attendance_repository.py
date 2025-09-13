"""
Unit tests for AttendanceRepository class
"""
import unittest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, date
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models import AttendanceRepository
from database import DatabaseQueryError


class TestAttendanceRepository(unittest.TestCase):
    """Test cases for AttendanceRepository class"""
    
    def setUp(self):
        """Set up test fixtures before each test method"""
        self.mock_db_manager = Mock()
        self.attendance_repo = AttendanceRepository(self.mock_db_manager)
        
        # Sample test data
        self.employee_id = 1
        self.sample_attendance = {
            'id': 1,
            'employee_id': 1,
            'check_in_time': datetime(2024, 1, 15, 9, 0, 0),
            'check_out_time': None,
            'work_date': date(2024, 1, 15),
            'created_at': datetime(2024, 1, 15, 9, 0, 0)
        }
        
        self.completed_attendance = {
            'id': 2,
            'employee_id': 1,
            'check_in_time': datetime(2024, 1, 14, 9, 0, 0),
            'check_out_time': datetime(2024, 1, 14, 17, 30, 0),
            'work_date': date(2024, 1, 14),
            'created_at': datetime(2024, 1, 14, 9, 0, 0)
        }
    
    def test_get_today_attendance_found(self):
        """Test get_today_attendance when record exists"""
        # Arrange
        self.mock_db_manager.execute_query.return_value = [self.sample_attendance]
        
        # Act
        result = self.attendance_repo.get_today_attendance(self.employee_id)
        
        # Assert
        self.assertEqual(result, self.sample_attendance)
        self.mock_db_manager.execute_query.assert_called_once_with(
            """
                SELECT id, employee_id, check_in_time, check_out_time, work_date, created_at
                FROM attendances 
                WHERE employee_id = %s AND work_date = CURDATE()
            """,
            (self.employee_id,),
            fetch_results=True
        )
    
    def test_get_today_attendance_not_found(self):
        """Test get_today_attendance when no record exists"""
        # Arrange
        self.mock_db_manager.execute_query.return_value = []
        
        # Act
        result = self.attendance_repo.get_today_attendance(self.employee_id)
        
        # Assert
        self.assertIsNone(result)
        self.mock_db_manager.execute_query.assert_called_once()
    
    def test_get_today_attendance_database_error(self):
        """Test get_today_attendance when database error occurs"""
        # Arrange
        self.mock_db_manager.execute_query.side_effect = DatabaseQueryError("Database connection failed")
        
        # Act & Assert
        with self.assertRaises(DatabaseQueryError):
            self.attendance_repo.get_today_attendance(self.employee_id)
    
    def test_create_checkin_success(self):
        """Test successful check-in creation"""
        # Arrange
        # First call returns empty (no existing attendance)
        # Second call returns the created attendance
        self.mock_db_manager.execute_query.side_effect = [
            [],  # get_today_attendance returns None
            None,  # INSERT query returns None
            [self.sample_attendance]  # get_today_attendance returns created record
        ]
        
        # Act
        result = self.attendance_repo.create_checkin(self.employee_id)
        
        # Assert
        self.assertEqual(result, self.sample_attendance)
        self.assertEqual(self.mock_db_manager.execute_query.call_count, 3)
        
        # Verify INSERT query was called
        insert_call = self.mock_db_manager.execute_query.call_args_list[1]
        self.assertIn("INSERT INTO attendances", insert_call[0][0])
        self.assertEqual(insert_call[0][1], (self.employee_id,))
    
    def test_create_checkin_duplicate_prevention(self):
        """Test that duplicate check-in is prevented"""
        # Arrange
        self.mock_db_manager.execute_query.return_value = [self.sample_attendance]
        
        # Act & Assert
        with self.assertRaises(DatabaseQueryError) as context:
            self.attendance_repo.create_checkin(self.employee_id)
        
        self.assertIn("already checked in today", str(context.exception))
        # Should only call get_today_attendance, not INSERT
        self.assertEqual(self.mock_db_manager.execute_query.call_count, 1)
    
    def test_create_checkin_database_error(self):
        """Test create_checkin when database error occurs during INSERT"""
        # Arrange
        self.mock_db_manager.execute_query.side_effect = [
            [],  # get_today_attendance returns None
            DatabaseQueryError("INSERT failed")  # INSERT query fails
        ]
        
        # Act & Assert
        with self.assertRaises(DatabaseQueryError):
            self.attendance_repo.create_checkin(self.employee_id)
    
    def test_create_checkin_retrieval_failure(self):
        """Test create_checkin when created record cannot be retrieved"""
        # Arrange
        self.mock_db_manager.execute_query.side_effect = [
            [],  # get_today_attendance returns None
            None,  # INSERT query succeeds
            []  # get_today_attendance returns None (retrieval fails)
        ]
        
        # Act & Assert
        with self.assertRaises(DatabaseQueryError) as context:
            self.attendance_repo.create_checkin(self.employee_id)
        
        self.assertIn("Failed to retrieve newly created attendance record", str(context.exception))
    
    def test_update_checkout_success(self):
        """Test successful check-out update"""
        # Arrange
        # First call returns existing check-in record
        # Second call returns None (UPDATE succeeds)
        # Third call returns updated record with check-out time
        updated_attendance = self.sample_attendance.copy()
        updated_attendance['check_out_time'] = datetime(2024, 1, 15, 17, 30, 0)
        
        self.mock_db_manager.execute_query.side_effect = [
            [self.sample_attendance],  # get_today_attendance returns check-in record
            None,  # UPDATE query returns None
            [updated_attendance]  # get_today_attendance returns updated record
        ]
        
        # Act
        result = self.attendance_repo.update_checkout(self.employee_id)
        
        # Assert
        self.assertEqual(result, updated_attendance)
        self.assertEqual(self.mock_db_manager.execute_query.call_count, 3)
        
        # Verify UPDATE query was called
        update_call = self.mock_db_manager.execute_query.call_args_list[1]
        self.assertIn("UPDATE attendances", update_call[0][0])
        self.assertIn("SET check_out_time = NOW()", update_call[0][0])
        self.assertEqual(update_call[0][1], (self.employee_id,))
    
    def test_update_checkout_no_checkin(self):
        """Test update_checkout when no check-in record exists"""
        # Arrange
        self.mock_db_manager.execute_query.return_value = []
        
        # Act & Assert
        with self.assertRaises(DatabaseQueryError) as context:
            self.attendance_repo.update_checkout(self.employee_id)
        
        self.assertIn("has not checked in today", str(context.exception))
        # Should only call get_today_attendance, not UPDATE
        self.assertEqual(self.mock_db_manager.execute_query.call_count, 1)
    
    def test_update_checkout_already_checked_out(self):
        """Test update_checkout when already checked out"""
        # Arrange
        self.mock_db_manager.execute_query.return_value = [self.completed_attendance]
        
        # Act & Assert
        with self.assertRaises(DatabaseQueryError) as context:
            self.attendance_repo.update_checkout(self.employee_id)
        
        self.assertIn("has already checked out today", str(context.exception))
        # Should only call get_today_attendance, not UPDATE
        self.assertEqual(self.mock_db_manager.execute_query.call_count, 1)
    
    def test_update_checkout_database_error(self):
        """Test update_checkout when database error occurs during UPDATE"""
        # Arrange
        self.mock_db_manager.execute_query.side_effect = [
            [self.sample_attendance],  # get_today_attendance returns check-in record
            DatabaseQueryError("UPDATE failed")  # UPDATE query fails
        ]
        
        # Act & Assert
        with self.assertRaises(DatabaseQueryError):
            self.attendance_repo.update_checkout(self.employee_id)
    
    def test_update_checkout_retrieval_failure(self):
        """Test update_checkout when updated record cannot be retrieved"""
        # Arrange
        self.mock_db_manager.execute_query.side_effect = [
            [self.sample_attendance],  # get_today_attendance returns check-in record
            None,  # UPDATE query succeeds
            []  # get_today_attendance returns None (retrieval fails)
        ]
        
        # Act & Assert
        with self.assertRaises(DatabaseQueryError) as context:
            self.attendance_repo.update_checkout(self.employee_id)
        
        self.assertIn("Failed to retrieve updated attendance record", str(context.exception))
    
    def test_get_recent_history_with_records(self):
        """Test get_recent_history when records exist"""
        # Arrange
        history_records = [
            self.completed_attendance,
            self.sample_attendance
        ]
        self.mock_db_manager.execute_query.return_value = history_records
        
        # Act
        result = self.attendance_repo.get_recent_history(self.employee_id)
        
        # Assert
        self.assertEqual(result, history_records)
        self.mock_db_manager.execute_query.assert_called_once_with(
            """
                SELECT id, employee_id, check_in_time, check_out_time, work_date, created_at
                FROM attendances 
                WHERE employee_id = %s 
                AND work_date >= DATE_SUB(CURDATE(), INTERVAL %s DAY)
                ORDER BY work_date DESC
            """,
            (self.employee_id, 14),
            fetch_results=True
        )
    
    def test_get_recent_history_custom_days(self):
        """Test get_recent_history with custom number of days"""
        # Arrange
        self.mock_db_manager.execute_query.return_value = []
        custom_days = 7
        
        # Act
        result = self.attendance_repo.get_recent_history(self.employee_id, custom_days)
        
        # Assert
        self.assertEqual(result, [])
        self.mock_db_manager.execute_query.assert_called_once_with(
            """
                SELECT id, employee_id, check_in_time, check_out_time, work_date, created_at
                FROM attendances 
                WHERE employee_id = %s 
                AND work_date >= DATE_SUB(CURDATE(), INTERVAL %s DAY)
                ORDER BY work_date DESC
            """,
            (self.employee_id, custom_days),
            fetch_results=True
        )
    
    def test_get_recent_history_no_records(self):
        """Test get_recent_history when no records exist"""
        # Arrange
        self.mock_db_manager.execute_query.return_value = []
        
        # Act
        result = self.attendance_repo.get_recent_history(self.employee_id)
        
        # Assert
        self.assertEqual(result, [])
    
    def test_get_recent_history_none_result(self):
        """Test get_recent_history when query returns None"""
        # Arrange
        self.mock_db_manager.execute_query.return_value = None
        
        # Act
        result = self.attendance_repo.get_recent_history(self.employee_id)
        
        # Assert
        self.assertEqual(result, [])
    
    def test_get_recent_history_database_error(self):
        """Test get_recent_history when database error occurs"""
        # Arrange
        self.mock_db_manager.execute_query.side_effect = DatabaseQueryError("Database connection failed")
        
        # Act & Assert
        with self.assertRaises(DatabaseQueryError):
            self.attendance_repo.get_recent_history(self.employee_id)
    
    def test_get_recent_history_zero_days(self):
        """Test get_recent_history with zero days (edge case)"""
        # Arrange
        self.mock_db_manager.execute_query.return_value = []
        
        # Act
        result = self.attendance_repo.get_recent_history(self.employee_id, 0)
        
        # Assert
        self.assertEqual(result, [])
        # Verify the query was called with 0 days
        call_args = self.mock_db_manager.execute_query.call_args[0]
        self.assertEqual(call_args[1], (self.employee_id, 0))
    
    def test_get_recent_history_large_days(self):
        """Test get_recent_history with large number of days"""
        # Arrange
        self.mock_db_manager.execute_query.return_value = []
        large_days = 365
        
        # Act
        result = self.attendance_repo.get_recent_history(self.employee_id, large_days)
        
        # Assert
        self.assertEqual(result, [])
        # Verify the query was called with large number of days
        call_args = self.mock_db_manager.execute_query.call_args[0]
        self.assertEqual(call_args[1], (self.employee_id, large_days))


if __name__ == '__main__':
    unittest.main()