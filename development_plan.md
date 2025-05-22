# Подробный план разработки Dashboard-приложения с архитектурой клиент-сервер

## Обзор проекта

Dashboard-приложение для ECDC представляет собой модульную масштабируемую платформу для управления рабочими станциями и задачами. Система построена на архитектуре клиент-сервер, где серверная часть обеспечивает централизованное хранение данных и интеграцию с внешними системами, а клиентская часть предоставляет интерфейс для работы операторов и администраторов.

### Ключевые функции:
- Авторизация пользователей с разделением на роли
- Управление рабочими станциями и спотами
- Назначение и отслеживание заданий (WO)
- Интеграция с SharePoint 365, BI
- Различные инструменты для разных типов операторов
- Демонстрационный режим с инфографикой

## 1. Архитектура системы

### 1.1. Клиент-серверная архитектура

```
+------------------------+        +-------------------------+
|                        |        |                         |
|  Клиент (EXE файл)     |<------>|  Сервер (Docker)        |
|  - Flet UI             |  API   |  - FastAPI              |
|  - Клиент API          |        |  - База данных          |
|  - Локальный кэш       |        |  - Интеграции           |
|                        |        |                         |
+------------------------+        +-------------------------+
          ^                                  ^
          |                                  |
          v                                  v
+------------------------+        +-------------------------+
|                        |        |                         |
|  Клиент на станции 2   |        |  Внешние системы        |
|                        |        |  - SharePoint 365       |
+------------------------+        |  - BI сервер            |
                                  |  - Replicon             |
                                  |                         |
                                  +-------------------------+
```

### 1.2. Компоненты системы

#### Серверная часть:
- **API-сервер** (FastAPI)
- **База данных** (PostgreSQL)
- **Кэширование** (Redis)
- **Интеграционные сервисы**
- **Система авторизации и аутентификации**

#### Клиентская часть:
- **UI-интерфейс** (Flet)
- **API-клиент**
- **Локальное кэширование**
- **Менеджер конфигурации**

## 2. Этапы разработки

### Этап 1: Реорганизация проекта (2-3 недели)

#### Задачи:
1. **Реструктуризация кодовой базы**
   - Разделение на серверную и клиентскую части
   - Создание общего кода в shared
   - Настройка структуры проекта

2. **Настройка системы сборки**
   - Создание Docker-конфигурации для сервера
   - Настройка сборки клиента в EXE
   - Создание скриптов для разработки

#### Структура проекта после реорганизации:
```
dashboard-app/
├── src/
│   ├── client/           # Клиентская часть (Flet UI)
│   │   ├── controllers/  # Контроллеры для работы с API
│   │   ├── views/        # UI компоненты 
│   │   ├── models/       # Клиентские модели данных
│   │   └── main.py       # Точка входа для клиентского приложения
│   │
│   ├── server/           # Серверная часть
│   │   ├── api/          # REST API endpoints
│   │   ├── db/           # Работа с базой данных
│   │   ├── services/     # Сервисы для внешних интеграций
│   │   ├── models/       # Серверные модели данных
│   │   └── main.py       # Точка входа для сервера
│   │
│   ├── shared/           # Общий код для клиента и сервера
│   │   ├── config.py     # Общие настройки
│   │   ├── constants.py  # Общие константы
│   │   └── utils.py      # Общие утилиты
│   │
│   └── app.py            # Основная точка входа (запуск сервера и/или клиента)
│
├── docker/               # Docker-конфигурация
│   ├── Dockerfile        # Сборка образа сервера
│   ├── docker-compose.yml # Конфигурация для разработки
│   └── entrypoint.sh     # Скрипт входа для контейнера
│
├── data/                 # Данные приложения
├── tests/                # Тесты
└── requirements/         # Зависимости проекта
    ├── base.txt          # Общие зависимости
    ├── client.txt        # Зависимости клиента
    └── server.txt        # Зависимости сервера
```

### Этап 2: Разработка серверной части (4-6 недель)

#### Задачи:
1. **Создание базы данных**
   - Определение схемы базы данных
   - Настройка ORM (SQLAlchemy)
   - Создание миграций (Alembic)

2. **Разработка API**
   - Реализация аутентификации и авторизации
   - API для работы со станциями и спотами
   - API для работы с заданиями (WO)
   - API для управления пользователями

3. **Интеграция с внешними системами**
   - Улучшение интеграции с SharePoint
   - Разработка интеграции с BI-сервером
   - Опционально: интеграция с Replicon

4. **Настройка Docker**
   - Оптимизация Docker-образа
   - Настройка томов для данных
   - Конфигурация сети

