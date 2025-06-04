import flet as ft

def TopBar(title, user_sso, dropdown=None, right_controls=None):
    
    LEFT_BLOCK_WIDTH = 340  
    TOPBAR_HEIGHT = 65     
    left_controls = [
        ft.Text(title, weight=ft.FontWeight.BOLD, size=20),
    ]
    if dropdown is not None:
        left_controls.append(ft.Container(width=16))
        left_controls.append(
            ft.Container(
                dropdown,
                width=180,  # Фиксированная ширина для выпадающего списка
                alignment=ft.alignment.center_left,
            )
        )
    else:
        left_controls.append(ft.Container(width=196))
    row = ft.Row(
        [
            ft.Container(
                ft.Row(left_controls, alignment=ft.MainAxisAlignment.START, expand=True),
                width=LEFT_BLOCK_WIDTH,  # всегда одинаковая ширина для левой части
                alignment=ft.alignment.center_left,
                height=TOPBAR_HEIGHT,   # фиксированная высота
            ),
            ft.Row([
                *(right_controls or []),
                ft.Icon(ft.Icons.PERSON, color=ft.Colors.YELLOW_700),
                ft.Text(user_sso, color=ft.Colors.BLACK, size=16),
            ], alignment=ft.MainAxisAlignment.END, height=TOPBAR_HEIGHT)
        ],
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
        expand=True,
        height=TOPBAR_HEIGHT,  # фиксированная высота для всей строки
    )
    return ft.Container(
        content=row,
        padding=ft.padding.only(left=24, right=24, top=12, bottom=0),  # отступ сверху
        bgcolor="#F7F7FA",
        border_radius=ft.border_radius.only(top_left=16, top_right=16),
        height=TOPBAR_HEIGHT,  # фиксированная высота для всего TopBar
    )
