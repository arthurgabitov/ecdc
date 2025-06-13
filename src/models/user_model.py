import os
from typing import List

class UserModel:
    # Model for working with users: only detection by Windows login or manual input.
    def get_user_by_windows_login(self) -> str:
        try:
            return os.getlogin().lower()
        except Exception:
            return "Unknown SSO"

    def get_user_by_id(self, user_id: str) -> str:
        # For compatibility: just return user_id as SSO
        return user_id if user_id else "Unknown SSO"

    def get_default_users(self) -> list:
        # Return only the current SSO user as a list
        try:
            username = os.getlogin().lower()
        except Exception:
            username = "unknown"
        return [username]

    def get_sso(self) -> str:
        try:
            return os.getlogin().lower()
        except Exception:
            return "Unknown SSO"