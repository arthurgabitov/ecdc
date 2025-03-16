import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import flet as ft
from controllers.station_controller import StationController
from views.station_view import StationView
from views.welcome_view import WelcomeView
from views.settings_view import SettingsView
from config import Config

def main(page: ft.Page):
    config = Config()
    app_settings = config.get_app_settings()
    controller = StationController(config)

    page.title = app_settings["title"]
    page.theme_mode = "light"
    page.padding = 0
    page.window.height = 1000
    page.window.width = 800
    page.window.title_bar_hidden = False
    page.window.title_bar_buttons_hidden = True

    content_container = ft.Container(expand=True)

    

    header = ft.Container(


    )

    

    nav_rail = ft.NavigationRail(
        selected_index=0,
        label_type=ft.NavigationRailLabelType.ALL,
        min_width=100,
        min_extended_width=200,
        width=100,
        bgcolor=ft.colors.ON_PRIMARY_CONTAINER,
    
        destinations=[
            ft.NavigationRailDestination(
                icon_content=ft.Icon(ft.Icons.HOME, color=ft.colors.WHITE),  # Невыбранная иконка
                selected_icon_content=ft.Icon(ft.Icons.HOME_FILLED, color=ft.Colors.WHITE),  # Выбранная иконка
                label_content=ft.Text("RO Station", color=ft.Colors.WHITE),  # Невыбранный текст
                label="RO Station"
                
            ),
            ft.NavigationRailDestination(
                icon_content=ft.Icon(ft.Icons.SETTINGS, color=ft.Colors.WHITE),
                selected_icon_content=ft.Icon(ft.Icons.SETTINGS_APPLICATIONS, color=ft.Colors.WHITE),
                label_content=ft.Text("Settings", color=ft.Colors.WHITE),
                label="Settings"
            ),
        ],
        on_change=lambda e: update_module(e.control.selected_index),
    )

    module_container = ft.Container(
        expand=True,
        padding=ft.padding.all(15)
    )

    main_layout = ft.Row(
        [
            nav_rail,
            
            ft.Column(
                [
                    header,
                    module_container
                ],
                spacing=0,
                expand=True
            )
        ],
        spacing=0,
        expand=True
    )

    def update_module(selected_index):
        module_container.content = None
        if selected_index == 0:
            station_view = StationView(page, controller, config, current_station_id, module_container)
            module_container.content = station_view.build()
        elif selected_index == 1:
            settings_view = SettingsView(page)
            module_container.content = settings_view.build()
        module_container.update()

    current_station_id = None

    def show_main_interface(selected_station_id):
        nonlocal current_station_id
        current_station_id = selected_station_id
        page.controls.clear()
        page.add(main_layout)
        update_module(nav_rail.selected_index)
        page.update()

    def handle_station_change(new_station_id):
        if new_station_id != current_station_id:
            show_main_interface(new_station_id)

    def show_welcome_view():
        page.controls.clear()
        welcome_view = WelcomeView(page, controller, show_main_interface)
        page.add(welcome_view.build())
        page.update()

    welcome_view = WelcomeView(page, controller, show_main_interface)
    page.add(welcome_view.build())
    page.update()

if __name__ == "__main__":
    ft.app(target=main)