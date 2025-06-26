import os
import subprocess
import re
import glob
import openpyxl
import xlrd
import xlwt
from xlutils.copy import copy as xl_copy
import sys

\
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
KCONVARS_PATH = os.path.join(BASE_DIR, '..', 'utils', 'WinOLPC', 'bin', 'kconvars.exe')
KCONVARS_PATH = os.path.abspath(KCONVARS_PATH)

DT_TARGET_DIR = r"J:\SC\SC_ALL\European Customisation Center\2.Robotics\ECC Internal\19_Data_Sheets_new"

class DTGenerator:
    def __init__(self, config):
        self.config = config

    def generate_dt(self, wo_number, e_number, usb_path, ro_tools, snack_bar=None):

        # Find the folder on the USB drive

        folder_name = f"{wo_number}_{e_number}"
        folder_path = os.path.join(usb_path, folder_name)
        if not os.path.exists(folder_path):
            return False, f"Folder not found: {folder_path}"
        
        # Find sysmast.sv

        sv_path = os.path.join(folder_path, "sysmast.sv")
        if not os.path.exists(sv_path):
            return False, f"sysmast.sv not found in {folder_path}"
        
        # Convert sv to txt
        txt_path = os.path.splitext(sv_path)[0] + ".txt"
        try:
            if not os.path.isfile(KCONVARS_PATH):
                return False, f"kconvars.exe not found! Expected path: {KCONVARS_PATH}"
            command = [KCONVARS_PATH, sv_path, txt_path]
            # portable PATH
            portable_dirs = [
                os.path.join(BASE_DIR, '..', "utils", "WinOLPC", "bin"),
                os.path.join(BASE_DIR, '..', "utils", "ROBOGUIDE", "bin"),
                os.path.join(BASE_DIR, '..', "utils", "Shared", "Utilities"),
            ]
            env = os.environ.copy()
            env["PATH"] = os.pathsep.join([os.path.abspath(p) for p in portable_dirs]) + os.pathsep + env.get("PATH", "")
            proc = subprocess.run(
                command,
                capture_output=True,
                text=True,
                cwd=os.path.dirname(KCONVARS_PATH),
                creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0),
                env=env
            )
            if os.path.exists(txt_path):
                pass
            else:
                alt_out_path = os.path.join(os.path.dirname(KCONVARS_PATH), os.path.basename(txt_path))
                if os.path.exists(alt_out_path):
                    txt_path = alt_out_path
                else:
                    return False, f"Failed to convert sysmast.sv: {proc.stderr or proc.stdout or 'No txt file created.'}"
        except Exception as ex:
            return False, f"Error running kconvars: {ex}"
        
        # Extract array from txt

        try:
            with open(txt_path, encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()
            arr_values = []
            arr_start = False
            for i, line in enumerate(lines):
                if "Field: $DMR_GRP[1].$MASTER_COUN" in line:
                    arr_start = True
                    
                    for j in range(1, 10):
                        if i + j < len(lines):
                            match = re.search(r"\[\d+\]\s*=\s*(-?\d+)", lines[i + j])
                            if match:
                                arr_values.append(int(match.group(1)))
                    break
            if len(arr_values) != 9:
                return False, 
        except Exception as ex:
            return False, f"Error reading txt: {ex}"
        
        # Find DT file via ro_tools

        dt_path = None
        try:
            found, msg = ro_tools.find_dt_file_path(e_number)
            if not found or not msg:
                return False, f"DT file not found for {e_number}: {msg}"
            dt_path = msg
        except Exception as ex:
            return False, f"Error finding DT file: {ex}"
        
        # Open DT file, replace values, save to target folder

        try:
            import win32com.client
            base_name = os.path.basename(dt_path)
            save_path = os.path.join(DT_TARGET_DIR, base_name)
            excel = win32com.client.Dispatch("Excel.Application")
            excel.Visible = False
            wb = excel.Workbooks.Open(dt_path)
            ws = wb.Worksheets(1)  # First sheet
            for idx, val in enumerate(arr_values):
                ws.Range(f"F{22+idx}").Value = val
            wb.SaveAs(save_path)
            wb.Close(False)
            excel.Quit()
            # Open the ready file in Excel
            os.startfile(save_path)
        except Exception as ex:
            return False, f"Error editing/saving Excel via COM: {ex}"
        return True, f"DT file updated and saved to {save_path} (opened in Excel)"

