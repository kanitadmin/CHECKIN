"""
Employee data model and repository for Employee Check-in System
"""
from flask_login import UserMixin
from typing import Optional, Dict, Any, List
from database import DatabaseManager, DatabaseQueryError
from security_utils import sanitize_user_input, SecurityValidator
import logging
import pymysql  # Added for cursor access

logger = logging.getLogger(__name__)


class Employee(UserMixin):
    """
    Employee class that implements Flask-Login UserMixin for session management
    
    This class represents an employee user and provides the required methods
    for Flask-Login integration to manage user sessions.
    """
    
    def __init__(self, id: int, google_id: str, email: str, name: str = None, picture_url: str = None, created_at: str = None, role: str = 'employee', department_id: int = None):
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
            department_id: Department ID (foreign key)
        """
        self.id = id
        self.google_id = google_id
        self.email = email
        self.name = name
        self.picture_url = picture_url
        self.created_at = created_at
        self.role = role
        self.department_id = department_id
    
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
            'role': self.role,
            'department_id': self.department_id
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
                SELECT id, google_id, email, name, picture_url, created_at, role, department_id
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
                    role=row.get('role', 'employee'),
                    department_id=row.get('department_id')
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
                SELECT id, google_id, email, name, picture_url, created_at, role, department_id
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
                    role=row.get('role', 'employee'),
                    department_id=row.get('department_id')
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
                SELECT id, google_id, email, name, picture_url, created_at, role, department_id
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
                    role=row.get('role', 'employee'),
                    department_id=row.get('department_id')
                )
            
            return None
            
        except DatabaseQueryError as e:
            logger.error(f"Failed to find employee by ID {employee_id}: {e}")
            raise
    
    def get_all_employees(self) -> List[Employee]:
        """
        Get all employees in the system
        
        Returns:
            List of Employee objects
        """
        try:
            query = """
                SELECT id, google_id, email, name, picture_url, created_at, role, department_id
                FROM employees 
                ORDER BY name
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
                    role=row.get('role', 'employee'),
                    department_id=row.get('department_id')
                ))
            
            return employees
            
        except DatabaseQueryError as e:
            logger.error(f"Failed to get all employees: {e}")
            raise
    
    def update_employee_role(self, employee_id: int, role: str) -> bool:
        """
        Update employee role (admin/employee)
        
        Args:
            employee_id: Database primary key
            role: New role ('employee' or 'admin')
            
        Returns:
            True if successful, False otherwise
        """
        try:
            query = """
                UPDATE employees 
                SET role = %s 
                WHERE id = %s
            """
            
            self.db_manager.execute_query(query, (role, employee_id))
            return True
            
        except DatabaseQueryError as e:
            logger.error(f"Failed to update employee role for ID {employee_id}: {e}")
            return False
    
    def update_employee_department(self, employee_id: int, department_id: int) -> bool:
        """
        Update employee department assignment
        
        Args:
            employee_id: Database primary key
            department_id: Department ID to assign (None to unassign)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            query = """
                UPDATE employees 
                SET department_id = %s 
                WHERE id = %s
            """
            
            self.db_manager.execute_query(query, (department_id, employee_id))
            return True
            
        except DatabaseQueryError as e:
            logger.error(f"Failed to update employee department for ID {employee_id}: {e}")
            return False
    
    def get_employees_by_department(self, department_id: int) -> List[Employee]:
        """
        Get all employees in a specific department
        
        Args:
            department_id: Department ID
            
        Returns:
            List of Employee objects
        """
        try:
            query = """
                SELECT id, google_id, email, name, picture_url, created_at, role, department_id
                FROM employees 
                WHERE department_id = %s
                ORDER BY name
            """
            
            results = self.db_manager.execute_query(query, (department_id,), fetch_results=True)
            
            employees = []
            for row in results:
                employees.append(Employee(
                    id=row['id'],
                    google_id=row['google_id'],
                    email=row['email'],
                    name=row['name'],
                    picture_url=row['picture_url'],
                    created_at=row['created_at'],
                    role=row.get('role', 'employee'),
                    department_id=row.get('department_id')
                ))
            
            return employees
            
        except DatabaseQueryError as e:
            logger.error(f"Failed to get employees by department {department_id}: {e}")
            raise


class Department:
    """
    Department class representing a department in the organization
    """
    
    def __init__(self, id: int, name: str, description: str = None, created_at: str = None):
        """
        Initialize Department instance
        
        Args:
            id: Database primary key
            name: Department name
            description: Department description
            created_at: Creation timestamp
        """
        self.id = id
        self.name = name
        self.description = description
        self.created_at = created_at
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert Department object to dictionary representation
        
        Returns:
            Dictionary containing department data
        """
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'created_at': self.created_at
        }


