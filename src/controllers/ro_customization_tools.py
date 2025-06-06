import os
import re
import subprocess
import time
import threading
import traceback
import glob
import shutil 
import PyPDF2



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
        """Extract E-number and model information from DAT file"""
        e_number = None
        model = None
        ref_line = None
        config_line = None
        
        # Try reading the file in binary mode first to handle any encoding
        try:
            with open(dat_file_path, 'rb') as f:
                # Try to detect encoding or use a fallback
                content = f.read()
                encodings = ['utf-8', 'latin1', 'iso-8859-1', 'cp1252', 'windows-1252']
                file_lines = None
                
                # Try different encodings
                for encoding in encodings:
                    try:
                        file_lines = content.decode(encoding).splitlines()
                        break
                    except UnicodeDecodeError:
                        continue
                
                # If we couldn't decode with any encoding, use latin1 which can decode any byte
                if file_lines is None:
                    file_lines = content.decode('latin1', errors='replace').splitlines()
                
                # Process lines
                for line in file_lines:
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
                        match = re.search(r'([A-Z][0-9]+[A-Za-z0-9-/]+)', config_line)
                        if match:
                            model = match.group(1)
                    
                    if e_number and model:
                        break
        except Exception as e:
            print(f"Error parsing file data: {e}")
        
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
                # Use direct ctypes approach which is more reliable across different packaging methods
                try:
                    import ctypes
                    
                    # Define the GetLogicalDrives function
                    GetLogicalDrives = ctypes.windll.kernel32.GetLogicalDrives
                    GetLogicalDrives.restype = ctypes.c_ulong
                    
                    # Define GetDriveType function
                    GetDriveType = ctypes.windll.kernel32.GetDriveTypeW
                    GetDriveType.argtypes = [ctypes.c_wchar_p]
                    GetDriveType.restype = ctypes.c_uint
                    
                    # Constants for drive types
                    DRIVE_REMOVABLE = 2
                    
                    # Get bitmask of available drives
                    bitmask = GetLogicalDrives()
                    
                    # Check each possible drive letter
                    for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
                        # If drive exists (bit is set in bitmask)
                        if bitmask & (1 << (ord(letter) - ord('A'))):
                            drive_path = f"{letter}:"
                            drive_type = GetDriveType(f"{drive_path}\\")
                            
                            # If it's a removable drive
                            if drive_type == DRIVE_REMOVABLE:
                                # Add extra validation to confirm it's a real USB drive
                                if self._is_physical_usb_drive(drive_path):
                                    try:
                                        # Define constants and structures for GetVolumeInformation
                                        buffer_len = 256
                                        volume_name_buffer = ctypes.create_unicode_buffer(buffer_len)
                                        fs_name_buffer = ctypes.create_unicode_buffer(buffer_len)
                                        
                                        # Call GetVolumeInformation directly
                                        result = ctypes.windll.kernel32.GetVolumeInformationW(
                                            ctypes.c_wchar_p(f"{drive_path}\\"),
                                            volume_name_buffer,
                                            buffer_len,
                                            None, None, None,
                                            fs_name_buffer,
                                            buffer_len
                                        )
                                        
                                        # Get volume name
                                        volume_name = volume_name_buffer.value if result else ""
                                        
                                        # Format the drive label - IMPORTANT: Remove parentheses for consistency
                                        if volume_name:
                                            drive_label = f"{drive_path} {volume_name}"
                                        else:
                                            drive_label = f"{drive_path} USB Drive"
                                        
                                        drives.append((drive_path, drive_label))
                                        
                                        
                                    except Exception as e:
                                        print(f"Error getting volume name for {drive_path}: {str(e)}")
                                        drives.append((drive_path, f"{drive_path} USB Drive"))
                
                except Exception as e:
                    print(f"Error using ctypes for drive detection: {str(e)}")
                    # Fall back to the original method if ctypes approach fails
                    try:
                        # Импортируем win32 модули только если они нужны и доступны
                        import win32file
                        import win32api
                        have_win32 = True
                    except ImportError:
                        print("Warning: win32api/win32file modules not available")
                        have_win32 = False
                    
                    for letter in "DEFGHIJKLMNOPQRSTUVWXYZ":
                        drive_path = f"{letter}:"
                        try:
                            if os.path.exists(drive_path) and os.access(drive_path, os.R_OK):
                                if have_win32:
                                    try:
                                        drive_type = win32file.GetDriveType(f"{drive_path}\\")
                                        
                                        if drive_type == win32file.DRIVE_REMOVABLE:
                                            try:
                                                volume_name = win32api.GetVolumeInformation(f"{drive_path}\\")[0]
                                                # IMPORTANT: Changed format to remove parentheses for consistency
                                                drive_label = f"{drive_path} {volume_name}" if volume_name else f"{drive_path} USB Drive"
                                            except:
                                                drive_label = f"{drive_path} USB Drive"
                                            
                                            drives.append((drive_path, drive_label))
                                    except Exception as e:
                                        print(f"Win32 API error for {drive_path}: {e}")
                                        if os.path.isdir(drive_path):
                                            drives.append((drive_path, f"{drive_path} Drive"))
                                else:
                                    # Альтернативный метод определения съемных дисков
                                    if os.path.isdir(drive_path):
                                        drives.append((drive_path, f"{drive_path} Drive"))
                        except Exception as e:
                            pass
            
            
            
        except Exception as e:
            print(f"Error in get_connected_usb_drives: {str(e)}")
            traceback.print_exc()
        
        return drives

    def _is_physical_usb_drive(self, drive_path):
        """Check if a drive is a physical USB drive by verifying it has typical USB drive characteristics"""
        try:
            # Check if the drive actually exists and is accessible
            if not os.path.exists(f"{drive_path}\\"):
                print(f"Drive path {drive_path}\\ does not exist or is not accessible")
                return False
                
            # When using flet build windows, trust GetDriveType's assessment
            return True
            
        except Exception as e:
            print(f"Error checking if {drive_path} is physical USB: {e}")
            return False

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
                
            time.sleep(2)  
        
        
    
    def start_usb_detection(self):
        if not self.usb_detection_active:
            self.usb_detection_active = True
            self.usb_thread = threading.Thread(target=self.monitor_usb_drives, daemon=True)
            self.usb_thread.start()
            
    
    def stop_usb_detection(self):
        self.usb_detection_active = False
        if self.usb_thread:
            self.usb_thread = None  # This doesn't actually stop the thread, just removes the reference

    def create_robot_sw(self, usb_path, wo_data):
        """Create robot SW on USB by copying the corresponding DAT file"""
        try:
            if not os.path.exists(usb_path) or not os.access(usb_path, os.W_OK):
                return False, "USB drive not found or not writable"
            
            
            dat_file = wo_data.get("dat_file")
            if not dat_file or not os.path.exists(dat_file):
                return False, "No SW file found for copying"
            
            
            wo_number = wo_data.get("wo_number", "Unknown")
            
            
            version = self.check_sw_version(usb_path) or "Unknown"
            print(f"USB SW version: {version}")
            
            
            memory_info = None
            mem_detail_line_index = -1
            content = []
            
            # Check if we have a CRX model - if so, use standard memory
            is_crx_model = False
            if wo_data.get("e_number") and wo_data["e_number"].get("model"):
                robot_model = wo_data["e_number"]["model"]
                if robot_model and "CRX" in robot_model.upper():
                    memory_info = "FROM256MB/SRAM3MB"
                    is_crx_model = True
                    print(f"CRX model detected: {robot_model}. Using standard memory: {memory_info}")
            
            # Read file in binary mode
            try:
                with open(dat_file, 'rb') as f:
                    file_bytes = f.read()
                    
                    # Try different encodings
                    encodings = ['utf-8', 'latin1', 'iso-8859-1', 'cp1252', 'windows-1252']
                    decoded_content = None
                    
                    for encoding in encodings:
                        try:
                            decoded_content = file_bytes.decode(encoding)
                            print(f"Successfully decoded with {encoding}")
                            break
                        except UnicodeDecodeError:
                            continue
                    
                    # Fall back to latin1 which can decode any byte sequence
                    if decoded_content is None:
                        decoded_content = file_bytes.decode('latin1', errors='replace')
                        print("Falling back to latin1 with replacement")
                    
                    # Split into lines
                    content = decoded_content.splitlines(keepends=True)
                    
                    # Find memory detail line
                    for i, line in enumerate(content):
                        if re.search(r'!SOF Ref8:', line, re.IGNORECASE) and "Mem Detail" in line:
                            mem_detail_line_index = i
                            print(f"Found memory detail line: {line.strip()}")
                            break
                            
            except Exception as e:
                print(f"Error reading DAT file: {e}")
                traceback.print_exc()
                return False, f"Error reading DAT file: {str(e)}"
            
            # If not CRX model, check PDF file for memory info if available
            if not is_crx_model and wo_data.get("pdf_file"):
                pdf_memory_info = self.extract_memory_from_pdf(wo_data.get("pdf_file"))
                if pdf_memory_info:
                    memory_info = pdf_memory_info
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
                # Safely create modified content
                if memory_info and content:
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
                    
                    # Write the modified file with the same encoding as we read it
                    temp_file = os.path.join(os.path.dirname(dat_file), f"temp_{os.path.basename(dat_file)}")
                    
                    # Use latin1 for writing which can encode any byte
                    try:
                        with open(temp_file, 'w', encoding='latin1', errors='replace') as f:
                            f.writelines(content)
                    except Exception as e:
                        print(f"Error writing modified file: {e}")
                        return False, f"Failed to create modified file: {str(e)}"
                    
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
        """Extract memory information from PDF file"""
        if not PyPDF2:
            print("PyPDF2 module not available. Cannot extract memory information.")
            return None

        try:
            # Check if the file exists
            if not os.path.exists(pdf_file_path):
                print(f"PDF file not found: {pdf_file_path}")
                return None
                
            # Open the PDF file
            with open(pdf_file_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                
                # Search each page
                for page_num in range(len(reader.pages)):
                    text = reader.pages[page_num].extract_text()
                    
                    # Search for memory module information
                    memory_patterns = [
                        # Various formats with space variations
                        r'A05B[-\s]2600[-\s]H\d+\s+.*?(FROM\s*\d+\s*MB\s*/\s*SRAM\s*\d+\s*MB)', 
                        r'A05B[-\s]2600[-\s]H\d+\s+.*?(FROM\s*\d+\s*MB[/\\]\s*SRAM\s*\d+\s*MB)',  
                        r'(FROM\s*\d+\s*MB\s*/\s*SRAM\s*\d+\s*MB)',  
                        r'(FROM\s*\d+\s*MB).*?(SRAM\s*\d+\s*MB)'  
                    ]
                    
                    for pattern in memory_patterns:
                        match = re.search(pattern, text, re.IGNORECASE)
                        if match:
                            if len(match.groups()) == 1:
                                memory_info = match.group(1).strip()
                                # Normalize format (remove extra spaces)
                                memory_info = re.sub(r'\s+', ' ', memory_info)
                                # Replace "FROM xxxMB / SRAM yMB" with "FROMxxxMB/SRAMyMB"
                                memory_info = re.sub(r'FROM\s+(\d+)\s*MB\s*[/\\]\s*SRAM\s+(\d+)\s*MB', r'FROM\1MB/SRAM\2MB', memory_info, flags=re.IGNORECASE)
                                return memory_info
                            elif len(match.groups()) > 1:
                                # Combine separate parts
                                from_part = match.group(1).strip()
                                sram_part = match.group(2).strip()
                                # Normalize format
                                from_part = re.sub(r'\s+', '', from_part)
                                sram_part = re.sub(r'\s+', '', sram_part)
                                combined = f"{from_part}/{sram_part}"
                                return combined
            
            return None
                
        except Exception as e:
            print(f"Error extracting memory from PDF: {str(e)}")
            traceback.print_exc()
            return None

    def find_and_open_dt_file(self, e_number):
        """Find and open DT file for the specified E-number"""
        try:
            # Clean up the number
            clean_e_number = e_number.strip().upper()
            if clean_e_number.startswith("E-"):
                clean_e_number = "E" + clean_e_number[2:]
            elif not clean_e_number.startswith("E"):
                clean_e_number = "E" + clean_e_number
            
            # Extract folder range
            match = re.match(r'E(\d{3})(\d{3})', clean_e_number)
            if not match:
                return False, f"Invalid E-number format: {e_number}"
            
            first_part = match.group(1)
            # Correct format for folder range
            range_folder = f"E{first_part}000-E{first_part}999"
            
            # Paths to possible directories
            base_path = r"\\fanuc\FS\Corporate\Products\Data_Sheets_MD"
            dt_path = os.path.join(base_path, range_folder, "DT")
            regular_path = os.path.join(base_path, range_folder)
            
            # File may have different formats, search by E-number
            # Use more general pattern for search but limit extensions
            e_number_dash = clean_e_number.replace('E', 'E-')
            
            # Create search patterns with Excel file extensions
            patterns = [
                f"*{e_number_dash}*.xls",   
                f"*{e_number_dash}*.xlsx",  
                f"*{e_number_dash}*.xlsm",  
                f"*{clean_e_number}*.xls",  
                f"*{clean_e_number}*.xlsx", 
                f"*{clean_e_number}*.xlsm", 
            ]
            
            found_files = []
            
            # Search in all possible locations with all patterns
            for pattern in patterns:
                # Search in DT folder
                if os.path.exists(dt_path):
                    dt_search = os.path.join(dt_path, pattern)
                    found_files.extend(glob.glob(dt_search))
                
                # Search in regular folder
                if os.path.exists(regular_path):
                    regular_search = os.path.join(regular_path, pattern)
                    found_files.extend(glob.glob(regular_search))
            
            # Remove duplicates
            found_files = list(set(found_files))
            
            # If no Excel files found, try to find any files with e-number for diagnostics
            if not found_files:
                # More general search for diagnostics
                any_patterns = [f"*{e_number_dash}*.*", f"*{clean_e_number}*.*"]
                diagnostic_files = []
                
                for pattern in any_patterns:
                    if os.path.exists(dt_path):
                        diagnostic_files.extend(glob.glob(os.path.join(dt_path, pattern)))
                    if os.path.exists(regular_path):
                        diagnostic_files.extend(glob.glob(os.path.join(regular_path, pattern)))
                
                # If other files found, list them for diagnostics
                if diagnostic_files:
                    return False, f"No Excel DT file found for {e_number}, but found {len(diagnostic_files)} other files"
                            
                return False, f"No DT file found for {e_number}"
            
            # Select the first found file and open it
            file_to_open = found_files[0]
            
            if self.open_file(file_to_open):
                return True, f"Opening DT file: {os.path.basename(file_to_open)}"
            else:
                return False, f"Failed to open DT file: {os.path.basename(file_to_open)}"
            
        except Exception as e:
            traceback.print_exc()
            return False, f"Error finding DT file: {str(e)}"

    def create_aoa_folder(self, usb_path, wo_number, e_number):
        """Create an AOA folder on USB drive"""
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
        """Move backup folders from USB to desktop"""
        try:
            # Check that USB exists and is readable
            if not os.path.exists(usb_path) or not os.access(usb_path, os.R_OK):
                return False, "USB drive not found or not readable"
            
            # Get user's desktop path
            desktop_path = os.path.join(os.path.expanduser('~'), 'Desktop')
            # Create backups folder on desktop if it doesn't exist
            backup_folder = os.path.join(desktop_path, 'Backups')
            if not os.path.exists(backup_folder):
                os.makedirs(backup_folder)
            
            # Counters for report
            moved_folders = 0
            errors = 0
            
            # Look for folders in format 12345678_E123456 on USB
            backup_folders = []
            for item in os.listdir(usb_path):
                item_path = os.path.join(usb_path, item)
                # Check that it's a folder and matches pattern "12345678_E123456"
                if os.path.isdir(item_path) and re.match(r'\d{8}_E\d+', item):
                    # Check that folder isn't empty
                    if os.listdir(item_path):
                        backup_folders.append((item, item_path))
            
            # If no folders to move
            if not backup_folders:
                return False, "No backup folders found on the USB drive."
                
            # Move folders
            for item, item_path in backup_folders:
                try:
                    target_path = os.path.join(backup_folder, item)
                    
                    # If target folder already exists, add timestamp
                    if os.path.exists(target_path):
                        import datetime
                        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                        target_path = os.path.join(backup_folder, f"{item}_{timestamp}")
                    
                    # Move folder from USB to desktop
                    shutil.copytree(item_path, target_path)
                    
                    # After successful copy, remove original folder
                    shutil.rmtree(item_path)
                    
                    moved_folders += 1
                except Exception as e:
                    print(f"Error moving folder {item}: {str(e)}")
                    errors += 1
            
            # Create result message
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
            
    def open_orderfil_from_usb(self, usb_path):
        """Open orderfil.dat file from USB drive"""
        try:
            # Проверяем, что USB существует
            if not os.path.exists(usb_path):
                return False, "USB drive not found"
            
            # Определяем возможные пути к файлу orderfil.dat
            # Для версии P9 и ниже файл находится в корне
            root_path = os.path.join(usb_path, "orderfil.dat")
            # Для более новых версий файл находится в папке config/p1
            config_path = os.path.join(usb_path, "config", "p1", "orderfil.dat")
            
            # Проверяем, существует ли файл по одному из путей
            if os.path.exists(root_path):
                success = self.open_file(root_path)
                path_display = root_path
            elif os.path.exists(config_path):
                success = self.open_file(config_path)
                path_display = config_path
            else:
                return False, "orderfil.dat not found on this USB drive"
            
            if success:
                return True, f"Opened orderfil.dat from {path_display}"
            else:
                return False, f"Failed to open orderfil.dat"
                
        except Exception as e:
            print(f"Error opening orderfil.dat: {e}")
            traceback.print_exc()
            return False, f"Error opening orderfil.dat: {str(e)}"
        
    def find_and_open_sw_file(self, wo_number):
        """Find and open SW txt file for the specified WO number in the shared directory"""
        import glob
        import os
        sw_dir = r"\\fanuc\fs\Shared\European_Customisation\ECDC-Customised Robot SW Order File"
        pattern = os.path.join(sw_dir, f"*{wo_number}*.dat")
        found_files = glob.glob(pattern)
        if not found_files:
            return False, f"No SW file found for WO {wo_number}"
        file_to_open = found_files[0]
        try:
            if os.name == 'nt':
                os.startfile(file_to_open)
            else:
                import subprocess
                subprocess.call(('xdg-open', file_to_open))
            return True, f"Opening SW file: {os.path.basename(file_to_open)}"
        except Exception as ex:
            return False, f"Failed to open file: {ex}"

    def find_and_open_bom_file(self, wo_number):
        """Find and open BOM PDF file for the specified WO number in the shared directory"""
        import glob
        import os
        sw_dir = r"\\fanuc\fs\Shared\European_Customisation\ECDC-Customised Robot SW Order File"
        pattern = os.path.join(sw_dir, f"*{wo_number}*.pdf")
        found_files = glob.glob(pattern)
        if not found_files:
            return False, f"No BOM PDF found for WO {wo_number}"
        file_to_open = found_files[0]
        try:
            if os.name == 'nt':
                os.startfile(file_to_open)
            else:
                import subprocess
                subprocess.call(('xdg-open', file_to_open))
            return True, f"Opening BOM PDF: {os.path.basename(file_to_open)}"
        except Exception as ex:
            return False, f"Failed to open file: {ex}"
