import flet as ft

class NavigationRailView:
    def __init__(self, page, stations_count, on_change_callback):
        self.page = page
        self.stations_count = stations_count
        self.on_change_callback = on_change_callback
        self.nav_rail = None

    def build(self):
        destinations = []
        labels = ["Station", "Dashboard", "Settings"]
        icons = [
            (ft.Icons.HOME, ft.Icons.HOME_FILLED),
            (ft.Icons.DASHBOARD, ft.Icons.DASHBOARD_CUSTOMIZE),
            (ft.Icons.SETTINGS, ft.Icons.SETTINGS_APPLICATIONS)
        ]
        for idx, (label, (icon, selected_icon)) in enumerate(zip(labels, icons)):
            destinations.append(
                ft.NavigationRailDestination(
                    icon=ft.Icon(icon),
                    selected_icon=ft.Icon(selected_icon),
                    label=label
                )
            )
    
        self.nav_rail = ft.NavigationRail(
            extended=True,
            selected_index=0,
            label_type=ft.NavigationRailLabelType.ALL,
            min_width=100,
            min_extended_width=200,
            width=200,
            destinations=destinations,
            on_change=self._on_change,
            bgcolor="#F7F7FA"
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