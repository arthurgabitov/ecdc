import flet as ft
from styles import BG_TOP_BAR, BORDER_RADIUS_TOPBAR, PADDING_TOPBAR, FONT_WEIGHT_BOLD, FONT_SIZE_MEDIUM, TEXT_ACCENT, TEXT_DEFAULT, FONT_SIZE_NORMAL
import ctypes

def get_full_username():
    GetUserNameEx = ctypes.windll.secur32.GetUserNameExW
    NameDisplay = 3  
    size = ctypes.pointer(ctypes.c_ulong(0))
    GetUserNameEx(NameDisplay, None, size)
    nameBuffer = ctypes.create_unicode_buffer(size.contents.value)
    GetUserNameEx(NameDisplay, nameBuffer, size)
    return nameBuffer.value


def TopBar(title, user_sso=None, dropdown=None, right_controls=None, on_logout=None):
    LEFT_BLOCK_WIDTH = 340  
    TOPBAR_HEIGHT = 65     
    
    full_name = get_full_username()
    # Состояние для меню
    def on_logout_click(e):
        if on_logout:
            on_logout(e)

    user_menu = ft.PopupMenuButton(
        items=[
            ft.PopupMenuItem(text="Logout", on_click=on_logout_click)
        ],
        content=ft.Row([
            ft.Container(
                ft.Icon(ft.Icons.PERSON, color=TEXT_ACCENT, size=24),
                width=32,
                height=32,
                bgcolor=ft.Colors.ON_SURFACE_VARIANT,
                border_radius=16,
                alignment=ft.alignment.center,
                margin=ft.margin.only(right=8)
            ),
            ft.Text(full_name, color=TEXT_DEFAULT, size=FONT_SIZE_NORMAL, font_family="Roboto-Light"),
        ], spacing=8),
    )
    
    if dropdown is not None:
        left_block = ft.Container(
            ft.Row([
                ft.Text(title, weight=FONT_WEIGHT_BOLD, size=FONT_SIZE_MEDIUM, font_family="Roboto-Light"),
                dropdown
            ], alignment=ft.MainAxisAlignment.START, spacing=16, expand=True),
            width=LEFT_BLOCK_WIDTH,  
            alignment=ft.alignment.center_left,
            height=TOPBAR_HEIGHT,   
        )
    else:
        left_block = ft.Container(
            ft.Row([
                ft.Text(title, weight=FONT_WEIGHT_BOLD, size=FONT_SIZE_MEDIUM, font_family="Roboto-Light")
            ], alignment=ft.MainAxisAlignment.START, expand=True),
            width=LEFT_BLOCK_WIDTH,  
            alignment=ft.alignment.center_left,
            height=TOPBAR_HEIGHT,   
        )
    right_row_controls = [
        *(right_controls or []),
        user_menu
    ]
    row = ft.Row(
        [
            left_block,
            ft.Row(right_row_controls, alignment=ft.MainAxisAlignment.END, height=TOPBAR_HEIGHT)
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
