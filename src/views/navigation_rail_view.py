import flet as ft
from styles import BG_NAV_RAIL

class NavigationRailView:
    def __init__(self, page, menu_items, on_change_callback):
        self.page = page
        self.menu_items = menu_items  # List of dicts: {label, icon, selected_icon}
        self.on_change_callback = on_change_callback
        self.nav_rail = None

    def build(self):
        destinations = []
        for item in self.menu_items:
            destinations.append(
                ft.NavigationRailDestination(
                    icon=ft.Icon(item['icon']),
                    selected_icon=ft.Icon(item['selected_icon'], color=ft.Colors.YELLOW_700),
                    label_content=ft.Text(item['label'], font_family="Roboto-Light")
                )
            )
        self.nav_rail = ft.NavigationRail(
            extended=False,
            selected_index=0,
            label_type=ft.NavigationRailLabelType.ALL,
            indicator_color=ft.Colors.ON_SURFACE_VARIANT,
            destinations=destinations,
            on_change=self._on_change,
            bgcolor=BG_NAV_RAIL
        )
        return self.nav_rail

    def _on_change(self, e):
        if self.on_change_callback:
            self.on_change_callback(e.control.selected_index)

    def set_selected_index(self, index):
        if self.nav_rail:
            self.nav_rail.selected_index = index
            self.nav_rail.update()

    def update(self):
        if self.nav_rail:
            self.nav_rail.update()