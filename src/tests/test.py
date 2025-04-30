#!/usr/bin/env python
# -*- coding: utf-8 -*-
Config:


mode: developer #box-sdk

appName: 'ECDC Dashboard'
appVersion: '2.5.0'

sharepoint:
  user: 'sECDCKANBAN'
  password: '%9&OwH0Pa#tt'
  # user: "92900050"
  # password: 
  url: https://intranet.fanuc.local/sites/ecdc
  # devurl: http://intranettest.fanuc.local/sites/wftest/ECDC
  fetchInterval: 7200 # seconds equal to two hours

database:
  host: localhost
  port: 3306
  user: ecdc
  password: 13lux21
  database: ecdc
  version: '8.0.29'
  # charset: utf8mb4
  timezone: local
  seed: "no"

www:
  # HTTP interface to listen on
  host: 0.0.0.0
  # HTTP(S) port to listen on
  port: 8443
  portFxx: 80
  #urlBase: http://localhost:8443
  urlBase: http://luechecdc99.fanuc.local

  postsize: 1024
  # logger interface for expressjs morgan
  log: dev

user:
  password: FanucECDC22!

log:
  # silly|verbose|info|http|warn|error|silent
  level: info



    
"""
Модуль для работы с рабочими заказами из SharePoint
"""

import os
import json
import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import httpx
import redis
from urllib.parse import urlparse, urlunparse
from dotenv import load_dotenv

# Добавляем необходимые библиотеки для работы с NTLM
try:
    from office365.runtime.auth.authentication_context import AuthenticationContext
    from office365.sharepoint.client_context import ClientContext
    OFFICE365_AVAILABLE = True
except ImportError:
    # Альтернативный вариант с requests_ntlm
    try:
        from requests_ntlm import HttpNtlmAuth
        REQUESTS_NTLM_AVAILABLE = True
        OFFICE365_AVAILABLE = False
    except ImportError:
        REQUESTS_NTLM_AVAILABLE = False
        OFFICE365_AVAILABLE = False

# Конфигурация логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
log = logging.getLogger('work_orders')

# Загрузка переменных среды из .env файла (если существует)
load_dotenv()

# Статусы из ecdc_statuses.js
class UnitStatuses:
    """Класс с константами статусов из shared/ecdc_statuses.js"""
    PICKUP_REQUESTED = "pickup_request"
    COMPELETED = "completed"

# Глобальные переменные
pfdfs = None
is_ready = 1  # 1: not yet started, 2: fetching data, 3: ready

# Конфигурация SharePoint
class SharePointConfig:
    """Класс с настройками подключения к SharePoint"""
    def __init__(self):
        """Инициализация конфигурации из переменных среды"""
        self.url = os.environ.get("SHAREPOINT_URL", "https://sharepoint.example.com")
        self.user = os.environ.get("SHAREPOINT_USER", "user@example.com")
        self.password = os.environ.get("SHAREPOINT_PASSWORD", "password")
        self.domain = os.environ.get("SHAREPOINT_DOMAIN", "")
        # Добавляем proxy для корпоративной сети, если требуется
        self.proxy = os.environ.get("HTTP_PROXY", None)
        # Параметры TLS/SSL
        self.verify_ssl = os.environ.get("VERIFY_SSL", "True").lower() == "true"
        # Таймаут запросов (в секундах)
        self.timeout = float(os.environ.get("SHAREPOINT_TIMEOUT", "100.0"))

# Конфигурация Redis
class RedisConfig:
    """Класс с настройками подключения к Redis"""
    def __init__(self):
        """Инициализация конфигурации из переменных среды"""
        self.host = os.environ.get("REDIS_HOST", "localhost")
        self.port = int(os.environ.get("REDIS_PORT", "6379"))
        self.db = int(os.environ.get("REDIS_DB", "0"))
        self.password = os.environ.get("REDIS_PASSWORD", None)

# Создание экземпляров конфигураций
config_sharepoint = SharePointConfig()
config_redis = RedisConfig()

# Глобальный клиент Redis
redis_client = None

