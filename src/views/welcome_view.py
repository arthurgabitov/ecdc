import flet as ft
from src.controllers.station_controller import StationController

class WelcomeView:
    def __init__(self, page: ft.Page, controller: StationController, on_complete):
        self.page = page
        self.controller = controller
        self.on_complete = on_complete

        self.welcome_text = ft.Text(
            "Welcome to Station App",
            size=40,
            text_align=ft.TextAlign.CENTER,
            weight=ft.FontWeight.BOLD
        )

        stations = self.controller.get_stations()
        self.station_selector = ft.Dropdown(
            label="Select Station",
            options=[ft.DropdownOption(f"Station {station_id}") for station_id in stations],
            on_change=self.handle_station_select,
            width=200
        )

        self.content = ft.Column(
            [   
            ft.Rive(
            "src/robot_looping_test.riv",
            placeholder=ft.ProgressBar(),
            width=300,
            height=200,
            ),
                self.welcome_text,
                self.station_selector
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=20
        )

        self.page_container = ft.Container(
            content=self.content,
            alignment=ft.alignment.center,
            expand=True,  
            bgcolor=ft.colors.WHITE
        )

    def handle_station_select(self, e):
        selected_station_id = int(e.control.value.split()[-1])
        self.on_complete(selected_station_id)

    def build(self):
        return self.page_container