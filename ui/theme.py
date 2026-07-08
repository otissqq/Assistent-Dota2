"""
Centralised colour palette for the two supported themes (dark / light).

Widgets that use the shared helpers in ui/widgets.py (make_card, card_title,
small_label, body_label, ToggleRow, ...) automatically follow whichever
theme is active, because those helpers call theme.current() at the moment
they build the widget. Switching themes therefore requires re-building the
pages that use them -- see MainWindow._rebuild_pages() in main.py.
"""
import database as db

DARK = {
    "bg":            "#0F1218",
    "sidebar":       "#0F1218",
    "titlebar":      "#0F1218",
    "border":        "#21262D",
    "surface":       "rgba(22, 27, 34, 0.85)",
    "surface_alt":   "#161B22",
    "surface_soft":  "#161B22",
    "input_bg":      "#0F1218",
    "border_soft":   "#21262D",
    "border_input":  "#30363D",
    "text":          "#e7e9f3",
    "text_bright":   "#ffffff",
    "text_dim":      "#c4c7d6",
    "text_muted":    "#8a8fa8",
    "text_faint":    "#7c8096",
    "text_ghost":    "#5a5f78",
    "accent":        "#4F46E5",
    "accent_hover":  "#6366F1",
    "accent_press":  "#4338CA",
    "accent_soft":   "#9d90f5",
    "green":         "#5ee08a",
    "red":           "#ef6f7a",
    "scrollbar":     "#2a2f45",
    "scrollbar_h":   "#393f5c",
}

LIGHT = {
    "bg":            "#eef0f7",
    "sidebar":       "#ffffff",
    "titlebar":      "#ffffff",
    "border":        "#e1e4f0",
    "surface":       "#ffffff",
    "surface_alt":   "#f4f5fb",
    "surface_soft":  "#eef0f9",
    "input_bg":      "#f5f6fc",
    "border_soft":   "#e1e4f0",
    "border_input":  "#d7dbec",
    "text":          "#20222f",
    "text_bright":   "#0c0e16",
    "text_dim":      "#3c3f52",
    "text_muted":    "#61667e",
    "text_faint":    "#767c96",
    "text_ghost":    "#9aa0b7",
    "accent":        "#4F46E5",
    "accent_hover":  "#4338CA",
    "accent_press":  "#4d3fc0",
    "accent_soft":   "#4F46E5",
    "green":         "#18965a",
    "red":           "#cf3652",
    "scrollbar":     "#d7dbec",
    "scrollbar_h":   "#c0c5dd",
}


def is_light() -> bool:
    return db.get_setting("theme", "dark") == "light"


def current() -> dict:
    return LIGHT if is_light() else DARK
