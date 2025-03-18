import flet as ft
from views.station_view import StationView

class OverviewView:
    def __init__(self, page, controller, config, module_container):
        self.page = page
        self.controller = controller
        self.config = config
        self.module_container = module_container

    def build(self):
        settings = self.config.get_app_settings()
        num_stations = settings["stations"]
        station_ids = self.controller.get_stations()

        stations = []
        for i, station_id in enumerate(station_ids):
            x_pos = 50 + (i % 4) * 150
            y_pos = 50 + (i // 4) * 100
            stations.append({
                "name": f"Station {station_id}",
                "x": x_pos,
                "y": y_pos,
                "id": station_id
            })

        def on_pan_update(self, e: ft.DragUpdateEvent, detector):  # Made this a class method
            detector.left = max(0, min(self.page.window.width - detector.content.width, detector.left + e.delta_x))
            detector.top = max(0, min(self.page.window.height - detector.content.height, detector.top + e.delta_y))
            self.page.update()

        def open_station_view(self, e, station_id):  # New method to handle station click
            station_view = StationView(self.page, self.controller, self.config, station_id, self.module_container)
            self.module_container.content = station_view.build()
            self.module_container.update()

        station_controls = []
        for station_data in stations:
            container = ft.Container(
                content=ft.Text(station_data["name"]),
                width=100,
                height=50,
                bgcolor=ft.colors.BLUE_200,
                border_radius=5,
            )
            
            detector_ref = ft.Ref[ft.GestureDetector]()
            draggable_container = ft.GestureDetector(
                ref=detector_ref,
                content=container,
                left=station_data["x"],
                top=station_data["y"],
                on_pan_update=lambda e, d=detector_ref: on_pan_update(self, e, d.current),
                on_tap=lambda e, sid=station_data["id"]: open_station_view(self, e, sid),
            )
            station_controls.append(draggable_container)

        dashboard = ft.Stack(
            controls=station_controls,
            width=self.page.window.width,
            height=self.page.window.height,
        )

        return ft.Column([
            ft.Text("Stations Overview", size=24, weight=ft.FontWeight.BOLD),
            ft.Container(
                content=dashboard,
                expand=True
            )
        ])