#### Схема базы данных:
```
+----------------+       +----------------+       +----------------+
|    Users       |       |    Stations    |       |    Spots       |
+----------------+       +----------------+       +----------------+
| id             |       | id             |       | id             |
| username       |       | name           |       | station_id     |
| password_hash  |       | description    |       | position       |
| email          |       | location       |       | status         |
| role_id        |       | active         |       | wo_number      |
| active         |       | created_at     |       | elapsed_time   |
| created_at     |       | updated_at     |       | running        |
| updated_at     |       +----------------+       | created_at     |
+----------------+               |                | updated_at     |
        |                        |                +----------------+
        v                        v                        |
+----------------+       +----------------+               |
|    Roles       |       | StationLayout  |               |
+----------------+       +----------------+               |
| id             |       | id             |               |
| name           |       | station_id     |               |
| permissions    |       | layout_data    |               |
| created_at     |       | created_at     |               |
| updated_at     |       | updated_at     |               |
+----------------+       +----------------+               |
                                                          v
                                                +----------------+
                                                |   WorkOrders   |
                                                +----------------+
                                                | id             |
                                                | wo_number      |
                                                | spot_id        |
                                                | device_type    |
                                                | serial_number  |
                                                | model          |
                                                | status         |
                                                | user_id        |
                                                | created_at     |
                                                | updated_at     |
                                                +----------------+
```

### Этап 3: Адаптация клиентской части (3-4 недели)

#### Задачи:
1. **Рефакторинг клиентского кода**
   - Создание API-клиента для работы с сервером
   - Адаптация контроллеров для использования API
   - Сохранение текущего UI

2. **Улучшение UI**
   - Доработка интерфейса для новой функциональности
   - Улучшение навигации и пользовательского опыта
   - Адаптация для разных ролей пользователей

3. **Настройка кэширования**
   - Локальное сохранение данных
   - Синхронизация при восстановлении соединения
   - Индикаторы состояния сети

4. **Упаковка клиента**
   - Настройка сборки EXE-файла
   - Создание конфигурационного файла
   - Проверка совместимости с разными версиями Windows

### Этап 4: Разработка функциональности для разных ролей (4-5 недель)

#### Задачи:
1. **Система ролей и прав доступа**
   - Определение ролей (Admin, RO, FA, RM, Support)
   - Настройка прав доступа к функциям
   - Реализация проверки прав в API и клиенте

2. **Административный интерфейс**
   - Управление пользователями
   - Настройка конфигурации системы
   - Редактор расположения станций

3. **Интерфейсы для операторов**
   - Функциональность для RO-операторов
   - Функциональность для FA-операторов
   - Функциональность для RM-операторов
   - Ограниченный доступ для Support

4. **Работа с заданиями WO**
   - Создание и назначение заданий
   - Отслеживание статусов
   - История изменений

### Этап 5: Интеграции и дополнительные функции (3-4 недели)

#### Задачи:
1. **Расширенная интеграция с SharePoint**
   - Синхронизация пользователей
   - Получение данных о заданиях
   - Обновление статусов

2. **Интеграция с BI-сервером**
   - Получение аналитических данных
   - Отображение статистики
   - Построение отчетов

3. **Демонстрационный режим**
   - Веб-интерфейс для обзора станций
   - Визуализация статусов в реальном времени
   - Инфографика и диаграммы

4. **Опционально: интеграция с Replicon**
   - Учет времени работы
   - Статистика по эффективности
   - Отчеты по использованию времени

### Этап 6: Тестирование и оптимизация (2-3 недели)

#### Задачи:
1. **Комплексное тестирование**
   - Юнит-тесты для серверной части
   - Интеграционные тесты
   - Пользовательское тестирование

2. **Оптимизация производительности**
   - Улучшение скорости работы API
   - Оптимизация запросов к базе данных
   - Улучшение отзывчивости интерфейса

3. **Исправление ошибок и доработка**
   - Исправление выявленных багов
   - Доработка по результатам тестирования
   - Улучшения UX на основе обратной связи

### Этап 7: Документация и развертывание (2 недели)

#### Задачи:
1. **Документация**
   - Техническая документация
   - Руководство администратора
   - Руководство пользователя

2. **Подготовка к развертыванию**
   - Создание инструкций по установке
   - Настройка сред (разработка, тестирование, продакшн)
   - Процедуры резервного копирования и восстановления

3. **Обучение пользователей**
   - Создание обучающих материалов
   - Проведение обучающих сессий
   - Подготовка FAQ

