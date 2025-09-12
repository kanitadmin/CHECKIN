"""
Unit tests for database connection and table creation functionality
"""
import unittest
from unittest.mock import patch, MagicMock, call
import pymysql
import os
from database import (
    DatabaseManager, 
    DatabaseConnectionError, 
    DatabaseQueryError,
    initialize_database,
    verify_database_schema,
    EMPLOYEES_TABLE_SQL,
    ATTENDANCES_TABLE_SQL
)


class TestDatabaseManager(unittest.TestCase):
    """Test cases for DatabaseManager class"""
    
    def setUp(self):
        """Set up test environment variables"""
        self.test_env_vars = {
            'DB_HOST': 'test_host',
            'DB_PORT': '3306',
            'DB_USER': 'test_user',
            'DB_PASSWORD': 'test_password',
            'DB_NAME': 'test_db'
        }
        
        # Patch environment variables
        self.env_patcher = patch.dict(os.environ, self.test_env_vars)
        self.env_patcher.start()
    
    def tearDown(self):
        """Clean up after tests"""
        self.env_patcher.stop()
    
    def test_database_manager_initialization_success(self):
        """Test successful DatabaseManager initialization with valid environment variables"""
        db_manager = DatabaseManager()
        
        self.assertEqual(db_manager.connection_config['host'], 'test_host')
        self.assertEqual(db_manager.connection_config['port'], 3306)
        self.assertEqual(db_manager.connection_config['user'], 'test_user')
        self.assertEqual(db_manager.connection_config['password'], 'test_password')
        self.assertEqual(db_manager.connection_config['database'], 'test_db')
    
    def test_database_manager_initialization_missing_env_vars(self):
        """Test DatabaseManager initialization fails with missing environment variables"""
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(ValueError) as context:
                DatabaseManager()
            
            self.assertIn("Missing required environment variables", str(context.exception))
    
    @patch('database.pymysql.connect')
    def test_get_connection_success(self, mock_connect):
        """Test successful database connection"""
        mock_connection = MagicMock()
        mock_connect.return_value = mock_connection
        
        db_manager = DatabaseManager()
        connection = db_manager.get_connection()
        
        self.assertEqual(connection, mock_connection)
        mock_connect.assert_called_once_with(**db_manager.connection_config)
    
    @patch('database.pymysql.connect')
    def test_get_connection_retry_logic(self, mock_connect):
        """Test connection retry logic on failure"""
        # First two attempts fail, third succeeds
        mock_connect.side_effect = [
            pymysql.Error("Connection failed"),
            pymysql.Error("Connection failed"),
            MagicMock()
        ]
        
        db_manager = DatabaseManager()
        connection = db_manager.get_connection()
        
        self.assertIsNotNone(connection)
        self.assertEqual(mock_connect.call_count, 3)
    
    @patch('database.pymysql.connect')
    def test_get_connection_max_retries_exceeded(self, mock_connect):
        """Test connection failure after max retries"""
        mock_connect.side_effect = pymysql.Error("Connection failed")
        
        db_manager = DatabaseManager()
        
        with self.assertRaises(DatabaseConnectionError):
            db_manager.get_connection()
        
        self.assertEqual(mock_connect.call_count, 3)
    
    @patch('database.DatabaseManager.get_db_connection')
    def test_execute_query_select_success(self, mock_get_db_connection):
        """Test successful SELECT query execution"""
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        mock_cursor.fetchall.return_value = [{'id': 1, 'name': 'test'}]
        mock_get_db_connection.return_value.__enter__.return_value = mock_connection
        
        db_manager = DatabaseManager()
        result = db_manager.execute_query("SELECT * FROM test", fetch_results=True)
        
        self.assertEqual(result, [{'id': 1, 'name': 'test'}])
        mock_cursor.execute.assert_called_once_with("SELECT * FROM test", ())
        mock_cursor.fetchall.assert_called_once()
        mock_connection.commit.assert_called_once()
    
    @patch('database.DatabaseManager.get_db_connection')
    def test_execute_query_insert_success(self, mock_get_db_connection):
        """Test successful INSERT query execution"""
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        mock_get_db_connection.return_value.__enter__.return_value = mock_connection
        
        db_manager = DatabaseManager()
        result = db_manager.execute_query("INSERT INTO test VALUES (%s)", ("value",))
        
        self.assertIsNone(result)
        mock_cursor.execute.assert_called_once_with("INSERT INTO test VALUES (%s)", ("value",))
        mock_connection.commit.assert_called_once()
    
    @patch('database.DatabaseManager.get_db_connection')
    def test_execute_query_error_handling(self, mock_get_db_connection):
        """Test query execution error handling and rollback"""
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        mock_cursor.execute.side_effect = pymysql.Error("Query failed")
        mock_get_db_connection.return_value.__enter__.return_value = mock_connection
        
        db_manager = DatabaseManager()
        
        with self.assertRaises(DatabaseQueryError):
            db_manager.execute_query("INVALID SQL")
        
        mock_connection.rollback.assert_called_once()
    
    @patch('database.DatabaseManager.get_db_connection')
    def test_execute_script_success(self, mock_get_db_connection):
        """Test successful script execution"""
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        mock_get_db_connection.return_value.__enter__.return_value = mock_connection
        
        script = "CREATE TABLE test1 (id INT); CREATE TABLE test2 (id INT);"
        
        db_manager = DatabaseManager()
        db_manager.execute_script(script)
        
        # Verify both statements were executed
        expected_calls = [
            call("CREATE TABLE test1 (id INT)"),
            call("CREATE TABLE test2 (id INT)")
        ]
        mock_cursor.execute.assert_has_calls(expected_calls)
        mock_connection.commit.assert_called_once()
    
    @patch('database.DatabaseManager.get_db_connection')
    def test_execute_script_error_handling(self, mock_get_db_connection):
        """Test script execution error handling"""
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        mock_cursor.execute.side_effect = pymysql.Error("Script failed")
        mock_get_db_connection.return_value.__enter__.return_value = mock_connection
        
        db_manager = DatabaseManager()
        
        with self.assertRaises(DatabaseQueryError):
            db_manager.execute_script("CREATE TABLE test (id INT);")
        
        mock_connection.rollback.assert_called_once()


