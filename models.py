"""
Employee data model and repository for Employee Check-in System
"""
from flask_login import UserMixin
from typing import Optional, Dict, Any, List
from database import DatabaseManager, DatabaseQueryError
from security_utils import sanitize_user_input, SecurityValidator
import logging

logger = logging.getLogger(__name__)


class Employee(UserMixin):
    """
    Employee class that implements Flask-Login UserMixin for session management
    
    This class represents an employee user and provides the required methods
    for Flask-Login integration to manage user sessions.
    """
    
    def __init__(self, id: int, google_id: str, email: str, name: str = None, picture_url: str = None, created_at: str = None, role: str = 'employee'):
        """
        Initialize Employee instance
        
        Args:
            id: Database primary key
            google_id: Google OAuth user ID
            email: Employee email address
            name: Employee display name
            picture_url: URL to employee's profile picture
            created_at: Account creation timestamp
            role: User role (employee or admin)
        """
        self.id = id
        self.google_id = google_id
        self.email = email
        self.name = name
        self.picture_url = picture_url
        self.created_at = created_at
        self.role = role
    
    def get_id(self) -> str:
        """
        Required by Flask-Login UserMixin
        Returns the unique identifier for the user as a string
        """
        return str(self.id)
    
    @property
    def is_authenticated(self) -> bool:
        """
        Required by Flask-Login UserMixin
        Returns True if the user is authenticated (always True for valid Employee objects)
        """
        return True
    
    @property
    def is_active(self) -> bool:
        """
        Required by Flask-Login UserMixin
        Returns True if the user account is active (always True for this implementation)
        """
        return True
    
    @property
    def is_anonymous(self) -> bool:
        """
        Required by Flask-Login UserMixin
        Returns False since Employee objects represent authenticated users
        """
        return False
    
    @property
    def is_admin(self) -> bool:
        """Check if user has admin role"""
        return self.role == 'admin'
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert Employee object to dictionary representation
        
        Returns:
            Dictionary containing employee data
        """
        return {
            'id': self.id,
            'google_id': self.google_id,
            'email': self.email,
            'name': self.name,
            'picture_url': self.picture_url,
            'created_at': self.created_at,
            'role': self.role
        }
    
    def __repr__(self) -> str:
        """String representation of Employee object"""
        return f"<Employee {self.email} (ID: {self.id})>"


class EmployeeRepository:
    """
    Repository class for Employee data operations
    
    Handles all database operations related to employees including
    creation, updates, and lookups by various criteria.
    """
    
    def __init__(self):
        """Initialize repository with database manager"""
        self.db_manager = DatabaseManager()
    
    def find_by_google_id(self, google_id: str) -> Optional[Employee]:
        """
        Find employee by Google OAuth ID
        
        Args:
            google_id: Google OAuth user identifier
            
        Returns:
            Employee object if found, None otherwise
        """
        try:
            query = """
                SELECT id, google_id, email, name, picture_url, created_at, role
                FROM employees 
                WHERE google_id = %s
            """
            
            results = self.db_manager.execute_query(query, (google_id,), fetch_results=True)
            
            if results:
                row = results[0]
                return Employee(
                    id=row['id'],
                    google_id=row['google_id'],
                    email=row['email'],
                    name=row['name'],
                    picture_url=row['picture_url'],
                    created_at=row['created_at'],
                    role=row.get('role', 'employee')
                )
            
            return None
            
        except DatabaseQueryError as e:
            logger.error(f"Failed to find employee by google_id {google_id}: {e}")
            raise
    
    def find_by_email(self, email: str) -> Optional[Employee]:
        """
        Find employee by email address
        
        Args:
            email: Employee email address
            
        Returns:
            Employee object if found, None otherwise
        """
        try:
            query = """
                SELECT id, google_id, email, name, picture_url, created_at, role
                FROM employees 
                WHERE email = %s
            """
            
            results = self.db_manager.execute_query(query, (email,), fetch_results=True)
            
            if results:
                row = results[0]
                return Employee(
                    id=row['id'],
                    google_id=row['google_id'],
                    email=row['email'],
                    name=row['name'],
                    picture_url=row['picture_url'],
                    created_at=row['created_at'],
                    role=row.get('role', 'employee')
                )
            
            return None
            
        except DatabaseQueryError as e:
            logger.error(f"Failed to find employee by email {email}: {e}")
            raise
    
    def find_by_id(self, employee_id: int) -> Optional[Employee]:
        """
        Find employee by database ID (used by Flask-Login user_loader)
        
        Args:
            employee_id: Database primary key
            
        Returns:
            Employee object if found, None otherwise
        """
        try:
            query = """
                SELECT id, google_id, email, name, picture_url, created_at, role
                FROM employees 
                WHERE id = %s
            """
            
            results = self.db_manager.execute_query(query, (employee_id,), fetch_results=True)
            
            if results:
                row = results[0]
                return Employee(
                    id=row['id'],
                    google_id=row['google_id'],
                    email=row['email'],
                    name=row['name'],
                    picture_url=row['picture_url'],
                    created_at=row['created_at'],
                    role=row.get('role', 'employee')
                )
            
            return None
            
        except DatabaseQueryError as e:
            logger.error(f"Failed to find employee by id {employee_id}: {e}")
            raise
    
    def create_or_update(self, google_user_info: Dict[str, Any]) -> Employee:
        """
        Create new employee or update existing employee with Google OAuth user data
        
        This method handles both creation of new employees and updating existing
        employees when they log in again with potentially updated information.
        
        Args:
            google_user_info: Dictionary containing Google OAuth user data
                Expected keys: 'sub' (google_id), 'email', 'name', 'picture'
                
        Returns:
            Employee object (newly created or updated)
            
        Raises:
            DatabaseQueryError: If database operation fails
            ValueError: If required fields are missing from google_user_info
        """
        # Validate required fields
        required_fields = ['sub', 'email']
        missing_fields = [field for field in required_fields if field not in google_user_info]
        if missing_fields:
            raise ValueError(f"Missing required fields in google_user_info: {missing_fields}")
        
        # Sanitize input data
        google_id = sanitize_user_input(google_user_info['sub'])
        email = sanitize_user_input(google_user_info['email'])
        name = sanitize_user_input(google_user_info.get('name'))
        picture_url = sanitize_user_input(google_user_info.get('picture'))
        
        # Additional validation for email format
        if not SecurityValidator.validate_xss_input(email) or '@' not in email:
            SecurityValidator.log_security_event("INVALID_EMAIL", f"Invalid email format: {email}")
            raise ValueError("Invalid email format")
        
        try:
            # Check if employee already exists
            existing_employee = self.find_by_google_id(google_id)
            
            if existing_employee:
                # Update existing employee
                logger.info(f"Updating existing employee: {email}")
                return self._update_employee(existing_employee.id, email, name, picture_url)
            else:
                # Create new employee
                logger.info(f"Creating new employee: {email}")
                return self._create_employee(google_id, email, name, picture_url)
                
        except DatabaseQueryError as e:
            logger.error(f"Failed to create or update employee {email}: {e}")
            raise
    
    def _create_employee(self, google_id: str, email: str, name: str = None, picture_url: str = None) -> Employee:
        """
        Create a new employee record
        
        Args:
            google_id: Google OAuth user ID
            email: Employee email
            name: Employee name (optional)
            picture_url: Profile picture URL (optional)
            
        Returns:
            Newly created Employee object
        """
        query = """
            INSERT INTO employees (google_id, email, name, picture_url)
            VALUES (%s, %s, %s, %s)
        """
        
        self.db_manager.execute_query(query, (google_id, email, name, picture_url))
        
        # Retrieve the newly created employee
        created_employee = self.find_by_google_id(google_id)
        if not created_employee:
            raise DatabaseQueryError("Failed to retrieve newly created employee")
        
        logger.info(f"Successfully created employee: {email} (ID: {created_employee.id})")
        return created_employee
    
    def _update_employee(self, employee_id: int, email: str, name: str = None, picture_url: str = None) -> Employee:
        """
        Update an existing employee record
        
        Args:
            employee_id: Database ID of employee to update
            email: Updated email address
            name: Updated name (optional)
            picture_url: Updated profile picture URL (optional)
            
        Returns:
            Updated Employee object
        """
        query = """
            UPDATE employees 
            SET email = %s, name = %s, picture_url = %s
            WHERE id = %s
        """
        
        self.db_manager.execute_query(query, (email, name, picture_url, employee_id))
        
        # Retrieve the updated employee
        updated_employee = self.find_by_id(employee_id)
        if not updated_employee:
            raise DatabaseQueryError("Failed to retrieve updated employee")
        
        logger.info(f"Successfully updated employee: {email} (ID: {employee_id})")
        return updated_employee
    
    def get_all_employees(self) -> List[Employee]:
        """
        Get all employees (admin function)
        
        Returns:
            List of Employee objects
        """
        try:
            query = """
                SELECT id, google_id, email, name, picture_url, created_at, role
                FROM employees 
                ORDER BY created_at DESC
            """
            
            results = self.db_manager.execute_query(query, fetch_results=True)
            
            employees = []
            for row in results:
                employees.append(Employee(
                    id=row['id'],
                    google_id=row['google_id'],
                    email=row['email'],
                    name=row['name'],
                    picture_url=row['picture_url'],
                    created_at=row['created_at'],
                    role=row.get('role', 'employee')
                ))
            
            return employees
            
        except DatabaseQueryError as e:
            logger.error(f"Failed to get all employees: {e}")
            raise
    
    def update_employee_role(self, employee_id: int, role: str) -> bool:
        """
        Update employee role (admin function)
        
        Args:
            employee_id: Database ID of employee
            role: New role ('employee' or 'admin')
            
        Returns:
            True if successful
        """
        try:
            if role not in ['employee', 'admin']:
                raise ValueError("Role must be 'employee' or 'admin'")
            
            query = """
                UPDATE employees 
                SET role = %s
                WHERE id = %s
            """
            
            self.db_manager.execute_query(query, (role, employee_id))
            logger.info(f"Successfully updated employee {employee_id} role to {role}")
            return True
            
        except DatabaseQueryError as e:
            logger.error(f"Failed to update employee {employee_id} role: {e}")
            raise


class AttendanceRepository:
    """
    Repository class for Attendance data operations
    
    Handles all database operations related to daily attendance including
    check-in, check-out, and attendance history retrieval.
    """
    
    def __init__(self, db_manager=None):
        """Initialize repository with database manager"""
        self.db_manager = db_manager or DatabaseManager()
    
    def get_today_attendance(self, employee_id: int) -> Optional[Dict[str, Any]]:
        """
        Find current day's attendance record for an employee
        
        Args:
            employee_id: Database ID of the employee
            
        Returns:
            Dictionary containing attendance data if found, None otherwise
            Keys: id, employee_id, check_in_time, check_out_time, work_date, created_at
        """
        try:
            query = """
                SELECT id, employee_id, check_in_time, check_out_time, work_date, created_at
                FROM attendances 
                WHERE employee_id = %s AND work_date = CURDATE()
            """
            
            results = self.db_manager.execute_query(query, (employee_id,), fetch_results=True)
            
            if results:
                return results[0]
            
            return None
            
        except DatabaseQueryError as e:
            logger.error(f"Failed to get today's attendance for employee {employee_id}: {e}")
            raise
    
    def create_checkin(self, employee_id: int) -> Dict[str, Any]:
        """
        Insert new attendance record with check_in_time and work_date
        
        Args:
            employee_id: Database ID of the employee
            
        Returns:
            Dictionary containing the created attendance record
            
        Raises:
            DatabaseQueryError: If database operation fails or duplicate check-in attempted
        """
        try:
            # Check if employee already checked in today
            existing_attendance = self.get_today_attendance(employee_id)
            if existing_attendance:
                raise DatabaseQueryError(f"Employee {employee_id} has already checked in today")
            
            # Insert new check-in record
            query = """
                INSERT INTO attendances (employee_id, check_in_time, work_date)
                VALUES (%s, NOW(), CURDATE())
            """
            
            self.db_manager.execute_query(query, (employee_id,))
            
            # Retrieve the newly created attendance record
            created_attendance = self.get_today_attendance(employee_id)
            if not created_attendance:
                raise DatabaseQueryError("Failed to retrieve newly created attendance record")
            
            logger.info(f"Successfully created check-in for employee {employee_id}")
            return created_attendance
            
        except DatabaseQueryError as e:
            logger.error(f"Failed to create check-in for employee {employee_id}: {e}")
            raise
    
    def update_checkout(self, employee_id: int) -> Dict[str, Any]:
        """
        Update existing attendance record with check_out_time
        
        Args:
            employee_id: Database ID of the employee
            
        Returns:
            Dictionary containing the updated attendance record
            
        Raises:
            DatabaseQueryError: If no check-in record exists or database operation fails
        """
        try:
            # Check if employee has checked in today
            existing_attendance = self.get_today_attendance(employee_id)
            if not existing_attendance:
                raise DatabaseQueryError(f"Employee {employee_id} has not checked in today")
            
            # Check if already checked out
            if existing_attendance['check_out_time']:
                raise DatabaseQueryError(f"Employee {employee_id} has already checked out today")
            
            # Update with check-out time
            query = """
                UPDATE attendances 
                SET check_out_time = NOW()
                WHERE employee_id = %s AND work_date = CURDATE()
            """
            
            self.db_manager.execute_query(query, (employee_id,))
            
            # Retrieve the updated attendance record
            updated_attendance = self.get_today_attendance(employee_id)
            if not updated_attendance:
                raise DatabaseQueryError("Failed to retrieve updated attendance record")
            
            logger.info(f"Successfully updated check-out for employee {employee_id}")
            return updated_attendance
            
        except DatabaseQueryError as e:
            logger.error(f"Failed to update check-out for employee {employee_id}: {e}")
            raise
    
    def get_recent_history(self, employee_id: int, days: int = 14) -> List[Dict[str, Any]]:
        """
        Retrieve attendance records for the last N days
        
        Args:
            employee_id: Database ID of the employee
            days: Number of days to retrieve (default: 14)
            
        Returns:
            List of dictionaries containing attendance records, ordered by work_date DESC
            Each dict contains: id, employee_id, check_in_time, check_out_time, work_date, created_at
        """
        try:
            query = """
                SELECT id, employee_id, check_in_time, check_out_time, work_date, created_at
                FROM attendances 
                WHERE employee_id = %s 
                AND work_date >= DATE_SUB(CURDATE(), INTERVAL %s DAY)
                ORDER BY work_date DESC
            """
            
            results = self.db_manager.execute_query(query, (employee_id, days), fetch_results=True)
            
            # Handle None result from database
            if results is None:
                results = []
            
            logger.info(f"Retrieved {len(results)} attendance records for employee {employee_id}")
            return results
            
        except DatabaseQueryError as e:
            logger.error(f"Failed to get recent history for employee {employee_id}: {e}")
            raise
    
    def get_all_attendance_records(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get all attendance records with employee info (admin function)
        
        Args:
            limit: Maximum number of records to return
            
        Returns:
            List of dictionaries containing attendance and employee data
        """
        try:
            query = """
                SELECT a.id, a.employee_id, a.check_in_time, a.check_out_time, 
                       a.work_date, a.created_at, e.name, e.email
                FROM attendances a
                JOIN employees e ON a.employee_id = e.id
                ORDER BY a.work_date DESC, a.check_in_time DESC
                LIMIT %s
            """
            
            results = self.db_manager.execute_query(query, (limit,), fetch_results=True)
            
            if results is None:
                results = []
            
            logger.info(f"Retrieved {len(results)} attendance records for admin")
            return results
            
        except DatabaseQueryError as e:
            logger.error(f"Failed to get all attendance records: {e}")
            raise
    
    def get_attendance_stats(self) -> Dict[str, Any]:
        """
        Get attendance statistics (admin function)
        
        Returns:
            Dictionary containing various attendance statistics
        """
        try:
            # Total employees
            total_employees_query = "SELECT COUNT(*) as count FROM employees"
            total_employees = self.db_manager.execute_query(total_employees_query, fetch_results=True)[0]['count']
            
            # Today's check-ins
            today_checkins_query = """
                SELECT COUNT(*) as count FROM attendances 
                WHERE work_date = CURDATE() AND check_in_time IS NOT NULL
            """
            today_checkins = self.db_manager.execute_query(today_checkins_query, fetch_results=True)[0]['count']
            
            # Today's completed (checked out)
            today_completed_query = """
                SELECT COUNT(*) as count FROM attendances 
                WHERE work_date = CURDATE() AND check_out_time IS NOT NULL
            """
            today_completed = self.db_manager.execute_query(today_completed_query, fetch_results=True)[0]['count']
            
            # This week's total records
            week_total_query = """
                SELECT COUNT(*) as count FROM attendances 
                WHERE work_date >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
            """
            week_total = self.db_manager.execute_query(week_total_query, fetch_results=True)[0]['count']
            
            return {
                'total_employees': total_employees,
                'today_checkins': today_checkins,
                'today_completed': today_completed,
                'week_total': week_total
            }
            
        except DatabaseQueryError as e:
            logger.error(f"Failed to get attendance stats: {e}")
            raise
    
    def get_employee_attendance_summary(self, employee_id: int, days: int = 30) -> Dict[str, Any]:
        """
        Get attendance summary for specific employee (admin function)
        
        Args:
            employee_id: Database ID of the employee
            days: Number of days to analyze
            
        Returns:
            Dictionary containing attendance summary
        """
        try:
            query = """
                SELECT 
                    COUNT(*) as total_days,
                    COUNT(check_out_time) as completed_days,
                    AVG(TIME_TO_SEC(check_in_time)) as avg_checkin_seconds,
                    AVG(CASE WHEN check_out_time IS NOT NULL 
                        THEN TIME_TO_SEC(TIMEDIFF(check_out_time, check_in_time)) 
                        ELSE NULL END) as avg_work_seconds
                FROM attendances 
                WHERE employee_id = %s 
                AND work_date >= DATE_SUB(CURDATE(), INTERVAL %s DAY)
            """
            
            results = self.db_manager.execute_query(query, (employee_id, days), fetch_results=True)
            
            if results and results[0]:
                data = results[0]
                return {
                    'total_days': data['total_days'] or 0,
                    'completed_days': data['completed_days'] or 0,
                    'avg_checkin_time': self._seconds_to_time_string(data['avg_checkin_seconds']),
                    'avg_work_hours': self._seconds_to_hours_string(data['avg_work_seconds'])
                }
            
            return {
                'total_days': 0,
                'completed_days': 0,
                'avg_checkin_time': 'N/A',
                'avg_work_hours': 'N/A'
            }
            
        except DatabaseQueryError as e:
            logger.error(f"Failed to get employee attendance summary: {e}")
            raise
    
    def _seconds_to_time_string(self, seconds: float) -> str:
        """Convert seconds to HH:MM format"""
        if seconds is None:
            return 'N/A'
        
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{hours:02d}:{minutes:02d}"
    
    def _seconds_to_hours_string(self, seconds: float) -> str:
        """Convert seconds to hours format"""
        if seconds is None:
            return 'N/A'
        
        hours = seconds / 3600
        return f"{hours:.1f} ชั่วโมง"