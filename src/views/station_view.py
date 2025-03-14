import flet as ft
from config import Config
from src.controllers.timer_component import TimerComponent

spot_style: dict = {
    "main": {
        "expand": True,
        "bgcolor": ft.colors.WHITE60,
        "border_radius": 10,
        "border": ft.border.all(width=0.5, color=ft.colors.GREY_300),
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
        self.label = f"Спот {self.spot_id % 100}"
        self.content = ft.Column(
            horizontal_alignment="center",
            controls=[
                ft.Text(self.label, size=18),
                self.timer.build(),
            ]
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
    
    def build(self):
        return ft.Container(
            content=self.content,
            **spot_style["main"],
            on_click=self.open_dialog,
            opacity=0.0,  # Начальная непрозрачность
            animate_opacity=300
        )

class StationView:
    def __init__(self, page: ft.Page, controller, config: Config, selected_station_id: int):
        self.page = page
        self.controller = controller
        self.config = config
        self.selected_station_id = selected_station_id
        self.station_container = None
        self.build()

    def build(self):
        app_settings = self.config.get_app_settings()
        spots_count = app_settings["spots"]
        columns_count = app_settings["columns"]

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
                self.station_container = ft.Column(expand=True)
                self.page.add(self.station_container)

            self.station_container.controls = [row]
            self.station_container.update()

            # Запускаем анимацию появления спотов
            for spot in spots:
                spot.opacity = 1.0
                spot.update()