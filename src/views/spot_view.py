import flet as ft
import os
import threading
import time
import traceback
from controllers.timer_component import TimerComponent
from controllers.ro_customization_tools import ROCustomizationController

spot_style: dict = {
    "main": {
        "expand": True,
        "bgcolor": ft.Colors.WHITE60,
        "border_radius": 20,
        "border": ft.border.all(width=1, color=ft.Colors.GREY_300),
        "ink": True,
        # "shadow" убран
    },
}

class Spot:
    def __init__(self, name: str, station_id: str, spot_id: str, page: ft.Page, controller):
        self.name = name
        self.station_id = station_id
        self.spot_id = spot_id
        self.page = page
        self.controller = controller
        self.is_ftl = (station_id == "FTL" or str(station_id) == "0" or station_id == 0)
        self.timer = None
        if not self.is_ftl:
            try:
                self.timer = TimerComponent(page, station_id, spot_id, controller)
            except Exception as ex:
                self.timer = None
        self.label = f"Spot {self.spot_id[-1]}"
        
        # Определяем, запущено ли приложение в браузере
        self.is_web = page.platform == "web"
        
        self.ro_tools = ROCustomizationController(controller.config)
        
        self.timer_state = "stopped"  
        self.wo_found = False  

        # Для FTL station_id не приводим к int
        if self.station_id == "FTL":
            spot_data = self.controller.get_spot_data(self.station_id, spot_id)
        else:
            spot_data = self.controller.get_spot_data(int(station_id), spot_id)
        # Pass config explicitly
        config = self.controller.config
        self.status_dropdown = ft.Dropdown(
            label="Status",
            value=spot_data["status"],
            options=[ft.dropdown.Option(status) for status in config.get_status_names()],
            on_change=self.update_status,
            width=250,
            visible=config.is_dashboard_test_mode_enabled()
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
        self.spot_e_number_label = ft.Text(
            "", 
            size=18, 
            text_align=ft.TextAlign.CENTER, 
            visible=False,
            height=20  # Fixed height to prevent shifting
        )
        
        self.file_buttons_container = ft.Container(
            content=ft.Row([]),
            visible=False
        )
        self.snack_bar = ft.SnackBar(
            content=ft.Text(""), 
            open=False,
            bgcolor=ft.Colors.BLUE_GREY_200, 
            duration=5000,  # Increased display time (5 seconds)
        )
        
        # Find DT button
        self.find_dt_button = ft.ElevatedButton(
            text=" Find DT ",
            on_click=self.on_find_dt_click,
            visible=False
        )

        # Robot Info section
        self.robot_info_section = ft.Container(
            content=ft.Column([
                ft.Text("Robot Information", size=16, weight=ft.FontWeight.BOLD),
                ft.Divider(),
                self.e_number_label,
                self.model_label,
                ft.Divider(),
                self.file_buttons_container  
            ]),
            visible=False,
            padding=10,
            border=ft.border.all(width=1, color=ft.Colors.ON_PRIMARY_CONTAINER),
            border_radius=20,
            margin=ft.margin.only(top=10, bottom=3)
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
            width=150,
            visible=False,
            on_click=self.on_create_sw_click
        )
        self.create_aoa_button = ft.ElevatedButton(
            text=" Create AOA Folder ",
            width=160,
            visible=False,
            on_click=self.on_create_aoa_click
        )
        self.open_orderfil_button = ft.ElevatedButton(
            text=" Show orderfil on USB ",
            width=160,
            visible=False,
            on_click=self.on_open_orderfil_click
        )
        self.move_backups_button = ft.ElevatedButton(
            text=" Move Backups ",
            width=130,
            visible=False,
            on_click=self.on_move_backups_click
        )
        self.usb_version_label = ft.Text(
            "SW version on USB: Not detected",
            visible=False
        )
        
        
        self.usb_section = ft.Container(
            content=ft.Column([
                ft.Text(" Robot Software and Backups ", size=16, weight=ft.FontWeight.BOLD),
                ft.Divider(),
                ft.Row([
                    self.usb_dropdown,
                    self.create_sw_button
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                self.usb_version_label,
                ft.Divider(),
                ft.Row([
                    self.create_aoa_button,
                    self.open_orderfil_button,
                    self.move_backups_button
                ], alignment=ft.MainAxisAlignment.CENTER, wrap=True, spacing=5),
                
            ]),
            visible=False,
            padding=10,
            border=ft.border.all(width=1, color=ft.Colors.ON_PRIMARY_CONTAINER),
            border_radius=20,
            margin=ft.margin.only(top=3)        )
        
        self.usb_detection_active = False
        self.usb_thread = None
        
        # Таймер и кнопки только если self.timer существует и не None
        timer_controls = []
        if self.timer is not None:
            try:
                timer_controls.append(
                    ft.Container(
                        content=ft.Container(
                            content=ft.Column([
                                self.timer.build_buttons(),
                                ft.Container(height=10, visible=False)
                            ], spacing=5,
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            alignment=ft.MainAxisAlignment.CENTER),
                            border_radius=20,
                            padding=ft.padding.all(10),
                        ),
                        expand=0,
                        alignment=ft.alignment.center,
                        padding=ft.padding.symmetric(horizontal=40),
                    )
                )
                timer_controls.append(
                    ft.Container(
                        content=ft.ElevatedButton(
                            content=ft.Row([
                                ft.Icon(ft.Icons.RESTART_ALT, size=20),
                                ft.Text("Reset", size=15, weight=ft.FontWeight.BOLD),
                            ], spacing=8, alignment=ft.MainAxisAlignment.CENTER),
                            on_click=self.reset_spot,
                            style=ft.ButtonStyle(
                                padding=ft.padding.symmetric(horizontal=10, vertical=4),
                            ),
                            height=26,
                            width=100,
                        ),
                        alignment=ft.alignment.center,
                        expand=0,
                        padding=ft.padding.only(bottom=10),
                    )
                )
            except Exception as ex:
                pass
        self.content = ft.Column(
            controls=[
                ft.Container(
                    content=ft.Text(self.label, weight=ft.FontWeight.BOLD, size=22, text_align=ft.TextAlign.CENTER),
                    padding=ft.padding.only(top=10),
                    expand=0,
                ),
                ft.Container(
                    content=self.spot_e_number_label,
                    expand=1,
                    alignment=ft.alignment.center
                ),
            ] + timer_controls,
            expand=1,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=10,
            alignment=ft.MainAxisAlignment.START
        )

        
        modal_timer_controls = []
        if self.timer is not None:
            modal_timer_controls.append(
                ft.Container(
                    content=self.timer.build_buttons(),
                    border_radius=20,
                    padding=ft.padding.all(10),
                    alignment=ft.alignment.center,
                )
            )
        modal_content = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Container(content=self.wo_number_field, alignment=ft.alignment.center),
                    ft.Container(content=self.status_dropdown, alignment=ft.alignment.center),
                ] + modal_timer_controls + [
                    ft.Container(content=self.robot_info_section, alignment=ft.alignment.center),
                    ft.Container(content=self.usb_section, alignment=ft.alignment.center),
                    ft.Container(content=self.snack_bar, alignment=ft.alignment.center),
                ],
                alignment=ft.MainAxisAlignment.START,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=20,
                tight=True,  
            ),
            padding=0,
            height=None,  
            width=500,    
        )

        self.dlg_modal = ft.AlertDialog(
            modal=False,
            barrier_color=ft.Colors.BLACK26,
            title=ft.Text("Spot Details", text_align=ft.TextAlign.CENTER),
            title_padding=ft.padding.symmetric(horizontal=0, vertical=10),
            content=modal_content,
            actions_alignment=ft.MainAxisAlignment.CENTER,
            content_padding=ft.padding.all(20),
            on_dismiss=self.on_dialog_dismiss,
        )

        # --- status bar (цветная полоса статуса) ---
        self.status_bar_color = ft.Colors.GREY_100  # default
        self.status_bar = ft.Container(
            width=22,  
            bgcolor=self.status_bar_color,
            expand=False,
            border=None,  # УБРАТЬ border, если был
            margin=0,
            padding=0,
            border_radius=ft.border_radius.only(top_left=spot_style["main"]["border_radius"], bottom_left=spot_style["main"]["border_radius"]),
        )
        main_content_container = ft.Container(
            content=self.content,
            expand=True,
            bgcolor=ft.Colors.WHITE,  # Явно белый фон для карточки
            border_radius=ft.border_radius.only(top_right=spot_style["main"]["border_radius"], bottom_right=spot_style["main"]["border_radius"]),
            ink=spot_style["main"]["ink"],
            on_click=self.open_dialog,
            border=None,  # УБРАТЬ border, если был
            margin=0,
            padding=0,
        )
        # --- общий border для всего блока (Row) ---
        self.container = ft.Container(
            content=ft.Row([
                self.status_bar,
                main_content_container
            ], expand=1, spacing=0, tight=True),  
            border=spot_style["main"]["border"],
            border_radius=spot_style["main"]["border_radius"],
            bgcolor=None,  # убираем фон у общего контейнера
            expand=1,
            margin=ft.margin.symmetric(vertical=8, horizontal=0),
        )
        
        # Initialize WO number data when creating the spot
        if spot_data.get("wo_number") and len(spot_data["wo_number"]) == 8:
            self.process_wo_number(spot_data["wo_number"])
        
        self.update_Color()
        self.timer.on_state_change = self.update_spot_state
        
        # Save WO data for use when creating SW
        self.wo_data = {}

    def update_status(self, e):
        new_status = e.control.value
        self.controller.set_spot_status(int(self.station_id), self.spot_id, new_status)
        self.update_Color()

    def update_wo_number(self, e):
        wo_number = e.control.value
        spot = self.controller.get_spot_data(int(self.station_id), self.spot_id)
        spot["wo_number"] = wo_number
        self.controller.save_spots_state()
        
        # Process WO number to find files and update UI
        self.process_wo_number(wo_number)
        
    def process_wo_number(self, wo_number):
        # Clear previous information
        self.file_buttons_container.content = ft.Row([])
        self.file_buttons_container.visible = False
        self.e_number_label.value = "E-number: Please enter WO-number"
        self.model_label.value = "Model: Unknown"
        self.spot_e_number_label.value = ""
        self.spot_e_number_label.visible = False
        self.robot_info_section.visible = False
        self.find_dt_button.visible = False
        self.create_aoa_button.visible = False
        self.open_orderfil_button.visible = False
        self.move_backups_button.visible = False
        self.wo_data = {"wo_number": wo_number}  # Save WO number
        
        # Reset WO found flag
        self.wo_found = False
        
        # Update border based on current state
        self.update_border()
        
        if not wo_number or len(wo_number) != 8 or not wo_number.isdigit():
            self.page.update()
            return
            
        # Search for files
        result = self.ro_tools.search_wo_files(wo_number)
        
        if "error" in result:
            self.e_number_label.value = "E-number: Not found"
            self.model_label.value = "Model: Unknown"
            
            # Use snackbar for this message
            self.snack_bar.content = ft.Text(f"SW on Server for WO {wo_number} not found")
            self.snack_bar.open = True
            self.page.update()
            
            # Hide USB section and Robot Info section
            self.usb_section.visible = False
            self.robot_info_section.visible = False
            
            self.page.update()
                
            # Stop USB monitoring
            self.ro_tools.unregister_usb_detection_callback(self.update_usb_drives_callback)
            
            return
            
        self.wo_found = True
        self.wo_data = result  # Save WO data
        
        self.update_border()
        
        # Show USB section
        self.usb_section.visible = True
        
        # Show Robot Info section
        self.robot_info_section.visible = True
        
        # Start USB device monitoring
        self.ro_tools.register_usb_detection_callback(self.update_usb_drives_callback)
        
        # Initiate first update of USB list
        initial_drives = self.ro_tools.get_connected_usb_drives()
        self.update_usb_drives(initial_drives)
        
        # Set button visibility based on USB presence
        # Check performed in update_usb_drives method
        
        # Update E-number and model display
        if result.get("e_number") and isinstance(result["e_number"], dict):
            e_number_data = result["e_number"]
            # Make sure we have string values, not None
            e_number_value = e_number_data.get("e_number", "Not found") or "Not found"
            model_value = e_number_data.get("model", "Unknown") or "Unknown"
            
            if e_number_value != "Not found":
                self.e_number_label.value = f"E-number: {e_number_value}"
                # Show Find DT button only if E-number is found
                self.find_dt_button.visible = True
            else:
                self.e_number_label.value = "E-number: Not found"
                self.find_dt_button.visible = False
                
            if model_value != "Unknown":
                self.model_label.value = f"Model: {model_value}"
            else:
                self.model_label.value = "Model: Unknown"
            
            # Update the spot container label with combined info if both are present
            if e_number_value != "Not found" or model_value != "Unknown":
                display_info = []
                if e_number_value != "Not found" and e_number_value:
                    display_info.append(str(e_number_value))
                if model_value != "Unknown" and model_value:
                    display_info.append(str(model_value))
                
                # Check if the list is not empty before joining
                if display_info:
                    self.spot_e_number_label.value = " - ".join(display_info)
                    self.spot_e_number_label.visible = True
                else:
                    self.spot_e_number_label.value = ""
                    self.spot_e_number_label.visible = False
        else:
            self.e_number_label.value = "E-number: Not found"
            self.model_label.value = "Model: Unknown"
            self.find_dt_button.visible = False
            
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
        
        # Add Find DT button in the same row of buttons
        if e_number_value != "Not found":
            buttons.append(
                self.find_dt_button
            )
            self.find_dt_button.visible = True
            self.create_aoa_button.visible = True
            self.open_orderfil_button.visible = True
            self.move_backups_button.visible = True
        else:
            self.find_dt_button.visible = False
            self.create_aoa_button.visible = False
            self.open_orderfil_button.visible = False
            self.move_backups_button.visible = False
            
        if buttons:
            self.file_buttons_container.content = ft.Row(
                buttons, 
                spacing=10, 
                alignment=ft.MainAxisAlignment.CENTER
            )
            self.file_buttons_container.visible = True
            
        self.page.update()
    
    def update_usb_drives_callback(self, drives):
        """Callback for updating USB drive list"""
        try:
            self.update_usb_drives(drives)
            self.page.update()
        except Exception as e:
            print(f"Error in update_usb_drives_callback: {str(e)}")
    
    def update_usb_drives(self, drives):
        try:
            current_value = self.usb_dropdown.value
            
            # Update options
            options = []
            current_value_exists = False
            
            for drive_path, drive_label in drives:
                option = ft.dropdown.Option(drive_path, text=drive_label)
                options.append(option)
                if drive_path == current_value:
                    current_value_exists = True
            
            self.usb_dropdown.options = options
            
            if not options:
                self.usb_dropdown.value = None
                self.usb_version_label.value = "No USB drives detected"
                self.usb_dropdown.visible = False
                self.create_sw_button.visible = False
                self.create_aoa_button.visible = False
                self.open_orderfil_button.visible = False
                self.move_backups_button.visible = False
                self.usb_version_label.visible = True
            else:
                if not current_value_exists or current_value is None:
                    self.usb_dropdown.value = options[0].key
                        
                self.usb_dropdown.visible = True
                self.create_sw_button.visible = True
                self.open_orderfil_button.visible = True
                
                # Show AOA button only if E-number is found
                if "e_number" in self.wo_data and isinstance(self.wo_data["e_number"], dict):
                    e_number_value = self.wo_data["e_number"].get("e_number", "Not found")
                    self.create_aoa_button.visible = e_number_value != "Not found"
                    self.move_backups_button.visible = True
                else:
                    self.create_aoa_button.visible = False
                    self.move_backups_button.visible = False
                    
                self.usb_version_label.visible = True
                    
                # Update version info for selected drive
                self.update_usb_version_label()
            
        except Exception as e:
            print(f"Error updating USB drives: {str(e)}")
            traceback.print_exc()
    
    def update_usb_version_label(self):
        if not self.usb_dropdown.value:
            self.usb_version_label.value = "SW version on USB: Not detected"
            return
        
        version = self.ro_tools.check_sw_version(self.usb_dropdown.value)
        if version:
            self.usb_version_label.value = f"SW version on USB: {version}"
        else:
            self.usb_version_label.value = "SW version on USB: No version file found"
    
    def on_create_sw_click(self, e):
        if not self.usb_dropdown.value:
            # Use snackbar for notification
            self.snack_bar.content = ft.Text("Please select a USB drive first")
            self.snack_bar.open = True
            self.page.update()
            return
        
        if not self.wo_data.get("dat_file"):
            # Use snackbar for notification
            self.snack_bar.content = ft.Text("No SW file available for copying")
            self.snack_bar.open = True
            self.page.update()
            return
            
        success, message = self.ro_tools.create_robot_sw(self.usb_dropdown.value, self.wo_data)
        
        # Use enhanced snackbar instead of separate dialog
        if success:
            self.snack_bar.bgcolor = ft.Colors.GREEN_700  # Green for success
            self.snack_bar.content = ft.Text(
                f"✅ SW Created Successfully: {message}", 
                color=ft.Colors.WHITE,
                weight=ft.FontWeight.BOLD
            )
        else:
            self.snack_bar.bgcolor = ft.Colors.RED_700  # Red for error
            self.snack_bar.content = ft.Text(
                f"❌ SW Creation Failed: {message}", 
                color=ft.Colors.WHITE,
                weight=ft.FontWeight.BOLD
            )
        
        self.snack_bar.open = True
        self.page.update()
    
    def on_usb_dropdown_change(self, e):
        self.update_usb_version_label()
        self.page.update()
    
    def open_file(self, file_path):
        success = self.ro_tools.open_file(file_path)
        if not success:
            # Use snackbar for notification
            self.snack_bar.content = ft.Text("Failed to open the file")
            self.snack_bar.open = True
            self.page.update()

    def open_dialog(self, e):
        if not self.dlg_modal.open:
            if self.dlg_modal not in self.page.overlay:
                self.page.overlay.append(self.dlg_modal)
            self.status_dropdown.visible = self.controller.config.is_dashboard_test_mode_enabled()
            # self.status_dropdown.update()  # УДАЛЕНО, чтобы не было AssertionError
            # УБРАНО: self.process_wo_number(self.wo_number_field.value)
            # Explicitly call USB list update перед открытии диалога
            if self.wo_found:
                drives = self.ro_tools.get_connected_usb_drives()
                self.update_usb_drives(drives)
                print(f"Found {len(drives)} USB drives когда открытии диалога")
            self.robot_info_section.visible = self.wo_found
            self.usb_section.visible = self.wo_found
            # Set button visibility based on USB presence
            if not self.usb_dropdown.options or len(self.usb_dropdown.options) == 0:
                self.create_sw_button.visible = False
                self.create_aoa_button.visible = False
                self.open_orderfil_button.visible = False
                self.move_backups_button.visible = False
            self.dlg_modal.open = True
            self.page.update()
        if self.wo_found:
            self.ro_tools.register_usb_detection_callback(self.update_usb_drives_callback)

    def handle_close(self, e):
        if self.dlg_modal.open:
            self.dlg_modal.open = False
            self.page.update()
    
    def on_dialog_dismiss(self, e):
        """Dialog close handler"""
        # Stop USB monitoring when dialog closes
        self.ro_tools.unregister_usb_detection_callback(self.update_usb_drives_callback)

    def update_spot_state(self):
        # Get spot data
        spot = self.controller.get_spot_data(int(self.station_id), self.spot_id)
        
        # Update timer state
        if spot["running"]:
            self.timer_state = "running"
        elif spot["elapsed_time"] > 0:
            self.timer_state = "paused"
        else:
            self.timer_state = "stopped"
        
        # Update border based on timer state and WO
        self.update_border()
        
        # Update background color based on status
        self.update_Color()
        self.page.update()
    
    def update_border(self):
        # Бордер не должен меняться автоматически при запуске таймера или открытии модального окна
        # Больше не меняем цвет бордера в зависимости от wo_found или таймера
        self.container.border = spot_style["main"]["border"]
        if self.container.page:
            self.container.update()

    def update_Color(self):
        spot = self.controller.get_spot_data(int(self.station_id), self.spot_id)
        status = spot["status"]
        statuses = self.controller.config.get_spot_statuses()
        # Цвет для unblocked теперь просто GREY_300
        if status.lower() == "unblocked":
            new_Color = ft.Colors.GREY_300
        else:
            new_Color = next((s["color"] for s in statuses if s["name"] == status), ft.Colors.GREY_500)
        self.status_bar.bgcolor = new_Color
        # Бордер не меняем, только статус-бар
        self.status_dropdown.visible = self.controller.config.is_dashboard_test_mode_enabled()
        if self.container.page:
            self.status_bar.update()
            self.status_dropdown.update()

    def reset_spot(self, e):
        default_status = self.controller.config.get_status_names()[0]
        self.controller.set_spot_status(int(self.station_id), self.spot_id, default_status)
        spot = self.controller.get_spot_data(int(self.station_id), self.spot_id)
        spot["wo_number"] = ""
        self.wo_number_field.value = ""
        
        
        self.file_buttons_container.content = ft.Row([])
        self.file_buttons_container.visible = False
        self.e_number_label.value = "E-number: Not found"
        self.model_label.value = "Model: Unknown"
        # Clear the label in the main spot container as well
        self.spot_e_number_label.value = ""
        self.spot_e_number_label.visible = False
        
        # Hide Robot Info section
        self.robot_info_section.visible = False
        
        # Hide Find DT button
        self.find_dt_button.visible = False
        
        # Hide Create AOA Folder button
        self.create_aoa_button.visible = False
            
        # Hide Open orderfil.dat button
        self.open_orderfil_button.visible = False
        
        # Hide Move Backups button
        self.move_backups_button.visible = False
        
        # Reset WO found flag and timer state
        self.wo_found = False
        self.timer_state = "stopped"
        
        # Return border to initial state
        self.container.border = spot_style["main"]["border"]
        
        self.timer.reset()
        self.status_dropdown.value = default_status
        self.update_Color()
        self.page.update()
        
        # Stop USB monitoring
        self.ro_tools.unregister_usb_detection_callback(self.update_usb_drives_callback)
                
        # Hide USB section
        self.usb_section.visible = False
        
        # Clear WO data
        self.wo_data = {}

    def on_find_dt_click(self, e):
        """Find DT button handler"""
        if "e_number" not in self.wo_data or not isinstance(self.wo_data["e_number"], dict):
            # Use snackbar for notification
            self.snack_bar.content = ft.Text("No E-number information available")
            self.snack_bar.open = True
            self.page.update()
            return
        
        e_number = self.wo_data["e_number"].get("e_number")
        if not e_number:
            # Use snackbar for notification
            self.snack_bar.content = ft.Text("No E-number found")
            self.snack_bar.open = True
            self.page.update()
            return
        
        success, message = self.ro_tools.find_and_open_dt_file(e_number)
        
        # Use snackbar for notification
        self.snack_bar.content = ft.Text(message)
        self.snack_bar.open = True
        self.page.update()

    def on_create_aoa_click(self, e):
        if not self.usb_dropdown.value:
            # Use snackbar for notification
            self.snack_bar.content = ft.Text("Please select a USB drive first")
            self.snack_bar.open = True
            self.page.update()
            return
        
        # Check that we have WO number and E-number
        wo_number = self.wo_number_field.value
        e_number = None
        
        if "e_number" in self.wo_data and isinstance(self.wo_data["e_number"], dict):
            e_number = self.wo_data["e_number"].get("e_number")
        
        if not wo_number or len(wo_number) != 8:
            self.snack_bar.content = ft.Text("Valid WO number is required")
            self.snack_bar.open = True
            self.page.update()
            return
                
        if not e_number:
            self.snack_bar.content = ft.Text("No E-number found for this WO")
            self.snack_bar.open = True
            self.page.update()
            return
        
        # Call method to create folder
        success, message = self.ro_tools.create_aoa_folder(self.usb_dropdown.value, wo_number, e_number)
        
        # Use snackbar for notification
        self.snack_bar.content = ft.Text(message)
        self.snack_bar.open = True
        self.page.update()

    def on_move_backups_click(self, e):
        if not self.usb_dropdown.value:
            # Use snackbar for notification
            self.snack_bar.content = ft.Text("Please select a USB drive first")
            self.snack_bar.open = True
            self.page.update()
            return
        
        # Show message that moving process has started
        self.snack_bar.content = ft.Text("Moving backup folders, please wait...")
        self.snack_bar.open = True
        self.page.update()
        
        # Start moving process directly
        try:
            success, message = self.ro_tools.move_backup_folders(self.usb_dropdown.value)
            
            # Show operation result
            self.snack_bar.content = ft.Text(message)
            self.snack_bar.open = True
            self.page.update()
            
        except Exception as ex:
            print(f"Error moving backups: {str(ex)}")
            traceback.print_exc()
                
            # Show error message
            self.snack_bar.content = ft.Text(f"Error moving backups: {str(ex)}")
            self.snack_bar.open = True
            self.page.update()

    def on_open_orderfil_click(self, e):
        """Open orderfil.dat button handler"""
        if not self.usb_dropdown.value:
            # Use snackbar for notification
            self.snack_bar.content = ft.Text("Please select a USB drive first")
            self.snack_bar.open = True
            self.page.update()
            return
            
        # Call method to open orderfil.dat file
        success, message = self.ro_tools.open_orderfil_from_usb(self.usb_dropdown.value)
        
        # Show result with enhanced formatting
        if success:
            self.snack_bar.bgcolor = ft.Colors.GREEN_700
            self.snack_bar.content = ft.Text(
                f"✅ {message}", 
                color=ft.Colors.WHITE,
                weight=ft.FontWeight.BOLD
            )
        else:
            self.snack_bar.bgcolor = ft.Colors.RED_700
            self.snack_bar.content = ft.Text(
                f"❌ {message}", 
                color=ft.Colors.WHITE,
                weight=ft.FontWeight.BOLD
            )
        
        self.snack_bar.open = True
        self.page.update()

    def build(self):
        return self.container