def get_redis_client():
    """
    Получение клиента Redis, создание нового подключения если не существует
    
    Returns:
        redis.Redis: Клиент Redis
    """
    global redis_client
    if redis_client is None:
        redis_client = redis.Redis(
            host=config_redis.host,
            port=config_redis.port,
            db=config_redis.db,
            password=config_redis.password,
            decode_responses=True
        )
    return redis_client

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
            self.auth_context = AuthenticationContext(self.url)
            
            # Формируем имя пользователя с доменом если указан
            user_with_domain = f"{self.domain}\\{self.username}" if self.domain else self.username
            
            # Получаем токен для пользователя
            self.auth_context.acquire_token_for_user(user_with_domain, self.password)
            
            # Создаем контекст клиента
            self.ctx = ClientContext(self.url, self.auth_context)
            
            # Настройка прокси если указан
            if self.proxy:
                self.ctx.request_options.proxies = {'http': self.proxy, 'https': self.proxy}
            
            # Настройка SSL верификации
            self.ctx.request_options.verify = self.verify_ssl
            
        else:
            # Используем httpx с NTLM аутентификацией если доступно
            log.info("Initializing SharePoint client using httpx")
            
            # Настройка аутентификации
            auth = None
            if REQUESTS_NTLM_AVAILABLE:
                # Используем NTLM аутентификацию
                log.info("Using requests_ntlm for NTLM authentication")
                user_with_domain = f"{self.domain}\\{self.username}" if self.domain else self.username
                auth = HttpNtlmAuth(user_with_domain, self.password)
            else:
                # Используем базовую или Digest авторизацию (может не работать с SharePoint)
                log.warning("NTLM libraries not available, using basic auth (may not work with SharePoint)")
                if self.domain:
                    auth = httpx.BasicAuth(f"{self.domain}\\{self.username}", self.password)
                else:
                    auth = httpx.BasicAuth(self.username, self.password)
            
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
                
                # Получаем web-объект
                web = self.ctx.web
                
                # Извлекаем название списка и параметры запроса
                # Пример: /web/lists/GetByTitle('ECDC Customisation Quality Report')/items?$filter=...
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
                    
                    # Преобразуем результат в формат, совместимый с оригиналом
                    for item in items:
                        item_dict = item.properties
                        # Преобразуем в формат, ожидаемый приложением
                        d_item = {"d": {"results": [item_dict]}}
                        data.append(item_dict)
                    
                    time_taken = (datetime.now() - start_time).total_seconds()
                    log.info(f"SharePoint request completed in {time_taken}s, retrieved {len(data)} items")
                    return data
                else:
                    log.error(f"Failed to parse SharePoint list name from URL: {url_params}")
                    return []
            else:
                # Используем httpx клиент
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
                    
                    time_taken = (datetime.now() - start_time).total_seconds()
                    log.info(f"SharePoint request completed in {time_taken}s, retrieved {len(data)} items")
                    return data
                else:
                    log.error(f"SharePoint API returned status code: {response.status_code}")
                    return []
                
        except Exception as e:
            log.error(f"Error fetching data from SharePoint: {str(e)}")
            return []
    
    async def close(self):
        """Закрывает httpx клиент если используется"""
        if not OFFICE365_AVAILABLE and hasattr(self, 'client'):
            await self.client.aclose()

# Создание экземпляра SharePoint клиента
sharepoint_client = SharePointClient(
    url=config_sharepoint.url,
    username=config_sharepoint.user,
    password=config_sharepoint.password,
    domain=config_sharepoint.domain,
    proxy=config_sharepoint.proxy,
    verify_ssl=config_sharepoint.verify_ssl,
    timeout=config_sharepoint.timeout
)

