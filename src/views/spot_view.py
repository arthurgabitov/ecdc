import flet as ft
import os
import threading
import time
import traceback
from controllers.timer_component import TimerComponent
from controllers.ro_customization_tools import ROCustomizationController
from models.db_connector import get_user_wo_numbers, get_wo_e_number_and_model
from models.user_model import UserModel
from styles import BG_CARD, BG_CARD_ALT, BG_STATUS_BAR_DEFAULT, BG_SNACKBAR_SUCCESS, BG_SNACKBAR_ERROR, FONT_SIZE_LARGE, FONT_SIZE_MEDIUM, FONT_SIZE_NORMAL, FONT_SIZE_SMALL, FONT_SIZE_XL, FONT_SIZE_CARD_TITLE, FONT_SIZE_BUTTON, FONT_WEIGHT_BOLD, FONT_WEIGHT_NORMAL, BORDER_RADIUS_MAIN, PADDING_CARD, PADDING_BUTTON, TEXT_DEFAULT, TEXT_SECONDARY, SHADOW_CARD

spot_style: dict = {
    "main": {
        "expand": True,
        "bgcolor": ft.Colors.WHITE60,
        "border_radius": 20,
        "border": ft.border.all(width=1, color=ft.Colors.GREY_300),
        "ink": True,
        # "shadow" removed
    },
}

