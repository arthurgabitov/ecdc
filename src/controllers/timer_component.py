import flet as ft
import asyncio
from src.controllers.station_controller import StationController

class TimerComponent:
    def __init__(self, page: ft.Page, station_id: str, spot_id: str, controller: StationController):
        self.page = page
        self.station_id = station_id
        self.spot_id = spot_id
        self.controller = controller
        self.timer_text = ft.Text("00:00", size=28)
        self.on_state_change = None

        self.start_button = ft.FilledButton(
            content=ft.Row([
                ft.Icon(ft.Icons.PLAY_ARROW, color=ft.colors.WHITE),
                ft.Text("Start  ", color=ft.colors.WHITE)
            ]),
            on_click=self.start_pause,
            bgcolor=ft.colors.GREEN_400,
        )

        self.stop_button = ft.FilledButton(
            content=ft.Row([
                ft.Icon(ft.Icons.STOP, color=ft.colors.WHITE),
                ft.Text("Stop  ", color=ft.colors.WHITE)
            ]),
            on_click=self.stop,
            bgcolor=ft.colors.RED_400,
        )

        spot = self.controller.get_spot_data(int(station_id), spot_id)
        self.update_button_state(spot["running"], update=False)  
        if spot["running"]:
            self.page.run_task(self.update_timer)
        else:
            self.update_display(spot["elapsed_time"])

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
            await asyncio.sleep(1)
            spot = self.controller.get_spot_data(int(self.station_id), self.spot_id)

    def update_button_state(self, running, update=True):
        if running:
            self.start_button.content = ft.Row([
                ft.Icon(ft.Icons.PAUSE, color=ft.colors.WHITE),
                ft.Text("Pause  ", color=ft.colors.WHITE)
            ])
            self.start_button.bgcolor = ft.colors.ORANGE
        else:
            self.start_button.content = ft.Row([
                ft.Icon(ft.Icons.PLAY_ARROW, color=ft.colors.WHITE),
                ft.Text("Start  ", color=ft.colors.WHITE)
            ])
            self.start_button.bgcolor = ft.colors.GREEN_400
        if update and self.start_button.page: 
            self.start_button.update()

    def start_pause(self, e):
        spot = self.controller.get_spot_data(int(self.station_id), self.spot_id)
        if spot and not spot["running"]:
            self.controller.start_timer(int(self.station_id), self.spot_id)
            self.update_button_state(True)
            self.page.run_task(self.update_timer)
        elif spot:
            self.controller.pause_timer(int(self.station_id), self.spot_id)
            self.update_button_state(False)
            elapsed_time = self.controller.get_timer_value(int(self.station_id), self.spot_id)
            self.update_display(elapsed_time)
        if self.on_state_change:
            self.on_state_change()

    def stop(self, e):
        spot = self.controller.get_spot_data(int(self.station_id), self.spot_id)
        if spot:
            elapsed_time = self.controller.get_timer_value(int(self.station_id), self.spot_id)
            labor_time = round(elapsed_time / 3600, 2)
            self.timer_text.value = f"Labor time: {labor_time} h"
            self.controller.stop_timer(int(self.station_id), self.spot_id)
            self.update_button_state(False)
            self.page.update()
            if self.on_state_change:
                self.on_state_change()

    def pause_on_close(self):
        spot = self.controller.get_spot_data(int(self.station_id), self.spot_id)
        if spot and spot["running"]:
            self.controller.pause_timer(int(self.station_id), self.spot_id)
            self.update_button_state(False)
            elapsed_time = self.controller.get_timer_value(int(self.station_id), self.spot_id)
            self.update_display(elapsed_time)
            if self.on_state_change:
                self.on_state_change()

    def reset(self):
        # Останавливаем таймер
        self.controller.stop_timer(int(self.station_id), self.spot_id)
        # Сбрасываем время через данные спота
        spot = self.controller.get_spot_data(int(self.station_id), self.spot_id)
        spot["elapsed_time"] = 0
        self.controller.save_timers_state()  # Сохраняем изменения
        # Обновляем UI
        self.update_button_state(False)
        self.update_display(0)
        if self.on_state_change:
            self.on_state_change()

    def build(self):
        return ft.Column(
            [
                self.timer_text,
                ft.Row(
                    [self.start_button, self.stop_button],
                    alignment=ft.MainAxisAlignment.CENTER
                )
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )