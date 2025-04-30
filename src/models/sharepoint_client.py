"""
Модуль для работы с SharePoint API через NTLM аутентификацию
"""
import logging
import asyncio
from datetime import datetime
from typing import Dict, List, Any, Optional

# Импорт для работы с HTTP запросами
try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False

# Импорт для работы с NTLM аутентификацией
try:
    from requests_ntlm import HttpNtlmAuth
    NTLM_AVAILABLE = True
except ImportError:
    NTLM_AVAILABLE = False

# Импорт для работы с SharePoint через Office365
try:
    from office365.runtime.auth.authentication_context import AuthenticationContext
    from office365.sharepoint.client_context import ClientContext
    OFFICE365_AVAILABLE = True
except ImportError:
    OFFICE365_AVAILABLE = False

# Настройка логгирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
log = logging.getLogger('sharepoint_client')

class SharePointClient:
    """Класс для взаимодействия с SharePoint API через NTLM аутентификацию"""
    
    def __init__(self, url: str, username: str, password: str, domain: str = None, 
                 proxy: str = None, verify_ssl: bool = True, timeout: float = 100.0):
        """
        Инициализация клиента SharePoint
        
        Args:
            url (str): URL SharePoint сайта
            username (str): Имя пользователя
            password (str): Пароль
            domain (str, optional): Домен для NTLM аутентификации. По умолчанию None.
            proxy (str, optional): HTTP прокси если требуется. По умолчанию None.
            verify_ssl (bool, optional): Проверка SSL сертификатов. По умолчанию True.
            timeout (float, optional): Таймаут запросов в секундах. По умолчанию 100.0.
        """
        self.url = url
        self.username = username
        self.password = password
        self.domain = domain
        self.proxy = proxy
        self.verify_ssl = verify_ssl
        self.timeout = timeout
        
        self._setup_client()
    
    def _setup_client(self):
        """Настройка клиента для работы с SharePoint в зависимости от доступных библиотек"""
        
        if OFFICE365_AVAILABLE:
            # Используем office365-rest-python-client (предпочтительный вариант)
            log.info("Initializing SharePoint client using Office365-REST-Python-Client")
            
            # Для локальных серверов SharePoint требуется явно указать тип аутентификации
            # вместо облачной аутентификации
            if "fanuc.local" in self.url:
                try:
                    from office365.runtime.auth.user_credential import UserCredential
                    from office365.runtime.auth.providers.ntlm_provider import NtlmProvider
                    
                    # Формируем имя пользователя с доменом если указан
                    user_with_domain = f"{self.domain}\\{self.username}" if self.domain else self.username
                    
                    # Создаем контекст клиента с NTLM провайдером
                    # В разных версиях библиотеки конструктор NtlmProvider может отличаться
                    try:
                        # Для более новых версий библиотеки
                        auth_provider = NtlmProvider(user_with_domain, self.password)
                        self.ctx = ClientContext(self.url).with_auth_provider(auth_provider)
                    except TypeError:
                        # Для старых версий библиотеки, использовавших UserCredential
                        user_credentials = UserCredential(user_with_domain, self.password)
                        auth_provider = NtlmProvider(user_credentials)
                        self.ctx = ClientContext(self.url).with_credentials(user_credentials)
                except Exception as ex:
                    # Запасной вариант - попробуем стандартную аутентификацию
                    log.warning(f"Failed to use NTLM auth: {str(ex)}, falling back to standard auth")
                    self.auth_context = AuthenticationContext(self.url)
            else:
                # Стандартная аутентификация для облачного SharePoint
                self.auth_context = AuthenticationContext(self.url)
                
                # Формируем имя пользователя с доменом если указан
                user_with_domain = f"{self.domain}\\{self.username}" if self.domain else self.username
                
                # Получаем токен для пользователя
                self.auth_context.acquire_token_for_user(user_with_domain, self.password)
                
                # Создаем контекст клиента
                self.ctx = ClientContext(self.url, self.auth_context)
            
            # В некоторых версиях Office365 библиотеки нет атрибута request_options
            # Попробуем настроить SSL и прокси, если атрибут существует
            if hasattr(self.ctx, 'request_options'):
                # Настройка прокси если указан
                if self.proxy:
                    self.ctx.request_options.proxies = {'http': self.proxy, 'https': self.proxy}
                
                # Настройка SSL верификации
                self.ctx.request_options.verify = self.verify_ssl
            
        elif HTTPX_AVAILABLE and NTLM_AVAILABLE:
            # Используем httpx с NTLM аутентификацией
            log.info("Initializing SharePoint client using httpx with NTLM")
            
            # Настройка аутентификации
            user_with_domain = f"{self.domain}\\{self.username}" if self.domain else self.username
            auth = HttpNtlmAuth(user_with_domain, self.password)
            
            # Настройка прокси
            proxies = None
            if self.proxy:
                proxies = {"http://": self.proxy, "https://": self.proxy}
            
            # Создание httpx клиента
            self.client = httpx.AsyncClient(
                base_url=self.url,
                auth=auth,
                verify=self.verify_ssl,
                timeout=self.timeout,
                proxies=proxies,
                headers={
                    "Accept": "application/json;odata=verbose",
                    "Content-Type": "application/json;odata=verbose",
                },
                follow_redirects=True
            )
        else:
            log.error("No suitable HTTP client found. Please install 'httpx' and 'requests_ntlm' or 'office365-rest-python-client'")
            raise ImportError("Required libraries are not installed")
    
    async def get_data(self, url_params: str) -> List[Dict]:
        """
        Получает данные из SharePoint API
        
        Args:
            url_params (str): Параметры запроса API
            
        Returns:
            List[Dict]: Список результатов запроса
        """
        data = []
        start_time = datetime.now()
        
        try:
            log.info(f"Requesting SharePoint API: {url_params}")
            
            if OFFICE365_AVAILABLE:
                # Используем office365 клиент
                # Преобразуем url_params в формат для office365 API
                if url_params.startswith('/_api'):
                    url_params = url_params[5:]  # Удаляем префикс /_api
                
                try:
                    # Получаем web-объект
                    web = self.ctx.web
                    
                    # Извлекаем название списка и параметры запроса
                    import re
                    list_name_match = re.search(r"GetByTitle\(%27([^%]+)%27\)", url_params)
                    
                    if list_name_match:
                        list_name = list_name_match.group(1)
                        
                        # Извлекаем параметры запроса
                        query_params = {}
                        
                        # Извлекаем $filter
                        filter_match = re.search(r"\$filter=([^&]+)", url_params)
                        if filter_match:
                            query_params["filter"] = filter_match.group(1)
                        
                        # Извлекаем $select
                        select_match = re.search(r"\$select=([^&]+)", url_params)
                        if select_match:
                            query_params["select"] = select_match.group(1).split(',')
                        
                        # Извлекаем $expand
                        expand_match = re.search(r"\$expand=([^&]+)", url_params)
                        if expand_match:
                            query_params["expand"] = expand_match.group(1).split(',')
                        
                        # Извлекаем $top
                        top_match = re.search(r"\$top=(\d+)", url_params)
                        if top_match:
                            query_params["top"] = int(top_match.group(1))
                        
                        # Получаем список
                        sp_list = web.lists.get_by_title(list_name)
                        
                        # Создаем запрос к элементам списка
                        items = sp_list.items
                        
                        # Применяем параметры запроса
                        if "filter" in query_params:
                            items = items.filter(query_params["filter"])
                        
                        if "select" in query_params:
                            items = items.select(query_params["select"])
                        
                        if "expand" in query_params:
                            items = items.expand(query_params["expand"])
                        
                        if "top" in query_params:
                            items = items.top(query_params["top"])
                        
                        # Выполняем запрос
                        self.ctx.load(items)
                        self.ctx.execute_query()
                        
                        # Преобразуем результат в формат для приложения
                        for item in items:
                            item_dict = item.properties
                            data.append(item_dict)
                        
                    else:
                        log.error(f"Failed to parse SharePoint list name from URL: {url_params}")
                        return []
                        
                except Exception as ex:
                    log.error(f"Error using Office365 client: {str(ex)}")
                    return []
            else:
                # Используем httpx клиент
                try:
                    response = await self.client.get(url_params)
                    response.raise_for_status()
                    
                    if response.status_code == 200:
                        json_data = response.json()
                        data.extend(json_data.get('d', {}).get('results', []))
                        
                        # Обработка пагинации
                        while json_data.get('d', {}).get('__next'):
                            next_url = json_data['d']['__next']
                            log.info(f"Requesting next page: {next_url}")
                            response = await self.client.get(next_url)
                            response.raise_for_status()
                            
                            if response.status_code == 200:
                                json_data = response.json()
                                data.extend(json_data.get('d', {}).get('results', []))
                            else:
                                log.error(f"Failed to get next page: {response.status_code}")
                                break
                    else:
                        log.error(f"SharePoint API returned status code: {response.status_code}")
                        return []
                except Exception as ex:
                    log.error(f"Error using httpx client: {str(ex)}")
                    return []
            
            time_taken = (datetime.now() - start_time).total_seconds()
            log.info(f"SharePoint request completed in {time_taken}s, retrieved {len(data)} items")
            return data
                
        except Exception as e:
            log.error(f"Error fetching data from SharePoint: {str(e)}")
            return []
    
    async def get_users(self) -> List[Dict]:
        """
        Получает список пользователей из SharePoint
        
        Returns:
            List[Dict]: Список пользователей с их данными
        """
        try:
            if OFFICE365_AVAILABLE:
                # Прямой запрос через Office365 API
                users = []
                try:
                    # Получаем пользователей сайта
                    web = self.ctx.web
                    site_users = web.site_users
                    self.ctx.load(site_users)
                    self.ctx.execute_query()
                    
                    # Преобразуем в список словарей
                    for user in site_users:
                        # Пропускаем системные аккаунты
                        if user.properties.get("PrincipalType", 0) == 1:  # 1 = User
                            users.append({
                                "Id": user.properties.get("Id", ""),
                                "Title": user.properties.get("Title", ""),
                                "LoginName": user.properties.get("LoginName", ""),
                                "Email": user.properties.get("Email", "")
                            })
                    
                    return users
                except Exception as ex:
                    log.error(f"Error getting users with Office365 client: {str(ex)}")
                    return []
            else:
                # Используем httpx клиент
                users_url = "/_api/web/siteusers?$filter=PrincipalType eq 1"
                users_data = await self.get_data(users_url)
                return users_data
        except Exception as e:
            log.error(f"Error getting users from SharePoint: {str(e)}")
            return []

    async def close(self):
        """Закрывает httpx клиент если используется"""
        if not OFFICE365_AVAILABLE and hasattr(self, 'client'):
            await self.client.aclose()

    async def test_connection(self) -> bool:
        """
        Проверяет соединение с SharePoint
        
        Returns:
            bool: True если соединение успешно, иначе False
        """
        try:
            # Простой запрос для проверки соединения
            test_url = "/_api/web/title"
            data = await self.get_data(test_url)
            
            # Если данные получены успешно
            if data and len(data) > 0:
                log.info("SharePoint connection test successful")
                return True
            else:
                log.warning("SharePoint connection test failed: No data received")
                return False
        except Exception as e:
            log.error(f"SharePoint connection test failed: {str(e)}")
            return False