import flet as ft
from config import Config
from src.controllers.timer_component import TimerComponent

spot_style: dict = {
    "main": {
        "expand": True,
        "bgcolor": ft.colors.WHITE60,
        "border_radius": 10,
        "border": ft.border.all(width=0.5, color=ft.colors.GREY_500),
        "ink": True
    },
}

class Spot:
    def __init__(self, name: str, station_id: str, spot_id: str, page: ft.Page, controller):
        self.name = name
        self.station_id = station_id
        self.spot_id = spot_id
        self.page = page
        self.controller = controller
        self.timer = TimerComponent(page, station_id, spot_id, controller)
        self.label = f"Spot {self.spot_id[-1]}"
        spot_data = self.controller.get_spot_data(int(station_id), spot_id)
        
        self.status_dropdown = ft.Dropdown(
            label="Status",
            value=spot_data["status"],
            options=[ft.dropdown.Option(status) for status in controller.config.get_status_names()],
            on_change=self.update_status,
            width=250,
            visible=self.page.config.is_dashboard_test_mode_enabled()
        )
        
        self.content = ft.Column(
            controls=[
                ft.Divider(height=20, color="transparent"),
                ft.Text(self.label, size=18, text_align=ft.TextAlign.CENTER),
                ft.Container(expand=1),
                ft.Container(
                    content=self.timer.build(),
                    expand=1,
                    alignment=ft.alignment.bottom_center
                ),
                ft.Container(
                    content=ft.TextButton("Reset", on_click=self.reset_spot),
                    alignment=ft.alignment.center,
                    padding=ft.padding.only(bottom=10)
                ),
            ],
            expand=True,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=0
        )

        self.on_click = self.open_dialog
        self.dlg_modal = ft.AlertDialog(
            modal=False,
            title=ft.Text("Spot Details"),
            content=ft.Text("Enter WO number"),
            actions=[
                ft.TextField(label="WO Number", value=spot_data["wo_number"], on_change=self.update_wo_number),
                ft.Divider(height=20, color="transparent"),
                self.status_dropdown,
                ft.Divider(height=40, color="transparent"),
                ft.Text("Notifications"),
                ft.Divider(height=40, color="transparent"),
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
        self.timer.on_state_change = self.update_spot_state

    def update_wo_number(self, e):
        spot = self.controller.get_spot_data(int(self.station_id), self.spot_id)
        spot["wo_number"] = e.control.value
        self.controller.save_timers_state()

    def update_status(self, e):
        new_status = e.control.value
        self.controller.set_spot_status(int(self.station_id), self.spot_id, new_status)
        self.update_color()

    def open_dialog(self, e):
        if not self.dlg_modal.open:
            if self.dlg_modal not in self.page.overlay:
                self.page.overlay.append(self.dlg_modal)
            self.status_dropdown.visible = self.page.config.is_dashboard_test_mode_enabled()
            self.dlg_modal.open = True
            self.page.update()

    def handle_close(self, e):
        if self.dlg_modal.open:
            self.dlg_modal.open = False
            self.page.update()

    def update_spot_state(self):
        self.update_color()
        self.page.update()

    def update_color(self):
        spot = self.controller.get_spot_data(int(self.station_id), self.spot_id)
        status = spot["status"]
        statuses = self.controller.config.get_spot_statuses()
        new_color = next((s["color"] for s in statuses if s["name"] == status), ft.colors.WHITE60)
        self.container.bgcolor = new_color
        if self.container.page:
            self.container.update()

    def reset_spot(self, e):
        
        default_status = self.controller.config.get_status_names()[0]  
        self.controller.set_spot_status(int(self.station_id), self.spot_id, default_status)
        
       
        spot = self.controller.get_spot_data(int(self.station_id), self.spot_id)
        spot["wo_number"] = ""
        self.controller.save_timers_state()

     
        self.timer.reset()

       
        self.status_dropdown.value = default_status 
        self.update_color()
        self.page.update()

    def build(self):
        return self.container
    

class StationView:
    def __init__(self, page: ft.Page, controller, config: Config, selected_station_id: int, module_container: ft.Container, stations_count: int):
        self.page = page
        self.controller = controller
        self.config = config
        self.selected_station_id = selected_station_id
        self.module_container = module_container
        self.station_container = None
        self.stations_count = stations_count

    def build(self):
        app_settings = self.config.get_app_settings()
        spots_count = app_settings["spots"]
        columns_count = app_settings["columns"]

       
        if self.stations_count > 1:
            station_dropdown = ft.Dropdown(
                label="Station",
                value=f"Station {self.selected_station_id}",
                options=[ft.dropdown.Option(f"Station {station_id}") for station_id in self.controller.get_stations()],
                on_change=self.on_station_change,
                width=150,
                text_size=14,
                content_padding=ft.padding.symmetric(horizontal=12, vertical=6),
                border_radius=8,
                tooltip="Change Station"
            )
        else:
            station_dropdown = ft.Text(f"Station {self.selected_station_id}", size=14)

        if self.selected_station_id is not None:
            selected_station = self.controller.get_station_by_id(self.selected_station_id)
            spots = [
                Spot(f"Spot {i + 1}", str(self.selected_station_id), f"{self.selected_station_id}_{i + 1}", self.page, self.controller).build()
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
                column = ft.Column(controls=column_spots, expand=True, spacing=10)
                columns.append(column)

            row = ft.Row(controls=columns, expand=True, spacing=10)

            if not self.station_container:
                self.station_container = ft.Column(
                    controls=[
                        ft.Container(content=station_dropdown, alignment=ft.alignment.center_left, padding=ft.padding.only(top=0, left=10)),
                        row
                    ],
                    expand=True,
                    spacing=10
                )

            return self.station_container

    def on_station_change(self, e):
        if self.stations_count > 1:
            new_station_id = int(e.control.value.split()[-1])
            if new_station_id != self.selected_station_id:
                self.update_module(0, station_id=new_station_id)  # Просто вызываем update_module