import flet as ft
import os
from models.user_model import UserModel
from styles import FONT_SIZE_MEDIUM, FONT_SIZE_NORMAL

class SettingsView:
    def __init__(self, page: ft.Page):
        self.page = page
        self.user_sso = UserModel().get_user_by_windows_login() or "Unknown SSO"
        
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

    def build(self, config=None):
        if config is None:
            raise ValueError("Config object must be provided to SettingsView.build()")
        self.config = config  
        test_mode_enabled = config.is_dashboard_test_mode_enabled()

        dashboard_test_mode = ft.Checkbox(
            label="Dashboard test mode",
            value=test_mode_enabled,
            on_change=lambda e: self.on_test_mode_change(e, config)
        )
        self.dashboard_test_mode_checkbox = dashboard_test_mode

        version = self.get_version()
        
        return ft.Column([
            ft.Text("Settings", size=20),
            ft.Text(f"Current Version: {version}", size=16),
            dashboard_test_mode,
        ], spacing=10, alignment=ft.MainAxisAlignment.START, expand=True)
    
    def on_test_mode_change(self, e, config=None):
        if config is None:
            config = getattr(self, 'config', None)
        if config:
            config.set_dashboard_test_mode(e.control.value)
            if hasattr(self.page, 'update_module'):
                self.page.update_module(0)
            else:
                self.page.update()