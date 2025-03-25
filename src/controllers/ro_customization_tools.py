import asyncio
import flet as ft
import os
import re
from config import Config

class ROCustomizationController:
    def __init__(self, config: Config):
        self.config = config

    async def search_and_copy_order_file(self, wo_number: str, page, show_snack_bar=None):
        print(f"Searching for WO Number: {wo_number}")
        if not re.match(r"^\d{8}$", wo_number):
            print("WO Number invalid - must be 8 digits")
            if show_snack_bar:
                show_snack_bar("WO Number must be an 8-digit number")
            return

        search_dir = os.path.normpath(self.config.get_customization_settings()["search_directory"])
        print(f"Checking directory: {search_dir}")
        if not os.path.exists(search_dir):
            print(f"Directory {search_dir} not found")
            if show_snack_bar:
                show_snack_bar(f"Directory {search_dir} not found")
            return

        found_file = None
        print("Files in directory:")
        for filename in os.listdir(search_dir):
            print(f" - {filename}")
            if wo_number in filename and filename.endswith(".dat"):
                found_file = os.path.join(search_dir, filename)
                print(f"Found file: {found_file}")
                break

        if not found_file:
            print(f"No file found for WO Number {wo_number}")
            if show_snack_bar:
                show_snack_bar(f"No file found for WO Number {wo_number}")
            return

        usb_drive = self.find_usb_drive()
        if not usb_drive:
            print("No USB drive detected")
            if show_snack_bar:
                show_snack_bar("No USB drive detected")
            return

        target_file = os.path.join(usb_drive, "orderfil.dat")
        try:
            with open(found_file, 'r', encoding='utf-8') as source:
                content = source.read()
            with open(target_file, 'w', encoding='utf-8') as target:
                target.write(content)
            print(f"File copied to {target_file}")
            if show_snack_bar:
                show_snack_bar(f"File copied to {target_file}")
        except Exception as e:
            print(f"Error copying file: {str(e)}")
            if show_snack_bar:
                show_snack_bar(f"Error copying file: {str(e)}")

    def find_usb_drive(self):
        import string
        from pathlib import Path

        for drive_letter in string.ascii_uppercase[3:]:
            drive_path = f"{drive_letter}:\\"
            if os.path.exists(drive_path):
                try:
                    import ctypes
                    kernel32 = ctypes.windll.kernel32
                    drive_type = kernel32.GetDriveTypeW(drive_path)
                    if drive_type == 2:  # DRIVE_REMOVABLE
                        return drive_path
                except Exception:
                    continue
        return None