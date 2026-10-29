"""Widgets y utilidades visuales compartidas."""
import time
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


class ListaDesplegable(ctk.CTkFrame):
    """Desplegable de una línea; al abrirse muestra `filas` opciones con barra.

    Misma interfaz que un combo: get() devuelve el texto elegido, set(valor) lo elige.
    """

    def __init__(self, parent, values, default=None, filas=5, ancho=110):
        super().__init__(parent, fg_color="transparent")
        self.values = list(values)
        self.filas = filas
        self.valor = default if default in self.values else self.values[0]
        self.popup = None
        self._cerrado_en = 0.0
        self.boton = ctk.CTkButton(
            self, text="", width=ancho, anchor="w", command=self._alternar,
            fg_color=("gray85", "gray25"), hover_color=("gray75", "gray30"),
            text_color=("gray10", "gray90"),
        )
        self.boton.grid(row=0, column=0)
        self.set(self.valor)

    def get(self) -> str:
        return self.valor

    def set(self, valor: str) -> None:
        self.valor = valor if valor in self.values else self.values[0]
        self.boton.configure(text=f"{self.valor}   ▾")

    def _alternar(self) -> None:
        if self.popup is not None:
            self._cerrar()
        elif time.monotonic() - self._cerrado_en > 0.2:  # evita reabrir al hacer clic fuera
            self._abrir()

    def _abrir(self) -> None:
        oscuro = ctk.get_appearance_mode().lower() == "dark"
        top = tk.Toplevel(self)
        top.overrideredirect(True)
        top.attributes("-topmost", True)
        top.geometry(f"+{self.boton.winfo_rootx()}"
                     f"+{self.boton.winfo_rooty() + self.boton.winfo_height() + 2}")
        lb = tk.Listbox(
            top, height=self.filas, width=max(self.boton.cget("width") // 9, 8),
            exportselection=False, activestyle="none", relief="flat", borderwidth=0,
            highlightthickness=1, font=("Segoe UI", 10),
            bg="#2b2b2b" if oscuro else "#ffffff",
            fg="#e5e7eb" if oscuro else "#111827",
            selectbackground="#3b82f6", selectforeground="#ffffff",
            highlightbackground="#4b5563" if oscuro else "#d1d5db",
        )
        sb = tk.Scrollbar(top, orient="vertical", command=lb.yview)
        lb.configure(yscrollcommand=sb.set)
        lb.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        for v in self.values:
            lb.insert("end", v)
        i = self.values.index(self.valor)
        lb.selection_set(i)
        lb.see(i)
        lb.bind("<ButtonRelease-1>", lambda e: self._elegir(lb))
        lb.bind("<Return>", lambda e: self._elegir(lb))
        lb.bind("<Escape>", lambda e: self._cerrar())
        top.bind("<FocusOut>", lambda e: self._cerrar())
        self.popup = top
        lb.focus_force()

    def _elegir(self, lb) -> None:
        sel = lb.curselection()
        if sel:
            self.set(self.values[sel[0]])
        self._cerrar()

    def _cerrar(self) -> None:
        if self.popup is not None:
            popup, self.popup = self.popup, None
            self._cerrado_en = time.monotonic()
            popup.destroy()
