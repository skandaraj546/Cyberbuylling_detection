# CyberGuard Setup Instructions

## ✅ Changes Implemented

### 1. **MongoDB Atlas Integration**
- Added PyMongo and bcrypt to `requirements.txt`
- Configured MongoDB connection with automatic fallback to in-memory storage
- User data now persists in MongoDB Atlas instead of being lost on restart
- Unique indexes created on `username` and `email` fields

### 2. **Expanded Image Upload Support**
All common image formats are now supported:
- **Standard formats**: png, jpg, jpeg, gif, webp, bmp, tiff, tif
- **Modern formats**: svg, ico, heic, heif, avif
- **Additional formats**: jfif, pjpeg, pjp

### 3. **Security Improvements**
- Passwords are now hashed using bcrypt (industry-standard)
- Email addresses stored in lowercase for consistency
- Duplicate username/email prevention with database-level unique constraints

### 4. **Fixed Redirects**
- Fixed signup page link from `login.html` to `/login` (proper Flask route)
- All authentication flows now redirect correctly

---

## 🔧 Setup Steps

### Step 1: Set Your MongoDB Password

You need to replace `<db_password>` in the `.env` file with your actual MongoDB Atlas password.

**Option A: Direct replacement in .env**
```bash
# Open .env and replace the line:
MONGODB_URI=mongodb+srv://cyberbulling:<db_password>@cluster0.uhkrcgq.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0

# With your actual password, for example:
MONGODB_URI=mongodb+srv://cyberbulling:YourActualPassword123@cluster0.uhkrcgq.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0
```

**Option B: Use separate password variable (more secure)**
```bash
# Add this line to .env:
MONGODB_PASSWORD=YourActualPassword123

# The app will automatically replace <db_password> with this value
```

### Step 2: Install Dependencies

```bash
# Navigate to the app directory
cd "c:\Users\HP\Documents\cyber updasted api (2)\cyber updasted api\cyber buling\cyber buling"

# Install/upgrade all dependencies
pip install -r requirements.txt
```

### Step 3: Run the Application

```bash
python app.py
```

The app will:
- ✅ Connect to MongoDB Atlas (if credentials are correct)
- ✅ Create unique indexes on username and email
- ⚠️ Fall back to in-memory storage if MongoDB connection fails (with warning)

---

## 📋 MongoDB Atlas Configuration

### Database Structure
- **Database name**: `cyberguard` (configurable via `MONGODB_DB_NAME` in .env)
- **Collections**:
  - `users` - Stores user accounts with hashed passwords
  - Indexes: unique on `username` and `email`

### User Document Schema
```json
{
  "_id": "uuid-string",
  "username": "john_doe",
  "email": "john@example.com",
  "password_hash": "bcrypt-hashed-password",
  "created_at": "2025-10-10T09:40:34.123Z",
  "is_active": true
}
```

---

## 🧪 Testing

### Test User Registration
1. Navigate to `http://localhost:5000/signup`
2. Create a new account
3. Check MongoDB Atlas dashboard to verify user was created

### Test Login
1. Navigate to `http://localhost:5000/login`
2. Login with your created credentials
3. Should redirect to main page (`/`)

### Test Image Upload
1. After logging in, try uploading various image formats
2. All formats (png, jpg, svg, heic, etc.) should now work

---

## 🔍 Troubleshooting

### MongoDB Connection Issues

**Error**: `MongoDB connection failed`
- **Solution**: Check your password in `.env` is correct
- **Solution**: Ensure your IP address is whitelisted in MongoDB Atlas (Network Access)
- **Solution**: Verify the connection string is correct

**Fallback Mode**
If MongoDB fails, the app will:
- Print a warning message
- Use in-memory storage (data lost on restart)
- Continue functioning normally

### Image Upload Issues

**Error**: `Unsupported file type`
- **Solution**: Verify file extension is in the allowed list
- **Solution**: Check file is not corrupted

### Redirect Issues

**Error**: Page not found after signup/login
- **Solution**: Clear browser cache
- **Solution**: Check Flask routes are loading correctly

---

## 🔐 Security Notes

1. **Never commit `.env` to version control** - It contains sensitive credentials
2. **Use strong passwords** for MongoDB Atlas
3. **Enable IP whitelisting** in MongoDB Atlas for production
4. **Consider using environment variables** instead of .env in production
5. **Rotate credentials regularly**

---

## 📝 Environment Variables Reference

```bash
# Required
SECRET_KEY=your-secret-key-here
MONGODB_URI=mongodb+srv://cyberbulling:<db_password>@cluster0.uhkrcgq.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0

# Optional
MONGODB_PASSWORD=your-mongodb-password  # Alternative to embedding in URI
MONGODB_DB_NAME=cyberguard              # Default: cyberguard

# AI Features (Optional)
GEMINI_API_KEY=your-gemini-key
GROQ_API_KEY=your-groq-key
TOXICITY_THRESHOLD=0.5

# Twitter Integration (Optional)
TWITTER_API_KEY=your-twitter-key
TWITTER_API_SECRET=your-twitter-secret
TWITTER_BEARER_TOKEN=your-bearer-token
```

---

## ✨ What's New

### Before
- ❌ Users stored in memory (lost on restart)
- ❌ Plain text passwords
- ❌ Limited image format support
- ❌ Broken signup redirect

### After
- ✅ Users persist in MongoDB Atlas
- ✅ Bcrypt password hashing
- ✅ Support for all image formats
- ✅ Fixed all redirects
- ✅ Automatic fallback if MongoDB unavailable
- ✅ Unique constraints on username/email

---

## 🚀 Next Steps

1. Set your MongoDB password in `.env`
2. Install dependencies: `pip install -r requirements.txt`
3. Run the app: `python app.py`
4. Test signup, login, and image uploads
5. Monitor MongoDB Atlas dashboard for user data

**Need help?** Check the console output for detailed error messages and connection status.
