#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Контроллер для работы с данными из SharePoint
Отвечает за получение, кеширование и обработку данных о роботах и заказах
"""

import os
import json
import time
import logging
import threading
from datetime import datetime
from typing import Dict, List, Any, Optional

from models.sharepoint_analysis import SharePointConfig, get_robot_data, save_data_to_json, get_robot_details, parse_robot_xml
from config import get_app_data_path

# Конфигурация логирования
logging.basicConfig(
    filename='sharepoint_analysis.log',
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
log = logging.getLogger('sharepoint_controller')

class SharePointController:
    """
    Контроллер для управления данными из SharePoint
    """
    
    def __init__(self, config_path: str = None):
        """
        Инициализирует контроллер SharePoint
        
        Args:
            config_path (str, optional): Путь к файлу конфигурации
        """
        self.config = SharePointConfig()
        self.data_cache = {}
        
        # Используем функцию get_app_data_path для правильного определения пути
        data_dir = os.path.join(get_app_data_path(), 'data')
        os.makedirs(data_dir, exist_ok=True)
        
        self.cache_path = os.path.join(data_dir, 'sharepoint_cache.json')
        self.users_cache_path = os.path.join(data_dir, 'users_cache.json')
        self.last_update = None
        self.is_updating = False
        self.update_interval = 60 * 60  # 1 час в секундах
        
        # Загружаем кеш из файла
        self.load_cache()

    def load_cache(self) -> None:
        """Загружает кешированные данные из файла"""
        try:
            if os.path.exists(self.cache_path):
                with open(self.cache_path, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)
                    self.data_cache = cache_data.get('data', {})
                    last_update_str = cache_data.get('last_update')
                    if last_update_str:
                        self.last_update = datetime.fromisoformat(last_update_str)
                log.info(f"Кеш загружен, количество записей: {len(self.data_cache)}")
            else:
                log.info("Кеш не найден, будет создан новый")
        except Exception as e:
            log.error(f"Ошибка при загрузке кеша: {str(e)}")
            self.data_cache = {}
    
    def save_cache(self) -> None:
        """Сохраняет данные в кеш-файл"""
        try:
            cache_data = {
                'data': self.data_cache,
                'last_update': datetime.now().isoformat()
            }
            with open(self.cache_path, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, indent=2, ensure_ascii=False)
            log.info(f"Кеш сохранен, количество записей: {len(self.data_cache)}")
        except Exception as e:
            log.error(f"Ошибка при сохранении кеша: {str(e)}")
    
    def update_data(self, force: bool = False) -> bool:
        """
        Обновляет данные из SharePoint, если это необходимо
        
        Args:
            force (bool): Принудительное обновление независимо от интервала
        
        Returns:
            bool: True, если обновление прошло успешно
        """
        current_time = time.time()
        
        # Проверяем, нужно ли обновлять данные
        if not force and self.last_update and not self.is_updating:
            last_update_time = self.last_update.timestamp()
            if current_time - last_update_time < self.update_interval:
                log.info("Обновление не требуется, данные актуальны")
                return True
        
        # Если обновление уже идёт, не запускаем его повторно
        if self.is_updating:
            log.info("Обновление уже выполняется")
            return False
        
        try:
            self.is_updating = True
            log.info("Начало обновления данных из SharePoint")
            
            # Получаем данные о роботах
            statuses = [36, 42, 48, 50, 90]  # Статусы, по которым фильтруем
            robot_data = get_robot_data(self.config, statuses)
            
            if not robot_data:
                log.error("Не удалось получить данные о роботах")
                self.is_updating = False
                return False
            
            # Группируем данные по техникам (SSO)
            technician_data = {}
            for item in robot_data:
                technician = item.get('Technician')
                if technician:
                    if technician not in technician_data:
                        technician_data[technician] = []
                    technician_data[technician].append(item)
            
            # Обновляем кеш
            self.data_cache = technician_data
            self.last_update = datetime.now()
            
            # Сохраняем в файл
            self.save_cache()
            
            log.info(f"Данные успешно обновлены: {len(robot_data)} роботов для {len(technician_data)} техников")
            self.is_updating = False
            return True
            
        except Exception as e:
            log.error(f"Ошибка при обновлении данных: {str(e)}")
            self.is_updating = False
            return False
    
    def schedule_update(self) -> None:
        """Запланировать обновление данных в отдельном потоке"""
        update_thread = threading.Thread(target=self.update_data)
        update_thread.daemon = True
        update_thread.start()
    
    def get_robot_list_by_technician(self, sso: str) -> List[Dict]:
        """
        Получает список роботов, назначенных технику
        
        Args:
            sso (str): SSO техника
        
        Returns:
            List[Dict]: Список роботов
        """
        # Проверяем, не устарел ли кеш
        current_time = time.time()
        if self.last_update:
            last_update_time = self.last_update.timestamp()
            if current_time - last_update_time > self.update_interval:
                # Запускаем обновление в отдельном потоке
                self.schedule_update()
        else:
            # Если кеш пустой, обновляем синхронно
            self.update_data()
        
        # Возвращаем данные из кеша
        return self.data_cache.get(sso, [])
    
    def get_robot_details(self, lot_number: str) -> Optional[Dict]:
        """
        Получает подробную информацию о роботе
        
        Args:
            lot_number (str): Номер партии робота (LotNumber)
        
        Returns:
            Optional[Dict]: Подробная информация о роботе или None
        """
        try:
            # Проверяем, есть ли подробные данные в кеше
            # В будущем можно добавить кеширование подробных данных
            
            robot_details = get_robot_details(self.config, lot_number)
            if robot_details:
                robot_xml = robot_details.get("RobotXML", "")
                if robot_xml:
                    parsed_data = parse_robot_xml(robot_xml)
                    return {
                        "lot_number": lot_number,
                        "work_order": robot_details.get("WorkOrder", ""),
                        "jde_status": robot_details.get("JDEStatus", ""),
                        "robot_info": parsed_data
                    }
            
            return None
        except Exception as e:
            log.error(f"Ошибка при получении данных робота {lot_number}: {str(e)}")
            return None

# Глобальный экземпляр контроллера
_instance = None

def get_sharepoint_controller() -> SharePointController:
    """
    Получает глобальный экземпляр контроллера SharePoint
    
    Returns:
        SharePointController: Экземпляр контроллера
    """
    global _instance
    if _instance is None:
        _instance = SharePointController()
    return _instance

if __name__ == "__main__":
    # Пример использования
    controller = get_sharepoint_controller()
    controller.update_data(force=True)
    
    # Получаем список техников с роботами
    for technician, robots in controller.data_cache.items():
        print(f"Техник: {technician}, Количество роботов: {len(robots)}")
        
        # Выводим первый робот для примера
        if robots:
            robot = robots[0]
            print(f"  Пример робота: {robot.get('LotNumber')} - {robot.get('device_model')}")
    
    # Получаем подробную информацию по первому роботу
    if controller.data_cache and list(controller.data_cache.values())[0]:
        first_robot = list(controller.data_cache.values())[0][0]
        lot_number = first_robot.get('LotNumber')
        print(f"\nПолучаем подробную информацию по роботу {lot_number}:")
        details = controller.get_robot_details(lot_number)
        if details:
            robot_header = details.get('robot_info', {}).get('header', {})
            print(f"  Модель: {robot_header.get('Series_Name', 'Нет данных')}")
            print(f"  Серийный номер: {robot_header.get('Mechanical_SerialNo', 'Нет данных')}")
            print(f"  Спецификация: {robot_header.get('Mechanical_Specification', 'Нет данных')}")
            print(f"  Заказчик: {robot_header.get('Customer_Name', 'Нет данных')}")