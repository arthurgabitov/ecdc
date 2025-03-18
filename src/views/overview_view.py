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
        spots_per_station = settings["spots"]
        station_ids = self.controller.get_stations()

        stations = []
        for i, station_id in enumerate(station_ids):
            station_key = f"station_{station_id}"
            station_data = self.controller.get_spot_data(station_id, station_key)
            if station_data["place"]["x"] != 0 or station_data["place"]["y"] != 0:
                x_pos = station_data["place"]["x"]
                y_pos = station_data["place"]["y"]
            else:
                x_pos = 50 + (i % 4) * 150
                y_pos = 50 + (i // 2) * 100
                self.controller.set_spot_coordinates(station_key, x_pos, y_pos)

            stations.append({
                "name": f"Station {station_id}",
                "x": x_pos,
                "y": y_pos,
                "id": station_id
            })

        def on_pan_update(self, e: ft.DragUpdateEvent, detector):
            detector.left = max(0, min(self.page.window.width - detector.content.width, detector.left + e.delta_x))
            detector.top = max(0, min(self.page.window.height - detector.content.height, detector.top + e.delta_y))
            station_id = detector.content.data["id"]
            station_key = f"station_{station_id}"
            self.controller.set_spot_coordinates(station_key, detector.left, detector.top)
            self.page.update()

        def open_station_view(self, e, station_id):
            station_view = StationView(self.page, self.controller, self.config, station_id, self.module_container)
            self.module_container.content = station_view.build()
            self.module_container.update()

        station_controls = []
        statuses = self.config.get_spot_statuses()
        for station_data in stations:
            station_id = station_data["id"]
            spot_controls = []
            for spot_idx in range(spots_per_station):
                spot_id = f"{station_id}_{spot_idx + 1}"
                spot_data = self.controller.get_spot_data(station_id, spot_id)
                status = spot_data["status"]
                spot_color = next((s["color"] for s in statuses if s["name"] == status), ft.colors.WHITE60)
                print(f"Overview - Spot {spot_id} - Status: {status}, Color: {spot_color}")  # Отладка
                spot_controls.append(
                    ft.Container(
                        width=20,
                        height=20,
                        bgcolor=spot_color,
                        border_radius=5,
                        margin=ft.margin.all(2)
                    )
                )

            station_container = ft.Container(
                content=ft.Column([
                    ft.Text(station_data["name"], size=16, weight=ft.FontWeight.BOLD),
                    ft.Row(spot_controls, alignment=ft.MainAxisAlignment.CENTER, spacing=5)
                ], alignment=ft.MainAxisAlignment.CENTER, spacing=5),
                width=150,
                height=80,
                bgcolor=ft.colors.GREY_200,
                border_radius=10,
                padding=5,
                data={"id": station_data["id"]}
            )

            detector_ref = ft.Ref[ft.GestureDetector]()
            draggable_container = ft.GestureDetector(
                ref=detector_ref,
                content=station_container,
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
            ft.Container(content=dashboard, expand=True)
        ])