import os
import re
import subprocess

class ROCustomizationController:
    def __init__(self, config):
        self.config = config

    def search_wo_files(self, wo_number: str):
        # Validate WO number (8 digits).
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
        ref_line = None
        try:
            with open(dat_file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    # Look for lines that contain "!SOF Ref6: Robot F/E No"
                    if "!SOF Ref6:" in line and "Robot F/E No" in line:
                        ref_line = line.strip()
                        # Extract E-number from the pattern: "!SOF Ref6: Robot F/E No - E213927"
                        match = re.search(r'Robot F/E No\s*-\s*(E-?\d+|F\d+)', ref_line, re.IGNORECASE)
                        if match:
                            e_number = match.group(1)
                            break
        except Exception as e:
            print(f"Error parsing E-number: {e}")
            pass
            
        # Return both the E-number and the entire reference line for display
        return {
            "e_number": e_number,
            "ref_line": ref_line
        }

    def open_file(self, file_path):
        """Open a file with the default application"""
        try:
            if os.path.exists(file_path):
                # Use the appropriate method based on the platform
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
