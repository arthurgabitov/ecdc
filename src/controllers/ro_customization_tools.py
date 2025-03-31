import os
import re
import subprocess
import time
import threading
import traceback
import glob
import shutil 

try:
    import PyPDF2
except ImportError:
    print("PyPDF2 module not found. PDF memory extraction will be unavailable.")
    PyPDF2 = None

class ROCustomizationController:
    def __init__(self, config):
        self.config = config
        self.usb_detection_callbacks = []
        self.usb_detection_active = False
        self.usb_thread = None

    def search_wo_files(self, wo_number: str):
        
        if not re.match(r"^\d{8}$", wo_number):
            return {"error": "WO number must be an 8-digit number"}

        search_dir = self.config.get_customization_settings().get("search_directory", "")
        if not os.path.isdir(search_dir):
            return {"error": f"Directory not found: {search_dir}"}

        found_dat = None
        found_pdf = None
        for filename in os.listdir(search_dir):
            if wo_number in filename:
                full_path = os.path.join(search_dir, filename)
                if filename.endswith(".dat"):
                    found_dat = full_path
                elif filename.endswith(".pdf"):
                    found_pdf = full_path
        
        if not found_dat and not found_pdf:
            return {"error": f"No .dat or .pdf found for {wo_number}"}

        e_number_data = None
        if found_dat:
            e_number_data = self.parse_e_number(found_dat)

        return {
            "dat_file": found_dat,
            "pdf_file": found_pdf,
            "e_number": e_number_data
        }

    def parse_e_number(self, dat_file_path: str):
        e_number = None
        model = None
        ref_line = None
        config_line = None
        
        try:
            with open(dat_file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    
                    if "!SOF Ref6:" in line and "Robot F/E No" in line:
                        ref_line = line.strip()
                        
                        match = re.search(r'Robot F/E No\s*-\s*(E-?\d+|F\d+)', ref_line, re.IGNORECASE)
                        if match:
                            e_number = match.group(1)
                    
                    
                    if "!STARTING CONFIGURATION" in line and "IND.ROBOT" in line:
                        config_line = line.strip()
                        
                        match = re.search(r'IND\.ROBOT\s+([A-Z0-9]+(?:[A-Z0-9-/]*[A-Z0-9]+)?)', config_line, re.IGNORECASE)
                        if match:
                            model = match.group(1)
                    
                    
                    if not model and "STARTING CONFIGURATION" in line:
                        config_line = line.strip()
                        # Попробуем найти паттерны типа "M710iC/50" или подобные
                        match = re.search(r'([A-Z][0-9]+[A-Za-z0-9-/]+)', config_line)
                        if match:
                            model = match.group(1)
                    
                    
                    if e_number and model:
                        break
                        
        except Exception as e:
            print(f"Error parsing file data: {e}")
            pass
            
        
        print(f"Found E-number: {e_number}, Model: {model}")
        if config_line:
            print(f"Configuration line: {config_line}")
            
        
        return {
            "e_number": e_number,
            "model": model,
            "ref_line": ref_line,
            "config_line": config_line
        }

    def open_file(self, file_path):
        
        try:
            if os.path.exists(file_path):
                
                if os.name == 'nt':  # Windows
                    os.startfile(file_path)
                elif os.name == 'posix':  # Linux, macOS
                    subprocess.call(('xdg-open', file_path))
                return True
            else:
                return False
        except Exception as e:
            print(f"Error opening file: {e}")
            return False

    def get_connected_usb_drives(self):
        
        drives = []
        
        try:
            if os.name == 'nt':  
                
                for letter in "DEFGHIKLMNOPQRSTUVWXYZ":
                    drive_path = f"{letter}:"
                    try:
                        
                        if os.path.exists(drive_path) and os.access(drive_path, os.R_OK):
                            try:
                               
                                import win32file
                                drive_type = win32file.GetDriveType(f"{drive_path}\\")
                                
                                
                                if drive_type == win32file.DRIVE_REMOVABLE:
                                    
                                    try:
                                        import win32api
                                        volume_name = win32api.GetVolumeInformation(f"{drive_path}\\")[0]
                                        drive_label = f"{drive_path} ({volume_name})" if volume_name else f"{drive_path} (USB Drive)"
                                    except:
                                        drive_label = f"{drive_path} (USB Drive)"
                                    
                                    
                                    drives.append((drive_path, drive_label))
                            except Exception as e:
                                
                                if os.path.isdir(drive_path):
                                    drives.append((drive_path, f"{drive_path} (Drive)"))
                    except Exception as e:
                        
                        pass
                        
            
        
        except Exception as e:
            print(f"Error in get_connected_usb_drives: {str(e)}")
            traceback.print_exc()
        
        return drives
    
    def check_sw_version(self, drive_path):
        
        version_file = os.path.join(drive_path, "version.txt")
        if os.path.exists(version_file):
            try:
                with open(version_file, 'r') as f:
                    return f.read().strip()
            except:
                pass
        return None
        
    def register_usb_detection_callback(self, callback):
        
        if callback not in self.usb_detection_callbacks:
            self.usb_detection_callbacks.append(callback)
        
        
        if self.usb_detection_callbacks and not self.usb_detection_active:
            self.start_usb_detection()
    
    def unregister_usb_detection_callback(self, callback):
        
        if callback in self.usb_detection_callbacks:
            self.usb_detection_callbacks.remove(callback)
            
        # Останавливаем мониторинг, если больше нет callback'ов
        if not self.usb_detection_callbacks and self.usb_detection_active:
            self.stop_usb_detection()
    
    def monitor_usb_drives(self):
       
        last_drives = []
        
        while self.usb_detection_active:
            try:
                
                drives = self.get_connected_usb_drives()
                
                
                drives_changed = len(drives) != len(last_drives) or any(d1 != d2 for d1, d2 in zip(drives, last_drives) if len(last_drives) == len(drives))
                
                if drives_changed:
                    
                    last_drives = drives.copy()
                    
                    
                    callbacks = list(self.usb_detection_callbacks)
                    for callback in callbacks:
                        try:
                            callback(drives)
                        except Exception as e:
                            print(f"Error in USB detection callback: {str(e)}")
            except Exception as e:
                print(f"Error in USB monitoring loop: {str(e)}")
                
            time.sleep(2)  # Проверка каждые 2 секунды
        
        
    
    def start_usb_detection(self):
        
        
        if not self.usb_detection_active:
            self.usb_detection_active = True
            self.usb_thread = threading.Thread(target=self.monitor_usb_drives, daemon=True)
            self.usb_thread.start()
            
    
    def stop_usb_detection(self):
        
        self.usb_detection_active = False
        if self.usb_thread:
            self.usb_thread = None

    def create_robot_sw(self, usb_path, wo_data):
        """Создает ПО робота на USB путем копирования соответствующего .dat файла"""
        try:
            # Проверяем, что USB существует и доступен для записи
            if not os.path.exists(usb_path) or not os.access(usb_path, os.W_OK):
                return False, "USB drive not found or not writable"
            
            # Проверяем, что у нас есть .dat файл для копирования
            dat_file = wo_data.get("dat_file")
            if not dat_file or not os.path.exists(dat_file):
                return False, "No SW file found for copying"
            
            # Получаем WO номер для вывода в сообщении
            wo_number = wo_data.get("wo_number", "Unknown")
            
            # Получаем версию SW из файла version.txt на USB-диске
            version = self.check_sw_version(usb_path) or "Unknown"
            print(f"USB SW version: {version}")
            
            # Читаем содержимое исходного файла для поиска информации о памяти
            memory_info = None
            mem_detail_line_index = -1
            
            with open(dat_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.readlines()
                
                for i, line in enumerate(content):
                    # Ищем строку с информацией о памяти (нечувствительно к регистру)
                    if re.search(r'!SOF Ref8:', line, re.IGNORECASE) and "Mem Detail" in line:
                        mem_detail_line_index = i
                        print(f"Found memory detail line: {line.strip()}")
            
            # Проверяем PDF файл на наличие информации о памяти
            if wo_data.get("pdf_file"):
                memory_info = self.extract_memory_from_pdf(wo_data.get("pdf_file"))
                print(f"Extracted memory info from PDF: {memory_info}")
            
            # Определяем путь для копирования файла в зависимости от версии
            # Для версий P9 и ниже (V9) файл должен быть в корне USB
            # Для более новых версий - в папке config/p1
            if version.startswith("V9") or version.startswith("9") or version == "Unknown":
                target_file = os.path.join(usb_path, "orderfil.dat")
                print(f"Using root path for version {version}")
            else:
                target_dir = os.path.join(usb_path, "config", "p1")
                os.makedirs(target_dir, exist_ok=True)
                target_file = os.path.join(target_dir, "orderfil.dat")
                print(f"Using config/p1 path for version {version}")
            
            # Копируем файл
            try:
                # Модифицируем содержимое файла, если есть информация о памяти
                if memory_info:
                    # Если нашли строку Mem Detail, модифицируем её
                    if mem_detail_line_index >= 0:
                        line = content[mem_detail_line_index]
                        print(f"Modifying line: {line.strip()}")
                        # Проверяем формат строки
                        if "-" in line:
                            # Формат: !SOF Ref8: Mem Detail - ЗНАЧЕНИЕ
                            
                            base_part = line.split("-")[0]
                            content[mem_detail_line_index] = f"{base_part}- {memory_info}\n"
                            print(f"Modified to: {content[mem_detail_line_index].strip()}")
                        elif ":" in line:
                            # Формат: !SOF Ref8: Mem Detail: ЗНАЧЕНИЕ
                            
                            parts = line.split(":", 2)
                            if len(parts) >= 2:
                                # Восстанавливаем оригинальную строку до двоеточия, добавляем тире и значение
                                prefix_part = parts[0] + ":"
                                if "Mem Detail" in parts[1]:
                                    detail_part = parts[1].split("Mem Detail")[0] + "Mem Detail"
                                    content[mem_detail_line_index] = f"{prefix_part}{detail_part} - {memory_info}\n"
                                else:
                                    content[mem_detail_line_index] = f"{prefix_part} Mem Detail - {memory_info}\n"
                            else:
                                content[mem_detail_line_index] = f"{line.rstrip()} - {memory_info}\n"
                            print(f"Modified to: {content[mem_detail_line_index].strip()}")
                        else:
                            # Неизвестный формат, добавляем в конец строки
                            content[mem_detail_line_index] = f"{line.rstrip()} - {memory_info}\n"
                            print(f"Modified to: {content[mem_detail_line_index].strip()}")
                    else:
                        # Если не нашли строку, ищем другие строки с !SOF Ref для определения регистра
                        sof_ref_format = "!SOF Ref"  # По умолчанию
                        sof_ref_indices = []
                        for i, line in enumerate(content):
                            if re.search(r'![Ss][Oo][Ff] [Rr]ef\d+:', line):
                                sof_ref_indices.append(i)
                                # Определяем формат используемый в файле
                                sof_match = re.search(r'(![Ss][Oo][Ff] [Rr]ef)\d+:', line)
                                if sof_match:
                                    sof_ref_format = sof_match.group(1)
                                    break
                        
                        # Создаем строку в правильном регистре
                        new_mem_detail_line = f"{sof_ref_format}8: Mem Detail - {memory_info}\n"
                        print(f"Creating new line: {new_mem_detail_line.strip()}")
                        
                        if sof_ref_indices:
                            # Если есть другие !SOF Ref строки, вставляем после последней
                            insert_index = max(sof_ref_indices) + 1
                            content.insert(insert_index, new_mem_detail_line)
                        else:
                            # Если нет !SOF Ref строк, вставляем в начало
                            content.insert(0, new_mem_detail_line)
                    
                    # Создаем временный файл для записи модифицированного содержимого
                    temp_file = os.path.join(os.path.dirname(dat_file), f"temp_{os.path.basename(dat_file)}")
                    with open(temp_file, 'w', encoding='utf-8') as f:
                        f.writelines(content)
                    
                    # Копируем модифицированный файл
                    shutil.copy2(temp_file, target_file)
                    
                    # Удаляем временный файл
                    try:
                        os.remove(temp_file)
                    except:
                        pass
                else:
                    # Если нет информации о памяти, копируем файл без изменений
                    shutil.copy2(dat_file, target_file)
                
                print(f"SW file copied from {dat_file} to {target_file}")
                
                # Формируем сообщение для пользователя
                source_filename = os.path.basename(dat_file)
                
                # Исправляем формирование пути назначения, чтобы отображалась буква диска
                if os.name == 'nt':  # Для Windows
                    # Получаем букву диска из полного пути
                    drive_letter = os.path.splitdrive(usb_path)[0]
                    # Получаем относительный путь от корня USB диска
                    relative_path = target_file[len(usb_path):].lstrip('\\/')
                    target_path_display = f"{drive_letter}\\{relative_path}"
                else:
                    # Для других ОС просто используем путь
                    target_path_display = target_file
                
                memory_info_msg = f" with {memory_info}" if memory_info else ""
                
                return True, f"SW file copied from {source_filename} to {target_path_display}{memory_info_msg}"
            except Exception as e:
                print(f"Error copying SW file: {e}")
                traceback.print_exc()
                return False, f"Failed to copy SW: {str(e)}"
                
        except Exception as e:
            print(f"Error creating robot SW: {e}")
            traceback.print_exc()
            return False, f"Error creating robot SW: {str(e)}"

    def extract_memory_from_pdf(self, pdf_file_path):
        """Извлекает информацию о памяти из PDF файла"""
        if not PyPDF2:
            print("PyPDF2 module not available. Cannot extract memory information.")
            return None

        try:
            # Проверяем существование файла
            if not os.path.exists(pdf_file_path):
                print(f"PDF file not found: {pdf_file_path}")
                return None
                
            # Открываем PDF файл
            with open(pdf_file_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                
                # Ищем на каждой странице
                for page_num in range(len(reader.pages)):
                    text = reader.pages[page_num].extract_text()
                    
                    # Выводим текст для отладки
                    print(f"Extracted text from page {page_num+1} (length: {len(text)})")
                    
                    # Поиск строки с указанием модуля памяти
                    memory_patterns = [
                        # Различные форматы с вариациями пробелов
                        r'A05B[-\s]2600[-\s]H\d+\s+.*?(FROM\s*\d+\s*MB\s*/\s*SRAM\s*\d+\s*MB)',  # С R30IB
                        r'A05B[-\s]2600[-\s]H\d+\s+.*?(FROM\s*\d+\s*MB[/\\]\s*SRAM\s*\d+\s*MB)',  # Альтернативно с другим слешем
                        r'(FROM\s*\d+\s*MB\s*/\s*SRAM\s*\d+\s*MB)',  # Только память
                        r'(FROM\s*\d+\s*MB).*?(SRAM\s*\d+\s*MB)'  # Раздельные части
                    ]
                    
                    for pattern in memory_patterns:
                        match = re.search(pattern, text, re.IGNORECASE)
                        if match:
                            if len(match.groups()) == 1:
                                memory_info = match.group(1).strip()
                                # Нормализуем формат (убираем лишние пробелы)
                                memory_info = re.sub(r'\s+', ' ', memory_info)
                                # Заменяем "FROM 128MB / SRAM 3MB" на "FROM128MB/SRAM3MB"
                                memory_info = re.sub(r'FROM\s+(\d+)\s*MB\s*[/\\]\s*SRAM\s+(\d+)\s*MB', r'FROM\1MB/SRAM\2MB', memory_info, flags=re.IGNORECASE)
                                print(f"Found memory info: {memory_info}")
                                return memory_info
                            elif len(match.groups()) > 1:
                                # Объединяем раздельные части
                                from_part = match.group(1).strip()
                                sram_part = match.group(2).strip()
                                # Нормализуем формат
                                from_part = re.sub(r'\s+', '', from_part)
                                sram_part = re.sub(r'\s+', '', sram_part)
                                combined = f"{from_part}/{sram_part}"
                                print(f"Found combined memory info: {combined}")
                                return combined
                    
                    # Ищем строки с содержанием A05B и FROM/SRAM для отладки
                    debug_lines = []
                    for line in text.split('\n'):
                        if ('A05B' in line and ('FROM' in line.upper() or 'SRAM' in line.upper())):
                            debug_lines.append(line.strip())
                    
                    if debug_lines:
                        print("Potential memory info lines found but not matched:")
                        for line in debug_lines:
                            print(f"  > {line}")
            
            print(f"Memory information not found in PDF: {pdf_file_path}")
            return None
                
        except Exception as e:
            print(f"Error extracting memory from PDF: {str(e)}")
            traceback.print_exc()
            return None

    def find_and_open_dt_file(self, e_number):
        """Находит и открывает DT файл для указанного E-number"""
        try:
            # Очищаем номер от лишнего
            clean_e_number = e_number.strip().upper()
            if clean_e_number.startswith("E-"):
                clean_e_number = "E" + clean_e_number[2:]
            elif not clean_e_number.startswith("E"):
                clean_e_number = "E" + clean_e_number
            
            # Извлекаем диапазон для папки
            match = re.match(r'E(\d{3})(\d{3})', clean_e_number)
            if not match:
                return False, f"Invalid E-number format: {e_number}"
            
            first_part = match.group(1)
            # Правильный формат для диапазона папок
            range_folder = f"E{first_part}000-E{first_part}999"
            
            # Пути к возможным директориям
            base_path = r"\\fanuc\FS\Corporate\Products\Data_Sheets_MD"
            dt_path = os.path.join(base_path, range_folder, "DT")
            regular_path = os.path.join(base_path, range_folder)
            
            # Выводим пути для отладки
            print(f"Searching in DT path: {dt_path}")
            print(f"Searching in regular path: {regular_path}")
            
            # Файл может иметь разные форматы имени, ищем по номеру E-number
            # Используем более общий шаблон для поиска, но ограничиваем расширения
            e_number_dash = clean_e_number.replace('E', 'E-')
            
            # Создаем более гибкие шаблоны поиска с указанием расширений Excel файлов
            patterns = [
                f"*{e_number_dash}*.xls",   # Старый формат Excel
                f"*{e_number_dash}*.xlsx",  # Новый формат Excel
                f"*{e_number_dash}*.xlsm",  # Excel с макросами
                f"*{clean_e_number}*.xls",  # Без дефиса, старый формат
                f"*{clean_e_number}*.xlsx", # Без дефиса, новый формат
                f"*{clean_e_number}*.xlsm", # Без дефиса, с макросами
            ]
            
            found_files = []
            
            # Ищем во всех возможных местах и по всем шаблонам
            for pattern in patterns:
                # Поиск в DT папке
                if os.path.exists(dt_path):
                    dt_search = os.path.join(dt_path, pattern)
                    found_files.extend(glob.glob(dt_search))
                    print(f"Searching with pattern '{dt_search}', found {len(glob.glob(dt_search))} files")
                
                # Поиск в обычной папке
                if os.path.exists(regular_path):
                    regular_search = os.path.join(regular_path, pattern)
                    found_files.extend(glob.glob(regular_search))
                    print(f"Searching with pattern '{regular_search}', found {len(glob.glob(regular_search))} files")
            
            # Убираем дубликаты
            found_files = list(set(found_files))
            
            # Если Excel файлы не найдены, попробуем найти любые файлы с e-number для диагностики
            if not found_files:
                print(f"No Excel files found for {e_number}, checking for any files")
                
                # Более общий поиск для диагностики
                any_patterns = [f"*{e_number_dash}*.*", f"*{clean_e_number}*.*"]
                diagnostic_files = []
                
                for pattern in any_patterns:
                    if os.path.exists(dt_path):
                        diagnostic_files.extend(glob.glob(os.path.join(dt_path, pattern)))
                    if os.path.exists(regular_path):
                        diagnostic_files.extend(glob.glob(os.path.join(regular_path, pattern)))
                
                # Если нашли другие файлы, выводим их для диагностики
                if diagnostic_files:
                    print(f"Found non-Excel files for {e_number}:")
                    for f in diagnostic_files:
                        print(f"  {f} ({os.path.splitext(f)[1]})")
                    return False, f"No Excel DT file found for {e_number}, but found {len(diagnostic_files)} other files"
                
                # Если ничего не нашли, перечисляем содержимое папок
                print(f"No files found for {e_number}")
                if os.path.exists(dt_path) and os.listdir(dt_path):
                    print(f"Files in {dt_path}:")
                    for f in os.listdir(dt_path):
                        if e_number_dash.lower() in f.lower() or clean_e_number.lower() in f.lower():
                            print(f"  {f} (PARTIAL MATCH)")
                        
                if os.path.exists(regular_path) and os.listdir(regular_path):
                    print(f"Files in {regular_path}:")
                    for f in os.listdir(regular_path):
                        if e_number_dash.lower() in f.lower() or clean_e_number.lower() in f.lower():
                            print(f"  {f} (PARTIAL MATCH)")
                            
                return False, f"No DT file found for {e_number}"
            
            # Выводим все найденные файлы для проверки
            print(f"Found {len(found_files)} Excel files for {e_number}:")
            for f in found_files:
                print(f"  {f} ({os.path.splitext(f)[1]})")
            
            # Выбираем первый найденный файл и открываем его
            file_to_open = found_files[0]
            
            
            if self.open_file(file_to_open):
                return True, f"Opening DT file: {os.path.basename(file_to_open)}"
            else:
                return False, f"Failed to open DT file: {os.path.basename(file_to_open)}"
            
        except Exception as e:
            traceback.print_exc()
            return False, f"Error finding DT file: {str(e)}"

    def create_aoa_folder(self, usb_path, wo_number, e_number):
        """Создает AOA папку на USB диске"""
        try:
            # Проверяем, что USB существует и доступен для записи
            if not os.path.exists(usb_path) or not os.access(usb_path, os.W_OK):
                return False, "USB drive not found or not writable"
            
            # Проверяем, что у нас есть номер WO и E-number
            if not wo_number:
                return False, "WO number is required to create AOA folder"
            
            if not e_number:
                return False, "E-number is required to create AOA folder"
            
            # Форматируем E-number, удаляя возможный дефис
            if e_number.startswith("E-"):
                e_number = "E" + e_number[2:]
                
            # Создаем имя папки в формате "12345678_Е123456"
            folder_name = f"{wo_number}_{e_number}"
            folder_path = os.path.join(usb_path, folder_name)
            
            # Проверяем, существует ли уже папка
            if os.path.exists(folder_path):
                return False, f"Folder '{folder_name}' already exists"
            
            # Создаем папку
            os.makedirs(folder_path)
            
            return True, f"Created AOA folder: {folder_path}"
            
        except Exception as e:
            print(f"Error creating AOA folder: {e}")
            traceback.print_exc()
            return False, f"Error creating AOA folder: {str(e)}"

    def move_backup_folders(self, usb_path):
        """Перемещает все папки с бэкапами с USB на рабочий стол"""
        try:
            # Проверяем, что USB существует и доступен для чтения
            if not os.path.exists(usb_path) or not os.access(usb_path, os.R_OK):
                return False, "USB drive not found or not readable"
            
            # Получаем путь к рабочему столу пользователя
            desktop_path = os.path.join(os.path.expanduser('~'), 'Desktop')
            # Создаем папку для бэкапов на рабочем столе, если её нет
            backup_folder = os.path.join(desktop_path, 'Backups')
            if not os.path.exists(backup_folder):
                os.makedirs(backup_folder)
            
            # Счетчики для отчета
            moved_folders = 0
            errors = 0
            
            # Ищем папки в формате 12345678_E123456 на USB
            backup_folders = []
            for item in os.listdir(usb_path):
                item_path = os.path.join(usb_path, item)
                # Проверяем, что это папка и соответствует шаблону "12345678_E123456"
                if os.path.isdir(item_path) and re.match(r'\d{8}_E\d+', item):
                    # Проверяем, что папка не пуста
                    if os.listdir(item_path):
                        backup_folders.append((item, item_path))
            
            # Если нет папок для перемещения
            if not backup_folders:
                return False, "No backup folders found on the USB drive."
                
            # Перемещаем папки
            for item, item_path in backup_folders:
                try:
                    target_path = os.path.join(backup_folder, item)
                    
                    # Если папка назначения уже существует, добавляем метку времени
                    if os.path.exists(target_path):
                        import datetime
                        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                        target_path = os.path.join(backup_folder, f"{item}_{timestamp}")
                    
                    # Перемещаем папку с USB на рабочий стол
                    shutil.copytree(item_path, target_path)
                    
                    # После успешного копирования удаляем оригинальную папку
                    shutil.rmtree(item_path)
                    
                    moved_folders += 1
                except Exception as e:
                    print(f"Error moving folder {item}: {str(e)}")
                    errors += 1
            
            # Формируем сообщение о результате
            if moved_folders > 0:
                message = f"Successfully moved {moved_folders} backup folder{'s' if moved_folders > 1 else ''} to {backup_folder}"
                if errors > 0:
                    message += f". {errors} folder{'s' if errors > 1 else ''} couldn't be moved due to errors."
                return True, message
            else:
                if errors > 0:
                    return False, f"Failed to move {errors} folder{'s' if errors > 1 else ''}. No backups were moved."
                else:
                    return False, "No backup folders found on the USB drive."
                
        except Exception as e:
            print(f"Error moving backup folders: {e}")
            traceback.print_exc()
            return False, f"Error moving backup folders: {str(e)}"
