import flet as ft

def main(page: ft.Page):
    page.title = "test"
    page.window_width = 800
    page.window_height = 600

    
    stations = [
        {"name": "station 1", "x": 50, "y": 50},
        {"name": "station 2", "x": 200, "y": 100},
        {"name": "station 3", "x": 300, "y": 200},
        {"name": "station 4", "x": 400, "y": 300},
        {"name": "station 5", "x": 500, "y": 300},
        {"name": "station 6", "x": 600, "y": 300},
        {"name": "station 7", "x": 700, "y": 300},
        {"name": "station 8", "x": 700, "y": 400},

    ]

    def on_pan_update(e: ft.DragUpdateEvent, detector):
        
        detector.left = max(0, min(page.window_width - detector.content.width, detector.left + e.delta_x))
        detector.top = max(0, min(page.window_height - detector.content.height, detector.top + e.delta_y))
        page.update()

    
    station_controls = []
    for station_data in stations:
        container = ft.Container(
            content=ft.Text(station_data["name"]),
            width=100,
            height=50,
            bgcolor=ft.Colors.BLUE_200,
            border_radius=5,
        )
        
        detector_ref = ft.Ref[ft.GestureDetector]()
        draggable_container = ft.GestureDetector(
            ref=detector_ref,  
            content=container,
            left=station_data["x"],
            top=station_data["y"],
            on_pan_update=lambda e, d=detector_ref: on_pan_update(e, d.current),
        )
        station_controls.append(draggable_container)

    
    dashboard = ft.Stack(
        controls=station_controls,
        width=page.window_width,
        height=page.window_height,
    )

    page.add(dashboard)

ft.app(target=main)