## 3. Техническая реализация

### 3.1. Серверная часть

#### Технологический стек:
- **Язык**: Python 3.10+
- **Фреймворк API**: FastAPI
- **ORM**: SQLAlchemy
- **База данных**: PostgreSQL
- **Кэширование**: Redis
- **Аутентификация**: JWT
- **Контейнеризация**: Docker

#### Примеры ключевых компонентов:

**Docker-конфигурация:**
```dockerfile
# Dockerfile для сервера
FROM python:3.10-slim

WORKDIR /app

# Установка зависимостей
COPY requirements/server.txt .
RUN pip install --no-cache-dir -r server.txt

# Копирование кода
COPY src/server /app/server
COPY src/shared /app/shared

# Переменные окружения
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Порт API
EXPOSE 8000

# Точка входа
COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
```

**Основной API-модуль:**
```python
# src/server/api/stations.py
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from sqlalchemy.orm import Session

from server.db.session import get_db
from server.models.station import Station, Spot
from server.schemas.station import StationCreate, StationResponse, SpotResponse
from server.api.deps import get_current_user

router = APIRouter(prefix="/api/stations", tags=["stations"])

@router.get("/", response_model=List[StationResponse])
def get_stations(db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    """Получение списка всех станций"""
    stations = db.query(Station).filter(Station.active == True).all()
    return stations

@router.get("/{station_id}/spots/{spot_id}", response_model=SpotResponse)
def get_spot(
    station_id: int, 
    spot_id: str, 
    db: Session = Depends(get_db), 
    current_user = Depends(get_current_user)
):
    """Получение данных конкретного спота"""
    spot = db.query(Spot).filter(
        Spot.station_id == station_id,
        Spot.id == spot_id
    ).first()
    
    if not spot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Spot {spot_id} in station {station_id} not found"
        )
        
    return spot
```

### 3.2. Клиентская часть

#### Технологический стек:
- **Язык**: Python 3.10+
- **UI-фреймворк**: Flet
- **HTTP-клиент**: httpx
- **Упаковка**: PyInstaller / Flet Pack

#### Примеры ключевых компонентов:

**API-клиент:**
```python
# src/client/api/api_client.py
import httpx
import asyncio
import json
import os
from typing import Dict, Any, Optional

class ApiClient:
    def __init__(self, base_url=None):
        self.base_url = base_url or self._load_config().get('api_url', 'http://localhost:8000')
        self.token = None
        self.client = httpx.AsyncClient(timeout=30.0)
    
    def _load_config(self) -> Dict[str, Any]:
        config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'client_config.json')
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}
    
    async def login(self, username: str, password: str) -> Dict[str, Any]:
        """Аутентификация пользователя"""
        response = await self.client.post(
            f"{self.base_url}/auth/login",
            json={"username": username, "password": password}
        )
        data = response.json()
        if response.status_code == 200:
            self.token = data.get('access_token')
            return data
        raise Exception(f"Authentication failed: {data.get('detail', 'Unknown error')}")
    
    async def get_stations(self) -> list:
        """Получение списка станций"""
        headers = self._get_auth_headers()
        response = await self.client.get(f"{self.base_url}/api/stations", headers=headers)
        return response.json()
    
    async def get_spot_data(self, station_id: int, spot_id: str) -> Dict[str, Any]:
        """Получение данных спота"""
        headers = self._get_auth_headers()
        response = await self.client.get(
            f"{self.base_url}/api/stations/{station_id}/spots/{spot_id}",
            headers=headers
        )
        return response.json()
    
    def _get_auth_headers(self) -> Dict[str, str]:
        """Создание заголовков с токеном авторизации"""
        headers = {}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers
    
    async def close(self):
        """Закрытие HTTP-клиента"""
        await self.client.aclose()
```

**Контроллер для работы с API:**
```python
# src/client/controllers/station_controller.py
from client.api.api_client import ApiClient

class StationController:
    def __init__(self, config):
        self.config = config
        self.api_client = ApiClient()
        self._stations_cache = []
        self._spots_cache = {}
    
    async def load_stations(self):
        """Загрузка списка станций с сервера"""
        try:
            stations = await self.api_client.get_stations()
            self._stations_cache = [station["id"] for station in stations]
            return self._stations_cache
        except Exception as e:
            print(f"Error loading stations: {e}")
            return self._stations_cache
    
    def get_stations(self):
        """Получение списка станций из кэша"""
        return self._stations_cache
    
    async def get_spot_data(self, station_id, spot_id):
        """Получение данных спота"""
        cache_key = f"{station_id}_{spot_id}"
        
        try:
            # Попытка получить свежие данные с сервера
            spot_data = await self.api_client.get_spot_data(station_id, spot_id)
            self._spots_cache[cache_key] = spot_data
            return spot_data
        except Exception as e:
            print(f"Error fetching spot data: {e}")
            # Возврат данных из кэша, если не удалось получить с сервера
            return self._spots_cache.get(cache_key, {
                "status": "Unblocked",
                "wo_number": "",
                "elapsed_time": 0,
                "running": False
            })
```

