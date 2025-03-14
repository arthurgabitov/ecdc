import flet as ft
from src.controllers.station_controller import StationController
import asyncio
class WelcomeView:
    def __init__(self, page: ft.Page, controller: StationController, on_complete):
        self.page = page
        self.controller = controller
        self.on_complete = on_complete

        self.welcome_text = ft.Text(
            "Welcome to ECDC Dashboard",
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

        self.container = ft.Container(
            content=ft.Column(
                [
                    self.welcome_text,
                    self.station_selector
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=20
            ),
            alignment=ft.alignment.center,
            expand=True,
            opacity=1.0,  # Начальная непрозрачность
            animate_opacity=300  # Длительность анимации в миллисекундах
        )

    async def handle_station_select(self, e):
        """Обработчик выбора станции с анимацией."""
        selected_station_id = int(e.control.value.split()[-1])
        
        # Запускаем анимацию затухания
        self.container.opacity = 0.0
        self.container.update()
        await asyncio.sleep(0.3)  # Ждём завершения анимации (300 мс)

        # Очищаем страницу и переходим дальше
        self.page.controls.clear()
        self.on_complete(selected_station_id)
        self.page.update()

    def build(self):
        return self.container