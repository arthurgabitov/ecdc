import flet as ft
import asyncio
from controllers.station_controller import StationController
from styles import BG_BUTTON_GREEN, BG_BUTTON_RED, BG_BUTTON_ORANGE, FONT_WEIGHT_BOLD, FONT_WEIGHT_NORMAL, FONT_SIZE_LARGE, FONT_SIZE_NORMAL, TEXT_DEFAULT, TEXT_SECONDARY

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
            size=FONT_SIZE_LARGE,
            color=TEXT_SECONDARY,
            weight=FONT_WEIGHT_NORMAL,
            height=None,
            font_family="Roboto-Light",  # Use Roboto-Light for timer
            text_align=ft.TextAlign.CENTER,
            no_wrap=False,  # Allow text wrapping
            max_lines=2     # Limit to two lines
        )
        self.start_button = ft.IconButton(
            icon=ft.Icons.PLAY_ARROW,
            icon_color=ft.Colors.WHITE,
            bgcolor=BG_BUTTON_GREEN,
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
            bgcolor=BG_BUTTON_RED,
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

        # Create mini-buttons only once
        self.mini_start_button = ft.IconButton(
            icon=None,  # Set in build_buttons
            icon_color=ft.Colors.WHITE,
            bgcolor=None,  # Set in build_buttons
            icon_size=20,
            width=32,
            height=32,
            on_click=self.start_pause,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=100),
                padding=0,
            ),
            tooltip="Start/Pause"
        )
        self.mini_stop_button = ft.IconButton(
            icon=ft.Icons.STOP,
            icon_color=ft.Colors.WHITE,
            bgcolor=ft.Colors.RED_400,
            icon_size=20,
            width=32,
            height=32,
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
        total_elapsed = int(elapsed_time)
        hours = total_elapsed // 3600
        minutes = (total_elapsed % 3600) // 60
        spot = self.controller.get_spot_data(int(self.station_id), self.spot_id)
        # If timer is stopped and labor time is shown, hide all buttons
        if hasattr(self, 'show_labor_time') and self.show_labor_time:
            self.timer_text.value = self.labor_time_text
            self.timer_text.size = FONT_SIZE_NORMAL  # Use smaller font for long text
            # Hide main buttons
            self.start_button.visible = False
            self.stop_button.visible = False
            # Hide mini-buttons if they exist
            if hasattr(self, 'mini_start_button'):
                self.mini_start_button.visible = False
            if hasattr(self, 'mini_stop_button'):
                self.mini_stop_button.visible = False
        else:
            self.timer_text.value = f"{hours:02d}:{minutes:02d}"
            self.timer_text.size = FONT_SIZE_LARGE  # Use normal font size for timer
            if spot and spot["running"]:
                self.timer_text.color = ft.Colors.BLACK
            else:
                self.timer_text.color = TEXT_SECONDARY
            # Show main buttons
            self.start_button.visible = True
            self.stop_button.visible = True
            # Show mini-buttons if they exist
            if hasattr(self, 'mini_start_button'):
                self.mini_start_button.visible = True
            if hasattr(self, 'mini_stop_button'):
                self.mini_stop_button.visible = True
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
            self.start_button.bgcolor = BG_BUTTON_ORANGE
            # Update mini-button appearance if it exists
            if hasattr(self, 'mini_start_button'):
                self.mini_start_button.icon = ft.Icons.PAUSE
                self.mini_start_button.bgcolor = BG_BUTTON_ORANGE
        else:
            self.start_button.icon = ft.Icons.PLAY_ARROW
            self.start_button.bgcolor = BG_BUTTON_GREEN
            # Update mini-button appearance if it exists
            if hasattr(self, 'mini_start_button'):
                self.mini_start_button.icon = ft.Icons.PLAY_ARROW
                self.mini_start_button.bgcolor = BG_BUTTON_GREEN
        if update:
            # Update all buttons if they are added to the page
            if self.start_button.page:
                self.start_button.update()
            if hasattr(self, 'mini_start_button') and self.mini_start_button.page:
                self.mini_start_button.update()

    def start_pause(self, e):
        spot = self.controller.get_spot_data(int(self.station_id), self.spot_id)
        if spot and not spot["running"]:
            self.controller.start_timer(int(self.station_id), self.spot_id)
            # --- Auto-set status to 'In Progress' if currently 'Unblocked' ---
            if spot["status"] == "Unblocked":
                self.controller.set_spot_status(int(self.station_id), self.spot_id, "In Progress")
            # Force update spot data after start
            spot = self.controller.get_spot_data(int(self.station_id), self.spot_id)
            self.update_button_state(True)
            self.update_display(spot["elapsed_time"])
            # Always start update_timer
            self._task = self.page.run_task(self.update_timer)
        elif spot:
            self.controller.pause_timer(int(self.station_id), self.spot_id)
            self.update_button_state(False)
            elapsed_time = self.controller.get_timer_value(int(self.station_id), self.spot_id)
            self.update_display(elapsed_time)

        # Force update of UI components
        if hasattr(self, 'mini_start_button') and self.mini_start_button.page:
            self.mini_start_button.update()
        if hasattr(self, 'mini_stop_button') and self.mini_stop_button.page:
            self.mini_stop_button.update()

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

            # Hide main buttons
            self.start_button.visible = False
            self.stop_button.visible = False
            # Hide mini-buttons if they exist
            if hasattr(self, 'mini_start_button'):
                self.mini_start_button.visible = False
                if self.mini_start_button.page:
                    self.mini_start_button.update()
            if hasattr(self, 'mini_stop_button'):
                self.mini_stop_button.visible = False
                if self.mini_stop_button.page:
                    self.mini_stop_button.update()

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

            # Update mini-buttons if they exist
            if hasattr(self, 'mini_start_button') and self.mini_start_button.page:
                self.mini_start_button.update()
            if hasattr(self, 'mini_stop_button') and self.mini_stop_button.page:
                self.mini_stop_button.update()

            if self.on_state_change:
                self.on_state_change()

    def reset(self):
        """Reset the timer to initial state"""
        self.controller.reset_spot(int(self.station_id), self.spot_id)
        self.update_button_state(False)
        self.show_labor_time = False
        self.labor_time_text = ""

        # Show mini-buttons if they exist
        if hasattr(self, 'mini_start_button'):
            self.mini_start_button.visible = True
            if self.mini_start_button.page:
                self.mini_start_button.update()
        if hasattr(self, 'mini_stop_button'):
            self.mini_stop_button.visible = True
            if self.mini_stop_button.page:
                self.mini_stop_button.update()

        self.update_display(0)
        if self.on_state_change:
            self.on_state_change()

    def build_buttons(self):
        # Synchronize mini-button icon and color with the main button
        self.mini_start_button.icon = self.start_button.icon
        self.mini_start_button.bgcolor = self.start_button.bgcolor
        # Timer and buttons are always in one row, elements shrink when compressed
        return ft.Row(
            [
                ft.Container(
                    self.timer_text,
                    alignment=ft.alignment.center,
                    bgcolor=None,
                    padding=ft.padding.only(right=4)
                ),
                self.mini_start_button,
                self.mini_stop_button
            ],
            alignment=ft.MainAxisAlignment.START,
            spacing=4,
            wrap=False  # Always in one row
        )

    def build(self):
        return ft.Container(
            content=self.build_buttons(),
            alignment=ft.alignment.center_left,
            expand=False,
            padding=ft.padding.all(0),
            bgcolor=None,
        )

    def restore_from_state(self):
        spot = self.controller.get_spot_data(int(self.station_id), self.spot_id)
        self.update_button_state(spot["running"], update=True)
        self.update_display(spot["elapsed_time"])
        # Не запускать update_timer автоматически, только если running
        # (иначе таймеры будут тикать после рестарта, если не нужно)
        # Кнопки и текст всегда будут в актуальном состоянии