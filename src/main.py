import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import flet as ft
from controllers.station_controller import StationController
from views.station_view import StationView
from views.welcome_view import WelcomeView
from views.settings_view import SettingsView
from views.overview_view import OverviewView  
from config import Config

def main(page: ft.Page):
    config = Config()
    app_settings = config.get_app_settings()
    controller = StationController(config)
    config.set_controller(controller)

    page.title = app_settings["title"]
    page.theme_mode = "light"
    page.window.height = 1000
    page.window.width = 800
    page.padding = 0

    nav_rail = ft.NavigationRail(
        selected_index=0,
        label_type=ft.NavigationRailLabelType.ALL,
        min_width=100,
        min_extended_width=200,
        width=100,
        bgcolor=ft.Colors.ON_PRIMARY_CONTAINER,  
        indicator_color=ft.Colors.WHITE10,       
        destinations=[
            ft.NavigationRailDestination(
                icon_content=ft.Icon(ft.Icons.HOME, color=ft.Colors.WHITE),                  
                selected_icon_content=ft.Icon(ft.Icons.HOME_FILLED, color=ft.Colors.WHITE),  
                label_content=ft.Text("RO Station", color=ft.Colors.WHITE),                  
                label="RO Station"
            ),
            ft.NavigationRailDestination(
                icon_content=ft.Icon(ft.Icons.DASHBOARD, color=ft.Colors.WHITE),                  
                selected_icon_content=ft.Icon(ft.Icons.DASHBOARD_CUSTOMIZE, color=ft.Colors.WHITE),  
                label_content=ft.Text("Overview", color=ft.Colors.WHITE),                         
                label="Overview"
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
        width=500,
        alignment=ft.alignment.center
    )

    main_layout = ft.Column(
        [
            ft.Row(
                [
                    nav_rail,
                    ft.Container(
                        content=module_container,
                        alignment=ft.alignment.center,
                        expand=True,
                        padding=ft.padding.all(15)
                    )
                ],
                expand=True,
                spacing=0,
                alignment=ft.MainAxisAlignment.START,
                vertical_alignment=ft.CrossAxisAlignment.STRETCH
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
            overview_view = OverviewView(page, controller, config, module_container) 
            module_container.content = overview_view.build()
        elif selected_index == 2:
            settings_view = SettingsView(page)  
            module_container.content = settings_view.build()
        module_container.update()

    current_station_id = None

    def adjust_module_width(e=None):
        available_width = page.window.width - nav_rail.min_width  
        if available_width < 500:
            module_container.width = 500  
        elif available_width > 1000:
            module_container.width = 1000  
        else:
            module_container.width = available_width  
        page.update()

    def show_main_interface(selected_station_id):
        nonlocal current_station_id
        current_station_id = selected_station_id
        page.controls.clear()
        page.add(main_layout)
        update_module(nav_rail.selected_index)
        adjust_module_width()
        page.update()

    page.on_resized = adjust_module_width

    welcome_view = WelcomeView(page, controller, show_main_interface)
    page.add(welcome_view.build())
    page.update()

if __name__ == "__main__":
    ft.app(target=main)