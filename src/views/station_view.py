import flet as ft
from config import Config
from controllers.timer_component import TimerComponent
from .spot_view import Spot
from .top_bar import TopBar
from models.user_model import UserModel


class StationView:
    def __init__(self, page: ft.Page, controller, config: Config, selected_station_id: int, module_container: ft.Container, stations_count: int, update_module):
        self.page = page
        self.controller = controller
        self.config = config
        self.selected_station_id = selected_station_id
        self.module_container = module_container
        self.stations_count = stations_count
        self.update_module = update_module
        self.station_container = None
        self.timer = None
        self.user_sso = UserModel().get_user_by_windows_login() or "Unknown SSO"

    def build(self):
        app_settings = self.config.get_app_settings()
        spots_count = app_settings["spots"]
        columns_count = app_settings["columns"]

        # Удаляем station_dropdown из StationView
        self.station_dropdown = None

        if self.selected_station_id is not None:
            selected_station = self.controller.get_station_by_id(self.selected_station_id)
            station_title = ft.Text(selected_station["name"], size=22, weight=ft.FontWeight.BOLD)
            
            spots = [
                Spot(f"Spot {i + 1}", str(self.selected_station_id), f"{self.selected_station_id}_{i + 1}", self.page, self.controller).build()
                for i in range(spots_count)
            ]
            
            columns = []
            spot_index = 0
            for i in range(columns_count):
                current_column_spots = spots_count // columns_count + (1 if i < spots_count % columns_count else 0)
                column_spots = spots[spot_index:spot_index + current_column_spots]
                spot_index += current_column_spots
                column = ft.Column(controls=column_spots, expand=True, spacing=10)
                columns.append(column)

            row = ft.Row(controls=columns, expand=True, spacing=10)

            if not self.station_container:
                controls = []
                controls.append(station_title)
                controls.append(row)
                self.station_container = ft.Column(
                    controls=controls,
                    expand=True,
                    spacing=10
                )

            return self.station_container

    def on_station_change(self, e):
        if self.stations_count > 1:
            new_station_id = int(e.control.value.split()[-1])
            if new_station_id != self.selected_station_id:
                self.update_module(0, station_id=new_station_id)