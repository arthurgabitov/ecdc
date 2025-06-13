import flet as ft
from styles import BG_TOP_BAR, BORDER_RADIUS_TOPBAR, PADDING_TOPBAR, FONT_WEIGHT_BOLD, FONT_SIZE_MEDIUM, TEXT_ACCENT, TEXT_DEFAULT, FONT_SIZE_NORMAL

def TopBar(title, user_sso, dropdown=None, right_controls=None):
    
    LEFT_BLOCK_WIDTH = 340  
    TOPBAR_HEIGHT = 65     
    left_controls = [
        ft.Text(title, weight=FONT_WEIGHT_BOLD, size=FONT_SIZE_MEDIUM, font_family="Roboto-Light"),
    ]
    if dropdown is not None:
        left_controls.append(ft.Container(width=16))
        left_controls.append(
            ft.Container(
                dropdown,
                width=180,  
                alignment=ft.alignment.center_left,
            )
        )
    else:
        left_controls.append(ft.Container(width=196))
    row = ft.Row(
        [
            ft.Container(
                ft.Row(left_controls, alignment=ft.MainAxisAlignment.START, expand=True),
                width=LEFT_BLOCK_WIDTH,  
                alignment=ft.alignment.center_left,
                height=TOPBAR_HEIGHT,   
            ),
            ft.Row([
                *(right_controls or []),
                ft.Container(
                    ft.Icon(ft.Icons.PERSON, color=TEXT_ACCENT, size=24),
                    width=32,
                    height=32,
                    bgcolor=ft.Colors.ON_SURFACE_VARIANT,
                    border_radius=16,
                    alignment=ft.alignment.center,
                    margin=ft.margin.only(right=8)
                ),
                ft.Text(user_sso, color=TEXT_DEFAULT, size=FONT_SIZE_NORMAL, font_family="Roboto-Light"),
            ], alignment=ft.MainAxisAlignment.END, height=TOPBAR_HEIGHT)
        ],
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
        expand=True,
        height=TOPBAR_HEIGHT,  
    )
    return ft.Container(
        content=row,
        padding=PADDING_TOPBAR, 
        bgcolor=BG_TOP_BAR,
        border_radius=ft.border_radius.only(top_left=BORDER_RADIUS_TOPBAR, top_right=BORDER_RADIUS_TOPBAR),
        height=TOPBAR_HEIGHT,  
    )
