# Implementation Plan

- [x] 1. Project Setup and Environment Configuration





  - Create project directory structure with static and templates folders
  - Create requirements.txt with all necessary Python dependencies (Flask, Flask-Login, Authlib, PyMySQL, python-dotenv)
  - Create .env template file with all required environment variables for database, Google OAuth, and Flask configuration
  - Create basic app.py with minimal Flask application that can run and serve a simple "Hello World" page
  - _Requirements: 6.1, 6.2_

- [x] 2. Database Schema Implementation





  - Create database connection utility class using PyMySQL with proper error handling and connection pooling
  - Implement SQL scripts to create employees table with all required fields (id, google_id, email, name, picture_url, created_at)
  - Implement SQL scripts to create attendances table with foreign key relationships and proper indexes
  - Create database initialization function that sets up tables and indexes
  - Write unit tests for database connection and table creation
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_

- [x] 3. Employee Data Model and Repository









  - Create Employee class that implements Flask-Login UserMixin for session management
  - Implement EmployeeRepository class with methods for finding employees by google_id and email
  - Create employee creation and update methods that handle Google OAuth user data
  - Write unit tests for employee data operations and Flask-Login integration
  - _Requirements: 1.6, 5.1, 5.2_

- [x] 4. Google OAuth Authentication Setup




  - Configure Authlib OAuth client with Google OAuth 2.0 endpoints and credentials
  - Create /login route that displays login page with "Login with Google" button
  - Implement /auth/google route that initiates OAuth flow with proper state parameter for CSRF protection
  - Create /auth/callback route that handles OAuth callback and exchanges authorization code for user information
  - Implement domain validation function that checks if user email belongs to company domain
  - Write unit tests for OAuth configuration and domain validation logic
  - _Requirements: 1.1, 1.2, 1.3, 1.4_

- [x] 5. Authentication Flow and Session Management





  - Integrate OAuth callback with employee repository to create or update employee records
  - Implement Flask-Login session creation after successful authentication and domain validation
  - Create logout route that clears session and redirects to login page
  - Add login_required decorator and redirect logic for unauthenticated users
  - Write integration tests for complete authentication flow from login to session creation
  - _Requirements: 1.5, 1.6, 5.1, 5.2, 5.3, 5.4, 5.5_

- [x] 6. Attendance Data Model and Repository





  - Create AttendanceRepository class with methods for daily attendance operations
  - Implement get_today_attendance method that finds current day's attendance record for an employee
  - Create create_checkin method that inserts new attendance record with check_in_time and work_date
  - Implement update_checkout method that updates existing record with check_out_time
  - Add get_recent_history method that retrieves last 14 days of attendance records
  - Write unit tests for all attendance repository methods including edge cases
  - _Requirements: 6.3, 6.4, 6.5_

- [x] 7. Check-in Logic Implementation





  - Create attendance status determination function that returns current state (not checked in, checked in, completed)
  - Implement /check-in POST route that validates user is authenticated and hasn't already checked in today
  - Add check-in business logic that creates new attendance record with current timestamp
  - Implement duplicate check-in prevention using database unique constraint on employee_id and work_date
  - Create success response handling that confirms check-in time to user
  - Write unit tests for check-in logic including duplicate prevention and error scenarios
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

- [x] 8. Check-out Logic Implementation





  - Implement /check-out POST route that validates user is authenticated and has checked in today
  - Add check-out business logic that updates existing attendance record with check_out_time
  - Create validation to ensure check-out only works when there's an existing check-in for the day
  - Implement success response handling that shows both check-in and check-out times
  - Add error handling for attempting check-out without prior check-in
  - Write unit tests for check-out logic including validation and error scenarios
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

- [x] 9. Main Dashboard Implementation





  - Create main dashboard route (/) that determines current attendance status for logged-in user
  - Implement template logic that conditionally displays Check In button, Check Out button, or completion message
  - Add attendance history retrieval and display for last 14 days in table format
  - Create status display logic that shows current check-in time when user is checked in but not out
  - Implement proper date and time formatting for user-friendly display
  - Write integration tests for dashboard logic with different attendance states
  - _Requirements: 2.1, 2.5, 3.1, 3.5, 4.1, 4.2, 4.3, 4.4, 4.5_

- [x] 10. HTML Templates and User Interface





  - Create layout.html base template with navigation, user info display, and logout functionality
  - Implement login.html template with Google OAuth login button and clean styling
  - Create index.html dashboard template with conditional check-in/check-out buttons and attendance history table
  - Add Pico.css framework integration for clean, minimal styling
  - Implement user profile display showing name and picture from Google OAuth data
  - Create error message display system for authentication and operation failures
  - _Requirements: 1.1, 4.2, 4.3, 4.4, 7.1, 7.2, 7.3, 7.4, 7.5_

- [x] 11. Error Handling and Validation





  - Implement comprehensive error handling for database connection failures with retry logic
  - Add OAuth error handling with user-friendly messages for authentication failures
  - Create validation error handling for duplicate operations and constraint violations
  - Implement session expiry handling with automatic redirect to login
  - Add environment variable validation at application startup
  - Write unit tests for all error handling scenarios and edge cases
  - _Requirements: 1.4, 5.5, 6.5_

- [x] 12. Security Implementation





  - Add CSRF protection for OAuth state parameter and form submissions
  - Implement secure session configuration with proper cookie flags
  - Add SQL injection prevention verification for all database queries
  - Enable template auto-escaping for XSS protection
  - Implement HTTPS redirect configuration for production deployment
  - Write security tests for CSRF, XSS, and SQL injection prevention
  - _Requirements: 5.1, 5.2, 5.3_

- [x] 13. Integration Testing and End-to-End Validation





  - Create integration tests for complete user workflow from login to check-out
  - Implement mock Google OAuth responses for testing authentication flow
  - Add database transaction testing with rollback scenarios
  - Create end-to-end tests for attendance history display and data consistency
  - Test session persistence across browser refresh and navigation
  - Validate all error scenarios work correctly with proper user feedback
  - _Requirements: All requirements validation_