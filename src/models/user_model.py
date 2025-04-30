"""
Модель для работы с пользователями из SharePoint
"""

import os
import json
import asyncio
import logging
from typing import Dict, List, Optional
from datetime import datetime
import requests
from requests_ntlm import HttpNtlmAuth

from models.sharepoint_config import SharePointConfig

# Настройка логирования
logging.basicConfig(level=logging.INFO)
log = logging.getLogger('user_model')

class UserModel:
    """Модель для работы с пользователями"""
    
    def __init__(self, config_path: str = None):
        """
        Инициализация модели пользователей
        
        Args:
            config_path (str, optional): Путь к файлу конфигурации SharePoint. По умолчанию None.
        """
        self.sp_config = SharePointConfig()
        self.users_cache = []
        self.last_fetch_time = None
        self.cache_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'users_cache.json')
        
        # Создаем директорию для кэша, если не существует
        os.makedirs(os.path.dirname(self.cache_file), exist_ok=True)
        
        # Загружаем кэш пользователей при инициализации
        self._load_users_cache()
    
    def _load_users_cache(self):
        """Загрузка кэшированных данных о пользователях"""
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)
                    self.users_cache = cache_data.get('users', [])
                    last_fetch_time_str = cache_data.get('last_fetch_time')
                    if last_fetch_time_str:
                        self.last_fetch_time = datetime.fromisoformat(last_fetch_time_str)
                    log.info(f"Загружено {len(self.users_cache)} пользователей из кэша")
        except Exception as e:
            log.error(f"Ошибка при загрузке кэша пользователей: {str(e)}")
    
    def _save_users_cache(self):
        """Сохранение данных о пользователях в кэш"""
        try:
            cache_data = {
                'users': self.users_cache,
                'last_fetch_time': self.last_fetch_time.isoformat() if self.last_fetch_time else None
            }
            
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=4)
            
            log.info(f"Сохранено {len(self.users_cache)} пользователей в кэш")
        except Exception as e:
            log.error(f"Ошибка при сохранении кэша пользователей: {str(e)}")
    
    async def fetch_users(self, force_refresh: bool = False) -> List[Dict]:
        """
        Получение списка пользователей из SharePoint
        
        Args:
            force_refresh (bool, optional): Принудительное обновление кэша. По умолчанию False.
            
        Returns:
            List[Dict]: Список пользователей
        """
        # Если у нас есть кэш и не нужно принудительное обновление
        if self.users_cache and not force_refresh:
            # Проверяем время последнего обновления
            if self.last_fetch_time:
                time_diff = (datetime.now() - self.last_fetch_time).total_seconds()
                # Если прошло менее 30 минут, возвращаем кэшированные данные
                if time_diff < 1800:  # 30 минут * 60 секунд
                    return self.users_cache
        
        try:
            # Используем синхронный requests с NTLM авторизацией
            # Это выполняется в отдельном потоке, чтобы не блокировать асинхронный цикл событий
            users_data = await asyncio.to_thread(self._fetch_users_sync)
            
            # Если не получили данные, возвращаем кэшированные, если они есть
            if not users_data and self.users_cache:
                log.warning("Не удалось получить данные о пользователях из SharePoint, используем кэш")
                return self.users_cache
            
            # Обрабатываем данные о пользователях (фильтрация, форматирование и т.д.)
            processed_users = []
            for user in users_data:
                # Проверяем, что это пользователь, а не системный аккаунт
                principal_type = user.get("PrincipalType", 0)
                if principal_type == 1:  # 1 = User
                    processed_users.append({
                        "id": user.get("Id", ""),
                        "name": user.get("Title", ""),
                        "login": user.get("LoginName", ""),
                        "email": user.get("Email", "")
                    })
            
            # Сортируем по имени
            processed_users.sort(key=lambda x: x["name"])
            
            # Обновляем кэш
            self.users_cache = processed_users
            self.last_fetch_time = datetime.now()
            
            # Сохраняем кэш
            self._save_users_cache()
            
            return processed_users
        
        except Exception as e:
            log.error(f"Ошибка при получении пользователей: {str(e)}")
            
            # Возвращаем кэшированные данные в случае ошибки
            if self.users_cache:
                return self.users_cache
            else:
                # Если кэша нет, возвращаем предустановленных пользователей
                return self.get_default_users()
    
    def _fetch_users_sync(self) -> List[Dict]:
        """
        Синхронное получение списка пользователей из SharePoint
        
        Returns:
            List[Dict]: Список пользователей
        """
        try:
            # Формируем URL для запроса пользователей
            users_url = f"{self.sp_config.url}/_api/web/siteusers"
            
            # Настраиваем авторизацию
            user_with_domain = f"{self.sp_config.domain}\\{self.sp_config.user}" if self.sp_config.domain else self.sp_config.user
            auth = HttpNtlmAuth(user_with_domain, self.sp_config.password)
            
            # Настраиваем заголовки
            headers = {
                "Accept": "application/json;odata=verbose",
                "Content-Type": "application/json;odata=verbose"
            }
            
            # Выполняем запрос
            log.info(f"Запрос списка пользователей из SharePoint: {users_url}")
            response = requests.get(
                users_url,
                auth=auth,
                headers=headers,
                verify=self.sp_config.verify_ssl,
                timeout=self.sp_config.timeout
            )
            
            # Обрабатываем ответ
            if response.status_code == 200:
                data = response.json()
                users = data.get("d", {}).get("results", [])
                log.info(f"Получено {len(users)} пользователей из SharePoint")
                return users
            else:
                log.error(f"Ошибка при получении пользователей: {response.status_code} {response.text}")
                return []
        
        except Exception as e:
            log.error(f"Ошибка при синхронном получении пользователей: {str(e)}")
            return []
    
    def get_user_by_id(self, user_id: str) -> Optional[Dict]:
        """
        Получение пользователя по ID
        
        Args:
            user_id (str): ID пользователя
            
        Returns:
            Optional[Dict]: Данные пользователя или None, если не найден
        """
        # Преобразуем ID в строку для гарантированного сравнения
        user_id_str = str(user_id)
        for user in self.users_cache:
            if str(user.get("id", "")) == user_id_str:
                return user
        
        # Логируем информацию для отладки
        log.info(f"Пользователь с ID {user_id} не найден в кэше. Доступные ID: {[str(u.get('id')) for u in self.users_cache]}")
        return None

    def get_default_users(self) -> List[Dict]:
        """
        Возвращает список предустановленных пользователей,
        если не удалось подключиться к SharePoint
        
        Returns:
            List[Dict]: Список предустановленных пользователей
        """
        return [
            {"id": "1", "name": "Test User 1", "login": "user1", "email": "user1@example.com"},
            {"id": "2", "name": "Test User 2", "login": "user2", "email": "user2@example.com"},
            {"id": "3", "name": "Admin", "login": "admin", "email": "admin@example.com"}
        ]