async def get_data_from_sharepoint(sso: str) -> List[Dict]:
    """
    Получает данные рабочих заказов из SharePoint для конкретного SSO
    
    Args:
        sso (str): Идентификатор пользователя SSO
        
    Returns:
        List[Dict]: Список рабочих заказов
    """
    global is_ready, pfdfs
    
    log.info('Started get_data_from_sharepoint')
    
    if is_ready == 1:
        log.info('get_data_from_sharepoint case 1')
        # Начинаем первое получение данных
        p = periodic_fetch_data_from_sharepoint()
        set_pfdfs(p)
        await p
        return await cache_work_orders_data(sso)
    
    elif is_ready == 2:
        log.info("Work Orders are being fetched...")
        log.info('get_data_from_sharepoint case 2')
        # Ждем завершения текущей задачи получения данных
        await pfdfs
        return await cache_work_orders_data(sso)
    
    elif is_ready == 3:
        log.info('get_data_from_sharepoint case 3')
        redis_client = get_redis_client()
        
        # Проверяем, когда последний раз обновлялись данные
        last_update_str = redis_client.get("lastUpdate")
        
        if last_update_str:
            last_update = datetime.fromisoformat(json.loads(last_update_str))
            time_diff = (datetime.now() - last_update).total_seconds()
            
            if time_diff > 600:  # 10 минут * 60 секунд
                log.info('lastUpdate was more than 10 minutes ago, update it again')
                
                # Обновляем данные снова
                p = periodic_fetch_data_from_sharepoint()
                set_pfdfs(p)
                await p
                return await cache_work_orders_data(sso)
        else:
            # Если нет данных о последнем обновлении, обновляем
            p = periodic_fetch_data_from_sharepoint()
            set_pfdfs(p)
            await p
            return await cache_work_orders_data(sso)
        
        # Если данные недавно обновлялись, возвращаем пустой список
        return []
    
    log.info("out of switch")
    return []

async def cache_work_orders_data(sso: str) -> Optional[List[Dict]]:
    """
    Получает кэшированные рабочие заказы для указанного SSO из Redis
    
    Args:
        sso (str): Идентификатор пользователя SSO
        
    Returns:
        Optional[List[Dict]]: Список рабочих заказов или None, если их нет в кэше
    """
    redis_client = get_redis_client()
    
    try:
        cache_results = redis_client.get(sso)
        if cache_results:
            results = json.loads(cache_results)
            return results
        else:
            return None
    except Exception as e:
        log.error(f"Error getting cached work orders: {str(e)}")
        return None

async def cache_work_orders_data_middleware(request, response):
    """
    Middleware для FastAPI, который проверяет наличие кэшированных данных
    и возвращает их, если они есть
    
    Args:
        request: Запрос FastAPI
        response: Ответ FastAPI
        
    Returns:
        dict: Ответ с данными или None для продолжения выполнения запроса
    """
    sso = request.query_params.get("sso")
    try:
        cache_results = await cache_work_orders_data(sso)
        if cache_results:
            return {"data": cache_results}
        else:
            # Продолжаем выполнение запроса
            return None
    except Exception as e:
        log.error(f"Error in cache_work_orders_data_middleware: {str(e)}")
        response.status_code = 404
        return {"error": str(e)}

