import flet as ft
import asyncio
import os
from src.controllers.station_controller import StationController

class WelcomeView:
    def __init__(self, page: ft.Page, controller: StationController, on_complete):
        self.page = page
        self.controller = controller
        self.on_complete = on_complete

        self.welcome_text = ft.Text(
            "Station App",
            size=40,
            text_align=ft.TextAlign.CENTER,
            weight=ft.FontWeight.BOLD
        )

        stations = self.controller.get_stations()
        self.stations_count = len(stations)
        
        # Determine if running in web mode
        is_web = getattr(page, "web", False)
        
        # Use different animation approach depending on mode
        if is_web:
            # For web mode: Use Lottie animation (better web support)
            self.animation = ft.LottieAnimation(
                "https://assets6.lottiefiles.com/packages/lf20_ghs9gkeh.json",
                width=300,
                height=200,
                animate=True,
                repeat=True,
                animate_automatically=True
            )
        else:
            # For desktop mode: Use Rive animation
            animation_path = os.path.join(os.path.dirname(__file__), "..", "robot_looping_test.riv")
            if not os.path.exists(animation_path):
                animation_path = "src/robot_looping_test.riv"
            
            self.animation = ft.Rive(
                animation_path,
                placeholder=ft.ProgressBar(),
                width=300,
                height=200
            )

        if self.stations_count == 1:
            self.station_selector = ft.Container()  
            self.auto_transition_needed = True
            self.station_id = stations[0]
        else:
            self.station_selector = ft.Dropdown(
                label="Select Station",
                options=[ft.dropdown.Option(f"Station {station_id}") for station_id in stations],
                on_change=self.handle_station_select,
                width=200
            )
            self.auto_transition_needed = False

        self.content = ft.Column(
            [   
                self.animation,
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
        if isinstance(self.station_selector, ft.Dropdown):
            selected_station_id = int(e.control.value.split()[-1])
            
            self.on_complete(selected_station_id)

    def build(self):
        return self.page_container

    async def run_auto_transition(self):
        if self.auto_transition_needed:
            await asyncio.sleep(1)
            self.on_complete(self.station_id)