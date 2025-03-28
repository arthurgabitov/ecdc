import flet as ft
from src.controllers.timer_component import TimerComponent
from src.controllers.ro_customization_tools import ROCustomizationController

spot_style: dict = {
    "main": {
        "expand": True,
        "bgcolor": ft.colors.WHITE60,
        "border_radius": 10,
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
        
        # E-number display label
        self.e_number_label = ft.Text("E-number: Please enter WO-number", size=16)
        
        # Container for file buttons
        self.file_buttons_container = ft.Container(
            content=ft.Row([]),
            visible=False
        )
        
        self.snack_bar = ft.SnackBar(content=ft.Text(""), open=False)

        self.content = ft.Column(
            controls=[
                ft.Divider(height=20, color="transparent"),
                ft.Text(self.label, size=18, text_align=ft.TextAlign.CENTER),
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
            title=ft.Text("Spot Details"),
            content=ft.Column(
                controls=[
                    ft.Container(content=self.e_number_label, expand=0, alignment=ft.alignment.center),
                    ft.Container(content=self.wo_number_field, expand=1, alignment=ft.alignment.center),
                    
                    ft.Container(content=self.file_buttons_container, expand=0, alignment=ft.alignment.center),
                    ft.Container(content=self.status_dropdown, expand=1, alignment=ft.alignment.center),
                    ft.Container(content=self.snack_bar, expand=1, alignment=ft.alignment.center),
                ],
                height=500,
                width=400,
                alignment=ft.MainAxisAlignment.START,
            ),
        )

        self.container = ft.Container(
            content=self.content,
            **spot_style["main"],
            on_click=self.open_dialog
        )
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
        # Clear previous file buttons
        self.file_buttons_container.content = ft.Row([])
        self.file_buttons_container.visible = False
        self.e_number_label.value = "E-number: Not found"
        
        if not wo_number or len(wo_number) != 8 or not wo_number.isdigit():
            self.page.update()
            return
            
        # Search for files
        result = self.ro_tools.search_wo_files(wo_number)
        
        if "error" in result:
            self.e_number_label.value = "E-number: Not found"
            # Показываем сообщение в snack_bar если файлы не найдены
            self.snack_bar.content.value = f"SW for {wo_number} not found"
            self.snack_bar.open = True
            self.page.update()
            return
            
        # Update E-number display
        if result.get("e_number") and isinstance(result["e_number"], dict):
            e_number_data = result["e_number"]
            if e_number_data.get("e_number"):
                self.e_number_label.value = f"E-number: {e_number_data['e_number']}"
            else:
                self.e_number_label.value = "E-number: Not found"
        else:
            self.e_number_label.value = "E-number: Not found"
            
        # Create file buttons if files were found
        buttons = []
        if result.get("dat_file"):
            buttons.append(
                ft.ElevatedButton(
                    text="Open DAT",
                    on_click=lambda e, f=result["dat_file"]: self.open_file(f)
                )
            )
        
        if result.get("pdf_file"):
            buttons.append(
                ft.ElevatedButton(
                    text="Open PDF",
                    on_click=lambda e, f=result["pdf_file"]: self.open_file(f)
                )
            )
            
        if buttons:
            self.file_buttons_container.content = ft.Row(buttons, spacing=10)
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
        self.update_color()
        self.page.update()

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
        
        # Clear file buttons and E-number
        self.file_buttons_container.content = ft.Row([])
        self.file_buttons_container.visible = False
        self.e_number_label.value = "E-number: Not found"
        
        self.timer.reset()
        self.status_dropdown.value = default_status
        self.update_color()
        self.page.update()

    def build(self):
        return self.container