## 4. Сборка и развертывание

### 4.1. Серверная часть (Docker)

#### Сборка Docker-образа:
```bash
docker build -t ecdc-dashboard-server -f docker/Dockerfile .
```

#### Запуск с использованием docker-compose:
```bash
docker-compose -f docker/docker-compose.yml up -d
```

#### Обновление серверной части:
```bash
git pull
docker-compose -f docker/docker-compose.yml down
docker-compose -f docker/docker-compose.yml build
docker-compose -f docker/docker-compose.yml up -d
```

### 4.2. Клиентская часть (EXE)

#### Сборка клиентского приложения:
```bash
# Использование Flet CLI
flet pack .\src\client\main.py --name "ECDC Dashboard Client" --icon .\src\icon.ico

# Или с помощью PyInstaller
pyinstaller --onefile --windowed --icon=.\src\icon.ico .\src\client\main.py --name "ECDC_Dashboard_Client"
```

#### Конфигурация клиента:
Файл `client_config.json` с настройками подключения к серверу:
```json
{
  "api_url": "http://server-address:8000",
  "connection_timeout": 30,
  "retry_attempts": 3,
  "retry_delay": 5,
  "cache_lifetime": 3600
}
```

## 5. Управление проектом

### 5.1. График и основные вехи

| Этап | Длительность | Основные вехи |
|------|--------------|---------------|
| 1. Реорганизация проекта | 2-3 недели | Готовая структура проекта, основные скрипты |
| 2. Серверная часть | 4-6 недель | Работающий API, база данных, Docker-контейнер |
| 3. Клиентская часть | 3-4 недели | Рефакторинг клиента, API-клиент, EXE-файл |
| 4. Функциональность для ролей | 4-5 недель | Разграничение ролей, специфические функции |
| 5. Интеграции | 3-4 недели | Внешние интеграции, демо-режим |
| 6. Тестирование | 2-3 недели | Исправление ошибок, оптимизация |
| 7. Документация и развертывание | 2 недели | Документация, инструкции, обучение |

### 5.2. Приоритеты и зависимости

**Высокий приоритет:**
- Реорганизация проекта
- Базовый API и клиент-серверное взаимодействие
- Авторизация и разграничение ролей
- Базовая работа со станциями и спотами

**Средний приоритет:**
- Интеграция с SharePoint
- Расширенные функции для операторов
- Административный интерфейс
- Улучшенный UI

**Низкий приоритет:**
- Интеграция с Replicon
- Демонстрационный режим
- Дополнительная аналитика
- Расширенная инфографика

### 5.3. Риски и их снижение

| Риск | Вероятность | Влияние | Меры снижения |
|------|-------------|---------|---------------|
| Сложности интеграции с внешними системами | Высокая | Высокое | Создание моков, поэтапная интеграция, тщательное тестирование |
| Проблемы производительности при масштабировании | Средняя | Высокое | Стресс-тестирование, мониторинг, кэширование |
| Сложности в переходе на новую архитектуру | Высокая | Среднее | Постепенный рефакторинг, четкое планирование, двойной режим работы |
| Проблемы совместимости клиента на разных ОС | Низкая | Среднее | Тестирование на разных версиях Windows, виртуализация |
| Сложности в разграничении ролей | Средняя | Среднее | Четкое определение ролей на старте, документирование прав доступа |

## 6. Заключение

Данный план разработки представляет собой детальное руководство по преобразованию текущего приложения в полноценную клиент-серверную архитектуру с учетом всех требований проекта. Модульный подход к разработке позволит поэтапно внедрять новые функции, сохраняя работоспособность системы на каждом этапе.

Разделение на серверную часть (в Docker) и клиентскую часть (в виде EXE-файлов) обеспечит оптимальную архитектуру для корпоративного применения, а интеграция с внешними системами значительно расширит функциональность приложения и его полезность для бизнеса.

В результате реализации плана будет создана масштабируемая, надежная и удобная система для управления рабочими станциями, спотами и заданиями, которая может быть легко адаптирована под меняющиеся требования бизнеса.