class DepartmentRepository:
    """
    Repository class for Department data operations
    """
    
    def __init__(self):
        """Initialize repository with database manager"""
        self.db_manager = DatabaseManager()
    
    def create_department(self, name: str, description: str = None) -> Department:
        """
        Create a new department
        
        Args:
            name: Department name
            description: Department description (optional)
            
        Returns:
            Created Department object
        """
        try:
            query = """
                INSERT INTO departments (name, description)
                VALUES (%s, %s)
            """
            
            # Execute the query and get the connection to retrieve the insert ID
            with self.db_manager.get_db_connection() as connection:
                with connection.cursor(pymysql.cursors.DictCursor) as cursor:
                    cursor.execute(query, (name, description))
                    connection.commit()
                    department_id = cursor.lastrowid
            
            return Department(
                id=department_id,
                name=name,
                description=description,
                created_at=None  # Will be set by database
            )
            
        except DatabaseQueryError as e:
            logger.error(f"Failed to create department '{name}': {e}")
            raise
    
    def get_all_departments(self) -> List[Department]:
        """
        Get all departments
        
        Returns:
            List of Department objects
        """
        try:
            query = """
                SELECT id, name, description, created_at
                FROM departments
                ORDER BY name
            """
            
            results = self.db_manager.execute_query(query, fetch_results=True)
            
            departments = []
            for row in results:
                departments.append(Department(
                    id=row['id'],
                    name=row['name'],
                    description=row['description'],
                    created_at=row['created_at']
                ))
            
            return departments
            
        except DatabaseQueryError as e:
            logger.error(f"Failed to get all departments: {e}")
            raise
    
    def get_department_by_id(self, department_id: int) -> Optional[Department]:
        """
        Get department by ID
        
        Args:
            department_id: Department ID
            
        Returns:
            Department object if found, None otherwise
        """
        try:
            query = """
                SELECT id, name, description, created_at
                FROM departments
                WHERE id = %s
            """
            
            results = self.db_manager.execute_query(query, (department_id,), fetch_results=True)
            
            if results:
                row = results[0]
                return Department(
                    id=row['id'],
                    name=row['name'],
                    description=row['description'],
                    created_at=row['created_at']
                )
            
            return None
            
        except DatabaseQueryError as e:
            logger.error(f"Failed to get department by ID {department_id}: {e}")
            raise
    
    def update_department(self, department_id: int, name: str = None, description: str = None) -> Optional[Department]:
        """
        Update department information
        
        Args:
            department_id: Department ID
            name: New department name (optional)
            description: New department description (optional)
            
        Returns:
            Updated Department object if successful, None otherwise
        """
        try:
            # Build dynamic update query
            update_fields = []
            params = []
            
            if name is not None:
                update_fields.append("name = %s")
                params.append(name)
            
            if description is not None:
                update_fields.append("description = %s")
                params.append(description)
            
            # If no fields to update, return None
            if not update_fields:
                return None
            
            # Add department_id to params
            params.append(department_id)
            
            query = f"""
                UPDATE departments
                SET {', '.join(update_fields)}
                WHERE id = %s
            """
            
            self.db_manager.execute_query(query, tuple(params))
            
            # Return updated department
            return self.get_department_by_id(department_id)
            
        except DatabaseQueryError as e:
            logger.error(f"Failed to update department ID {department_id}: {e}")
            raise
    
    def delete_department(self, department_id: int) -> bool:
        """
        Delete a department
        
        Args:
            department_id: Department ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            query = "DELETE FROM departments WHERE id = %s"
            self.db_manager.execute_query(query, (department_id,))
            return True
            
        except DatabaseQueryError as e:
            logger.error(f"Failed to delete department ID {department_id}: {e}")
            return False
    
    def get_department_employee_count(self, department_id: int) -> int:
        """
        Get the number of employees in a department
        
        Args:
            department_id: Department ID
            
        Returns:
            Number of employees in the department
        """
        try:
            query = """
                SELECT COUNT(*) as count
                FROM employees
                WHERE department_id = %s
            """
            
            results = self.db_manager.execute_query(query, (department_id,), fetch_results=True)
            
            if results:
                return results[0]['count']
            
            return 0
            
        except DatabaseQueryError as e:
            logger.error(f"Failed to get employee count for department {department_id}: {e}")
            return 0


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
    
    def create_checkin(self, employee_id: int, latitude: float = None, longitude: float = None, 
                      location_verified: bool = False) -> Dict[str, Any]:
        """
        Insert new attendance record with check_in_time, work_date, and location data
        
        Args:
            employee_id: Database ID of the employee
            latitude: User's latitude coordinate
            longitude: User's longitude coordinate
            location_verified: Whether the location was verified against allowed locations
            
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
            
            # Insert new check-in record with location data
            query = """
                INSERT INTO attendances (employee_id, check_in_time, work_date, latitude, longitude, location_verified)
                VALUES (%s, NOW(), CURDATE(), %s, %s, %s)
            """
            
            self.db_manager.execute_query(query, (employee_id, latitude, longitude, location_verified))
            
            # Retrieve the newly created attendance record
            created_attendance = self.get_today_attendance(employee_id)
            if not created_attendance:
                raise DatabaseQueryError("Failed to retrieve newly created attendance record")
            
            logger.info(f"Successfully created check-in for employee {employee_id} with location verification: {location_verified}")
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


