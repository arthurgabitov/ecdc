import flet as ft
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
        
        
        self.e_number_label = ft.Text("E-number: Please enter WO-number", size=16, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER)
        
        
        self.model_label = ft.Text("Model: Unknown", size=16, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER)
        
        # E-number and model display label for spot container
        self.spot_e_number_label = ft.Text("", size=14, text_align=ft.TextAlign.CENTER, visible=False)
        
        
        self.file_buttons_container = ft.Container(
            content=ft.Row([]),
            visible=False
        )
        
        self.snack_bar = ft.SnackBar(content=ft.Text(""), open=False)

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
                    ft.Divider(),
                    ft.Container(content=self.e_number_label, expand=0, alignment=ft.alignment.center),
                    
                    ft.Container(content=self.model_label, expand=0, alignment=ft.alignment.center),
                    ft.Container(content=self.file_buttons_container, expand=0, alignment=ft.alignment.center),
                    
                    ft.Container(content=self.status_dropdown, expand=0, alignment=ft.alignment.center),
                    ft.Container(content=self.snack_bar, expand=0, alignment=ft.alignment.center),
                ],
                height=300,
                width=400,
                alignment=ft.MainAxisAlignment.START,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            actions_alignment=ft.MainAxisAlignment.CENTER,
            content_padding=ft.padding.all(20),
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
        
        self.file_buttons_container.content = ft.Row([])
        self.file_buttons_container.visible = False
        self.e_number_label.value = ""
        self.model_label.value = ""
        self.spot_e_number_label.value = ""
        self.spot_e_number_label.visible = False
        
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
            self.page.update()
            return
            
        
        self.wo_found = True
        
        
        self.update_border()
            
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
            
            self.dlg_modal.open = True
            self.page.update()

    def handle_close(self, e):
        if self.dlg_modal.open:
            self.dlg_modal.open = False
            self.page.update()

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
        
        # Сбрасываем флаг найденного WO и состояние таймера
        self.wo_found = False
        self.timer_state = "stopped"
        
        # Возвращаем бордер к исходному состоянию
        self.container.border = spot_style["main"]["border"]
        
        self.timer.reset()
        self.status_dropdown.value = default_status
        self.update_color()
        self.page.update()

    def build(self):
        return self.container