import os
import re
import subprocess

class ROCustomizationController:
    def __init__(self, config):
        self.config = config

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
