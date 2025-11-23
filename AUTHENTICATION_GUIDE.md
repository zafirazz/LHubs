# Authentication System Guide

## Overview

The AML Streamlit applications now include authentication to secure access to sensitive AML analysis features.

## Default Users

The system comes with three pre-configured users:

| Username | Password | Role |
|----------|----------|------|
| `demo` | `demo` | Demo user (quickest access) |
| `analyst` | `analyst123` | AML Analyst |
| `admin` | `admin123` | Administrator |

## How It Works

### Login Screen
1. Open the Streamlit app
2. You'll see a login form
3. Enter username and password
4. Click "Login"

### Logout
- Click the "🚪 Logout" button in the top-right corner

### Session Management
- Authentication persists during your browser session
- Closing the browser/tab will require re-login

## User Management

### User Storage
Users are stored in `/workspace/LHubs_Zafira/users.json` with hashed passwords (SHA-256).

### Managing Users via Python

```python
from src.utils.auth import Authenticator

# Initialize authenticator
auth = Authenticator(users_file="users.json")

# Add new user
auth.add_user("newuser", "password123")

# Change password
auth.change_password("analyst", "analyst123", "new_password")

# Remove user
auth.remove_user("demo")
```

### Manual User Management

Edit `/workspace/LHubs_Zafira/users.json`:

```json
{
  "username": "hashed_password_sha256"
}
```

To generate a password hash:

```python
import hashlib
password = "your_password"
hashed = hashlib.sha256(password.encode()).hexdigest()
print(hashed)
```

## Security Features

✅ **Password Hashing**: Passwords stored as SHA-256 hashes  
✅ **Session Management**: Session-based authentication  
✅ **Auto-logout**: Manual logout available  
✅ **No Plaintext**: Passwords never stored in plaintext  

## Production Recommendations

For production deployment, consider:

1. **Stronger Hashing**: Use bcrypt or Argon2 instead of SHA-256
2. **Database Storage**: Move from JSON file to secure database
3. **HTTPS**: Enable SSL/TLS encryption
4. **2FA**: Add two-factor authentication
5. **Role-Based Access**: Implement different permission levels
6. **Audit Logging**: Track user actions
7. **Password Policies**: Enforce complexity requirements
8. **Session Timeouts**: Auto-logout after inactivity

## Customization

### Change Default Credentials

Edit `/workspace/LHubs_Zafira/src/utils/auth.py`:

```python
default_users = {
    "your_username": self._hash_password("your_password"),
}
```

### Add Role-Based Permissions

Modify `Authenticator` class to include roles:

```python
self.users = {
    "analyst": {
        "password": hashed_password,
        "role": "analyst",
        "permissions": ["view", "analyze"]
    }
}
```

## Troubleshooting

### Forgot Password
1. Delete `/workspace/LHubs_Zafira/users.json`
2. Restart app (default users will be recreated)

### Can't Login
- Check username is correct (case-sensitive)
- Try default credentials: `demo` / `demo`
- Check `/workspace/LHubs_Zafira/users.json` exists

### Users.json Missing
- App will auto-create with default users on first run
- Check file permissions if creation fails

## Testing Authentication

```bash
cd /workspace/LHubs_Zafira
streamlit run streamlit_aml_app.py
```

1. Try logging in with `demo` / `demo`
2. Upload a test file
3. Click logout
4. Verify you're redirected to login

## Integration with Backend

If using the backend API (`streamlit_app.py` with `src/main.py`):
- Authentication only secures the Streamlit frontend
- Backend API remains open (add JWT tokens for API security)

## Quick Start

**For Demos:**
- Use `demo` / `demo` (fastest)

**For Testing:**
- Use `analyst` / `analyst123`

**For Admin:**
- Use `admin` / `admin123`
- Change password immediately after first login

