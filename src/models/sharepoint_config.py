"""
Конфигурация для подключения к SharePoint
"""
import os
from typing import Dict, Any

class SharePointConfig:
    """Класс с настройками подключения к SharePoint"""
    
    def __init__(self):
        """Инициализация конфигурации из переменных окружения или значений по умолчанию"""
        # URL SharePoint сайта
        self.url = os.environ.get("SHAREPOINT_URL", "https://intranet.fanuc.local/sites/ecdc")
        
        # Учётные данные
        self.user = os.environ.get("SHAREPOINT_USER", "sECDCKANBAN")
        self.password = os.environ.get("SHAREPOINT_PASSWORD", "%9&OwH0Pa#tt")
        
        # Домен для NTLM авторизации (если требуется)
        self.domain = os.environ.get("SHAREPOINT_DOMAIN", "")
        
        # HTTP прокси (если требуется)
        self.proxy = os.environ.get("HTTP_PROXY", None)
        
        # Настройки TLS/SSL
        # Отключаем проверку SSL для корпоративного сервера
        self.verify_ssl = False
        
        # Таймаут запросов в секундах
        self.timeout = float(os.environ.get("SHAREPOINT_TIMEOUT", "100.0"))
        
        # Интервал обновления данных с SharePoint (в секундах)
        self.fetch_interval = int(os.environ.get("SHAREPOINT_FETCH_INTERVAL", "7200"))
    
    def to_dict(self) -> Dict[str, Any]:
        """Преобразование настроек в словарь (без пароля)"""
        return {
            "url": self.url,
            "user": self.user,
            "domain": self.domain,
            "proxy": self.proxy,
            "verify_ssl": self.verify_ssl,
            "timeout": self.timeout,
            "fetch_interval": self.fetch_interval
        }