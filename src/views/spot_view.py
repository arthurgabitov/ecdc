import flet as ft
import os
import threading
import time
import traceback
from src.controllers.timer_component import TimerComponent
from src.controllers.ro_customization_tools import ROCustomizationController

spot_style: dict = {
    "main": {
        "expand": True,
        "bgcolor": ft.colors.WHITE60,
        "border_radius": 20,
        "border": ft.border.all(width=0.5, color=ft.colors.GREY_500),
        "ink": True
    },
}

class Spot:
    def __init__(self, name: str, station_id: str, spot_id: str, page: ft.Page, controller):
        self.name = name
        self.station_id = station_id
        self.spot_id = spot_id
        self.page = page
        self.controller = controller
        self.timer = TimerComponent(page, station_id, spot_id, controller)
        self.label = f"Spot {self.spot_id[-1]}"
        
        self.ro_tools = ROCustomizationController(controller.config)
        
        self.timer_state = "stopped"  
        self.wo_found = False  

        spot_data = self.controller.get_spot_data(int(station_id), spot_id)
        self.status_dropdown = ft.Dropdown(
            label="Status",
            value=spot_data["status"],
            options=[ft.dropdown.Option(status) for status in controller.config.get_status_names()],
            on_change=self.update_status,
            width=250,
            visible=self.page.config.is_dashboard_test_mode_enabled()
        )

        self.wo_number_field = ft.TextField(
            label="WO Number",
            value=spot_data["wo_number"],
            on_change=self.update_wo_number,
            width=300,
            keyboard_type=ft.KeyboardType.NUMBER
        )
        
        self.e_number_label = ft.Text("E-number: Please enter WO-number", size=16, text_align=ft.TextAlign.CENTER)
        
        self.model_label = ft.Text("Model: Unknown", size=16,  text_align=ft.TextAlign.CENTER)
        
        # E-number and model display label for spot container
        self.spot_e_number_label = ft.Text("", size=14, text_align=ft.TextAlign.CENTER, visible=False)
        
        self.file_buttons_container = ft.Container(
            content=ft.Row([]),
            visible=False
        )
        
        self.snack_bar = ft.SnackBar(content=ft.Text(""), open=False)
        
        # Robot Info section
        self.robot_info_section = ft.Container(
            content=ft.Column([
                ft.Text("Robot Information", size=16, weight=ft.FontWeight.BOLD),
                ft.Divider(),
                self.e_number_label,
                self.model_label,
                self.file_buttons_container,
            ]),
            visible=False,
            padding=10,
            border=ft.border.all(width=1, color=ft.colors.BLUE_100),
            border_radius=10,
            margin=ft.margin.only(top=10, bottom=10)
        )

        # USB devices section
        self.usb_dropdown = ft.Dropdown(
            label="Select USB drive",
            width=200,
            options=[],
            visible=False,
            on_change=self.on_usb_dropdown_change
        )
        
        self.create_sw_button = ft.ElevatedButton(
            text=" Create SW ",
            width=120,
            visible=False,
            on_click=self.on_create_sw_click
        )
        
        self.usb_version_label = ft.Text(
            "SW version on USB: Not detected",
            visible=False,
            size=14
        )
        
        # Container for USB section
        self.usb_section = ft.Container(
            content=ft.Column([
                ft.Text("Create Robot Software", size=16, weight=ft.FontWeight.BOLD),
                ft.Divider(),
                ft.Row([
                    self.usb_dropdown,
                    self.create_sw_button
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                self.usb_version_label
            ]),
            visible=False,
            padding=10,
            border=ft.border.all(width=1, color=ft.colors.BLUE_100),
            border_radius=10,
            margin=ft.margin.only(top=10)
        )
        
        # USB detection thread
        self.usb_detection_active = False
        self.usb_thread = None

        self.content = ft.Column(
            controls=[
                ft.Divider(height=20, color="transparent"),
                ft.Text(self.label, weight=ft.FontWeight.BOLD, size=18, text_align=ft.TextAlign.CENTER),
                self.spot_e_number_label,  
                ft.Container(expand=1),
                ft.Container(
                    content=self.timer.build(),
                    expand=1,
                    alignment=ft.alignment.bottom_center
                ),
                ft.Container(
                    content=ft.TextButton("Reset", on_click=self.reset_spot),
                    alignment=ft.alignment.center,
                    padding=ft.padding.all(10) 
                ),
            ],
            expand=True,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=0
        )

        self.dlg_modal = ft.AlertDialog(
            modal=False,
            barrier_color=ft.colors.BLACK26,
            title=ft.Text("Spot Details", text_align=ft.TextAlign.CENTER),
            title_padding=ft.padding.symmetric(horizontal=0, vertical=10),
            content=ft.Column(
                controls=[
                    ft.Container(content=self.wo_number_field, expand=0, alignment=ft.alignment.center),
                    
                    ft.Container(content=self.robot_info_section, expand=0, alignment=ft.alignment.center),
                    ft.Container(content=self.usb_section, expand=0, alignment=ft.alignment.center),
                    ft.Container(content=self.status_dropdown, expand=0, alignment=ft.alignment.center),
                    ft.Container(content=self.snack_bar, expand=0, alignment=ft.alignment.center),
                ],
                height=500,  # Увеличиваем высоту для размещения всех разделов
                width=400,
                alignment=ft.MainAxisAlignment.START,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            actions_alignment=ft.MainAxisAlignment.CENTER,
            content_padding=ft.padding.all(20),
            on_dismiss=self.on_dialog_dismiss
        )

        self.container = ft.Container(
            content=self.content,
            **spot_style["main"],
            on_click=self.open_dialog
        )
        
        # Инициализируем данные WO номера при создании спота
        if spot_data.get("wo_number") and len(spot_data["wo_number"]) == 8:
            self.process_wo_number(spot_data["wo_number"])
        
        self.update_color()
        self.timer.on_state_change = self.update_spot_state
        
        # Сохраняем WO данные для использования при создании SW
        self.wo_data = {}

    def update_status(self, e):
        new_status = e.control.value
        self.controller.set_spot_status(int(self.station_id), self.spot_id, new_status)
        self.update_color()

    def update_wo_number(self, e):
        wo_number = e.control.value
        spot = self.controller.get_spot_data(int(self.station_id), self.spot_id)
        spot["wo_number"] = wo_number
        self.controller.save_spots_state()
        
        # Process WO number to find files and update UI
        self.process_wo_number(wo_number)
        
    def process_wo_number(self, wo_number):
        # Очищаем предыдущую информацию
        self.file_buttons_container.content = ft.Row([])
        self.file_buttons_container.visible = False
        self.e_number_label.value = "E-number: Please enter WO-number"
        self.model_label.value = "Model: Unknown"
        self.spot_e_number_label.value = ""
        self.spot_e_number_label.visible = False
        self.robot_info_section.visible = False
        self.wo_data = {"wo_number": wo_number}  # Сохраняем WO номер
        
        # Сбрасываем флаг найденного WO
        self.wo_found = False
        
        # Обновляем бордер на основе текущего состояния
        self.update_border()
        
        if not wo_number or len(wo_number) != 8 or not wo_number.isdigit():
            self.page.update()
            return
            
        # Search for files
        result = self.ro_tools.search_wo_files(wo_number)
        
        if "error" in result:
            self.e_number_label.value = "E-number: Not found"
            self.model_label.value = "Model: Unknown"
            
            self.snack_bar.content.value = f"SW on Server for WO {wo_number} not found"
            self.snack_bar.open = True
            
            # Скрываем USB секцию и Robot Info секцию
            self.usb_section.visible = False
            self.robot_info_section.visible = False
            
            self.page.update()
            
            # Останавливаем мониторинг USB
            self.ro_tools.unregister_usb_detection_callback(self.update_usb_drives_callback)
            
            return
            
        self.wo_found = True
        self.wo_data = result  # Сохраняем данные о WO
        
        self.update_border()
        
        # Показываем USB секцию
        self.usb_section.visible = True
        
        # Показываем Robot Info секцию
        self.robot_info_section.visible = True
        
        # Запускаем мониторинг USB устройств
        self.ro_tools.register_usb_detection_callback(self.update_usb_drives_callback)
        
        # Инициируем первое обновление списка USB
        initial_drives = self.ro_tools.get_connected_usb_drives()
        self.update_usb_drives(initial_drives)
            
        # Update E-number and model display
        if result.get("e_number") and isinstance(result["e_number"], dict):
            e_number_data = result["e_number"]
            e_number_value = e_number_data.get("e_number", "Not found")
            model_value = e_number_data.get("model", "Unknown")
            
            if e_number_value != "Not found":
                self.e_number_label.value = f"E-number: {e_number_value}"
            else:
                self.e_number_label.value = "E-number: Not found"
                
            if model_value != "Unknown":
                self.model_label.value = f"Model: {model_value}"
            else:
                self.model_label.value = "Model: Unknown"
            
            # Update the spot container label with combined info if both are present
            if e_number_value != "Not found" or model_value != "Unknown":
                display_info = []
                if e_number_value != "Not found":
                    display_info.append(e_number_value)
                if model_value != "Unknown":
                    display_info.append(model_value)
                
                self.spot_e_number_label.value = " - ".join(display_info)
                self.spot_e_number_label.visible = True
        else:
            self.e_number_label.value = "E-number: Not found"
            self.model_label.value = "Model: Unknown"
            
        # Create file buttons if files were found
        buttons = []
        if result.get("dat_file"):
            buttons.append(
                ft.ElevatedButton(
                    text=" Show SW on server ",
                    on_click=lambda e, f=result["dat_file"]: self.open_file(f)
                )
            )
        
        if result.get("pdf_file"):
            buttons.append(
                ft.ElevatedButton(
                    text=" Show BOM ",
                    on_click=lambda e, f=result["pdf_file"]: self.open_file(f)
                )
            )
            
        if buttons:
            self.file_buttons_container.content = ft.Row(
                buttons, 
                spacing=10, 
                alignment=ft.MainAxisAlignment.CENTER
            )
            self.file_buttons_container.visible = True
            
        self.page.update()
    
    def update_usb_drives_callback(self, drives):
        """Callback для обновления списка USB-дисков"""
        try:
            # Безопасно выполняем обновление через стандартный update страницы
            self.update_usb_drives(drives)
            self.page.update()
        except Exception as e:
            print(f"Error in update_usb_drives_callback: {str(e)}")
    
    def update_usb_drives(self, drives):
        """Обновляет список USB-дисков в выпадающем списке"""
        try:
            # Запоминаем текущее значение
            current_value = self.usb_dropdown.value
            
            # Обновляем опции
            options = []
            current_value_exists = False
            
            for drive_path, drive_label in drives:
                option = ft.dropdown.Option(drive_path, text=drive_label)
                options.append(option)
                if drive_path == current_value:
                    current_value_exists = True
            
            self.usb_dropdown.options = options
            
            # Если нет дисков или текущее значение не существует
            if not options:
                # Нет подключенных дисков
                self.usb_dropdown.value = None
                self.usb_version_label.value = "No USB drives detected"
                self.usb_dropdown.visible = False
                self.create_sw_button.visible = False
                self.usb_version_label.visible = True
            else:
                # Есть подключенные диски
                if not current_value_exists or current_value is None:
                    self.usb_dropdown.value = options[0].key
                
                self.usb_dropdown.visible = True
                self.create_sw_button.visible = True
                self.usb_version_label.visible = True
                
                # Обновляем информацию о версии для выбранного диска
                self.update_usb_version_label()
            
        except Exception as e:
            print(f"Error updating USB drives: {str(e)}")
            traceback.print_exc()
    
    def update_usb_version_label(self):
        """Обновляет надпись с версией SW на USB"""
        if not self.usb_dropdown.value:
            self.usb_version_label.value = "SW version on USB: Not detected"
            return
        
        version = self.ro_tools.check_sw_version(self.usb_dropdown.value)
        if version:
            self.usb_version_label.value = f"SW version on USB: {version}"
        else:
            self.usb_version_label.value = "SW version on USB: No version file found"
    
    def on_create_sw_click(self, e):
        """Обработчик нажатия на кнопку Create SW"""
        if not self.usb_dropdown.value:
            self.snack_bar.content.value = "Please select a USB drive first"
            self.snack_bar.open = True
            self.page.update()
            return
            
        # Передаем данные WO в функцию создания ПО
        success, message = self.ro_tools.create_robot_sw(self.usb_dropdown.value, self.wo_data)
        self.snack_bar.content.value = message
        self.snack_bar.open = True
        
        # Если успешно, обновляем версию ПО
        if success:
            self.update_usb_version_label()
            
        self.page.update()
    
    def on_usb_dropdown_change(self, e):
        """Обработчик изменения выбранного USB-накопителя"""
        self.update_usb_version_label()
        self.page.update()
    
    def open_file(self, file_path):
        success = self.ro_tools.open_file(file_path)
        if not success:
            self.snack_bar.content.value = f"Failed to open the file"
            self.snack_bar.open = True
            self.page.update()

    def open_dialog(self, e):
        if not self.dlg_modal.open:
            if self.dlg_modal not in self.page.overlay:
                self.page.overlay.append(self.dlg_modal)
            self.status_dropdown.visible = self.page.config.is_dashboard_test_mode_enabled()
            
            # Process WO number when opening dialog to update UI
            self.process_wo_number(self.wo_number_field.value)
            
            # Явно вызываем обновление списка USB перед открытием диалога
            if self.wo_found:
                drives = self.ro_tools.get_connected_usb_drives()
                self.update_usb_drives(drives)
                print(f"Found {len(drives)} USB drives when opening dialog")
                
            self.dlg_modal.open = True
            self.page.update()
        
        # Если WO найден, запускаем мониторинг USB
        if self.wo_found:
            self.ro_tools.register_usb_detection_callback(self.update_usb_drives_callback)

    def handle_close(self, e):
        if self.dlg_modal.open:
            self.dlg_modal.open = False
            self.page.update()
    
    def on_dialog_dismiss(self, e):
        """Обработчик закрытия диалога"""
        # Останавливаем мониторинг USB при закрытии диалога
        self.ro_tools.unregister_usb_detection_callback(self.update_usb_drives_callback)

    def update_spot_state(self):
        # Получаем данные о споте
        spot = self.controller.get_spot_data(int(self.station_id), self.spot_id)
        
        # Обновляем состояние таймера
        if spot["running"]:
            self.timer_state = "running"
        elif spot["elapsed_time"] > 0:
            self.timer_state = "paused"
        else:
            self.timer_state = "stopped"
        
        # Обновляем бордер в зависимости от состояния таймера и WO
        self.update_border()
        
        # Обновляем цвет фона в зависимости от статуса
        self.update_color()
        self.page.update()
    
    def update_border(self):
        
        if self.wo_found:
            self.container.border = ft.border.all(width=1.5, color=ft.colors.GREEN)
        
        else:
            self.container.border = spot_style["main"]["border"]
            
        # Обновляем контейнер если он уже на странице
        if self.container.page:
            self.container.update()

    def update_color(self):
        spot = self.controller.get_spot_data(int(self.station_id), self.spot_id)
        status = spot["status"]
        statuses = self.controller.config.get_spot_statuses()
        new_color = next((s["color"] for s in statuses if s["name"] == status), ft.colors.WHITE60)
        self.container.bgcolor = new_color
        if self.container.page:
            self.container.update()

    def reset_spot(self, e):
        default_status = self.controller.config.get_status_names()[0]
        self.controller.set_spot_status(int(self.station_id), self.spot_id, default_status)
        spot = self.controller.get_spot_data(int(self.station_id), self.spot_id)
        spot["wo_number"] = ""
        self.wo_number_field.value = ""
        
        # Clear file buttons and E-number/model info
        self.file_buttons_container.content = ft.Row([])
        self.file_buttons_container.visible = False
        self.e_number_label.value = "E-number: Not found"
        self.model_label.value = "Model: Unknown"
        # Очищаем также надпись в основном контейнере спота
        self.spot_e_number_label.value = ""
        self.spot_e_number_label.visible = False
        
        # Скрываем Robot Info секцию
        self.robot_info_section.visible = False
        
        # Сбрасываем флаг найденного WO и состояние таймера
        self.wo_found = False
        self.timer_state = "stopped"
        
        # Возвращаем бордер к исходному состоянию
        self.container.border = spot_style["main"]["border"]
        
        self.timer.reset()
        self.status_dropdown.value = default_status
        self.update_color()
        self.page.update()
        
        # Останавливаем мониторинг USB
        self.ro_tools.unregister_usb_detection_callback(self.update_usb_drives_callback)
        
        # Скрываем USB секцию
        self.usb_section.visible = False
        
        # Очищаем данные WO
        self.wo_data = {}

    def build(self):
        return self.container