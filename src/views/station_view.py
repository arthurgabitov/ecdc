import flet as ft
from config import Config
from src.controllers.timer_component import TimerComponent

spot_style: dict = {
    "main": {
        "expand": True,
        "bgcolor": ft.Colors.WHITE60,  # Исходный цвет по умолчанию
        "border_radius": 10,
        "border": ft.border.all(width=0.5, color=ft.Colors.GREY_500),
        "ink": True
    },
}

class Spot:
    def __init__(self, name: str, station_id: str, spot_id: int, page: ft.Page, controller):
        self.name = name
        self.station_id = station_id
        self.spot_id = spot_id
        self.page = page
        self.controller = controller
        self.timer = TimerComponent(page, station_id, spot_id, controller)
        self.label = f"Spot {self.spot_id % 100}"

        # Создаём Column с тремя частями: верх, середина, низ
        self.content = ft.Column(
            controls=[
                ft.Divider(height=20, color="transparent"),
                ft.Text(self.label, size=18, text_align=ft.TextAlign.CENTER),
                ft.Container(expand=1),  
                  
                ft.Container(
                    content=self.timer.build(),
                    expand=1,  
                    alignment=ft.alignment.bottom_center  # Таймер внизу
                ),
            ],
            expand=True,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=0  
        )

        self.on_click = self.open_dialog

        self.dlg_modal = ft.AlertDialog(
            modal=False,
            title=ft.Text("Example"),
            content=ft.Text("Here something with WO and SW"),
            actions=[
                ft.TextField(label="Enter WO number"),
                ft.Divider(height=15, color="transparent"),
                ft.TextButton("Exit", on_click=self.handle_close),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        self.container = ft.Container(
            content=self.content,
            **spot_style["main"],
            on_click=self.on_click
        )
        self.update_color()

        # Подписываем таймер на обновление цвета при изменении состояния
        self.timer.on_state_change = self.update_color

    def open_dialog(self, e):
        if not self.dlg_modal.open:
            if self.dlg_modal not in self.page.overlay:
                self.page.overlay.append(self.dlg_modal)
            self.dlg_modal.open = True
            self.page.update()

    def handle_close(self, e):
        if self.dlg_modal.open:
            self.dlg_modal.open = False
            self.page.update()

    def update_color(self):
        """Обновляет цвет спота в зависимости от состояния таймера"""
        spot = self.controller.get_spot_data(int(self.station_id), self.spot_id)
        elapsed_time = self.controller.get_timer_value(int(self.station_id), self.spot_id)
        
        if spot and spot["running"]:  # Запущен
            self.container.bgcolor = ft.Colors.WHITE60
        elif elapsed_time > 0:  # На паузе (время > 0, но не запущен)
            self.container.bgcolor = ft.Colors.WHITE60
        else:  # Остановлен (время = 0 или не начинался)
            self.container.bgcolor = ft.Colors.WHITE60
        
        if self.container.page:  # Проверяем, добавлен ли контейнер на страницу
            self.container.update()

    def build(self):
        return self.container

class StationView:
    def __init__(self, page: ft.Page, controller, config: Config, selected_station_id: int, module_container: ft.Container):
        self.page = page
        self.controller = controller
        self.config = config
        self.selected_station_id = selected_station_id
        self.module_container = module_container
        self.station_container = None

    def build(self):
        app_settings = self.config.get_app_settings()
        spots_count = app_settings["spots"]
        columns_count = app_settings["columns"]

        # Dropdown для выбора станции
        station_dropdown = ft.Dropdown(
            label="Station",
            value=f"Station {self.selected_station_id}",
            options=[
                ft.dropdown.Option(f"Station {station_id}") for station_id in self.controller.get_stations()
            ],
            on_change=self.on_station_change,
            width=150,
            text_size=14,
            content_padding=ft.padding.symmetric(horizontal=12, vertical=6),
            border_radius=8,
            tooltip="Change Station"
        )

        if self.selected_station_id is not None:
            selected_station = self.controller.get_station_by_id(self.selected_station_id)

            spots = [
                Spot(f"Spot {i + 1}", str(self.selected_station_id), (self.selected_station_id * 100 + i + 1), self.page, self.controller).build()
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

                column = ft.Column(
                    controls=column_spots,
                    expand=True,
                    spacing=10,
                )
                columns.append(column)

            row = ft.Row(
                controls=columns,
                expand=True,
                spacing=10,
            )

            if not self.station_container:
                self.station_container = ft.Column(
                    controls=[
                        ft.Container(
                            content=station_dropdown,
                            alignment=ft.alignment.center_left,
                            padding=ft.padding.only(top=0, left=10)
                        ),
                        row
                    ],
                    expand=True,
                    spacing=10
                )

            return self.station_container

    def on_station_change(self, e):
        new_station_id = int(e.control.value.split()[-1])
        if new_station_id != self.selected_station_id:
            self.selected_station_id = new_station_id
            new_view = StationView(self.page, self.controller, self.config, self.selected_station_id, self.module_container)
            self.module_container.content = new_view.build()
            self.module_container.update()