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

    def build(self, config=None):
        if config is None:
            raise ValueError("Config object must be provided to SettingsView.build()")
        test_mode_enabled = config.is_dashboard_test_mode_enabled()

        dashboard_test_mode = ft.Checkbox(
            label="Dashboard test mode",
            value=test_mode_enabled,
            on_change=self.on_test_mode_change
        )

        version = self.get_version()
        return ft.Column(
            [
                ft.Text("Settings", size=20),
                ft.Text(f"Current Version: {version}", size=16),
                dashboard_test_mode,
            ],
            spacing=10,
            alignment=ft.MainAxisAlignment.START,
            expand=True
        )
    
    def on_test_mode_change(self, e):
        # config must be passed explicitly now
        pass