class WorkTimeSettings:
    """
    Work time settings model for managing work hours configuration
    """
    
    def __init__(self, id: int = None, start_time: str = None, end_time: str = None, 
                 break_duration_minutes: int = 60, is_active: bool = True, 
                 created_at: str = None, updated_at: str = None):
        """
        Initialize WorkTimeSettings instance
        
        Args:
            id: Database primary key
            start_time: Work start time (HH:MM format)
            end_time: Work end time (HH:MM format)
            break_duration_minutes: Break duration in minutes
            is_active: Whether this setting is active
            created_at: Creation timestamp
            updated_at: Last update timestamp
        """
        self.id = id
        self.start_time = start_time
        self.end_time = end_time
        self.break_duration_minutes = break_duration_minutes
        self.is_active = is_active
        self.created_at = created_at
        self.updated_at = updated_at
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert WorkTimeSettings object to dictionary"""
        return {
            'id': self.id,
            'start_time': self.start_time,
            'end_time': self.end_time,
            'break_duration_minutes': self.break_duration_minutes,
            'is_active': self.is_active,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }
    
    def __repr__(self) -> str:
        """String representation of WorkTimeSettings object"""
        return f"<WorkTimeSettings {self.start_time}-{self.end_time} (ID: {self.id})>"


class WorkTimeRepository:
    """
    Repository class for WorkTimeSettings data operations
    """
    
    def __init__(self):
        """Initialize repository with database manager"""
        self.db_manager = DatabaseManager()
    
    def get_active_settings(self) -> Optional[WorkTimeSettings]:
        """
        Get currently active work time settings
        
        Returns:
            WorkTimeSettings object if found, None otherwise
        """
        try:
            query = """
                SELECT id, start_time, end_time, break_duration_minutes, 
                       is_active, created_at, updated_at
                FROM work_time_settings 
                WHERE is_active = 1
                ORDER BY created_at DESC
                LIMIT 1
            """
            
            results = self.db_manager.execute_query(query, fetch_results=True)
            
            if results:
                row = results[0]
                return WorkTimeSettings(
                    id=row['id'],
                    start_time=str(row['start_time']) if row['start_time'] else None,
                    end_time=str(row['end_time']) if row['end_time'] else None,
                    break_duration_minutes=row['break_duration_minutes'],
                    is_active=bool(row['is_active']),
                    created_at=row['created_at'],
                    updated_at=row['updated_at']
                )
            
            return None
            
        except DatabaseQueryError as e:
            logger.error(f"Failed to get active work time settings: {e}")
            raise
    
    def get_all_settings(self) -> List[WorkTimeSettings]:
        """
        Get all work time settings
        
        Returns:
            List of WorkTimeSettings objects
        """
        try:
            query = """
                SELECT id, start_time, end_time, break_duration_minutes, 
                       is_active, created_at, updated_at
                FROM work_time_settings 
                ORDER BY created_at DESC
            """
            
            results = self.db_manager.execute_query(query, fetch_results=True)
            
            settings = []
            for row in results:
                settings.append(WorkTimeSettings(
                    id=row['id'],
                    start_time=str(row['start_time']) if row['start_time'] else None,
                    end_time=str(row['end_time']) if row['end_time'] else None,
                    break_duration_minutes=row['break_duration_minutes'],
                    is_active=bool(row['is_active']),
                    created_at=row['created_at'],
                    updated_at=row['updated_at']
                ))
            
            return settings
            
        except DatabaseQueryError as e:
            logger.error(f"Failed to get all work time settings: {e}")
            raise
    
    def create_settings(self, start_time: str, end_time: str, 
                       break_duration_minutes: int = 60) -> WorkTimeSettings:
        """
        Create new work time settings
        
        Args:
            start_time: Work start time (HH:MM format)
            end_time: Work end time (HH:MM format)
            break_duration_minutes: Break duration in minutes
            
        Returns:
            Created WorkTimeSettings object
        """
        try:
            # Deactivate all existing settings first
            self._deactivate_all_settings()
            
            # Create new active setting
            query = """
                INSERT INTO work_time_settings (start_time, end_time, break_duration_minutes, is_active)
                VALUES (%s, %s, %s, 1)
            """
            
            self.db_manager.execute_query(query, (start_time, end_time, break_duration_minutes))
            
            # Get the newly created settings
            created_settings = self.get_active_settings()
            if not created_settings:
                raise DatabaseQueryError("Failed to retrieve newly created work time settings")
            
            logger.info(f"Successfully created work time settings: {start_time}-{end_time}")
            return created_settings
            
        except DatabaseQueryError as e:
            logger.error(f"Failed to create work time settings: {e}")
            raise
    
    def update_settings(self, settings_id: int, start_time: str = None, 
                       end_time: str = None, break_duration_minutes: int = None) -> WorkTimeSettings:
        """
        Update existing work time settings
        
        Args:
            settings_id: Database ID of settings to update
            start_time: New start time (optional)
            end_time: New end time (optional)
            break_duration_minutes: New break duration (optional)
            
        Returns:
            Updated WorkTimeSettings object
        """
        try:
            # Build dynamic update query
            update_fields = []
            params = []
            
            if start_time is not None:
                update_fields.append("start_time = %s")
                params.append(start_time)
            
            if end_time is not None:
                update_fields.append("end_time = %s")
                params.append(end_time)
            
            if break_duration_minutes is not None:
                update_fields.append("break_duration_minutes = %s")
                params.append(break_duration_minutes)
            
            if not update_fields:
                raise ValueError("No fields to update")
            
            update_fields.append("updated_at = NOW()")
            params.append(settings_id)
            
            query = f"""
                UPDATE work_time_settings 
                SET {', '.join(update_fields)}
                WHERE id = %s
            """
            
            self.db_manager.execute_query(query, params)
            
            # Get updated settings
            updated_settings = self.get_settings_by_id(settings_id)
            if not updated_settings:
                raise DatabaseQueryError("Failed to retrieve updated work time settings")
            
            logger.info(f"Successfully updated work time settings ID: {settings_id}")
            return updated_settings
            
        except DatabaseQueryError as e:
            logger.error(f"Failed to update work time settings: {e}")
            raise
    
    def get_settings_by_id(self, settings_id: int) -> Optional[WorkTimeSettings]:
        """
        Get work time settings by ID
        
        Args:
            settings_id: Database ID of settings
            
        Returns:
            WorkTimeSettings object if found, None otherwise
        """
        try:
            query = """
                SELECT id, start_time, end_time, break_duration_minutes, 
                       is_active, created_at, updated_at
                FROM work_time_settings 
                WHERE id = %s
            """
            
            results = self.db_manager.execute_query(query, (settings_id,), fetch_results=True)
            
            if results:
                row = results[0]
                return WorkTimeSettings(
                    id=row['id'],
                    start_time=str(row['start_time']) if row['start_time'] else None,
                    end_time=str(row['end_time']) if row['end_time'] else None,
                    break_duration_minutes=row['break_duration_minutes'],
                    is_active=bool(row['is_active']),
                    created_at=row['created_at'],
                    updated_at=row['updated_at']
                )
            
            return None
            
        except DatabaseQueryError as e:
            logger.error(f"Failed to get work time settings by ID {settings_id}: {e}")
            raise
    
    def activate_settings(self, settings_id: int) -> WorkTimeSettings:
        """
        Activate specific work time settings (deactivates all others)
        
        Args:
            settings_id: Database ID of settings to activate
            
        Returns:
            Activated WorkTimeSettings object
        """
        try:
            # Deactivate all settings first
            self._deactivate_all_settings()
            
            # Activate the specified settings
            query = """
                UPDATE work_time_settings 
                SET is_active = 1, updated_at = NOW()
                WHERE id = %s
            """
            
            self.db_manager.execute_query(query, (settings_id,))
            
            # Get activated settings
            activated_settings = self.get_settings_by_id(settings_id)
            if not activated_settings:
                raise DatabaseQueryError("Failed to retrieve activated work time settings")
            
            logger.info(f"Successfully activated work time settings ID: {settings_id}")
            return activated_settings
            
        except DatabaseQueryError as e:
            logger.error(f"Failed to activate work time settings: {e}")
            raise
    
    def delete_settings(self, settings_id: int) -> bool:
        """
        Delete work time settings
        
        Args:
            settings_id: Database ID of settings to delete
            
        Returns:
            True if successful
        """
        try:
            query = "DELETE FROM work_time_settings WHERE id = %s"
            self.db_manager.execute_query(query, (settings_id,))
            
            logger.info(f"Successfully deleted work time settings ID: {settings_id}")
            return True
            
        except DatabaseQueryError as e:
            logger.error(f"Failed to delete work time settings: {e}")
            raise
    
    def _deactivate_all_settings(self):
        """Deactivate all work time settings"""
        query = "UPDATE work_time_settings SET is_active = 0, updated_at = NOW()"
        self.db_manager.execute_query(query)