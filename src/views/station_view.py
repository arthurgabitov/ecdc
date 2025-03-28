import flet as ft
from config import Config
from src.controllers.timer_component import TimerComponent
from .spot_view import Spot


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

    def build(self):
        app_settings = self.config.get_app_settings()
        spots_count = app_settings["spots"]
        columns_count = app_settings["columns"]

        if self.stations_count > 1:
            station_dropdown = ft.Dropdown(
                label="Station",
                value=f"Station {self.selected_station_id}",
                options=[ft.dropdown.Option(f"Station {station_id}") for station_id in self.controller.get_stations()],
                on_change=self.on_station_change,
                width=150,
                text_size=14,
                content_padding=ft.padding.symmetric(horizontal=12, vertical=6),
                border_radius=8,
                tooltip="Change Station"
            )
        else:
            station_dropdown = ft.Text(f"Station {self.selected_station_id}", size=14)

        if self.selected_station_id is not None:
            selected_station = self.controller.get_station_by_id(self.selected_station_id)
            spots = [
                Spot(f"Spot {i + 1}", str(self.selected_station_id), f"{self.selected_station_id}_{i + 1}", self.page, self.controller).build()
                for i in range(spots_count)
            ]

            spots_per_column = spots_count // columns_count
            extra_spots = spots_count % columns_count

            columns = []
            spot_index = 0
            for i in range(columns_count):
                current_column_spots = spots_per_column + (1 if i < extra_spots else 0)
                column_spots = spots[spot_index:spot_index + current_column_spots]
                spot_index += current_column_spots
                column = ft.Column(controls=column_spots, expand=True, spacing=10)
                columns.append(column)

            row = ft.Row(controls=columns, expand=True, spacing=10)

            if not self.station_container:
                self.station_container = ft.Column(
                    controls=[
                        ft.Container(content=station_dropdown, alignment=ft.alignment.center_left, padding=ft.padding.only(top=0, left=10)),
                        row
                    ],
                    expand=True,
                    spacing=10
                )

            return self.station_container

    def on_station_change(self, e):
        if self.stations_count > 1:
            new_station_id = int(e.control.value.split()[-1])
            if new_station_id != self.selected_station_id:
                self.update_module(0, station_id=new_station_id)