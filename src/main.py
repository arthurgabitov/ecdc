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
from models.user_model import UserModel

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
    stations = controller.get_stations()
    stations_count = len(stations)
    show_nav_rail = stations_count > 1
    
    if not is_web:
        page.window.height = 1000
        page.window.width = 1200 if show_nav_rail else 800
    
    
    page.padding = 0
    
    
    current_user = {"id": None, "name": ""}
    user_model = UserModel()
    
    def format_display_name(full_name):
        
        return full_name  

    
    dropdown_content = ft.Row(
        [
            ft.Icon(ft.icons.PERSON),
            ft.Text("Пользователь", color=ft.colors.BLACK, size=14),
        ],
        spacing=5,
    )
    
    # AppBar dropdown menu
    user_dropdown = ft.PopupMenuButton(
        content=dropdown_content,
        tooltip="User menu",
        items=[]
    )
    
    # Create AppBar
    appbar = ft.AppBar(
        title=ft.Container(
            content=ft.Text('ECDC Station App'),
            padding=ft.padding.only(left=15)
        ),
        leading_width=55,  
        bgcolor=ft.Colors.YELLOW_600,
        actions=[] if not show_nav_rail else [
            ft.Container(
                content=user_dropdown,
                padding=ft.padding.only(right=15)
            )
        ],
        elevation=3,
        shadow_color=ft.Colors.BLACK,
        center_title=False,  
    )
    
    main_container = ft.Container(
        expand=True,
        
    )

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

    def update_user_menu(user_id):
        # Get user data from model
        user = None
        if user_id:
            user = user_model.get_user_by_id(user_id)
        
        # Update current user information
        if user:
            current_user["id"] = user_id
            current_user["name"] = user.get("name", "Unknown User")
            # Форматируем имя для отображения
            display_name = format_display_name(current_user["name"])
        else:
            current_user["id"] = None
            current_user["name"] = "Unknown User"
            display_name = "Unknown User"
        
        # Update dropdown button text
        if isinstance(user_dropdown.content, ft.Row) and len(user_dropdown.content.controls) > 1:
            user_dropdown.content.controls[1].value = display_name
        
        # Update dropdown menu items
        user_dropdown.items = [
            ft.PopupMenuItem(
                text=display_name,
                disabled=True,
            ),
            ft.PopupMenuDivider(),
            ft.PopupMenuItem(
                text="Logout",
                icon=ft.Icons.LOGOUT,
                on_click=lambda _: show_welcome_view(),
            ),
        ]
        
        
        if user_dropdown.page:
            user_dropdown.update()

    def show_main_interface(selected_station_id, selected_user_id):
        
        current_station_id[0] = selected_station_id
        
        
        
        
       
        if selected_user_id:
            user = user_model.get_user_by_id(selected_user_id)
            
            
            if user:
                current_user["id"] = selected_user_id
                current_user["name"] = user.get("name", "Unknown User")
                
                display_name = format_display_name(current_user["name"])
                
            else:
                
                display_name = "Unknown User"
        else:
            display_name = "Unknown User"
        
        
        if isinstance(user_dropdown.content, ft.Row) and len(user_dropdown.content.controls) > 1:
            user_dropdown.content.controls[1].value = display_name
            
        
        
        user_dropdown.items = [
            ft.PopupMenuItem(
                text=display_name,
                disabled=True,
            ),
            ft.PopupMenuItem(),
            ft.PopupMenuItem(
                text="Logout",
                icon=ft.Icons.LOGOUT,
                on_click=lambda _: show_welcome_view(),
            ),
        ]
        
        
        page.controls.clear()
        page.appbar = appbar  
        page.add(main_container)
        
        
        update_module(0, selected_station_id)
        page.update()

    def show_welcome_view():
        page.controls.clear()
        page.appbar = None
        welcome_view = WelcomeView(page, controller, lambda station_id, user_id: show_main_interface(station_id, user_id))
        page.add(welcome_view.build())
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

    # Для режима с одной станцией сразу показываем основной интерфейс без логина
    if not show_nav_rail and stations:
        # Используем первую станцию и пустой ID пользователя
        show_main_interface(stations[0], None)
    else:
        # Стандартный запуск с экраном приветствия
        welcome_view = WelcomeView(page, controller, lambda station_id, user_id: show_main_interface(station_id, user_id))
        page.add(welcome_view.build())
        page.update()

        if welcome_view.auto_transition_needed:
            await welcome_view.run_auto_transition()

if __name__ == "__main__":
    ft.app(main)