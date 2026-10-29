"""Widgets y utilidades visuales compartidas."""
import customtkinter as ctk

ACCENT = ("#2563eb", "#3b82f6")
DANGER = ("#c0392b", "#e05d52")


class FormError(Exception):
    pass


def styled_button(parent, text, command, width=120, primary=False, danger=False):
    if primary:
        fg, hover = ACCENT, ("#1d4ed8", "#2563eb")
    elif danger:
        fg, hover = DANGER, ("#a93226", "#c0392b")
    else:
        fg, hover = None, None
    return ctk.CTkButton(
        parent, text=text, command=command, width=width,
        fg_color=fg, hover_color=hover,
    )


def field_label(parent, text):
    return ctk.CTkLabel(parent, text=text, font=ctk.CTkFont(size=12, weight="bold"),
                         anchor="w")


def entry(parent, placeholder="", width=240):
    return ctk.CTkEntry(parent, placeholder_text=placeholder, width=width)


def multiline(parent, width=240, height=90):
    return ctk.CTkTextbox(parent, width=width, height=height)
