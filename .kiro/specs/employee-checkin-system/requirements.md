# Requirements Document

## Introduction

This document outlines the requirements for an employee check-in/check-out web application that allows employees to log their work attendance through Google Workspace authentication. The system will be built using Flask (Python), MariaDB, and will restrict access to employees with company domain email addresses only. The application focuses on core functionality with a simple, clean interface that prioritizes ease of use and reliable time tracking.

## Requirements

### Requirement 1: Google Workspace Authentication

**User Story:** As an employee, I want to log in using my company Google Workspace account, so that I can securely access the time tracking system without creating additional credentials.

#### Acceptance Criteria

1. WHEN an employee visits the application THEN the system SHALL display a "Login with Google" button
2. WHEN an employee clicks the login button THEN the system SHALL redirect to Google OAuth 2.0 authentication
3. WHEN an employee successfully authenticates with Google THEN the system SHALL verify the email domain matches the company domain
4. IF the email domain does not match the company domain THEN the system SHALL reject the login and display an error message
5. WHEN authentication is successful and domain is verified THEN the system SHALL create or update the employee record in the database
6. WHEN employee data is stored THEN the system SHALL save google_id, email, name, and picture_url to the employees table

### Requirement 2: Daily Check-in Functionality

**User Story:** As an employee, I want to check in when I start work, so that my arrival time is accurately recorded for attendance tracking.

#### Acceptance Criteria

1. WHEN an authenticated employee accesses the main page AND has not checked in today THEN the system SHALL display a "Check In" button
2. WHEN an employee clicks the "Check In" button THEN the system SHALL record the current timestamp as check_in_time
3. WHEN check-in is recorded THEN the system SHALL create a new attendance record with employee_id, check_in_time, and work_date
4. WHEN check-in is successful THEN the system SHALL display confirmation message and show the recorded check-in time
5. WHEN an employee has already checked in today THEN the system SHALL NOT display the "Check In" button

### Requirement 3: Daily Check-out Functionality

**User Story:** As an employee, I want to check out when I finish work, so that my departure time is recorded and my work hours are complete.

#### Acceptance Criteria

1. WHEN an authenticated employee has checked in today AND has not checked out THEN the system SHALL display a "Check Out" button
2. WHEN an employee clicks the "Check Out" button THEN the system SHALL update the attendance record with current timestamp as check_out_time
3. WHEN check-out is recorded THEN the system SHALL display confirmation message showing both check-in and check-out times
4. WHEN an employee has completed both check-in and check-out for the day THEN the system SHALL display "Attendance completed for today" message
5. WHEN an employee has not checked in today THEN the system SHALL NOT display the "Check Out" button

### Requirement 4: Attendance History Display

**User Story:** As an employee, I want to view my recent attendance history, so that I can track my work patterns and verify my recorded hours.

#### Acceptance Criteria

1. WHEN an authenticated employee accesses the main page THEN the system SHALL display attendance history for the last 14 days
2. WHEN displaying attendance history THEN the system SHALL show work_date, check_in_time, and check_out_time in a table format
3. WHEN an attendance record has no check_out_time THEN the system SHALL display "Not checked out" or similar indicator
4. WHEN there are no attendance records THEN the system SHALL display "No attendance history found" message
5. WHEN attendance data is displayed THEN the system SHALL format dates and times in a user-friendly format

### Requirement 5: Session Management

**User Story:** As an employee, I want my login session to be maintained securely, so that I don't need to re-authenticate frequently while using the application.

#### Acceptance Criteria

1. WHEN an employee successfully logs in THEN the system SHALL create a secure session using Flask-Login
2. WHEN an employee navigates between pages THEN the system SHALL maintain their authenticated state
3. WHEN an employee closes the browser and returns within a reasonable time THEN the system SHALL remember their login status
4. WHEN an employee clicks logout THEN the system SHALL clear the session and redirect to login page
5. WHEN an unauthenticated user tries to access protected pages THEN the system SHALL redirect to the login page

### Requirement 6: Database Schema and Data Integrity

**User Story:** As a system administrator, I want employee and attendance data to be stored reliably, so that time tracking records are accurate and persistent.

#### Acceptance Criteria

1. WHEN the system starts THEN the database SHALL contain an employees table with id, google_id, email, name, picture_url, and created_at fields
2. WHEN the system starts THEN the database SHALL contain an attendances table with id, employee_id, check_in_time, check_out_time, and work_date fields
3. WHEN an employee record is deleted THEN the system SHALL cascade delete all related attendance records
4. WHEN attendance data is stored THEN the system SHALL ensure work_date is properly indexed for efficient queries
5. WHEN duplicate check-ins are attempted for the same date THEN the system SHALL prevent creation of duplicate records

### Requirement 7: User Interface and Experience

**User Story:** As an employee, I want a clean and simple interface, so that I can quickly perform check-in/check-out actions without confusion.

#### Acceptance Criteria

1. WHEN the application loads THEN the system SHALL display a clean, minimal interface using Pico.css or similar framework
2. WHEN displaying the main page THEN the system SHALL show current status (not checked in, checked in, or completed) prominently
3. WHEN showing attendance history THEN the system SHALL use a clear table layout with proper spacing and readability
4. WHEN displaying user information THEN the system SHALL show the employee's name and profile picture from Google
5. WHEN errors occur THEN the system SHALL display user-friendly error messages with clear next steps