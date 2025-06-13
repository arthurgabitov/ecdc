# styles.py
# Centralized style constants for the ECDC Station App

import flet as ft

# Colors
BG_MAIN = "#F1F1F1"
BG_CONTAINER = "#F1F1F1"
BG_NAV_RAIL = "#F1F1F1"
BG_TOP_BAR = "#F1F1F1"
BG_CARD = ft.Colors.WHITE
BG_CARD_ALT = ft.Colors.WHITE60
BG_STATUS_BAR_DEFAULT = ft.Colors.GREY_100
BG_SNACKBAR_SUCCESS = ft.Colors.GREEN_700
BG_SNACKBAR_ERROR = ft.Colors.RED_700
BG_BUTTON_GREEN = ft.Colors.GREEN_400
BG_BUTTON_RED = ft.Colors.RED_400
BG_BUTTON_ORANGE = ft.Colors.ORANGE
BG_BLUE_GREY = ft.Colors.BLUE_GREY_200

# Text colors
TEXT_DEFAULT = ft.Colors.BLACK
TEXT_SECONDARY = ft.Colors.GREY
TEXT_ACCENT = ft.Colors.YELLOW_700

# Font sizes
FONT_SIZE_LARGE = 28
FONT_SIZE_MEDIUM = 20
FONT_SIZE_NORMAL = 16
FONT_SIZE_SMALL = 14
FONT_SIZE_XL = 40
FONT_SIZE_CARD_TITLE = 22
FONT_SIZE_BUTTON = 15

# Font weights
FONT_WEIGHT_BOLD = ft.FontWeight.BOLD
FONT_WEIGHT_NORMAL = ft.FontWeight.W_300

# Font family
FONT_FAMILY_INCONSOLATA_LIGHT = "Inconsolata-Light"

# Border radius
BORDER_RADIUS_MAIN = 20
BORDER_RADIUS_TOPBAR = 16
BORDER_RADIUS_DROPDOWN = 8
BORDER_RADIUS_CARD = 10
BORDER_RADIUS_DASHBOARD = 3

# Padding
PADDING_MAIN = ft.padding.all(15)
PADDING_CARD = 10
PADDING_DROPDOWN = ft.padding.symmetric(horizontal=12, vertical=6)
PADDING_TOPBAR = ft.padding.only(left=24, right=24, top=12, bottom=0)
PADDING_BUTTON = ft.padding.only(right=12, top=10, left=10, bottom=10)

# Box Shadows
SHADOW_CARD = [
    ft.BoxShadow(
        blur_radius=8,
        color="#E7F1FF",  # на 2 тона темнее фона
        offset=(0, 2),
        spread_radius=0
    ),
    ft.BoxShadow(
        blur_radius=16,
        color="#D0E3FF",  # еще чуть темнее
        offset=(0, 6),
        spread_radius=0
    )
]
