import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import flet as ft
from controllers.station_controller import StationController
from views.station_view import StationView
from views.welcome_view import WelcomeView
from config import Config

def main(page: ft.Page):
    config = Config()
    app_settings = config.get_app_settings()
    controller = StationController()

    page.title = app_settings["title"]
    page.theme_mode = "light"
    page.window.height = 1000
    page.window.width = 700
    page.window.title_bar_hidden = True
    page.window.title_bar_buttons_hidden = True

    def show_station_view(selected_station_id):
        page.add(
            ft.Row(
                [
                    ft.WindowDragArea(
                        ft.Container(
                            ft.Text("ECDC Station Dashboard"),
                            alignment=ft.alignment.center,
                            padding=10
                        ),
                        expand=True
                    ),
                    ft.IconButton(
                        ft.Icons.CLOSE,
                        on_click=lambda _: page.window.close()
                    )
                ]
            ),
            ft.Row()
        )
        station_view = StationView(page, controller, config, selected_station_id)
        page.update()

    welcome_view = WelcomeView(page, controller, show_station_view)
    page.add(welcome_view.build())
    page.update()

if __name__ == "__main__":
    ft.app(target=main)