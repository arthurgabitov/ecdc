import flet as ft
import asyncio
from controllers.station_controller import StationController
from models.user_model import UserModel

class WelcomeView:
    def __init__(self, page: ft.Page, controller: StationController, on_complete):
        self.page = page
        self.controller = controller
        self.on_complete = on_complete
        self.user_model = UserModel()
        self.selected_user_id = None
        
        self.welcome_text = ft.Text(
            "Station App",
            size=40,
            text_align=ft.TextAlign.CENTER,
            weight=ft.FontWeight.BOLD
        )

        stations = self.controller.get_stations()
        self.stations_count = len(stations)
        
        # Create user dropdown (initially empty)
        self.user_selector = ft.Dropdown(
            label="Your SSO",
            options=[],
            on_change=self.handle_user_select,
            width=300,
            hint_text="Loading users..."
        )

        if self.stations_count == 1:
            self.station_selector = ft.Dropdown(
                label="Select Station",
                options=[ft.dropdown.Option(f"Station {station_id}") for station_id in stations],
                on_change=self.handle_station_select,
                width=200
            )
            self.auto_transition_needed = False
        else:
            self.station_selector = ft.Dropdown(
                label="Select Station",
                options=[ft.dropdown.Option(f"Station {station_id}") for station_id in stations],
                on_change=self.handle_station_select,
                width=200
            )
            self.auto_transition_needed = False

        self.continue_button = ft.ElevatedButton(
            "Login",
            on_click=self.handle_continue,
            disabled=True,
            width=200
        )

        self.content = ft.Column(
            [   
                self.welcome_text,
                ft.Row([
                    self.user_selector
                ], alignment=ft.MainAxisAlignment.CENTER),
                self.station_selector,
                self.continue_button
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=20
        )        
        
        self.page_container = ft.Container(
            content=self.content,
            alignment=ft.alignment.center,
            expand=True,
            bgcolor=ft.Colors.WHITE
        )
        
        # Try to auto-detect user by Windows login
        windows_user = self.user_model.get_user_by_windows_login()
        if windows_user and windows_user != "Unknown SSO":
            self.selected_user_id = windows_user
            self.user_selector.options = [
                ft.dropdown.Option(key=windows_user, text=windows_user)
            ]
            self.user_selector.value = windows_user
            self.user_selector.hint_text = "User detected automatically"
            self.continue_button.disabled = False
            self.page.update()
        else:
            self.user_selector.options = [
                ft.dropdown.Option(key="none", text="User not detected")
            ]
            self.user_selector.value = "none"
            self.user_selector.hint_text = "User not found. Contact your administrator."
            self.continue_button.disabled = True
            self.page.update()

    async def load_users(self):
        # Больше не нужен, оставляем пустым для совместимости
        pass

    def handle_user_select(self, e):
        """User selection handler"""
        self.selected_user_id = e.control.value
        
        # Allow continue only if user is selected
        if self.selected_user_id:
            self.continue_button.disabled = False
            if self.stations_count == 1:
                # If only one station, enable auto transition
                self.auto_transition_needed = True
            self.page.update()

    def handle_station_select(self, e):
        """Station selection handler"""
        value = e.control.value
        if value == "FTL Station":
            self.station_id = "FTL"
        else:
            self.station_id = value.split()[-1]
        self.continue_button.disabled = False
        self.page.update()

    def handle_continue(self, e):
        """Continue button handler"""
        # selected_user_id is now login, not id
        if self.selected_user_id and self.selected_user_id != "none":
            # If multiple stations, use selected station
            if self.stations_count > 1 and hasattr(self, 'station_id'):
                self.on_complete(self.station_id, self.selected_user_id)
            # Otherwise use the only station
            elif self.stations_count == 1:
                self.on_complete(self.station_id, self.selected_user_id)

    def build(self):
        return self.page_container

    async def run_auto_transition(self):
        if self.auto_transition_needed and self.selected_user_id:
            await asyncio.sleep(1)
            self.on_complete(self.station_id, self.selected_user_id)