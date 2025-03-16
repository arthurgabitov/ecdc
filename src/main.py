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
    controller = StationController(config)
    config.set_controller(controller)

    page.title = app_settings["title"]
    page.theme_mode = "light"
    page.window.height = 1000
    page.window.width = 800
    page.padding = 0
    

    
    

    # Navigation Rail (слева)
    nav_rail = ft.NavigationRail(
        selected_index=0,
        label_type=ft.NavigationRailLabelType.ALL,
        min_width=100,
        min_extended_width=200,
        width=100,
        bgcolor=ft.colors.ON_PRIMARY_CONTAINER,
        indicator_color=ft.colors.WHITE10,
    
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

    # Контейнер для модуля (справа) с управляемой шириной
    module_container = ft.Container(
        expand=True,
        width=500,  # Начальная ширина
        alignment=ft.alignment.center
    )

    # Основной интерфейс (шапка + rail + модуль)
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
        """Обновляет содержимое модуля в зависимости от выбранного пункта в Navigation Rail."""
        module_container.content = None
        if selected_index == 0:
            station_view = StationView(page, controller, config, current_station_id, module_container)
            module_container.content = station_view.build()
        elif selected_index == 1:
            module_container.content = ft.Text("Settings Module (Coming Soon)", size=20)
        module_container.update()

    # Храним текущий выбранный station_id
    current_station_id = None

    def adjust_module_width(e=None):
        """Динамически подстраивает ширину module_container."""
        available_width = page.window.width - nav_rail.min_width  # Учитываем ширину rail
        if available_width < 500:
            module_container.width = 500  # Минимальная ширина
        elif available_width > 1000:
            module_container.width = 1000  # Максимальная ширина
        else:
            module_container.width = available_width  # Промежуточное значение
        page.update()

    def show_main_interface(selected_station_id):
        """Переключает интерфейс на основной после выбора станции."""
        nonlocal current_station_id
        current_station_id = selected_station_id
        page.controls.clear()
        page.add(main_layout)
        update_module(nav_rail.selected_index)
        adjust_module_width()  # Устанавливаем начальную ширину
        page.update()

    # Обработчик изменения размера окна
    page.on_resized = adjust_module_width

    # Инициализируем приветственный экран
    welcome_view = WelcomeView(page, controller, show_main_interface)
    page.add(welcome_view.build())
    page.update()

if __name__ == "__main__":
    ft.app(target=main)