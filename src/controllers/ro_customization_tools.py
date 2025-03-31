import os
import re
import subprocess
import time
import threading
import traceback

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
        
        try:
            
            if not os.path.exists(usb_path) or not os.access(usb_path, os.W_OK):
                return False, "USB drive not found or not writable"
            
            # Здесь будет логика создания ПО робота
            # Пока это просто заглушка, которая возвращает успех
            
            # Для демонстрации создадим файл с текущими данными WO
            try:
                with open(os.path.join(usb_path, "robot_sw_info.txt"), "w") as f:
                    f.write(f"WO: {wo_data.get('wo_number', 'Unknown')}\n")
                    if isinstance(wo_data.get('e_number'), dict):
                        f.write(f"E-number: {wo_data['e_number'].get('e_number', 'Unknown')}\n")
                        f.write(f"Model: {wo_data['e_number'].get('model', 'Unknown')}\n")
            except Exception as e:
                return False, f"Failed to create robot SW: {str(e)}"
                
            # Создаем или обновляем файл версии
            try:
                with open(os.path.join(usb_path, "version.txt"), "w") as f:
                    f.write(f"1.0.0 (Created: {time.strftime('%Y-%m-%d %H:%M:%S')})")
            except:
                pass
                
            return True, "Robot SW created successfully"
        except Exception as e:
            return False, f"Error creating robot SW: {str(e)}"
