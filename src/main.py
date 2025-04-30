import sys
import os

from controllers.timer_component import TimerComponent
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import flet as ft
from controllers.station_controller import StationController

from views.station_view import StationView
from views.welcome_view import WelcomeView
from views.settings_view import SettingsView
from views.overview_view import OverviewView
from views.navigation_rail_view import NavigationRailView
from config import Config

async def main(page: ft.Page):
    config = Config()
    app_settings = config.get_app_settings()
    controller = StationController(config)
    config.set_controller(controller)
    
    page.config = config
    page.snack_bar = ft.SnackBar(content=ft.Text(""))  

    page.title = app_settings["title"]
    page.theme_mode = "light"
    
    
    is_web = page.platform == "web"
    
    
    if not is_web:
        page.window.height = 1000
        page.window.width = 1000
    
    
    page.padding = 0
    
    
    main_container = ft.Container(
        expand=True,
        
    )

    stations = controller.get_stations()
    stations_count = len(stations)

    show_nav_rail = stations_count > 1
    
    nav_rail_view = NavigationRailView(page, stations_count, lambda idx: update_module(idx)) if show_nav_rail else None
    nav_rail = nav_rail_view.build() if nav_rail_view else None

    module_container = ft.Container(
        content=ft.AnimatedSwitcher(
            content=ft.Container(),
            transition=ft.AnimatedSwitcherTransition.FADE,
            duration=300,
            reverse_duration=300,
        ),
        expand=True,
        alignment=ft.alignment.center
    )

    if show_nav_rail:
        layout_content = ft.Row(
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
    else:
        layout_content = ft.Container(
            content=module_container,
            alignment=ft.alignment.center,
            expand=True,
            padding=ft.padding.all(15)
        )
    
    main_layout = ft.Column(
        [layout_content],
        spacing=0,
        expand=True
    )
    
    main_container.content = main_layout

    current_station_id = [None]

    def create_station_view(station_id=None):
        if station_id is not None:
            current_station_id[0] = station_id
        return StationView(page, controller, config, current_station_id[0], module_container, stations_count, update_module).build()

    def create_overview_view():
        return OverviewView(page, controller, config, module_container, update_module).build()

    def create_settings_view():
        return SettingsView(page).build()

    def update_module(selected_index, station_id=None):
        if not show_nav_rail:
            new_content = create_station_view(station_id if station_id else stations[0])
        else:
            if nav_rail_view:
                nav_rail_view.set_selected_index(selected_index)
            
            new_content = ft.Container()
            if selected_index == 0:
                new_content = create_station_view(station_id)
            elif selected_index == 1 and stations_count > 1:
                new_content = create_overview_view()
            elif selected_index == 2:
                new_content = create_settings_view()
        
        if module_container.content.content != new_content:
            module_container.content.content = new_content
            if show_nav_rail and nav_rail_view:
                nav_rail_view.update()
            module_container.update()

    def adjust_module_width(e=None):
        if is_web:
            page.update()
        elif show_nav_rail:
            available_width = page.window.width - 100  # nav_rail width
            module_container.width = max(300, min(available_width, page.window.width * 0.75))
            page.update()
        else:
            module_container.width = page.window.width
            page.update()

    def show_main_interface(selected_station_id):
        current_station_id[0] = selected_station_id
        page.controls.clear()
        page.add(main_container)
        update_module(0, selected_station_id)
        page.update()

    def on_close(e):
        for station_id in controller.get_stations():
            for spot_idx in range(1, app_settings["spots"] + 1):
                spot_id = f"{station_id}_{spot_idx}"
                timer = TimerComponent(page, str(station_id), spot_id, controller)
                timer.pause_on_close()  
        page.window_close()

    page.on_resized = adjust_module_width
    page.on_close = on_close

    welcome_view = WelcomeView(page, controller, show_main_interface)
    page.add(welcome_view.build())
    page.update()

    if welcome_view.auto_transition_needed:
        await welcome_view.run_auto_transition()

if __name__ == "__main__":
    ft.app(main)