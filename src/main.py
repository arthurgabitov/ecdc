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

    is_web = page.platform == "web"
    stations = controller.get_stations()
    stations_count = len(stations)
    show_nav_rail = stations_count > 1

    page.padding = 0

    # Remove current_user dict, use only current_sso string
    user_model = UserModel()
    current_sso = user_model.get_sso()

    # Get current Windows SSO (login)
    current_sso = user_model.get_user_by_windows_login()
    if not current_sso:
        current_sso = os.getlogin() if hasattr(os, 'getlogin') else "Unknown SSO"

    def build_appbar(current_sso):
        return ft.AppBar(
            title=ft.Container(
                content=ft.Text('ECDC Station App'),
                padding=ft.padding.only(left=15)
            ),
            leading_width=55,
            bgcolor=ft.Colors.YELLOW_600,
            actions=[] if not show_nav_rail else [
                ft.Container(
                    content=ft.PopupMenuButton(
                        content=ft.Row([
                            ft.Icon(ft.Icons.PERSON),
                            ft.Text(current_sso, color=ft.Colors.BLACK, size=14),
                        ], spacing=5),
                        tooltip="User menu",
                        items=[
                            ft.PopupMenuItem(text=current_sso, disabled=True),
                            ft.PopupMenuItem(text="-", disabled=True),
                            ft.PopupMenuItem(
                                text="Logout",
                                icon=ft.Icons.LOGOUT,
                                on_click=lambda _: show_welcome_view(),
                            ),
                        ]
                    ),
                    padding=ft.padding.only(right=15)
                )
            ],
            elevation=3,
            shadow_color=ft.Colors.BLACK,
            center_title=False,
        )

    appbar = build_appbar(current_sso)

    main_container = ft.Container(expand=True)
    nav_rail_view = NavigationRailView(page, stations_count, lambda idx: update_module(idx)) if show_nav_rail else None
    nav_rail = nav_rail_view.build() if nav_rail_view else None

    # AnimatedSwitcher for module content
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
        [layout_content],
        spacing=0,
        expand=True
    )
    main_container.content = main_layout

    current_station_id = None

    def create_station_view(station_id=None):
        sid = int(station_id) if station_id is not None else int(stations[0])
        nonlocal current_station_id
        current_station_id = sid
        return StationView(page, controller, config, sid, module_container, stations_count, update_module).build()

    def create_dashboard_view():
        return DashboardView(page, controller, config, module_container, update_module).build()

    def create_settings_view():
        return SettingsView(page).build(config)

    def update_module(selected_index, station_id=None):
        if not show_nav_rail:
            new_content = create_station_view(station_id if station_id else stations[0])
        else:
            if nav_rail_view:
                nav_rail_view.set_selected_index(selected_index)
            if selected_index == 0:
                new_content = create_station_view(station_id)
            elif selected_index == 1 and stations_count > 1:
                new_content = create_dashboard_view()
            elif selected_index == 2:
                new_content = create_settings_view()
            else:
                new_content = ft.Container()
        # AnimatedSwitcher: update content and call update
        animated_switcher.content = new_content if new_content is not None else ft.Container()
        animated_switcher.update()
        module_container.update()

    # Пробрасываем update_module в page для глобального обновления
    page.update_module = update_module

    def adjust_module_width(e=None):
        # No window_width/window_height API, so just update page
        page.update()

    def show_main_interface(selected_station_id, _):
        nonlocal current_station_id, appbar
        current_station_id = int(selected_station_id)
        appbar = build_appbar(current_sso)
        page.appbar = appbar
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