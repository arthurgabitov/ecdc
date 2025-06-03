import flet as ft
import asyncio
from controllers.station_controller import StationController
from models.user_model import UserModel

class WelcomeView:
    def __init__(self, page: ft.Page, controller: StationController, on_complete):
        self.page = page
        self.controller = controller
        self.on_complete = on_complete
        self.user_model = UserModel()
        self.selected_user_id = None
        
        self.welcome_text = ft.Text(
            "Station App",
            size=40,
            text_align=ft.TextAlign.CENTER,
            weight=ft.FontWeight.BOLD
        )

        stations = self.controller.get_stations()
        self.stations_count = len(stations)
        
        # Создаем выпадающий список пользователей (изначально пустой)
        self.user_selector = ft.Dropdown(
            label="Select SSO User",
            options=[],
            on_change=self.handle_user_select,
            width=300,
            hint_text="Loading users..."
        )

        if self.stations_count == 1:
            self.station_selector = ft.Container()  
            self.auto_transition_needed = True
            self.station_id = stations[0]
        else:
            self.station_selector = ft.Dropdown(
                label="Select Station",
                options=[ft.dropdown.Option(f"Station {station_id}") for station_id in stations],
                on_change=self.handle_station_select,
                width=200
            )
            self.auto_transition_needed = False

        
        self.loading_indicator = ft.ProgressRing(width=20, height=20, visible=True)

        
        self.continue_button = ft.ElevatedButton(
            "Login",
            on_click=self.handle_continue,
            disabled=True,
            width=200
        )

        self.content = ft.Column(
            [   
                #ft.Rive(
                #    "src/robot_looping_test.riv",
                #    placeholder=ft.ProgressBar(),
                #    width=300,
                #    height=200,
                #),
                self.welcome_text,
                ft.Row([
                    self.user_selector,
                    self.loading_indicator
                ], alignment=ft.MainAxisAlignment.CENTER),
                self.station_selector,
                self.continue_button
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=20
        )        
        
        self.page_container = ft.Container(
            content=self.content,
            alignment=ft.alignment.center,
            expand=True,
            bgcolor=ft.Colors.WHITE
        )
        
        # Загружаем пользователей асинхронно
        self.page.run_task(self.load_users)

    async def load_users(self):
        """Асинхронная загрузка списка пользователей"""
        try:
            # Получаем список пользователей из модели
            users = await self.user_model.fetch_users()
            
            # Если список пуст, используем предустановленных пользователей
            if not users:
                users = self.user_model.get_default_users()

            # Обновляем выпадающий список пользователей
            self.user_selector.options = [
                ft.dropdown.Option(key=str(user["id"]), text=f"{user['name']}") 
                for user in users
            ]
            
            # Скрываем индикатор загрузки
            self.loading_indicator.visible = False
            
            # Обновляем подсказку
            self.user_selector.hint_text = "Выберите пользователя из списка"
            
            # Применяем изменения в UI
            self.page.update()
        except Exception as e:
            print(f"Ошибка при загрузке пользователей: {str(e)}")
            # В случае ошибки показываем предустановленных пользователей
            default_users = self.user_model.get_default_users()
            self.user_selector.options = [
                ft.dropdown.Option(key=user["id"], text=user["name"]) 
                for user in default_users
            ]
            self.loading_indicator.visible = False
            self.user_selector.hint_text = "Выберите пользователя из списка (работа в автономном режиме)"
            self.page.update()

    def handle_user_select(self, e):
        """Обработчик выбора пользователя"""
        self.selected_user_id = e.control.value
        
        # Разрешаем продолжить только если выбран пользователь
        if self.selected_user_id:
            self.continue_button.disabled = False
            if self.stations_count == 1:
                # Если станция только одна, делаем автопереход
                self.auto_transition_needed = True
            self.page.update()

    def handle_station_select(self, e):
        """Обработчик выбора станции"""
        if isinstance(self.station_selector, ft.Dropdown):
            selected_station_id = int(e.control.value.split()[-1])
            self.station_id = selected_station_id

    def handle_continue(self, e):
        """Обработчик нажатия кнопки продолжения"""
        if self.selected_user_id:
            # Если есть несколько станций, используем выбранную станцию
            if self.stations_count > 1 and hasattr(self, 'station_id'):
                self.on_complete(self.station_id, self.selected_user_id)
            # Иначе используем единственную станцию
            elif self.stations_count == 1:
                self.on_complete(self.station_id, self.selected_user_id)

    def build(self):
        return self.page_container

    async def run_auto_transition(self):
        if self.auto_transition_needed and self.selected_user_id:
            await asyncio.sleep(1)
            self.on_complete(self.station_id, self.selected_user_id)