class Spot:
    def __init__(self, name: str, station_id: str, spot_id: str, page: ft.Page, controller):
        self.name = name
        self.station_id = station_id
        self.spot_id = spot_id
        self.page = page
        self.controller = controller
        
        self.timer = None
        try:
            self.timer = TimerComponent(page, station_id, spot_id, controller)
        except Exception as ex:
            self.timer = None
        self.label = f"Spot {self.spot_id[-1]}"
        
        # Determine if the app is running in a browser
        self.is_web = page.platform == "web"
        
        self.ro_tools = ROCustomizationController(controller.config)
        
        self.timer_state = "stopped"  
        self.wo_found = False  

        # Get spot data BEFORE using spot_data
        spot_data = self.controller.get_spot_data(int(station_id), spot_id)
        config = self.controller.config
        self.status_dropdown = ft.Dropdown(
            label="Status",
            value=spot_data["status"],
            options=[ft.dropdown.Option(status) for status in config.get_status_names()],
            on_change=self.update_status,
            width=250,
            visible=config.is_dashboard_test_mode_enabled()
        )

        # --- UI elements initialization (must be before any logic that uses them) ---
        self.file_buttons_container = ft.Container(content=ft.Row([]), visible=False)
        self.e_number_label = ft.Text("E-number: Please enter WO-number", size=FONT_SIZE_NORMAL)
        self.model_label = ft.Text("Model: Unknown", size=FONT_SIZE_NORMAL)
        self.spot_e_number_label = ft.Text("", size=FONT_SIZE_NORMAL, visible=False)
        self.robot_info_section = ft.Container(visible=False)
        self.find_dt_button = ft.ElevatedButton("Find DT", visible=False)
        self.create_aoa_button = ft.ElevatedButton("Create AOA Folder", visible=False)
        self.open_orderfil_button = ft.ElevatedButton("Open orderfil.dat", visible=False)
        self.move_backups_button = ft.ElevatedButton("Move Backups", visible=False)
        self.usb_section = ft.Container(visible=False)
        self.snack_bar = ft.SnackBar(content=ft.Text(""), open=False)
        self.generate_dt_button = ft.ElevatedButton("Generate DT", visible=False)
        
        # Restore WO number if present
        user_model = UserModel()
        current_sso = user_model.get_user_by_windows_login()
        wo_numbers = get_user_wo_numbers(current_sso)
        saved_wo = spot_data.get("wo_number", "")
        # Новый алгоритм: если сохранённый WO есть в списке с сервера, просто выбрать его, иначе сбросить спот
        if saved_wo and saved_wo in wo_numbers:
            self.wo_number_dropdown = ft.Dropdown(
                label="WO Number",
                options=[ft.dropdown.Option(str(wo)) for wo in wo_numbers],
                value=saved_wo,
                on_change=self.update_wo_number_from_dropdown,
                width=300,
                visible=True
            )
        else:
            # Если сохранённого WO нет в списке, сбросить спот
            self.wo_number_dropdown = ft.Dropdown(
                label="WO Number",
                options=[ft.dropdown.Option(str(wo)) for wo in wo_numbers],
                value="",
                on_change=self.update_wo_number_from_dropdown,
                width=300,
                visible=True
            )
            # Сбросить все секции, если WO невалидный
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
            self.usb_section.visible = False
            self.wo_found = False
        

        self.show_sw_on_server_button = ft.ElevatedButton(
            text=" Show SW on Server ",
            on_click=self.on_show_sw_on_server_click,
            visible=True
        )
        
        self.show_bom_button = ft.ElevatedButton(
            text=" Show BOM ",
            on_click=self.on_show_bom_click,
            visible=True
        )

        self.find_dt_button = ft.ElevatedButton(
            text=" Find DT ",
            on_click=self.on_find_dt_click,
            visible=False
        )
        
        self.generate_dt_button = ft.ElevatedButton(
            text=" Generate DT ",
            on_click=self.on_generate_dt_click,
            visible=False
        )
        



        self.robot_info_section = ft.Container(
            content=ft.Column([
                ft.Text("Robot Information", size=16, weight=ft.FontWeight.BOLD),
                ft.Divider(),
                self.e_number_label,
                self.model_label,
                ft.Row([
                    self.find_dt_button,
                    self.generate_dt_button,
                    self.show_sw_on_server_button,
                    self.show_bom_button
                ], alignment=ft.MainAxisAlignment.START, spacing=10),
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
            visible=False,
            font_family="Roboto-Light"
        )
        
        
        self.usb_section = ft.Container(
            content=ft.Column([
                ft.Text(" Robot Software and Backups ", size=16, weight=ft.FontWeight.BOLD, font_family="Roboto-Light"),
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
        
        # Timer and buttons only if self.timer exists and is not None
        timer_controls = []
        if self.timer is not None:
            try:
                timer_controls.append(
                    ft.Container(
                        content=ft.Container(
                            content=ft.Column([
                                ft.Row([
                                    self.timer.build_buttons()
                                ], alignment=ft.MainAxisAlignment.CENTER),
                                ft.Container(height=10, visible=False)
                            ], spacing=5,
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            alignment=ft.MainAxisAlignment.CENTER),
                            border_radius=20,
                            padding=ft.padding.all(10),
                            alignment=ft.alignment.center
                        ),
                        alignment=ft.alignment.center
                    )
                )
                timer_controls.append(
                    ft.Container(
                        content=ft.ElevatedButton(
                            content=ft.Row([
                                ft.Icon(ft.Icons.RESTART_ALT, size=20),
                                ft.Text("Reset", size=15, weight=ft.FontWeight.BOLD, font_family="Roboto-Light"),
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
                    content=ft.Text(self.label, weight=ft.FontWeight.BOLD, size=22, text_align=ft.TextAlign.CENTER, font_family="Roboto-Light"),
                    padding=ft.padding.only(top=10),
                    expand=0,
                    alignment=ft.alignment.center
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
                    padding=ft.padding.all(0),
                    alignment=ft.alignment.center,
                )
            )
        
        modal_content = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Container(content=self.wo_number_dropdown, alignment=ft.alignment.center, padding=ft.padding.only(right=12)),
                    ft.Container(content=self.status_dropdown, alignment=ft.alignment.center, padding=ft.padding.only(right=12)),
                
                    ft.Container(content=self.robot_info_section, alignment=ft.alignment.center, padding=ft.padding.only(right=12)),
                    ft.Container(content=self.usb_section, alignment=ft.alignment.center, padding=ft.padding.only(right=12)),
                    ft.Container(content=self.snack_bar, alignment=ft.alignment.center, padding=ft.padding.only(right=12)), ]
                ,
                alignment=ft.MainAxisAlignment.START,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=5,
                tight=True,
                scroll=ft.ScrollMode.AUTO,
            ),
            padding=0,
            height=None,
            width=500,
            expand=False,
        )

        self.dlg_modal = ft.AlertDialog(
            modal=False,
            barrier_color=ft.Colors.BLACK26,
            title=ft.Text("Spot Details", text_align=ft.TextAlign.CENTER, font_family="Roboto-Light"),
            title_padding=ft.padding.symmetric(horizontal=0, vertical=10),
            content=modal_content,
            actions_alignment=ft.MainAxisAlignment.CENTER,
            content_padding=ft.padding.all(20),
            on_dismiss=self.on_dialog_dismiss,
        )

        # --- status bar (colored status stripe) ---
        self.status_bar_color = ft.Colors.GREY_100  # default
        self.status_bar = ft.Container(
            width=28,  
            bgcolor=self.status_bar_color,
            expand=False,
            border=None,  # REMOVE border if present
            margin=0,
            padding=0,
            border_radius=ft.border_radius.only(top_left=spot_style["main"]["border_radius"], bottom_left=spot_style["main"]["border_radius"]),
        )
        main_content_container = ft.Container(
            content=self.content,
            expand=True,
            bgcolor=ft.Colors.WHITE,  # Explicit white background for the card
            border_radius=ft.border_radius.only(top_right=spot_style["main"]["border_radius"], bottom_right=spot_style["main"]["border_radius"]),
            ink=spot_style["main"]["ink"],
            on_click=self.open_dialog,
            border=None,  # REMOVE border if present
            margin=0,
            padding=0
        )
        # --- general border for the whole block (Row) ---
        self.container = ft.Container(
            content=ft.Row([
                self.status_bar,
                main_content_container
            ], expand=1, spacing=0, tight=True),  
            border=spot_style["main"]["border"],
            border_radius=spot_style["main"]["border_radius"],
            bgcolor=None,  # remove background from the general container
            expand=1,
            margin=ft.margin.symmetric(vertical=0, horizontal=0),
            shadow=SHADOW_CARD
        )
        # После создания всех UI-элементов:
        if saved_wo and len(saved_wo) == 8:
            self.wo_number_dropdown.value = saved_wo
            self.process_wo_number(saved_wo)
        
        self.update_Color()
        self.timer.on_state_change = self.update_spot_state
        
        # Save WO data for use when creating SW
        self.wo_data = {}
        # Восстановить UI полностью из состояния контроллера
        self.restore_ui_from_state()

    def restore_ui_from_state(self):
        spot_data = self.controller.get_spot_data(int(self.station_id), self.spot_id)
        # Восстановить статус
        self.status_dropdown.value = spot_data.get("status", self.controller.config.get_status_names()[0])
        # Восстановить WO
        wo = spot_data.get("wo_number", "")
        self.wo_number_dropdown.value = wo
        if wo and len(wo) == 8 and wo.isdigit():
            self.process_wo_number(wo)
        else:
            # Сбросить все секции, если WO невалидный
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
            self.usb_section.visible = False
            self.wo_found = False
        # Восстановить цвет и таймер
        self.update_Color()
        if self.timer:
            self.timer.restore_from_state()
        self.page.update()

    def update_status(self, e):
        new_status = e.control.value
        self.controller.set_spot_status(int(self.station_id), self.spot_id, new_status)
        self.update_Color()

    def update_wo_number_from_dropdown(self, e):
        wo_number = e.control.value
        spot = self.controller.get_spot_data(int(self.station_id), self.spot_id)
        spot["wo_number"] = wo_number
        self.controller.save_spots_state()
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
            
        # Get e_number and model from the database
        db_result = get_wo_e_number_and_model(wo_number)
        e_number_value = db_result.get("e_number") or "Not found"
        model_value = db_result.get("model") or "Unknown"
        self.wo_data["e_number"] = {"e_number": e_number_value, "model": model_value}
        # --- Update UI labels with robot info ---
        self.e_number_label.value = f"E-number: {e_number_value}"
        self.model_label.value = f"Model: {model_value}"
        # --- Update spot card label ---
        self.spot_e_number_label.value = f"{e_number_value} | {model_value}" if e_number_value != "Not found" else ""
        self.spot_e_number_label.visible = e_number_value != "Not found"
        # --- Get files for robot software section ---
        file_result = self.ro_tools.search_wo_files(wo_number)
        if file_result.get("dat_file"):
            self.wo_data["dat_file"] = file_result["dat_file"]
        if file_result.get("pdf_file"):
            self.wo_data["pdf_file"] = file_result["pdf_file"]
        # --- Show sections if data is available ---
        self.robot_info_section.visible = True
        self.usb_section.visible = True
        self.wo_found = True
        # --- Show Find DT button if E-number is found ---
        self.find_dt_button.visible = e_number_value != "Not found"
        self.generate_dt_button.visible = e_number_value != "Not found"
        self.update_border()
        # --- Update USB section if dialog is already open ---
        if hasattr(self, 'dlg_modal') and getattr(self.dlg_modal, 'open', False):
            drives = self.ro_tools.get_connected_usb_drives()
            self.update_usb_drives(drives)
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
            self.snack_bar.content = ft.Text("Please select a USB drive first", font_family="Roboto-Light")
            self.snack_bar.open = True
            self.page.update()
            return
        
        if not self.wo_data.get("dat_file"):
            # Use snackbar for notification
            self.snack_bar.content = ft.Text("No SW file available for copying", font_family="Roboto-Light")
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
            self.snack_bar.content = ft.Text("Failed to open the file", font_family="Roboto-Light")
            self.snack_bar.open = True
            self.page.update()

    def open_dialog(self, e):
        if not self.dlg_modal.open:
            if self.dlg_modal not in self.page.overlay:
                self.page.overlay.append(self.dlg_modal)
            self.status_dropdown.visible = self.controller.config.is_dashboard_test_mode_enabled()
            
            if self.wo_found:
                drives = self.ro_tools.get_connected_usb_drives()
                self.update_usb_drives(drives)
                
            self.robot_info_section.visible = self.wo_found
            self.usb_section.visible = self.wo_found
            self.generate_dt_button.visible = self.wo_found and ("e_number" in self.wo_data and isinstance(self.wo_data["e_number"], dict) and self.wo_data["e_number"].get("e_number", "Not found") != "Not found")
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
        # Unsubscribe from callback on close to avoid leaks
        self.ro_tools.unregister_usb_detection_callback(self.update_usb_drives_callback)
    
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
        # Border should not change automatically when starting the timer or opening the modal window
        # No longer change border color depending on wo_found or timer
        self.container.border = spot_style["main"]["border"]
        if self.container.page:
            self.container.update()

    def update_Color(self):
        spot = self.controller.get_spot_data(int(self.station_id), self.spot_id)
        status = spot["status"]
        statuses = self.controller.config.get_spot_statuses()
        # Color for unblocked is now just GREY_300
        if status.lower() == "unblocked":
            new_Color = ft.Colors.GREY_300
        else:
            new_Color = next((s["color"] for s in statuses if s["name"] == status), ft.Colors.GREY_500)
        self.status_bar.bgcolor = new_Color
        # Do not change border, only status bar
        self.status_dropdown.visible = self.controller.config.is_dashboard_test_mode_enabled()
        if self.container.page:
            self.status_bar.update()
        if self.status_dropdown.page:
            self.status_dropdown.update()

    def reset_spot(self, e):
        default_status = self.controller.config.get_status_names()[0]
        self.controller.set_spot_status(int(self.station_id), self.spot_id, default_status)
        spot = self.controller.get_spot_data(int(self.station_id), self.spot_id)
        spot["wo_number"] = ""
        self.wo_number_dropdown.value = ""
        
        
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
            self.snack_bar.content = ft.Text("No E-number information available", font_family="Roboto-Light")
            self.snack_bar.open = True
            self.page.update()
            return
        
        e_number = self.wo_data["e_number"].get("e_number")
        if not e_number:
            # Use snackbar for notification
            self.snack_bar.content = ft.Text("No E-number found", font_family="Roboto-Light")
            self.snack_bar.open = True
            self.page.update()
            return
        
        success, message = self.ro_tools.find_and_open_dt_file(e_number)
        
        # Use snackbar for notification
        self.snack_bar.content = ft.Text(message, font_family="Roboto-Light")
        self.snack_bar.open = True
        self.page.update()

    def on_create_aoa_click(self, e):
        if not self.usb_dropdown.value:
            # Use snackbar for notification
            self.snack_bar.content = ft.Text("Please select a USB drive first", font_family="Roboto-Light")
            self.snack_bar.open = True
            self.page.update()
            return
        
        # Check that we have WO number and E-number
        # Заменяем получение WO number на значение из Dropdown
        wo_number = self.wo_number_dropdown.value
        e_number = None
        
        if "e_number" in self.wo_data and isinstance(self.wo_data["e_number"], dict):
            e_number = self.wo_data["e_number"].get("e_number")
        
        if not wo_number or len(wo_number) != 8:
            self.snack_bar.content = ft.Text("Valid WO number is required", font_family="Roboto-Light")
            self.snack_bar.open = True
            self.page.update()
            return
                
        if not e_number:
            self.snack_bar.content = ft.Text("No E-number found for this WO", font_family="Roboto-Light")
            self.snack_bar.open = True
            self.page.update()
            return
        
        # Call method to create folder
        success, message = self.ro_tools.create_aoa_folder(self.usb_dropdown.value, wo_number, e_number)
        
        # Use snackbar for notification
        self.snack_bar.content = ft.Text(message, font_family="Roboto-Light")
        self.snack_bar.open = True
        self.page.update()

    def on_move_backups_click(self, e):
        if not self.usb_dropdown.value:
            # Use snackbar for notification
            self.snack_bar.content = ft.Text("Please select a USB drive first", font_family="Roboto-Light")
            self.snack_bar.open = True
            self.page.update()
            return
        
        # Show message that moving process has started
        self.snack_bar.content = ft.Text("Moving backup folders, please wait...", font_family="Roboto-Light")
        self.snack_bar.open = True
        self.page.update()
        
        # Start moving process directly
        try:
            success, message = self.ro_tools.move_backup_folders(self.usb_dropdown.value)
            
            # Show operation result
            self.snack_bar.content = ft.Text(message, font_family="Roboto-Light")
            self.snack_bar.open = True
            self.page.update()
            
        except Exception as ex:
            print(f"Error moving backups: {str(ex)}")
            traceback.print_exc()
                
            # Show error message
            self.snack_bar.content = ft.Text(f"Error moving backups: {str(ex)}", font_family="Roboto-Light")
            self.snack_bar.open = True
            self.page.update()

    def on_open_orderfil_click(self, e):
        """Open orderfil.dat button handler"""
        if not self.usb_dropdown.value:
            # Use snackbar for notification
            self.snack_bar.content = ft.Text("Please select a USB drive first", font_family="Roboto-Light")
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

    def on_show_sw_on_server_click(self, e):
        """Show SW on Server button handler"""
        wo_number = self.wo_data.get("wo_number")
        if not wo_number or len(wo_number) != 8:
            self.snack_bar.content = ft.Text("No valid WO number available", font_family="Roboto-Light")
            self.snack_bar.open = True
            self.page.update()
            return
        success, message = self.ro_tools.find_and_open_sw_file(wo_number)
        self.snack_bar.content = ft.Text(message, font_family="Roboto-Light")
        self.snack_bar.open = True
        self.page.update()

    def on_show_bom_click(self, e):
        """Show BOM button handler"""
        wo_number = self.wo_data.get("wo_number")
        if not wo_number or len(wo_number) != 8:
            self.snack_bar.content = ft.Text("No valid WO number available", font_family="Roboto-Light")
            self.snack_bar.open = True
            self.page.update()
            return
        success, message = self.ro_tools.find_and_open_bom_file(wo_number)
        self.snack_bar.content = ft.Text(message, font_family="Roboto-Light")
        self.snack_bar.open = True
        self.page.update()

    def on_generate_dt_click(self, e):
        from controllers.dt_generator import DTGenerator
        wo_number = self.wo_number_dropdown.value
        e_number = None
        usb_path = self.usb_dropdown.value
        if "e_number" in self.wo_data and isinstance(self.wo_data["e_number"], dict):
            e_number = self.wo_data["e_number"].get("e_number")
        if not wo_number or len(wo_number) != 8:
            self.snack_bar.content = ft.Text("Valid WO number is required", font_family="Roboto-Light")
            self.snack_bar.open = True
            self.page.update()
            return
        if not e_number:
            self.snack_bar.content = ft.Text("No E-number found for this WO", font_family="Roboto-Light")
            self.snack_bar.open = True
            self.page.update()
            return
        if not usb_path:
            self.snack_bar.content = ft.Text("Please select a USB drive first", font_family="Roboto-Light")
            self.snack_bar.open = True
            self.page.update()
            return
        generator = DTGenerator(self.controller.config)
        success, message = generator.generate_dt(wo_number, e_number, usb_path, self.ro_tools, self.snack_bar)
        self.snack_bar.content = ft.Text(message, font_family="Roboto-Light")
        self.snack_bar.open = True
        self.page.update()