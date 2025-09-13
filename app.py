from flask import Flask, render_template, redirect, url_for, session, request, flash, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user

from authlib.integrations.flask_client import OAuth
from dotenv import load_dotenv
import os
import logging
import secrets
import requests
import time
from database import initialize_database, verify_database_schema, DatabaseConnectionError, DatabaseQueryError
from models import EmployeeRepository, AttendanceRepository
from location_models import LocationRepository, LocationValidator
from security_utils import SecurityValidator, sanitize_user_input

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ConfigurationError(Exception):
    """Custom exception for configuration errors"""
    pass


class AuthenticationError(Exception):
    """Custom exception for authentication errors"""
    pass

# Create Flask application
app = Flask(__name__)

# Security configuration
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'dev-secret-key')

# Secure session configuration
app.config['SESSION_COOKIE_SECURE'] = os.getenv('FLASK_ENV') == 'production'
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['PERMANENT_SESSION_LIFETIME'] = 3600  # 1 hour

# Security configuration (CSRF removed for simplicity)

# HTTPS redirect for production
@app.before_request
def force_https():
    """Force HTTPS in production environment"""
    if os.getenv('FLASK_ENV') == 'production':
        if not request.is_secure and request.headers.get('X-Forwarded-Proto') != 'https':
            return redirect(request.url.replace('http://', 'https://'), code=301)

# Template auto-escaping is enabled by default in Flask/Jinja2
# Verify it's enabled and configure additional security headers
@app.after_request
def add_security_headers(response):
    """Add security headers to all responses"""
    # XSS Protection
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    
    # Content Security Policy
    if os.getenv('FLASK_ENV') == 'production':
        response.headers['Content-Security-Policy'] = (
            "default-src 'self'; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "script-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "connect-src 'self'; "
            "font-src 'self' https://cdn.jsdelivr.net; "
            "frame-ancestors 'none';"
        )
    
    # HSTS for production
    if os.getenv('FLASK_ENV') == 'production' and request.is_secure:
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    
    return response

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'  # Redirect to login page for unauthenticated users

# Initialize OAuth
oauth = OAuth(app)

# Configure Google OAuth client with fallback configuration
try:
    google = oauth.register(
        name='google',
        client_id=os.getenv('GOOGLE_CLIENT_ID'),
        client_secret=os.getenv('GOOGLE_CLIENT_SECRET'),
        server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
        client_kwargs={
            'scope': 'openid email profile',
            'hd': os.getenv('HOSTED_DOMAIN')  # Restrict to company domain
        }
    )
except Exception as e:
    logger.warning(f"Failed to fetch Google metadata automatically: {e}")
    # Fallback to manual configuration
    google = oauth.register(
        name='google',
        client_id=os.getenv('GOOGLE_CLIENT_ID'),
        client_secret=os.getenv('GOOGLE_CLIENT_SECRET'),
        authorize_url='https://accounts.google.com/o/oauth2/auth',
        authorize_params=None,
        access_token_url='https://oauth2.googleapis.com/token',
        access_token_params=None,
        refresh_token_url=None,
        redirect_uri=None,
        client_kwargs={
            'scope': 'openid email profile',
            'hd': os.getenv('HOSTED_DOMAIN')
        },
        jwks_uri='https://www.googleapis.com/oauth2/v3/certs',
        issuer='https://accounts.google.com'
    )

# Initialize repositories
employee_repo = EmployeeRepository()
attendance_repo = AttendanceRepository()
location_repo = LocationRepository()

@login_manager.user_loader
def load_user(user_id):
    """
    Flask-Login user loader callback with comprehensive error handling
    
    This function is called by Flask-Login to reload the user object from the user ID
    stored in the session. It's required for Flask-Login to work properly.
    
    Args:
        user_id: String representation of the user's ID
        
    Returns:
        Employee object if found, None otherwise
    """
    if not user_id:
        return None
    
    try:
        employee_id = int(user_id)
        return employee_repo.find_by_id(employee_id)
    except (ValueError, TypeError) as e:
        logger.warning(f"Invalid user_id format in session: {user_id} - {e}")
        return None
    except DatabaseConnectionError as e:
        logger.error(f"Database connection error loading user {user_id}: {e}")
        return None
    except DatabaseQueryError as e:
        logger.error(f"Database query error loading user {user_id}: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error loading user {user_id}: {e}")
        return None

class AttendanceStatus:
    """Enumeration for attendance status states"""
    NOT_CHECKED_IN = "not_checked_in"
    CHECKED_IN = "checked_in"
    COMPLETED = "completed"


