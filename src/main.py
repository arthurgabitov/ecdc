import sys
import os

from controllers.timer_component import TimerComponent
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import flet as ft
from controllers.station_controller import StationController

from views.station_view import StationView
from views.welcome_view import WelcomeView
from views.settings_view import SettingsView
from views.navigation_rail_view import NavigationRailView
from views.dashboard_view import DashboardView
from views.top_bar import TopBar
from config import Config
from models.user_model import UserModel

def format_display_name(full_name):
    return full_name

async def main(page: ft.Page):
    config = Config()
    app_settings = config.get_app_settings()
    controller = StationController(config)
    config.set_controller(controller)

    page.title = app_settings["title"]
    page.window.maximized = True
    page.bgcolor = "#F7F7FA"

    # Увеличиваем базовый размер шрифта для всего приложения
    # page.theme = ft.Theme(font_family=None, font_size=18)  # Удалено: такого параметра нет в Flet

    is_web = page.platform == "web"
    stations = controller.get_stations()
    stations_count = len(stations)
    show_nav_rail = stations_count > 1

    page.padding = 0

    user_model = UserModel()
    current_sso = user_model.get_sso()
    current_sso = user_model.get_user_by_windows_login()
    if not current_sso:
        current_sso = os.getlogin() if hasattr(os, 'getlogin') else "Unknown SSO"

    main_container = ft.Container(expand=True, bgcolor="#F7F7FA")
    nav_rail_view = NavigationRailView(page, stations_count, lambda idx: update_module(idx)) if show_nav_rail else None
    nav_rail = nav_rail_view.build() if nav_rail_view else None

    animated_switcher = ft.AnimatedSwitcher(
        content=ft.Container(),
        transition=ft.AnimatedSwitcherTransition.FADE,
        duration=300,
        reverse_duration=300,
    )
    module_container = ft.Container(
        content=animated_switcher,
        expand=True,
        alignment=ft.alignment.center
    )

    # Состояние для выпадающего списка станции
    station_dropdown = None
    current_station_id = None
    selected_module_index = 0

    def on_station_change(e):
        nonlocal current_station_id
        current_station_id = int(e.control.value)
        update_module(selected_module_index, current_station_id)

    def build_station_dropdown(selected_station_id):
        # Стилизация как в StationView
        return ft.Dropdown(
            label="Station",
            value=f"Station {selected_station_id}",
            options=[ft.dropdown.Option(f"Station {station_id}") for station_id in stations],
            on_change=on_station_change,
            width=150,
            text_size=14,
            content_padding=ft.padding.symmetric(horizontal=12, vertical=6),
            border_radius=8,
            tooltip="Change Station"
        )

    def create_station_view(station_id=None):
        sid = int(station_id) if station_id is not None else int(stations[0])
        nonlocal current_station_id
        current_station_id = sid
        return StationView(page, controller, config, sid, module_container, stations_count, update_module).build()

    def create_dashboard_view():
        return DashboardView(page, controller, config, module_container, update_module).build()

    def create_settings_view():
        return SettingsView(page).build(config)

    def update_topbar(selected_index, station_id=None):
        nonlocal station_dropdown
        # Всегда подпись ECDC Station App, dropdown только для StationView
        if selected_index == 0:
            station_dropdown = build_station_dropdown(station_id if station_id else stations[0])
            topbar = TopBar("ECDC Station App", current_sso, dropdown=station_dropdown)
        else:
            topbar = TopBar("ECDC Station App", current_sso)
            station_dropdown = None
        main_layout.controls[0] = topbar
        main_layout.update()

    def update_module(selected_index, station_id=None):
        nonlocal selected_module_index
        selected_module_index = selected_index
        if not show_nav_rail:
            new_content = create_station_view(station_id if station_id else stations[0])
            update_topbar(0, station_id if station_id else stations[0])
        else:
            if nav_rail_view:
                nav_rail_view.set_selected_index(selected_index)
            if selected_index == 0:
                new_content = create_station_view(station_id)
                update_topbar(0, station_id if station_id else stations[0])
            elif selected_index == 1 and stations_count > 1:
                new_content = create_dashboard_view()
                update_topbar(1)
            elif selected_index == 2:
                new_content = create_settings_view()
                update_topbar(2)
            else:
                new_content = ft.Container()
                update_topbar(-1)
        animated_switcher.content = new_content if new_content is not None else ft.Container()
        animated_switcher.update()
        module_container.update()

    page.update_module = update_module

    def adjust_module_width(e=None):
        page.update()

    def show_main_interface(selected_station_id, _):
        nonlocal current_station_id
        current_station_id = int(selected_station_id)
        page.clean()
        page.add(main_container)
        update_module(0, selected_station_id)
        page.update()

    def show_welcome_view():
        page.appbar = None
        page.clean()
        welcome_view = WelcomeView(page, controller, lambda station_id, _: show_main_interface(station_id, None))
        page.add(welcome_view.build())
        page.update()

    def on_close(e):
        for station_id in controller.get_stations():
            for spot_idx in range(1, app_settings["spots"] + 1):
                spot_id = f"{station_id}_{spot_idx}"
                timer = TimerComponent(page, str(station_id), spot_id, controller)
                timer.pause_on_close()
    

    page.on_resized = adjust_module_width
    page.on_close = on_close

   
    if show_nav_rail:
        layout_content = ft.Row(
            [
                nav_rail if nav_rail else ft.Container(),
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
        [TopBar("ECDC Station App", current_sso)],  
        spacing=0,
        expand=True
    )
    main_layout.controls.append(layout_content)
    main_container.content = main_layout

    if not show_nav_rail and stations:
        show_main_interface(stations[0], None)
    else:
        welcome_view = WelcomeView(page, controller, lambda station_id, _: show_main_interface(station_id, None))
        page.add(welcome_view.build())
        page.update()
        if hasattr(welcome_view, 'auto_transition_needed') and welcome_view.auto_transition_needed:
            await welcome_view.run_auto_transition()

if __name__ == "__main__":
    ft.app(main)
    #ft.app(target=main, view=ft.AppView.WEB_BROWSER)