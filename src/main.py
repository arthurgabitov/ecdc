import sys
import os

from controllers.timer_component import TimerComponent

import flet as ft
from controllers.station_controller import StationController
from styles import BG_MAIN, BG_CONTAINER, PADDING_MAIN, BORDER_RADIUS_DROPDOWN, FONT_SIZE_SMALL, PADDING_DROPDOWN

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
    #page.window.maximized = True
    page.bgcolor = BG_MAIN
    page.window.height = 760
    page.window.width = 760
    page.theme_mode = ft.ThemeMode.LIGHT

    is_web = page.platform == "web"
    stations = controller.get_stations()
    stations_count = len(stations)
    # Navigation rail is always shown if stations exist, but dashboard button only if stations_count > 1
    show_nav_rail = stations_count > 0
    show_dashboard = stations_count > 1

    # Build menu items for navigation rail
    menu_items = [
        {"label": "Station", "icon": ft.Icons.HOME, "selected_icon": ft.Icons.HOME_FILLED},
    ]
    if show_dashboard:
        menu_items.append({"label": "Dashboard", "icon": ft.Icons.DASHBOARD, "selected_icon": ft.Icons.DASHBOARD_CUSTOMIZE})
    menu_items.append({"label": "Settings", "icon": ft.Icons.SETTINGS, "selected_icon": ft.Icons.SETTINGS_APPLICATIONS})

    page.padding = 0

    user_model = UserModel()
    current_sso = user_model.get_sso()
    current_sso = user_model.get_user_by_windows_login()
    if not current_sso:
        current_sso = os.getlogin() if hasattr(os, 'getlogin') else "Unknown SSO"

    main_container = ft.Container(expand=True, bgcolor=BG_CONTAINER)
    nav_rail_view = NavigationRailView(page, menu_items, lambda idx: update_module(idx)) if show_nav_rail else None
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


    station_dropdown = None
    current_station_id = None
    selected_module_index = 0

    def on_station_change(e):
        nonlocal current_station_id
        current_station_id = int(e.control.value)
        update_module(selected_module_index, current_station_id)

    def build_station_dropdown(selected_station_id):
        return ft.Dropdown(
            label="Station selection",
            value=str(selected_station_id),
            options=[ft.dropdown.Option(str(station_id), text=f"Station {station_id}") for station_id in stations],
            on_change=on_station_change,
            width=150,
            text_size=FONT_SIZE_SMALL,
            content_padding=PADDING_DROPDOWN,
            border_radius=BORDER_RADIUS_DROPDOWN,
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
        def handle_logout(e):
            show_welcome_view()
        if selected_index == 0:
            station_dropdown = build_station_dropdown(station_id if station_id else stations[0])
            topbar = TopBar("ECDC Station App", current_sso, dropdown=station_dropdown, on_logout=handle_logout)
        else:
            topbar = TopBar("ECDC Station App", current_sso, on_logout=handle_logout)
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
            # Map selected_index to content: 0 - Station, 1 - Dashboard (if present), last - Settings
            if selected_index == 0:
                new_content = create_station_view(station_id)
                update_topbar(0, station_id if station_id else stations[0])
            elif show_dashboard and selected_index == 1:
                new_content = create_dashboard_view()
                update_topbar(1)
            elif (show_dashboard and selected_index == 2) or (not show_dashboard and selected_index == 1):
                new_content = create_settings_view()
                update_topbar(2 if show_dashboard else 1)
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
        controller.save_spots_state()
        for station_id in controller.get_stations():
            for spot_idx in range(1, app_settings["spots"] + 1):
                spot_id = f"{station_id}_{spot_idx}"
                timer = TimerComponent(page, str(station_id), spot_id, controller)
                timer.pause_on_close()
    

    page.on_resized = adjust_module_width
    page.on_close = on_close

    # Get the correct font path for both development and packaged modes
    if getattr(sys, 'frozen', False):
        # If packaged with PyInstaller, use the executable directory
        font_base_path = os.path.dirname(sys.executable)
    else:
        # In development mode, use the project root
        font_base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    font_path = os.path.join(font_base_path, "fonts", "ttf", "Roboto-Light.ttf")
    
    page.fonts = {
        "Roboto-Light": font_path,
    }
   
    if show_nav_rail:
        layout_content = ft.Row(
            [
                nav_rail if nav_rail else ft.Container(),
                ft.Container(
                    content=module_container,
                    alignment=ft.alignment.center,
                    expand=True,
                    padding=PADDING_MAIN
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
            padding=PADDING_MAIN
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