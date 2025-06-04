import flet as ft
from views.station_view import StationView
from .top_bar import TopBar
from models.user_model import UserModel

class DashboardView:
    def __init__(self, page, controller, config, module_container, update_module):
        self.page = page
        self.controller = controller
        self.config = config
        self.module_container = module_container
        self.update_module = update_module
        self.user_sso = UserModel().get_user_by_windows_login() or "Unknown SSO"

    def build(self):
        """Build the dashboard screen with draggable station indicators"""
        settings = self.config.get_app_settings()
        num_stations = settings["stations"]
        spots_per_station = settings["spots"]
        grid_settings = self.config.get_station_dashboard_grid()
        columns = max(1, min(spots_per_station, grid_settings["columns"])) 
        station_ids = self.controller.get_stations()

        stations = []
        for i, station_id in enumerate(station_ids):
            station_key = f"station_{station_id}"
            station_data = self.controller.get_spot_data(station_id, station_key)
            # Initialize place dictionary if it doesn't exist
            if "place" not in station_data:
                station_data["place"] = {"x": 0, "y": 0}
                self.controller.save_spots_state()
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
            """Update station position during drag"""
            detector.left = max(0, min(self.page.window.width - detector.content.width, detector.left + e.delta_x))
            detector.top = max(0, min(self.page.window.height - detector.content.height, detector.top + e.delta_y))
            station_id = detector.content.data["id"]
            station_key = f"station_{station_id}"
            self.controller.set_spot_coordinates(station_key, detector.left, detector.top)
            detector.update()

        def on_pan_end(self, e: ft.DragEndEvent, station_id):
            """Save station position when drag ends"""
            station_key = f"station_{station_id}"
            self.controller.save_spots_state()
            print(f"Saved position for {station_key} after drag end")

        def open_station_view(self, e, station_id):
            """Open station view when station is clicked"""
            self.update_module(0, station_id=station_id)

        station_controls = []
        statuses = self.config.get_spot_statuses()
        for station_data in stations:
            station_id = station_data["id"]
            spot_controls = []
            for spot_idx in range(spots_per_station):
                spot_id = f"{station_id}_{spot_idx + 1}"
                spot_data = self.controller.get_spot_data(station_id, spot_id)
                status = spot_data["status"]
                spot_Color = next((s["color"] for s in statuses if s["name"] == status), ft.Colors.WHITE60)
                spot_controls.append(
                    ft.Container(
                        width=20,
                        height=20,
                        bgcolor=spot_Color,
                        border_radius=5,
                        margin=ft.margin.all(2)
                    )
                )
            rows = (spots_per_station + columns - 1) // columns  
            grid_rows = []
            for row in range(rows):
                start_idx = row * columns
                end_idx = min(start_idx + columns, spots_per_station)
                row_spots = spot_controls[start_idx:end_idx]
                grid_rows.append(
                    ft.Row(
                        controls=row_spots,
                        alignment=ft.MainAxisAlignment.CENTER,
                        spacing=5
                    )
                )
            station_width = 50 + columns * 25  
            station_height = 40 + rows * 25 + 10 
            station_container = ft.Container(
                content=ft.Column([
                    ft.Text(
                        station_data["name"],
                        size=22,
                        weight=ft.FontWeight.BOLD
                    ),
                    ft.Column(
                        controls=grid_rows,
                        alignment=ft.MainAxisAlignment.CENTER,
                        spacing=5
                    ),
                    ft.Container(height=10)  
                ], 
                alignment=ft.MainAxisAlignment.CENTER,  
                spacing=5),
                width=station_width,
                height=station_height,
                bgcolor=ft.Colors.GREY_200,
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
                on_pan_end=lambda e, sid=station_data["id"]: on_pan_end(self, e, sid),
                on_tap=lambda e, sid=station_data["id"]: open_station_view(self, e, sid),
            )
            station_controls.append(draggable_container)
        dashboard = ft.Stack(
            controls=station_controls,
            expand=True  # Вместо width=self.page.window.width, height=self.page.window.height
        )
        # Только основной контент, без TopBar
        return ft.Column([
            ft.Text("Stations Dashboard", size=28, weight=ft.FontWeight.BOLD),
            ft.Container(content=dashboard, expand=True)
        ], expand=True)
