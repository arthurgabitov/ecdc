import flet as ft
import asyncio
from controllers.station_controller import StationController

class TimerComponent:
    def __init__(self, page: ft.Page, station_id: str, spot_id: str, controller: StationController):
        self.page = page
        self.station_id = station_id
        self.spot_id = spot_id
        self.controller = controller
        self.timer_text = ft.Text("00:00", size=22)
        self.on_state_change = None
        self._task = None

        self.start_button = ft.FilledButton(
            content=ft.Row([
                ft.Icon(ft.Icons.PLAY_ARROW, color=ft.Colors.WHITE),
                ft.Text("Start  ", color=ft.Colors.WHITE)
            ]),
            on_click=self.start_pause,
            bgcolor=ft.Colors.GREEN_400,
        )

        self.stop_button = ft.FilledButton(
            content=ft.Row([
                ft.Icon(ft.Icons.STOP, color=ft.Colors.WHITE),
                ft.Text("Stop  ", color=ft.Colors.WHITE)
            ]),
            on_click=self.stop,
            bgcolor=ft.Colors.RED_400,
        )

        spot = self.controller.get_spot_data(int(station_id), spot_id)
        self.update_button_state(spot["running"], update=False)
        self.update_display(spot["elapsed_time"])
        if spot["running"]:
            self._task = self.page.run_task(self.update_timer)

    def update_display(self, elapsed_time):
        """Update timer display with formatted time"""
        total_elapsed = elapsed_time
        minutes = int(total_elapsed // 60)
        seconds = int(total_elapsed % 60)
        self.timer_text.value = f"{minutes:02d}:{seconds:02d}"
        if self.page:
            self.page.update()

    async def update_timer(self):
        """Periodically update timer while running"""
        spot = self.controller.get_spot_data(int(self.station_id), self.spot_id)
        while spot and spot["running"]:
            elapsed_time = self.controller.get_timer_value(int(self.station_id), self.spot_id)
            self.update_display(elapsed_time)
            await asyncio.sleep(1)
            spot = self.controller.get_spot_data(int(self.station_id), self.spot_id)
        self._task = None

    def update_button_state(self, running, update=True):
        """Update button appearance based on timer state"""
        if running:
            self.start_button.content = ft.Row([
                ft.Icon(ft.Icons.PAUSE, color=ft.Colors.WHITE),
                ft.Text("Pause  ", color=ft.Colors.WHITE)
            ])
            self.start_button.bgcolor = ft.Colors.ORANGE
        else:
            self.start_button.content = ft.Row([
                ft.Icon(ft.Icons.PLAY_ARROW, color=ft.Colors.WHITE),
                ft.Text("Start  ", color=ft.Colors.WHITE)
            ])
            self.start_button.bgcolor = ft.Colors.GREEN_400
        if update and self.start_button.page:
            self.start_button.update()

    def start_pause(self, e):
        """Handle start/pause button click"""
        spot = self.controller.get_spot_data(int(self.station_id), self.spot_id)
        if spot and not spot["running"]:
            self.controller.start_timer(int(self.station_id), self.spot_id)
            self.update_button_state(True)
            if not self._task:
                self._task = self.page.run_task(self.update_timer)
        elif spot:
            self.controller.pause_timer(int(self.station_id), self.spot_id)
            self.update_button_state(False)
            elapsed_time = self.controller.get_timer_value(int(self.station_id), self.spot_id)
            self.update_display(elapsed_time)
        if self.on_state_change:
            self.on_state_change()

    def stop(self, e):
        """Handle stop button click"""
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
        """Pause timer when page closes"""
        spot = self.controller.get_spot_data(int(self.station_id), self.spot_id)
        if spot and spot["running"]:
            self.controller.pause_timer(int(self.station_id), self.spot_id)
            self.update_button_state(False)
            elapsed_time = self.controller.get_timer_value(int(self.station_id), self.spot_id)
            self.update_display(elapsed_time)
            if self.on_state_change:
                self.on_state_change()

    def reset(self):
        """Reset the timer to initial state"""
        self.controller.reset_spot(int(self.station_id), self.spot_id)
        self.update_button_state(False)
        self.update_display(0)
        if self.on_state_change:
            self.on_state_change()
        spot = self.controller.get_spot_data(int(self.station_id), self.spot_id)

    def build_text(self):
        """Return just the timer text component"""
        return self.timer_text
        
    def build_buttons(self):
        """Return just the timer buttons in a row"""
        return ft.Row(
            [self.start_button, self.stop_button],
            alignment=ft.MainAxisAlignment.CENTER
        )

    def build(self):
        
        return ft.Column(
            [
                ft.Container(
                    content=self.timer_text,
                    alignment=ft.alignment.center,
                    expand=True
                ),
                ft.Container(
                    content=ft.Row(
                        [self.start_button, self.stop_button],
                        alignment=ft.MainAxisAlignment.CENTER
                    ),
                    alignment=ft.alignment.center,
                    expand=True
                )
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            expand=True
        )