class TestDatabaseInitialization(unittest.TestCase):
    """Test cases for database initialization functions"""
    
    def setUp(self):
        """Set up test environment variables"""
        self.test_env_vars = {
            'DB_HOST': 'test_host',
            'DB_PORT': '3306',
            'DB_USER': 'test_user',
            'DB_PASSWORD': 'test_password',
            'DB_NAME': 'test_db'
        }
        
        self.env_patcher = patch.dict(os.environ, self.test_env_vars)
        self.env_patcher.start()
    
    def tearDown(self):
        """Clean up after tests"""
        self.env_patcher.stop()
    
    @patch('database.DatabaseManager')
    def test_initialize_database_success(self, mock_db_manager_class):
        """Test successful database initialization"""
        mock_db_manager = MagicMock()
        mock_db_manager_class.return_value = mock_db_manager
        
        initialize_database()
        
        # Verify DatabaseManager was created
        mock_db_manager_class.assert_called_once()
        
        # Verify both table creation queries were executed
        expected_calls = [
            call(EMPLOYEES_TABLE_SQL),
            call(ATTENDANCES_TABLE_SQL)
        ]
        mock_db_manager.execute_query.assert_has_calls(expected_calls)
    
    @patch('database.DatabaseManager')
    def test_initialize_database_failure(self, mock_db_manager_class):
        """Test database initialization failure handling"""
        mock_db_manager = MagicMock()
        mock_db_manager.execute_query.side_effect = Exception("Database error")
        mock_db_manager_class.return_value = mock_db_manager
        
        with self.assertRaises(Exception):
            initialize_database()
    
    @patch('database.DatabaseManager')
    def test_verify_database_schema_success(self, mock_db_manager_class):
        """Test successful database schema verification"""
        mock_db_manager = MagicMock()
        mock_db_manager_class.return_value = mock_db_manager
        
        # Mock successful table existence checks
        mock_db_manager.execute_query.side_effect = [
            [{'Tables_in_test_db': 'employees'}],  # employees table exists
            [{'Tables_in_test_db': 'attendances'}],  # attendances table exists
            [{'CONSTRAINT_NAME': 'attendances_ibfk_1'}]  # foreign key exists
        ]
        
        result = verify_database_schema()
        
        self.assertTrue(result)
        self.assertEqual(mock_db_manager.execute_query.call_count, 3)
    
    @patch('database.DatabaseManager')
    def test_verify_database_schema_missing_tables(self, mock_db_manager_class):
        """Test schema verification with missing tables"""
        mock_db_manager = MagicMock()
        mock_db_manager_class.return_value = mock_db_manager
        
        # Mock missing employees table
        mock_db_manager.execute_query.side_effect = [
            [],  # employees table missing
            [{'Tables_in_test_db': 'attendances'}]  # attendances table exists
        ]
        
        result = verify_database_schema()
        
        self.assertFalse(result)
    
    @patch('database.DatabaseManager')
    def test_verify_database_schema_missing_foreign_key(self, mock_db_manager_class):
        """Test schema verification with missing foreign key"""
        mock_db_manager = MagicMock()
        mock_db_manager_class.return_value = mock_db_manager
        
        # Mock tables exist but foreign key missing
        mock_db_manager.execute_query.side_effect = [
            [{'Tables_in_test_db': 'employees'}],  # employees table exists
            [{'Tables_in_test_db': 'attendances'}],  # attendances table exists
            []  # foreign key missing
        ]
        
        result = verify_database_schema()
        
        self.assertFalse(result)
    
    @patch('database.DatabaseManager')
    def test_verify_database_schema_exception_handling(self, mock_db_manager_class):
        """Test schema verification exception handling"""
        mock_db_manager = MagicMock()
        mock_db_manager.execute_query.side_effect = Exception("Database error")
        mock_db_manager_class.return_value = mock_db_manager
        
        result = verify_database_schema()
        
        self.assertFalse(result)


class TestSQLSchemas(unittest.TestCase):
    """Test cases for SQL schema definitions"""
    
    def test_employees_table_sql_structure(self):
        """Test employees table SQL contains required elements"""
        sql = EMPLOYEES_TABLE_SQL.upper()
        
        # Check table name
        self.assertIn('CREATE TABLE', sql)
        self.assertIn('EMPLOYEES', sql)
        
        # Check required columns
        required_columns = ['ID', 'GOOGLE_ID', 'EMAIL', 'NAME', 'PICTURE_URL', 'CREATED_AT']
        for column in required_columns:
            self.assertIn(column, sql)
        
        # Check constraints and indexes
        self.assertIn('PRIMARY KEY', sql)
        self.assertIn('UNIQUE', sql)
        self.assertIn('INDEX', sql)
    
    def test_attendances_table_sql_structure(self):
        """Test attendances table SQL contains required elements"""
        sql = ATTENDANCES_TABLE_SQL.upper()
        
        # Check table name
        self.assertIn('CREATE TABLE', sql)
        self.assertIn('ATTENDANCES', sql)
        
        # Check required columns
        required_columns = ['ID', 'EMPLOYEE_ID', 'CHECK_IN_TIME', 'CHECK_OUT_TIME', 'WORK_DATE', 'CREATED_AT']
        for column in required_columns:
            self.assertIn(column, sql)
        
        # Check constraints and relationships
        self.assertIn('PRIMARY KEY', sql)
        self.assertIn('FOREIGN KEY', sql)
        self.assertIn('REFERENCES EMPLOYEES', sql)
        self.assertIn('ON DELETE CASCADE', sql)
        self.assertIn('UNIQUE KEY', sql)
        self.assertIn('INDEX', sql)


if __name__ == '__main__':
    # Run all tests
    unittest.main(verbosity=2)