async def periodic_fetch_data_from_sharepoint() -> None:
    """
    Периодически получает данные из SharePoint и сохраняет их в Redis
    
    Returns:
        None
    """
    global is_ready
    
    start_time_ms = datetime.now().timestamp() * 1000
    
    log.info(f"Started periodic_fetch_data_from_sharepoint at {datetime.now().isoformat()}")
    
    if is_ready == 2:
        return
    
    is_ready = 2
    
    results = {}  # Используем словарь вместо Map из JS
    
    # URL для запроса к SharePoint API
    url_params = "/_api/web/lists/GetByTitle(%27ECDC%20Customisation%20Quality%20Report%27)/items?$filter=JDEStatus eq 36 or JDEStatus eq 42 or JDEStatus eq 48 or JDEStatus eq 50 or JDEStatus eq 90&$select=Modified,Technician/Name,JDEStatus,LotNumber,WorkOrder&$expand=Technician&$top=1000"
    
    try:
        data = await sharepoint_client.get_data(url_params)
        
        time_taken = (datetime.now().timestamp() * 1000 - start_time_ms) / 1000
        log.info(f"WORK_ORDERS TS sec LEN {time_taken} {len(data)}")
        
        # Обработка полученных данных
        for d in data:
            # Проверка правильности фильтрации статусов
            if d['JDEStatus'] not in ["90", "50", "48", "42", "36"]:
                log.error("sharepoint filter api did not work")
                log.error(str(d))
            
            # Извлекаем SSO пользователя
            ssoa = None
            if "Technician" in d and "Name" in d["Technician"] and d["Technician"]["Name"] is not None:
                ssoa = d["Technician"]["Name"][13:]  # Извлекаем SSO из полного имени
            
            if ssoa:
                if d["JDEStatus"] == "90":
                    # Обновляем статус до pickup request
                    await update_status_to_pickup_request(d["LotNumber"])
                else:
                    # Создаем элемент с данными работы
                    item = {
                        "Modified": d["Modified"],
                        "Technician": ssoa,
                        "JDEStatus": d["JDEStatus"],
                        "LotNumber": d["LotNumber"] if d["LotNumber"] else "NA",
                        "WorkOrder": d["WorkOrder"],
                        "device_model": ""  # В оригинале здесь извлекался Series_Name из RobotXML
                    }
                    
                    # Добавляем элемент к соответствующему пользователю
                    if ssoa in results:
                        results[ssoa].append(item)
                    else:
                        results[ssoa] = [item]
        
        # Сохраняем время последнего обновления в Redis
        redis_client = get_redis_client()
        redis_client.set("lastUpdate", json.dumps(datetime.now().isoformat()))
        
        # Сохраняем данные в Redis для каждого пользователя
        for user_sso in results:
            log.info(f"Processing user: {user_sso}")
            
            # Сортируем работы по времени модификации (новые сначала)
            results[user_sso].sort(key=lambda x: datetime.fromisoformat(x["Modified"].replace('Z', '+00:00')).timestamp(), reverse=True)
            
            # Сохраняем в кэш
            redis_client.set(user_sso, json.dumps(results[user_sso]))
        
        is_ready = 3
        log.info(f"Ended periodic_fetch_data_from_sharepoint {len(results)}")
        
    except Exception as e:
        log.error(f"Error in periodic_fetch_data_from_sharepoint: {str(e)}")
        is_ready = 1  # Сбрасываем статус, чтобы можно было попробовать снова

async def update_status_to_pickup_request(enumber: str) -> bool:
    """
    Обновляет статус заказа до "запрос на получение"
    
    Args:
        enumber (str): Номер заказа
        
    Returns:
        bool: True, если обновление прошло успешно, False в противном случае
    """
    try:
        # В этом месте должно быть взаимодействие с базой данных
        # В оригинале используется knex.transaction
        # Здесь это нужно заменить на работу с базой данных через SQLAlchemy
        
        # Это заглушка, которая имитирует успешное выполнение
        log.info(f"Updating status to pickup request for enumber: {enumber}")
        return True
        
    except Exception as e:
        log.error(f"Error updating status to pickup request: {str(e)}")
        return False

def get_is_ready() -> int:
    """
    Возвращает текущий статус готовности данных
    
    Returns:
        int: Статус готовности (1, 2 или 3)
    """
    global is_ready
    return is_ready

def set_pfdfs(p):
    """
    Устанавливает глобальную переменную pfdfs
    
    Args:
        p: Асинхронная задача
        
    Returns:
        Переданная задача p
    """
    global pfdfs
    pfdfs = p
    return p

async def test_sharepoint_availability() -> None:
    """
    Проверяет доступность SharePoint, делая тестовый запрос
    
    Returns:
        None
    """
    start_time = datetime.now()
    
    log.info('Testing SharePoint availability...')
    
    url_params = "/_api/web/lists/GetByTitle(%27ECDC%20Customisation%20Quality%20Report%27)/items?$filter=JDEStatus eq 36&$select=JDEStatus,LotNumber&$top=2"
    
    try:
        data = await sharepoint_client.get_data(url_params)
        time_taken = (datetime.now() - start_time).total_seconds()
        log.info(f"SharePoint availability test completed in {time_taken}s, retrieved {len(data)} items")
    except Exception as e:
        log.error(f"SharePoint availability test failed: {str(e)}")