def get_attendance_status(employee_id):
    """
    Determine current attendance status for today with comprehensive error handling
    
    Args:
        employee_id: Database ID of the employee
        
    Returns:
        str: AttendanceStatus enum value indicating current state
    """
    if not employee_id:
        logger.warning("get_attendance_status called with empty employee_id")
        return AttendanceStatus.NOT_CHECKED_IN
    
    max_retries = 3
    retry_delay = 1  # seconds
    
    for attempt in range(max_retries):
        try:
            today_attendance = attendance_repo.get_today_attendance(employee_id)
            
            if not today_attendance:
                return AttendanceStatus.NOT_CHECKED_IN
            elif today_attendance['check_out_time'] is None:
                return AttendanceStatus.CHECKED_IN
            else:
                return AttendanceStatus.COMPLETED
                
        except DatabaseConnectionError as e:
            logger.warning(f"Database connection error getting attendance status (attempt {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                time.sleep(retry_delay * (attempt + 1))  # Exponential backoff
                continue
            else:
                logger.error(f"Failed to get attendance status after {max_retries} attempts due to connection issues")
                return AttendanceStatus.NOT_CHECKED_IN
                
        except DatabaseQueryError as e:
            logger.error(f"Database query error getting attendance status for employee {employee_id}: {e}")
            return AttendanceStatus.NOT_CHECKED_IN
            
        except Exception as e:
            logger.error(f"Unexpected error getting attendance status for employee {employee_id}: {e}")
            return AttendanceStatus.NOT_CHECKED_IN
    
    # Should not reach here, but fallback
    return AttendanceStatus.NOT_CHECKED_IN


def validate_company_domain(email):
    """
    Validates that user email belongs to company domain
    
    Args:
        email: User's email address
        
    Returns:
        tuple: (is_valid: bool, error_message: str)
    """
    if not email or (isinstance(email, str) and email.strip() == ''):
        return False, "Email address is required"
    
    company_domain = os.getenv('HOSTED_DOMAIN')
    if not company_domain:
        return False, "Company domain not configured"
    
    try:
        # Basic email format validation
        if '@' not in email or email.count('@') != 1:
            return False, "Invalid email format"
        
        parts = email.split('@')
        if len(parts) != 2 or not parts[0] or not parts[1]:
            return False, "Invalid email format"
        
        user_domain = parts[1].lower().strip()
        company_domain = company_domain.lower().strip()
        
        if user_domain == company_domain:
            return True, ""
        else:
            return False, f"Access restricted to {company_domain} domain only"
    except (IndexError, AttributeError, TypeError):
        return False, "Invalid email format"

@app.route('/login')
def login():
    """
    Display login page with Google OAuth login button
    
    Returns:
        Rendered login template with Google login option
    """
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    return render_template('login.html')

@app.route('/auth/google')
def auth_google():
    """
    Initiate Google OAuth flow with proper state parameter for CSRF protection
    
    Returns:
        Redirect to Google OAuth authorization URL
    """
    # Generate and store state parameter for CSRF protection
    state = secrets.token_urlsafe(32)
    session['oauth_state'] = state
    
    # Build redirect URI
    redirect_uri = url_for('auth_callback', _external=True)
    
    # Initiate OAuth flow
    return google.authorize_redirect(redirect_uri, state=state)

@app.route('/auth/callback')
def auth_callback():
    """
    Handle OAuth callback with comprehensive error handling and user-friendly messages
    
    Returns:
        Redirect to main dashboard on success, or login page on failure
    """
    try:
        # Check for OAuth provider errors
        oauth_error = request.args.get('error')
        if oauth_error:
            error_description = request.args.get('error_description', 'Unknown OAuth error')
            logger.error(f"OAuth provider error: {oauth_error} - {error_description}")
            
            # Provide user-friendly error messages
            if oauth_error == 'access_denied':
                flash('Login was cancelled. Please try again to access the system.', 'error')
            elif oauth_error == 'invalid_request':
                flash('Invalid login request. Please try again.', 'error')
            elif oauth_error == 'unauthorized_client':
                flash('Application is not authorized. Please contact your administrator.', 'error')
            elif oauth_error == 'unsupported_response_type':
                flash('Login configuration error. Please contact your administrator.', 'error')
            elif oauth_error == 'invalid_scope':
                flash('Insufficient permissions. Please contact your administrator.', 'error')
            elif oauth_error == 'server_error':
                flash('Google authentication service is temporarily unavailable. Please try again later.', 'error')
            elif oauth_error == 'temporarily_unavailable':
                flash('Authentication service is temporarily unavailable. Please try again in a few minutes.', 'error')
            else:
                flash(f'Authentication error: {error_description}', 'error')
            
            return redirect(url_for('login'))
        
        # Verify state parameter for CSRF protection
        received_state = request.args.get('state')
        expected_state = session.get('oauth_state')
        
        if not received_state or not expected_state or received_state != expected_state:
            logger.warning(f"CSRF state mismatch: received={received_state}, expected={expected_state}")
            flash('Security validation failed. Please try logging in again.', 'error')
            session.pop('oauth_state', None)  # Clear invalid state
            return redirect(url_for('login'))
        
        # Clear the state from session
        session.pop('oauth_state', None)
        
        # Exchange authorization code for token with retry logic
        logger.info("Exchanging authorization code for access token...")
        token = None
        max_token_retries = 3
        
        for attempt in range(max_token_retries):
            try:
                token = google.authorize_access_token()
                break
            except Exception as token_error:
                logger.warning(f"Token exchange attempt {attempt + 1} failed: {token_error}")
                if attempt == max_token_retries - 1:
                    raise AuthenticationError(f"Failed to obtain access token after {max_token_retries} attempts")
                time.sleep(1)  # Brief delay before retry
        
        if not token:
            raise AuthenticationError('No access token received from Google')
        
        # Extract user information with fallback methods
        logger.info("Retrieving user information from Google...")
        user_info = None
        
        # Try userinfo endpoint first
        try:
            user_info = token.get('userinfo')
        except Exception as e:
            logger.warning(f"Failed to get userinfo from token: {e}")
        
        # Fallback to ID token parsing
        if not user_info:
            try:
                id_token = token.get('id_token')
                if id_token:
                    user_info = google.parse_id_token(token)
                    logger.info("Successfully parsed user info from ID token")
            except Exception as e:
                logger.warning(f"Failed to parse ID token: {e}")
        
        # Final fallback - try direct API call
        if not user_info and token.get('access_token'):
            try:
                response = requests.get(
                    'https://www.googleapis.com/oauth2/v2/userinfo',
                    headers={'Authorization': f"Bearer {token['access_token']}"},
                    timeout=10
                )
                if response.status_code == 200:
                    user_info = response.json()
                    logger.info("Successfully retrieved user info from direct API call")
            except Exception as e:
                logger.warning(f"Failed to get user info from direct API call: {e}")
        
        if not user_info:
            raise AuthenticationError('Unable to retrieve user information from Google')
        
        # Validate and sanitize required user info fields
        email = sanitize_user_input(user_info.get('email'))
        google_id = sanitize_user_input(user_info.get('sub'))
        picture_url = user_info.get('picture')
        
        # Log user info for debugging (remove in production)
        logger.info(f"Google user info - Email: {email}, Picture URL: {picture_url}")
        
        if not email:
            raise AuthenticationError('No email address received from Google')
        if not google_id:
            raise AuthenticationError('No user ID received from Google')
        
        # Additional validation for email format
        if not SecurityValidator.validate_xss_input(email) or '@' not in email:
            SecurityValidator.log_security_event("INVALID_EMAIL", f"Invalid email format from OAuth: {email}")
            raise AuthenticationError('Invalid email format received from Google')
        
        logger.info(f"Retrieved user info for: {email}")
        
        # Validate company domain
        is_valid, error_message = validate_company_domain(email)
        if not is_valid:
            logger.warning(f"Domain validation failed for {email}: {error_message}")
            flash(error_message, 'error')
            return redirect(url_for('login'))
        
        # Create or update employee record with retry logic
        logger.info(f"Creating/updating employee record for: {email}")
        employee = None
        max_db_retries = 3
        
        for attempt in range(max_db_retries):
            try:
                employee = employee_repo.create_or_update(user_info)
                break
            except DatabaseConnectionError as e:
                logger.warning(f"Database connection error on attempt {attempt + 1}: {e}")
                if attempt == max_db_retries - 1:
                    flash('Database connection issue. Please try again in a moment.', 'error')
                    return redirect(url_for('login'))
                time.sleep(1 * (attempt + 1))  # Exponential backoff
            except DatabaseQueryError as e:
                logger.error(f"Database query error creating/updating employee: {e}")
                flash('Unable to save user information. Please try again.', 'error')
                return redirect(url_for('login'))
        
        if not employee:
            flash('Failed to create user account. Please try again.', 'error')
            return redirect(url_for('login'))
        
        # Log the user in using Flask-Login
        try:
            login_user(employee, remember=True)
            logger.info(f"User {email} logged in successfully")
        except Exception as e:
            logger.error(f"Failed to create user session: {e}")
            flash('Login session creation failed. Please try again.', 'error')
            return redirect(url_for('login'))
        
        # Redirect to main dashboard
        return redirect(url_for('index'))
        
    except AuthenticationError as e:
        logger.error(f"Authentication error: {e}")
        flash(str(e), 'error')
        return redirect(url_for('login'))
        
    except requests.exceptions.Timeout:
        logger.error("Timeout during OAuth callback")
        flash('Authentication request timed out. Please try again.', 'error')
        return redirect(url_for('login'))
        
    except requests.exceptions.ConnectionError:
        logger.error("Connection error during OAuth callback")
        flash('Network connection issue. Please check your connection and try again.', 'error')
        return redirect(url_for('login'))
        
    except Exception as e:
        logger.error(f"Unexpected OAuth callback error: {e}", exc_info=True)
        flash('An unexpected error occurred during login. Please try again.', 'error')
        return redirect(url_for('login'))

@app.route('/check-in', methods=['POST'])
@login_required
def check_in():
    """
    Record check-in time for authenticated employee with comprehensive error handling
    
    Validates user is authenticated and hasn't already checked in today,
    then creates new attendance record with current timestamp.
    
    Returns:
        JSON response with success/error message and check-in time
    """
    if not current_user or not current_user.id:
        logger.error("Check-in attempted with invalid user session")
        return {
            'success': False,
            'error': 'Invalid session. Please log in again.'
        }, 401
    
    # Basic request validation (CSRF removed)
    if request.method != 'POST':
        return {
            'success': False,
            'error': 'Invalid request method.'
        }, 405
    
    employee_id = current_user.id
    max_retries = 3
    
    # Get location data from request
    data = request.get_json() or {}
    user_latitude = data.get('latitude')
    user_longitude = data.get('longitude')
    
    for attempt in range(max_retries):
        try:
            # Check current attendance status
            status = get_attendance_status(employee_id)
            
            if status != AttendanceStatus.NOT_CHECKED_IN:
                if status == AttendanceStatus.CHECKED_IN:
                    return {
                        'success': False,
                        'error': 'You have already checked in today. Please check out first.'
                    }, 400
                else:  # COMPLETED
                    return {
                        'success': False,
                        'error': 'You have already completed attendance for today.'
                    }, 400
            
            # Validate location if coordinates provided
            location_verified = False
            matched_location = None
            
            if user_latitude is not None and user_longitude is not None:
                try:
                    # Get active location settings
                    allowed_locations = location_repo.get_active_locations()
                    
                    if allowed_locations:
                        is_valid, matched_location, distance = LocationValidator.validate_user_location(
                            user_latitude, user_longitude, allowed_locations
                        )
                        
                        if not is_valid:
                            closest_location_name = matched_location.name if matched_location else "ไม่ทราบ"
                            return {
                                'success': False,
                                'error': f'คุณอยู่นอกพื้นที่ที่อนุญาต ตำแหน่งที่ใกล้ที่สุด: {closest_location_name} ({distance:.0f} เมตร)',
                                'location_error': True,
                                'distance': distance,
                                'closest_location': closest_location_name
                            }, 400
                        
                        location_verified = True
                        logger.info(f"Location verified for employee {employee_id}: {matched_location.name} ({distance:.0f}m)")
                    else:
                        logger.warning("No active locations configured, allowing check-in without location verification")
                        
                except Exception as e:
                    logger.error(f"Location validation error: {e}")
                    # Continue without location verification if there's an error
                    pass
            else:
                logger.warning(f"Check-in without location data for employee {employee_id}")
            
            # Create check-in record with location data
            attendance_record = attendance_repo.create_checkin(
                employee_id, 
                latitude=user_latitude, 
                longitude=user_longitude, 
                location_verified=location_verified
            )
            
            # Format check-in time for response
            check_in_time = attendance_record['check_in_time']
            if hasattr(check_in_time, 'strftime'):
                formatted_time = check_in_time.strftime('%I:%M %p')
            else:
                formatted_time = str(check_in_time)
            
            logger.info(f"Employee {employee_id} ({current_user.email}) checked in at {formatted_time}")
            
            return {
                'success': True,
                'message': f'Check-in successful! Time: {formatted_time}',
                'check_in_time': formatted_time,
                'attendance_id': attendance_record['id']
            }, 200
            
        except DatabaseConnectionError as e:
            logger.warning(f"Database connection error during check-in (attempt {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                time.sleep(1 * (attempt + 1))  # Exponential backoff
                continue
            else:
                return {
                    'success': False,
                    'error': 'Database connection issue. Please try again in a moment.'
                }, 503
                
        except DatabaseQueryError as e:
            error_message = str(e).lower()
            
            # Handle specific constraint violations
            if "already checked in today" in error_message or "duplicate" in error_message:
                return {
                    'success': False,
                    'error': 'You have already checked in today.'
                }, 400
            elif "unique constraint" in error_message or "duplicate entry" in error_message:
                return {
                    'success': False,
                    'error': 'Duplicate check-in detected. Please refresh the page.'
                }, 400
            else:
                logger.error(f"Database query error during check-in: {e}")
                return {
                    'success': False,
                    'error': 'Unable to record check-in. Please try again.'
                }, 500
                
        except Exception as e:
            logger.error(f"Unexpected error during check-in for employee {employee_id}: {e}")
            return {
                'success': False,
                'error': 'An unexpected error occurred. Please try again.'
            }, 500
    
    # Should not reach here due to the loop structure, but fallback
    return {
        'success': False,
        'error': 'Check-in failed after multiple attempts. Please try again later.'
    }, 500


@app.route('/check-out', methods=['POST'])
@login_required
def check_out():
    """
    Record check-out time for authenticated employee with comprehensive error handling
    
    Validates user is authenticated and has checked in today,
    then updates existing attendance record with check_out_time.
    
    Returns:
        JSON response with success/error message and both check-in and check-out times
    """
    if not current_user or not current_user.id:
        logger.error("Check-out attempted with invalid user session")
        return {
            'success': False,
            'error': 'Invalid session. Please log in again.'
        }, 401
    
    # Basic request validation (CSRF removed)
    if request.method != 'POST':
        return {
            'success': False,
            'error': 'Invalid request method.'
        }, 405
    
    employee_id = current_user.id
    max_retries = 3
    
    for attempt in range(max_retries):
        try:
            # Check current attendance status
            status = get_attendance_status(employee_id)
            
            if status == AttendanceStatus.NOT_CHECKED_IN:
                return {
                    'success': False,
                    'error': 'You must check in first before checking out.'
                }, 400
            elif status == AttendanceStatus.COMPLETED:
                return {
                    'success': False,
                    'error': 'You have already completed attendance for today.'
                }, 400
            
            # Update attendance record with check-out time
            attendance_record = attendance_repo.update_checkout(employee_id)
            
            # Format times for response
            check_in_time = attendance_record['check_in_time']
            check_out_time = attendance_record['check_out_time']
            
            if hasattr(check_in_time, 'strftime'):
                formatted_check_in = check_in_time.strftime('%I:%M %p')
            else:
                formatted_check_in = str(check_in_time)
                
            if hasattr(check_out_time, 'strftime'):
                formatted_check_out = check_out_time.strftime('%I:%M %p')
            else:
                formatted_check_out = str(check_out_time)
            
            logger.info(f"Employee {employee_id} ({current_user.email}) checked out at {formatted_check_out}")
            
            return {
                'success': True,
                'message': f'Check-out successful! Check-in: {formatted_check_in}, Check-out: {formatted_check_out}',
                'check_in_time': formatted_check_in,
                'check_out_time': formatted_check_out,
                'attendance_id': attendance_record['id']
            }, 200
            
        except DatabaseConnectionError as e:
            logger.warning(f"Database connection error during check-out (attempt {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                time.sleep(1 * (attempt + 1))  # Exponential backoff
                continue
            else:
                return {
                    'success': False,
                    'error': 'Database connection issue. Please try again in a moment.'
                }, 503
                
        except DatabaseQueryError as e:
            error_message = str(e).lower()
            
            # Handle specific validation errors
            if "has not checked in today" in error_message:
                return {
                    'success': False,
                    'error': 'You must check in first before checking out.'
                }, 400
            elif "has already checked out today" in error_message or "already checked out" in error_message:
                return {
                    'success': False,
                    'error': 'You have already checked out for today.'
                }, 400
            else:
                logger.error(f"Database query error during check-out: {e}")
                return {
                    'success': False,
                    'error': 'Unable to record check-out. Please try again.'
                }, 500
                
        except Exception as e:
            logger.error(f"Unexpected error during check-out for employee {employee_id}: {e}")
            return {
                'success': False,
                'error': 'An unexpected error occurred. Please try again.'
            }, 500
    
    # Should not reach here due to the loop structure, but fallback
    return {
        'success': False,
        'error': 'Check-out failed after multiple attempts. Please try again later.'
    }, 500


@app.route('/logout')
@login_required
def logout():
    """
    Clear session and logout user
    
    Returns:
        Redirect to login page
    """
    logout_user()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('login'))

@app.route('/proxy-image')
@login_required
def proxy_image():
    """
    Proxy Google profile images to avoid CORS and loading issues
    
    Returns:
        Proxied image or default avatar
    """
    image_url = request.args.get('url')
    
    if not image_url:
        # Return default avatar
        return redirect(url_for('static', filename='default-avatar.png'))
    
    try:
        # Validate URL is from Google
        if not image_url.startswith('https://lh3.googleusercontent.com/') and \
           not image_url.startswith('https://lh4.googleusercontent.com/') and \
           not image_url.startswith('https://lh5.googleusercontent.com/') and \
           not image_url.startswith('https://lh6.googleusercontent.com/'):
            logger.warning(f"Invalid image URL attempted: {image_url}")
            return redirect(url_for('static', filename='default-avatar.png'))
        
        # Fetch image from Google
        response = requests.get(image_url, timeout=10, stream=True)
        
        if response.status_code == 200:
            # Return the image with proper headers
            return response.content, 200, {
                'Content-Type': response.headers.get('Content-Type', 'image/jpeg'),
                'Cache-Control': 'public, max-age=3600',  # Cache for 1 hour
                'Access-Control-Allow-Origin': '*'
            }
        else:
            logger.warning(f"Failed to fetch image: {image_url}, status: {response.status_code}")
            return redirect(url_for('static', filename='default-avatar.png'))
            
    except requests.exceptions.Timeout:
        logger.warning(f"Timeout fetching image: {image_url}")
        return redirect(url_for('static', filename='default-avatar.png'))
    except requests.exceptions.RequestException as e:
        logger.warning(f"Error fetching image {image_url}: {e}")
        return redirect(url_for('static', filename='default-avatar.png'))
    except Exception as e:
        logger.error(f"Unexpected error proxying image {image_url}: {e}")
        return redirect(url_for('static', filename='default-avatar.png'))

@app.route('/')
@login_required
def index():
    """
    Main dashboard with comprehensive error handling and session validation
    
    Displays appropriate check-in/check-out buttons based on current status
    and shows attendance history for the last 14 days.
    
    Returns:
        Rendered dashboard template with attendance status and history
    """
    # Validate current user session
    if not current_user or not current_user.id:
        logger.warning("Dashboard accessed with invalid user session")
        flash('Your session has expired. Please log in again.', 'warning')
        return redirect(url_for('login'))
    
    employee_id = current_user.id
    max_retries = 2
    
    for attempt in range(max_retries):
        try:
            # Get current attendance status
            status = get_attendance_status(employee_id)
            
            # Get today's attendance record for display
            today_attendance = None
            try:
                today_attendance = attendance_repo.get_today_attendance(employee_id)
            except DatabaseConnectionError as e:
                logger.warning(f"Connection error getting today's attendance (attempt {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(1)
                    continue
                else:
                    flash('Unable to load current attendance status. Some features may be limited.', 'warning')
            except Exception as e:
                logger.error(f"Error getting today's attendance: {e}")
                flash('Unable to load current attendance status.', 'warning')
            
            # Get attendance history for last 14 days
            attendance_history = []
            try:
                attendance_history = attendance_repo.get_recent_history(employee_id, days=14)
            except DatabaseConnectionError as e:
                logger.warning(f"Connection error getting attendance history: {e}")
                flash('Unable to load attendance history. Please refresh the page.', 'warning')
            except Exception as e:
                logger.error(f"Error getting attendance history: {e}")
                flash('Unable to load attendance history.', 'warning')
            
            # Format today's attendance times if available
            current_check_in_time = None
            if today_attendance and today_attendance['check_in_time']:
                check_in_time = today_attendance['check_in_time']
                if hasattr(check_in_time, 'strftime'):
                    current_check_in_time = check_in_time.strftime('%I:%M %p')
                else:
                    current_check_in_time = str(check_in_time)
            
            return render_template('index.html',
                                 status=status,
                                 current_check_in_time=current_check_in_time,
                                 attendance_history=attendance_history or [],
                                 employee=current_user)
            
        except DatabaseConnectionError as e:
            logger.warning(f"Database connection error loading dashboard (attempt {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                time.sleep(1 * (attempt + 1))
                continue
            else:
                flash('Database connection issue. Please try again in a moment.', 'error')
                return render_template('index.html',
                                     status=AttendanceStatus.NOT_CHECKED_IN,
                                     current_check_in_time=None,
                                     attendance_history=[],
                                     employee=current_user)
                
        except Exception as e:
            logger.error(f"Unexpected dashboard error for employee {employee_id}: {e}")
            flash('Error loading dashboard. Please refresh the page.', 'error')
            return render_template('index.html',
                                 status=AttendanceStatus.NOT_CHECKED_IN,
                                 current_check_in_time=None,
                                 attendance_history=[],
                                 employee=current_user)
    
    # Fallback if all retries failed
    flash('Unable to load dashboard after multiple attempts. Please try again later.', 'error')
    return render_template('index.html',
                         status=AttendanceStatus.NOT_CHECKED_IN,
                         current_check_in_time=None,
                         attendance_history=[],
                         employee=current_user)

def validate_environment_variables():
    """
    Comprehensive validation of all required environment variables at startup
    
    Returns:
        tuple: (is_valid: bool, error_messages: list)
    """
    required_vars = {
        'GOOGLE_CLIENT_ID': 'Google OAuth Client ID',
        'GOOGLE_CLIENT_SECRET': 'Google OAuth Client Secret', 
        'HOSTED_DOMAIN': 'Company domain for email validation',
        'DB_HOST': 'Database host',
        'DB_USER': 'Database username',
        'DB_PASSWORD': 'Database password',
        'DB_NAME': 'Database name'
    }
    
    optional_vars = {
        'FLASK_SECRET_KEY': 'Flask secret key (will use default if not set)',
        'DB_PORT': 'Database port (will use 3306 if not set)'
    }
    
    missing_vars = []
    warnings = []
    
    # Check required variables
    for var, description in required_vars.items():
        value = os.getenv(var)
        if not value or (isinstance(value, str) and value.strip() == ''):
            missing_vars.append(f"{var} ({description})")
    
    # Check optional variables and warn if missing
    for var, description in optional_vars.items():
        value = os.getenv(var)
        if not value or (isinstance(value, str) and value.strip() == ''):
            warnings.append(f"{var} not set - {description}")
    
    # Log warnings for optional variables
    for warning in warnings:
        logger.warning(warning)
    
    if missing_vars:
        error_msg = f"Missing required environment variables: {', '.join(missing_vars)}"
        logger.error(error_msg)
        return False, missing_vars
    
    # Validate specific formats
    validation_errors = []
    
    # Validate email domain format
    hosted_domain = os.getenv('HOSTED_DOMAIN')
    if hosted_domain and not _is_valid_domain_format(hosted_domain):
        validation_errors.append(f"HOSTED_DOMAIN '{hosted_domain}' is not a valid domain format")
    
    # Validate database port if provided
    db_port = os.getenv('DB_PORT')
    if db_port:
        try:
            port_num = int(db_port)
            if port_num < 1 or port_num > 65535:
                validation_errors.append(f"DB_PORT '{db_port}' must be between 1 and 65535")
        except ValueError:
            validation_errors.append(f"DB_PORT '{db_port}' must be a valid integer")
    
    if validation_errors:
        for error in validation_errors:
            logger.error(error)
        return False, validation_errors
    
    logger.info("Environment variable validation passed")
    return True, []


def _is_valid_domain_format(domain):
    """
    Basic domain format validation
    
    Args:
        domain: Domain string to validate
        
    Returns:
        bool: True if domain format appears valid
    """
    if not domain or not isinstance(domain, str):
        return False
    
    domain = domain.strip().lower()
    
    # Basic checks
    if len(domain) == 0 or len(domain) > 253:
        return False
    
    if domain.startswith('.') or domain.endswith('.'):
        return False
    
    if '..' in domain:
        return False
    
    # Check for at least one dot
    if '.' not in domain:
        return False
    
    # Basic character validation
    allowed_chars = set('abcdefghijklmnopqrstuvwxyz0123456789.-')
    if not all(c in allowed_chars for c in domain):
        return False
    
    return True


def validate_oauth_config():
    """
    Validate Google OAuth configuration and connectivity
    
    Returns:
        tuple: (is_valid: bool, error_message: str)
    """
    # Check if OAuth variables are set (already validated in validate_environment_variables)
    required_vars = ['GOOGLE_CLIENT_ID', 'GOOGLE_CLIENT_SECRET', 'HOSTED_DOMAIN']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        error_msg = f"Missing OAuth configuration: {', '.join(missing_vars)}"
        logger.error(error_msg)
        return False, error_msg
    
    # Test connectivity to Google's OAuth endpoints
    try:
        logger.info("Testing connectivity to Google OAuth endpoints...")
        response = requests.get(
            'https://accounts.google.com/.well-known/openid-configuration', 
            timeout=10
        )
        if response.status_code == 200:
            logger.info("Google OAuth discovery document accessible")
            return True, ""
        else:
            warning_msg = f"Google OAuth discovery document returned status {response.status_code}"
            logger.warning(warning_msg)
            return True, ""  # Still allow app to start with manual config
    except requests.exceptions.Timeout:
        warning_msg = "Timeout connecting to Google OAuth - will use manual configuration"
        logger.warning(warning_msg)
        return True, ""  # Allow app to start with manual config
    except requests.exceptions.ConnectionError:
        warning_msg = "Could not connect to Google OAuth - will use manual configuration"
        logger.warning(warning_msg)
        return True, ""  # Allow app to start with manual config
    except Exception as e:
        warning_msg = f"Unexpected error testing Google OAuth connectivity: {e}"
        logger.warning(warning_msg)
        return True, ""  # Allow app to start with manual config

def setup_database():
    """Initialize and verify database schema on application startup"""
    try:
        logger.info("Setting up database schema...")
        initialize_database()
        
        if verify_database_schema():
            logger.info("Database schema setup completed successfully")
        else:
            logger.error("Database schema verification failed")
            raise Exception("Database schema verification failed")
            
    except Exception as e:
        logger.error(f"Database setup failed: {e}")
        raise

# Error handlers for better user experience
@app.errorhandler(404)
def not_found_error(error):
    """Handle 404 errors with user-friendly page"""
    logger.warning(f"404 error: {request.url}")
    return render_template('error.html', 
                         error_code=404,
                         error_message="Page not found",
                         error_description="The page you're looking for doesn't exist."), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors with user-friendly page"""
    logger.error(f"500 error: {error}")
    return render_template('error.html',
                         error_code=500,
                         error_message="Internal server error",
                         error_description="An unexpected error occurred. Please try again later."), 500


@app.errorhandler(503)
def service_unavailable_error(error):
    """Handle 503 errors (service unavailable)"""
    logger.error(f"503 error: {error}")
    return render_template('error.html',
                         error_code=503,
                         error_message="Service temporarily unavailable",
                         error_description="The service is temporarily unavailable. Please try again in a few minutes."), 503


# Session expiry handling
@app.before_request
def check_session_expiry():
    """
    Check for session expiry and handle automatic redirect to login
    """
    # Skip session checks for static files and auth routes
    if (request.endpoint and 
        (request.endpoint.startswith('static') or 
         request.endpoint in ['login', 'auth_google', 'auth_callback'])):
        return
    
    # Check if user is supposed to be logged in but session is invalid
    if current_user.is_authenticated:
        try:
            # Validate that the user still exists in database
            if not employee_repo.find_by_id(current_user.id):
                logger.warning(f"User {current_user.id} no longer exists in database, clearing session")
                logout_user()
                flash('Your account is no longer active. Please contact your administrator.', 'error')
                return redirect(url_for('login'))
        except DatabaseConnectionError:
            # Don't logout on connection errors, just log the issue
            logger.warning("Database connection error during session validation")
        except Exception as e:
            logger.error(f"Error validating user session: {e}")


# Admin decorator
def admin_required(f):
    """Decorator to require admin role for certain routes"""
    from functools import wraps
    
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('login'))
        
        if not hasattr(current_user, 'is_admin') or not current_user.is_admin:
            flash('คุณไม่มีสิทธิ์เข้าถึงหน้านี้', 'error')
            return redirect(url_for('index'))
        
        return f(*args, **kwargs)
    return decorated_function


@app.route('/admin')
@login_required
@admin_required
def admin_dashboard():
    """Admin dashboard with statistics and employee management"""
    try:
        # Get attendance statistics
        stats = attendance_repo.get_attendance_stats()
        
        # Get recent attendance records
        recent_records = attendance_repo.get_all_attendance_records(limit=50)
        
        # Get all employees
        all_employees = employee_repo.get_all_employees()
        
        # Get location statistics
        all_locations = location_repo.get_all_locations()
        active_locations = location_repo.get_active_locations()
        
        return render_template('admin/dashboard.html',
                             stats=stats,
                             recent_records=recent_records,
                             employees=all_employees,
                             all_locations=all_locations,
                             active_locations=active_locations)
        
    except Exception as e:
        logger.error(f"Error loading admin dashboard: {e}")
        flash('เกิดข้อผิดพลาดในการโหลดข้อมูล', 'error')
        return redirect(url_for('index'))


@app.route('/admin/employees')
@login_required
@admin_required
def admin_employees():
    """Admin employee management page"""
    try:
        employees = employee_repo.get_all_employees()
        return render_template('admin/employees.html', employees=employees)
        
    except Exception as e:
        logger.error(f"Error loading employees: {e}")
        flash('เกิดข้อผิดพลาดในการโหลดข้อมูลพนักงาน', 'error')
        return redirect(url_for('admin_dashboard'))


@app.route('/admin/employee/<int:employee_id>')
@login_required
@admin_required
def admin_employee_detail(employee_id):
    """Admin employee detail page with attendance summary"""
    try:
        employee = employee_repo.find_by_id(employee_id)
        if not employee:
            flash('ไม่พบข้อมูลพนักงาน', 'error')
            return redirect(url_for('admin_employees'))
        
        # Get attendance summary
        summary = attendance_repo.get_employee_attendance_summary(employee_id, days=30)
        
        # Get recent attendance records
        recent_records = attendance_repo.get_recent_history(employee_id, days=30)
        
        return render_template('admin/employee_detail.html',
                             employee=employee,
                             summary=summary,
                             recent_records=recent_records)
        
    except Exception as e:
        logger.error(f"Error loading employee detail: {e}")
        flash('เกิดข้อผิดพลาดในการโหลดข้อมูลพนักงาน', 'error')
        return redirect(url_for('admin_employees'))


@app.route('/admin/employee/<int:employee_id>/role', methods=['POST'])
@login_required
@admin_required
def admin_update_employee_role(employee_id):
    """Update employee role (admin function)"""
    try:
        data = request.get_json()
        if not data or 'role' not in data:
            return jsonify({'success': False, 'error': 'ข้อมูลไม่ถูกต้อง'})
        
        new_role = data['role']
        if new_role not in ['employee', 'admin']:
            return jsonify({'success': False, 'error': 'บทบาทไม่ถูกต้อง'})
        
        # Don't allow changing own role
        if employee_id == current_user.id:
            return jsonify({'success': False, 'error': 'ไม่สามารถเปลี่ยนบทบาทของตนเองได้'})
        
        employee_repo.update_employee_role(employee_id, new_role)
        
        return jsonify({
            'success': True,
            'message': f'อัปเดตบทบาทเป็น {new_role} เรียบร้อยแล้ว'
        })
        
    except Exception as e:
        logger.error(f"Error updating employee role: {e}")
        return jsonify({'success': False, 'error': 'เกิดข้อผิดพลาดในการอัปเดตบทบาท'})


@app.route('/admin/locations')
@login_required
@admin_required
def admin_locations():
    """Admin location management page"""
    try:
        locations = location_repo.get_all_locations()
        return render_template('admin/locations.html', locations=locations)
    except Exception as e:
        logger.error(f"Error loading locations page: {e}")
        flash('เกิดข้อผิดพลาดในการโหลดข้อมูลตำแหน่ง', 'error')
        return redirect(url_for('admin_dashboard'))


@app.route('/admin/locations', methods=['POST'])
@login_required
@admin_required
def admin_create_location():
    """Create new location setting"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'error': 'ไม่พบข้อมูลที่ส่งมา'})
        
        # Validate required fields
        required_fields = ['name', 'latitude', 'longitude', 'radius_meters']
        for field in required_fields:
            if field not in data or data[field] is None or data[field] == '':
                return jsonify({'success': False, 'error': f'กรุณากรอก{field}'})
        
        # Convert and validate numeric fields
        try:
            latitude = float(data['latitude'])
            longitude = float(data['longitude'])
            radius_meters = int(data['radius_meters'])
        except (ValueError, TypeError):
            return jsonify({'success': False, 'error': 'ข้อมูลพิกัดหรือรัศมีไม่ถูกต้อง'})
        
        # Create location
        location = location_repo.create_location(
            name=data['name'],
            description=data.get('description'),
            latitude=latitude,
            longitude=longitude,
            radius_meters=radius_meters
        )
        
        logger.info(f"Admin {current_user.email} created location: {location.name}")
        return jsonify({
            'success': True, 
            'message': 'เพิ่มตำแหน่งใหม่สำเร็จ',
            'location': location.to_dict()
        })
        
    except ValueError as e:
        return jsonify({'success': False, 'error': str(e)})
    except Exception as e:
        logger.error(f"Error creating location: {e}")
        return jsonify({'success': False, 'error': 'เกิดข้อผิดพลาดในการเพิ่มตำแหน่ง'})


@app.route('/admin/locations/<int:location_id>')
@login_required
@admin_required
def admin_get_location(location_id):
    """Get location details"""
    try:
        location = location_repo.get_location_by_id(location_id)
        
        if not location:
            return jsonify({'success': False, 'error': 'ไม่พบตำแหน่งที่ระบุ'})
        
        return jsonify({
            'success': True,
            'location': location.to_dict()
        })
        
    except Exception as e:
        logger.error(f"Error getting location {location_id}: {e}")
        return jsonify({'success': False, 'error': 'เกิดข้อผิดพลาดในการโหลดข้อมูล'})


@app.route('/admin/locations/<int:location_id>', methods=['PUT'])
@login_required
@admin_required
def admin_update_location(location_id):
    """Update location setting"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'error': 'ไม่พบข้อมูลที่ส่งมา'})
        
        # Convert numeric fields if provided
        update_data = {}
        
        if 'name' in data:
            update_data['name'] = data['name']
        
        if 'description' in data:
            update_data['description'] = data['description']
        
        if 'latitude' in data:
            try:
                update_data['latitude'] = float(data['latitude'])
            except (ValueError, TypeError):
                return jsonify({'success': False, 'error': 'ข้อมูลละติจูดไม่ถูกต้อง'})
        
        if 'longitude' in data:
            try:
                update_data['longitude'] = float(data['longitude'])
            except (ValueError, TypeError):
                return jsonify({'success': False, 'error': 'ข้อมูลลองจิจูดไม่ถูกต้อง'})
        
        if 'radius_meters' in data:
            try:
                update_data['radius_meters'] = int(data['radius_meters'])
            except (ValueError, TypeError):
                return jsonify({'success': False, 'error': 'ข้อมูลรัศมีไม่ถูกต้อง'})
        
        # Update location
        location = location_repo.update_location(location_id, **update_data)
        
        if not location:
            return jsonify({'success': False, 'error': 'ไม่พบตำแหน่งที่ระบุ'})
        
        logger.info(f"Admin {current_user.email} updated location: {location.name}")
        return jsonify({
            'success': True,
            'message': 'อัปเดตตำแหน่งสำเร็จ',
            'location': location.to_dict()
        })
        
    except ValueError as e:
        return jsonify({'success': False, 'error': str(e)})
    except Exception as e:
        logger.error(f"Error updating location {location_id}: {e}")
        return jsonify({'success': False, 'error': 'เกิดข้อผิดพลาดในการอัปเดตตำแหน่ง'})


@app.route('/admin/locations/<int:location_id>/toggle', methods=['POST'])
@login_required
@admin_required
def admin_toggle_location(location_id):
    """Toggle location active status"""
    try:
        location = location_repo.get_location_by_id(location_id)
        
        if not location:
            return jsonify({'success': False, 'error': 'ไม่พบตำแหน่งที่ระบุ'})
        
        # Toggle status
        new_status = not location.is_active
        updated_location = location_repo.update_location(location_id, is_active=new_status)
        
        action = 'เปิดใช้งาน' if new_status else 'ปิดใช้งาน'
        logger.info(f"Admin {current_user.email} {action} location: {location.name}")
        
        return jsonify({
            'success': True,
            'message': f'{action}ตำแหน่งสำเร็จ',
            'location': updated_location.to_dict()
        })
        
    except Exception as e:
        logger.error(f"Error toggling location {location_id}: {e}")
        return jsonify({'success': False, 'error': 'เกิดข้อผิดพลาดในการเปลี่ยนสถานะ'})


@app.route('/admin/locations/<int:location_id>', methods=['DELETE'])
@login_required
@admin_required
def admin_delete_location(location_id):
    """Delete location setting"""
    try:
        location = location_repo.get_location_by_id(location_id)
        
        if not location:
            return jsonify({'success': False, 'error': 'ไม่พบตำแหน่งที่ระบุ'})
        
        # Soft delete (set is_active = False)
        location_repo.delete_location(location_id)
        
        logger.info(f"Admin {current_user.email} deleted location: {location.name}")
        return jsonify({
            'success': True,
            'message': 'ลบตำแหน่งสำเร็จ'
        })
        
    except Exception as e:
        logger.error(f"Error deleting location {location_id}: {e}")
        return jsonify({'success': False, 'error': 'เกิดข้อผิดพลาดในการลบตำแหน่ง'})


if __name__ == '__main__':
    try:
        # Comprehensive environment variable validation
        logger.info("Starting Employee Check-in System...")
        logger.info("Validating environment configuration...")
        
        is_valid, errors = validate_environment_variables()
        if not is_valid:
            logger.error("Environment validation failed:")
            for error in errors:
                logger.error(f"  - {error}")
            logger.error("Please check your .env file and ensure all required variables are set.")
            exit(1)
        
        # Validate OAuth configuration and connectivity
        logger.info("Validating OAuth configuration...")
        oauth_valid, oauth_error = validate_oauth_config()
        if not oauth_valid:
            logger.error(f"OAuth configuration validation failed: {oauth_error}")
            exit(1)
        
        # Setup database before starting the application
        logger.info("Setting up database...")
        setup_database()
        
        logger.info("All validations passed. Starting Flask application...")
        
        # Run the application in debug mode for development
        app.run(debug=True, host='0.0.0.0', port=5000)
        
    except KeyboardInterrupt:
        logger.info("Application shutdown requested by user")
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        exit(1)