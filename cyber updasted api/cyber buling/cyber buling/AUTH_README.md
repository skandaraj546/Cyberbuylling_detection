# CyberGuard Authentication System

## Overview
The CyberGuard application now includes a complete authentication system with user registration, login, and session management.

## Features

### 🔐 Authentication Pages
- **Login Page** (`/login`) - User authentication with username/email and password
- **Signup Page** (`/signup`) - User registration with validation and password strength indicator
- **Protected Main Page** (`/`) - Requires authentication to access

### 🛡️ Security Features
- **Session Management** - Flask sessions with secure cookies
- **Input Validation** - Client and server-side validation
- **Password Requirements** - Minimum 8 characters with strength indicator
- **Duplicate Prevention** - Username and email uniqueness checks
- **Authentication Middleware** - Automatic redirect to login for protected routes

### 🎨 User Interface
- **Modern Design** - Twitter-style split-screen layout
- **Responsive** - Works on desktop, tablet, and mobile
- **Interactive Elements** - Real-time validation, loading states, animations
- **User Profile** - Shows current user info and logout functionality

## API Endpoints

### Authentication Routes
- `POST /api/auth/signup` - User registration
- `POST /api/auth/login` - User authentication
- `POST /api/auth/logout` - User logout
- `GET /api/auth/me` - Get current user information

### Page Routes
- `GET /` - Main application (protected)
- `GET /login` - Login page
- `GET /signup` - Registration page
- `GET /logout` - Logout and redirect to login

## Usage

### Starting the Application
```bash
python app.py
```

### Accessing the Application
1. Navigate to `http://localhost:5000`
2. You'll be redirected to `/login` if not authenticated
3. Create an account using `/signup` or login with existing credentials
4. Access the main application after successful authentication

### User Registration
1. Go to `/signup`
2. Fill in username (3-20 characters, alphanumeric + underscore)
3. Enter valid email address
4. Create password (minimum 8 characters)
5. Confirm password
6. Agree to terms and conditions
7. Click "Create Account"

### User Login
1. Go to `/login`
2. Enter username/email and password
3. Click "Sign In"
4. You'll be redirected to the main application

## Technical Details

### Data Storage
- **In-Memory Storage** - User data stored in Flask app memory (resets on restart)
- **Session Storage** - User sessions managed by Flask sessions
- **Future Enhancement** - Can be easily migrated to database storage

### Security Considerations
- **Password Hashing** - Currently stores plain text (should be hashed in production)
- **Session Security** - Uses Flask's secure session management
- **Input Sanitization** - Basic validation implemented
- **CSRF Protection** - Can be added with Flask-WTF

### File Structure
```
templates/
├── index.html          # Main application (protected)
├── login.html          # Login page
└── signup.html         # Registration page

static/
└── style.css           # All styles including auth pages

app.py                  # Flask application with auth routes
```

## Future Enhancements

### Database Integration
- Replace in-memory storage with SQLite/PostgreSQL
- Add user roles and permissions
- Implement password reset functionality

### Security Improvements
- Add password hashing (bcrypt)
- Implement CSRF protection
- Add rate limiting for login attempts
- Email verification for registration

### User Experience
- Remember me functionality
- Social login integration
- Password reset via email
- User profile management

## Development Notes

### Adding New Protected Routes
```python
@app.route("/protected-page")
@login_required
def protected_page():
    return render_template("protected.html")
```

### Accessing Current User
```python
@app.route("/api/user-data")
@login_required
def get_user_data():
    username = session.get('username')
    # Get user data and return
```

### Customizing Validation
Edit the validation functions in `signup.html` and the corresponding API endpoints in `app.py`.

## Troubleshooting

### Common Issues
1. **Session not persisting** - Check Flask secret key configuration
2. **Redirect loops** - Ensure login route is not protected
3. **Validation errors** - Check client and server validation logic
4. **Styling issues** - Verify CSS file is properly linked

### Debug Mode
Set `FLASK_DEBUG=1` to enable debug mode for detailed error messages.
