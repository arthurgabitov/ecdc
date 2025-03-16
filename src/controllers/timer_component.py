import flet as ft
import asyncio
from src.controllers.station_controller import StationController

class TimerComponent:
    def __init__(self, page: ft.Page, station_id: str, spot_id: int, controller: StationController):
        self.page = page
        self.station_id = station_id
        self.spot_id = spot_id
        self.controller = controller
        self.timer_text = ft.Text("00:00", size=32)
        self.on_state_change = None  # Callback для уведомления об изменении состояния

        self.start_button = ft.IconButton(
            content=ft.Row([ft.Icon(ft.Icons.PLAY_ARROW), ft.Text("Start")]),
            on_click=self.start_pause,
        )
        self.stop_button = ft.IconButton(
            content=ft.Row([ft.Icon(ft.Icons.STOP), ft.Text("Stop")]),
            on_click=self.stop
        )

        spot = self.controller.get_spot_data(int(station_id), spot_id)
        if spot and spot["running"]:
            self.start_button.content = ft.Row([ft.Icon(ft.Icons.PAUSE), ft.Text("Pause")])
            self.page.run_task(self.update_timer)

    def update_display(self, elapsed_time):
        total_elapsed = elapsed_time
        minutes = int(total_elapsed // 60)
        seconds = int(total_elapsed % 60)
        
        self.timer_text.value = f"{minutes:02d}:{seconds:02d}"
        self.page.update()

    async def update_timer(self):
        spot = self.controller.get_spot_data(int(self.station_id), self.spot_id)
        while spot and spot["running"]:
            elapsed_time = self.controller.get_timer_value(int(self.station_id), self.spot_id)
            self.update_display(elapsed_time)
            await asyncio.sleep(0.1)
            spot = self.controller.get_spot_data(int(self.station_id), self.spot_id)

    def start_pause(self, e):
        spot = self.controller.get_spot_data(int(self.station_id), self.spot_id)
        if spot and not spot["running"]:
            self.controller.start_timer(int(self.station_id), self.spot_id)
            self.start_button.content = ft.Row([ft.Icon(ft.Icons.PAUSE), ft.Text("Pause")])
            self.page.run_task(self.update_timer)
        elif spot:
            self.controller.pause_timer(int(self.station_id), self.spot_id)
            self.start_button.content = ft.Row([ft.Icon(ft.Icons.PLAY_ARROW), ft.Text("Start")])
            elapsed_time = self.controller.get_timer_value(int(self.station_id), self.spot_id)
            self.update_display(elapsed_time)
        if self.on_state_change:
            self.on_state_change()  # Уведомляем об изменении состояния

    def stop(self, e):
        spot = self.controller.get_spot_data(int(self.station_id), self.spot_id)
        if spot:
            elapsed_time = self.controller.get_timer_value(int(self.station_id), self.spot_id)
            labor_time = round(elapsed_time / 3600, 2)
            self.timer_text.value = f"Labor time: {labor_time} h"
            self.controller.stop_timer(int(self.station_id), self.spot_id)
            self.start_button.content = ft.Row([ft.Icon(ft.Icons.PLAY_ARROW), ft.Text("Start")])
            self.page.update()
            if self.on_state_change:
                self.on_state_change()  # Уведомляем об изменении состояния

    def pause_on_close(self):
        spot = self.controller.get_spot_data(int(self.station_id), self.spot_id)
        if spot and spot["running"]:
            self.controller.pause_timer(int(self.station_id), self.spot_id)
            elapsed_time = self.controller.get_timer_value(int(self.station_id), self.spot_id)
            self.update_display(elapsed_time)
            if self.on_state_change:
                self.on_state_change()  # Уведомляем об изменении состояния

    def build(self):
        return ft.Column(
            [
                self.timer_text,
                ft.Row(
                    [self.start_button, self.stop_button],
                    alignment=ft.MainAxisAlignment.CENTER
                )
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER
        )