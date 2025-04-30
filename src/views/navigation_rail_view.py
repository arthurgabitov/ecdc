import flet as ft

class NavigationRailView:
    def __init__(self, page, stations_count, on_change_callback):
        self.page = page
        self.stations_count = stations_count
        self.on_change_callback = on_change_callback
        self.nav_rail = None

    def build(self):
        destinations = []
        
        destinations.append(
            ft.NavigationRailDestination(
                icon_content=ft.Icon(ft.Icons.HOME, ),
                selected_icon_content=ft.Icon(ft.Icons.HOME_FILLED, ),
                label_content=ft.Text("RO Station", ),
                label="RO Station"
            )
        )
    
        if self.stations_count > 1:
            destinations.append(
                ft.NavigationRailDestination(
                    icon_content=ft.Icon(ft.Icons.DASHBOARD, ),
                    selected_icon_content=ft.Icon(ft.Icons.DASHBOARD_CUSTOMIZE, ),
                    label_content=ft.Text("Overview", ),
                    label="Overview"
                )
            )
    
        destinations.append(
            ft.NavigationRailDestination(
                icon_content=ft.Icon(ft.Icons.SETTINGS, ),
                selected_icon_content=ft.Icon(ft.Icons.SETTINGS_APPLICATIONS, ),
                label_content=ft.Text("Settings", ),
                label="Settings"
            )
        )

        self.nav_rail = ft.NavigationRail(
            extended=True,
            selected_index=0,
            label_type=ft.NavigationRailLabelType.ALL,
            min_width=100,
            min_extended_width=200,
            width=200,
            #bgcolor=ft.Colors.ON_PRIMARY_CONTAINER,
            #indicator_color=ft.Colors.WHITE10,
            destinations=destinations,
            on_change=lambda e: self.on_change_callback(e.control.selected_index)
        )
        
        return self.nav_rail
    
    def set_selected_index(self, index):
        if self.nav_rail:
            self.nav_rail.selected_index = index
            self.nav_rail.update()
    
    def update(self):
        if self.nav_rail:
            self.nav_rail.update()