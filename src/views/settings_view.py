import flet as ft
import os

class SettingsView:
    def __init__(self, page: ft.Page):
        self.page = page

    def get_version(self):
        
        version_file_path = os.path.join(os.path.dirname(__file__), '..', '..', 'version.txt')
        try:
            with open(version_file_path, 'r') as f:
                version = f.read().strip()
                return version
        except FileNotFoundError:
            return "Version not found"
        except Exception as e:
            return f"Error reading version: {e}"

    def build(self):
        version = self.get_version()
        return ft.Column(
            [
                ft.Text("Settings Module", size=20),
                ft.Text(f"Current Version: {version}", size=16)
            ],
            spacing=10,
            alignment=ft.MainAxisAlignment.START,
            expand=True
        )