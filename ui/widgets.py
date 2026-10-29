"""Widgets y utilidades visuales compartidas."""
import tkinter as tk

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


class ListaSeleccion(ctk.CTkFrame):
    """Lista compacta con barra de desplazamiento; todas las opciones a la vista.

    Misma interfaz que un combo: get() devuelve el texto elegido, set(valor) lo elige.
    """

    def __init__(self, parent, values, default=None, filas=4, ancho=9):
        super().__init__(parent, fg_color="transparent")
        self.values = list(values)
        self.default = default if default in self.values else self.values[0]
        self.lista = tk.Listbox(
            self, height=filas, width=ancho, exportselection=False,
            activestyle="none", relief="flat", borderwidth=0,
            highlightthickness=1, font=("Segoe UI", 10),
        )
        self.barra = ctk.CTkScrollbar(self, command=self.lista.yview, width=14)
        self.lista.configure(yscrollcommand=self.barra.set)
        self.lista.grid(row=0, column=0, sticky="nsew")
        self.barra.grid(row=0, column=1, sticky="ns", padx=(2, 0))
        for v in self.values:
            self.lista.insert("end", v)
        self._colorear(ctk.get_appearance_mode())
        self.set(self.default)

    def _colorear(self, modo: str) -> None:
        oscuro = str(modo).lower() == "dark"
        self.lista.configure(
            bg="#2b2b2b" if oscuro else "#ffffff",
            fg="#e5e7eb" if oscuro else "#111827",
            selectbackground="#3b82f6", selectforeground="#ffffff",
            highlightbackground="#4b5563" if oscuro else "#d1d5db",
            highlightcolor="#3b82f6",
        )

    def _set_appearance_mode(self, mode_string):  # llamado al cambiar el tema
        super()._set_appearance_mode(mode_string)
        if hasattr(self, "lista"):
            self._colorear(mode_string)

    def get(self) -> str:
        sel = self.lista.curselection()
        return self.values[sel[0]] if sel else self.default

    def set(self, valor: str) -> None:
        if valor not in self.values:
            valor = self.default
        i = self.values.index(valor)
        self.lista.selection_clear(0, "end")
        self.lista.selection_set(i)
        self.lista.see(i)
