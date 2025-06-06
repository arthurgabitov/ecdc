import flet as ft
import asyncio
from controllers.station_controller import StationController

class TimerComponent:
    def __init__(self, page: ft.Page, station_id: str, spot_id: str, controller: StationController):
        self.page = page
        self.station_id = station_id
        self.spot_id = spot_id
        self.controller = controller
        icon_size = 32
        btn_size = 48
        self.timer_text = ft.Text(
            "00:00",
            size=32,
            color=ft.Colors.GREY,
            weight=ft.FontWeight.W_300,
            height=None,
            font_family="JetBrains Mono, Fira Mono, Consolas, monospace",  # Современный моноширинный шрифт
            text_align=ft.TextAlign.CENTER,
            no_wrap=False,  # Разрешить перенос
            max_lines=2     # До двух строк
        )
        self.start_button = ft.IconButton(
            icon=ft.Icons.PLAY_ARROW,
            icon_color=ft.Colors.WHITE,
            bgcolor=ft.Colors.GREEN_400,
            icon_size=icon_size,
            width=btn_size,
            height=btn_size,
            on_click=self.start_pause,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=100),
                padding=0,
            ),
            tooltip="Start/Pause"
        )

        self.stop_button = ft.IconButton(
            icon=ft.Icons.STOP,
            icon_color=ft.Colors.WHITE,
            bgcolor=ft.Colors.RED_400,
            icon_size=icon_size,
            width=btn_size,
            height=btn_size,
            on_click=self.stop,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=100),
                padding=0,
            ),
            tooltip="Stop"
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
        spot = self.controller.get_spot_data(int(self.station_id), self.spot_id)
        # Если таймер остановлен и показывается Labor time, скрываем кнопки
        if hasattr(self, 'show_labor_time') and self.show_labor_time:
            self.timer_text.value = self.labor_time_text
            self.timer_text.size = 24  # Меньше размер для длинного текста
            self.start_button.visible = False
            self.stop_button.visible = False
        else:
            self.timer_text.value = f"{minutes:02d}:{seconds:02d}"
            self.timer_text.size = 32  # Обычный размер для таймера
            if spot and spot["running"]:
                self.timer_text.color = ft.Colors.BLACK
            else:
                self.timer_text.color = ft.Colors.GREY
            self.start_button.visible = True
            self.stop_button.visible = True
        if self.page:
            self.page.update()

    async def update_timer(self):
        spot = self.controller.get_spot_data(int(self.station_id), self.spot_id)
        self.update_display(spot["elapsed_time"])
        while spot and spot["running"]:
            elapsed_time = self.controller.get_timer_value(int(self.station_id), self.spot_id)
            self.update_display(elapsed_time)
            await asyncio.sleep(1)
            spot = self.controller.get_spot_data(int(self.station_id), self.spot_id)
        self._task = None

    def update_button_state(self, running, update=True):
        """Update button appearance based on timer state"""
        if running:
            self.start_button.icon = ft.Icons.PAUSE
            self.start_button.bgcolor = ft.Colors.ORANGE
        else:
            self.start_button.icon = ft.Icons.PLAY_ARROW
            self.start_button.bgcolor = ft.Colors.GREEN_400
        if update and self.start_button.page:
            self.start_button.update()

    def start_pause(self, e):
        spot = self.controller.get_spot_data(int(self.station_id), self.spot_id)
        if spot and not spot["running"]:
            self.controller.start_timer(int(self.station_id), self.spot_id)
            # --- Auto-set status to 'In Progress' if currently 'Unblocked' ---
            if spot["status"] == "Unblocked":
                self.controller.set_spot_status(int(self.station_id), self.spot_id, "In Progress")
            # Принудительно обновляем данные spot после старта
            spot = self.controller.get_spot_data(int(self.station_id), self.spot_id)
            self.update_button_state(True)
            self.update_display(spot["elapsed_time"])
            # Всегда запускаем update_timer
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
            self.labor_time_text = f"Labor time: {labor_time} h"
            self.show_labor_time = True
            self.timer_text.value = self.labor_time_text
            self.timer_text.color = ft.Colors.BLACK  # Always show labor time in black
            self.start_button.visible = False
            self.stop_button.visible = False
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
        self.show_labor_time = False
        self.labor_time_text = ""
        self.update_display(0)
        if self.on_state_change:
            self.on_state_change()
        spot = self.controller.get_spot_data(int(self.station_id), self.spot_id)

    def build_buttons(self):
        """Вернуть только таймер и кнопки управления в одну строку, с адаптивной шириной и переносом"""
        return ft.Row(
            [
                ft.Container(self.timer_text, width=270, alignment=ft.alignment.center, bgcolor=None, padding=ft.padding.only(right=8)),  # увеличена ширина
                self.start_button,
                self.stop_button
            ],
            alignment=ft.MainAxisAlignment.START,
            spacing=12,
            wrap=True  # разрешаем перенос
        )

    def build(self):
        return ft.Container(
            content=self.build_buttons(),
            alignment=ft.alignment.center_left,
            expand=True,
            padding=ft.padding.all(0),
            bgcolor=None,
        )