"""
Модель для работы с пользователями локально (без SharePoint)
"""

import os
from typing import List

class UserModel:
    """Модель для работы с пользователями: только определение по Windows-логину или ручной ввод."""
    def get_user_by_windows_login(self) -> str:
        try:
            return os.getlogin().lower()
        except Exception:
            return "Unknown SSO"

    def get_user_by_id(self, user_id: str) -> str:
        # Для совместимости: просто возвращаем user_id как SSO
        return user_id if user_id else "Unknown SSO"

    def get_default_users(self) -> list:
        # Только текущий пользователь SSO в виде списка
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