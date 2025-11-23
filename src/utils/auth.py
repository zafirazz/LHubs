"""
Authentication utilities for Streamlit app.
"""

import hashlib
import json
from pathlib import Path
from typing import Optional, Dict

class Authenticator:
    """Simple authentication for Streamlit app."""
    
    def __init__(self, users_file: str = "users.json"):
        """
        Initialize authenticator.
        
        Args:
            users_file: Path to users configuration file
        """
        self.users_file = Path(users_file)
        self.users = self._load_users()
    
    def _load_users(self) -> Dict[str, str]:
        """Load users from configuration file."""
        # Default users if file doesn't exist
        default_users = {
            "admin": self._hash_password("admin123"),
            "analyst": self._hash_password("analyst123"),
            "demo": self._hash_password("demo")
        }
        
        if self.users_file.exists():
            try:
                with open(self.users_file, 'r') as f:
                    return json.load(f)
            except Exception:
                return default_users
        
        # Save default users
        self._save_users(default_users)
        return default_users
    
    def _save_users(self, users: Dict[str, str]):
        """Save users to configuration file."""
        try:
            with open(self.users_file, 'w') as f:
                json.dump(users, f, indent=2)
        except Exception as e:
            print(f"Error saving users: {e}")
    
    def _hash_password(self, password: str) -> str:
        """Hash password using SHA-256."""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def authenticate(self, username: str, password: str) -> bool:
        """
        Authenticate user.
        
        Args:
            username: Username
            password: Password (plain text)
            
        Returns:
            True if authenticated, False otherwise
        """
        if username not in self.users:
            return False
        
        hashed_password = self._hash_password(password)
        return self.users[username] == hashed_password
    
    def add_user(self, username: str, password: str) -> bool:
        """
        Add new user.
        
        Args:
            username: Username
            password: Password (plain text)
            
        Returns:
            True if user added, False if user exists
        """
        if username in self.users:
            return False
        
        self.users[username] = self._hash_password(password)
        self._save_users(self.users)
        return True
    
    def change_password(self, username: str, old_password: str, new_password: str) -> bool:
        """
        Change user password.
        
        Args:
            username: Username
            old_password: Current password
            new_password: New password
            
        Returns:
            True if password changed, False otherwise
        """
        if not self.authenticate(username, old_password):
            return False
        
        self.users[username] = self._hash_password(new_password)
        self._save_users(self.users)
        return True
    
    def remove_user(self, username: str) -> bool:
        """
        Remove user.
        
        Args:
            username: Username to remove
            
        Returns:
            True if removed, False if user doesn't exist
        """
        if username not in self.users:
            return False
        
        del self.users[username]
        self._save_users(self.users)
        return True

