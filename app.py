"""Ventana principal con pestañas y persistencia de geometría/tema."""
import json
import tkinter

import customtkinter as ctk

import db
import fechas
from ui.day_view import DayView
from ui.week_view import WeekView
from ui.knowledge_view import KnowledgeView
from ui.settings_view import SettingsView
from ui.widgets import styled_button

GEOMETRY_DEFAULT = "1200x760"
MIN_SIZE = (1100, 700)


class App(ctk.CTk):
    def __init__(self, conn):
        super().__init__()
        self.conn = conn
        self.feriados = fechas.cargar_feriados()
        self.meta_diaria = fechas.get_meta_diaria(conn)

        tema = db.get_setting(conn, "tema", "dark")
        ctk.set_appearance_mode(tema)
        ctk.set_default_color_theme("blue")

        self.title("TimeKeeper — Registro de tiempo y conocimiento")
        self.minsize(*MIN_SIZE)
        self._aplicar_geometria(db.get_setting(conn, "geometry", GEOMETRY_DEFAULT))

        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self._build_topbar()
        self._build_tabs()

        self.protocol("WM_DELETE_WINDOW", self.on_close)

    # ---------- construcción ----------

    def _build_topbar(self):
        bar = ctk.CTkFrame(self, corner_radius=0, fg_color=("gray92", "gray14"))
        bar.grid(row=0, column=0, sticky="ew", padx=0, pady=0)
        bar.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(bar, text="⏱ TimeKeeper", font=ctk.CTkFont(size=18, weight="bold")
                     ).grid(row=0, column=0, padx=16, pady=10, sticky="w")

        right = ctk.CTkFrame(bar, fg_color="transparent")
        right.grid(row=0, column=2, padx=12, pady=8)
        self.lbl_meta = ctk.CTkLabel(right, text="", font=ctk.CTkFont(size=12))
        self.lbl_meta.grid(row=0, column=0, padx=(0, 12))
        self.btn_tema = styled_button(right, "🌙 Tema", self.toggle_theme, width=90)
        self.btn_tema.grid(row=0, column=1)
        self.actualizar_barra_meta()

    def _build_tabs(self):
        self.tabs = ctk.CTkTabview(
            self,
            segmented_button_fg_color=("gray86", "gray20"),
            anchor="w",
        )
        self.tabs.grid(row=1, column=0, sticky="nsew", padx=0, pady=0)
        nombres = ("Registro del día", "Calendario semanal",
                   "Base de conocimiento", "Ajustes")
        for nombre in nombres:
            tab = self.tabs.add(nombre)
            tab.grid_rowconfigure(0, weight=1)
            tab.grid_columnconfigure(0, weight=1)

        self.day_view = DayView(self.tabs.tab("Registro del día"), self)
        self.day_view.grid(row=0, column=0, sticky="nsew", padx=14, pady=12)

        self.week_view = WeekView(self.tabs.tab("Calendario semanal"), self)
        self.week_view.grid(row=0, column=0, sticky="nsew", padx=14, pady=12)

        self.knowledge_view = KnowledgeView(self.tabs.tab("Base de conocimiento"), self)
        self.knowledge_view.grid(row=0, column=0, sticky="nsew", padx=14, pady=12)

        self.settings_view = SettingsView(self.tabs.tab("Ajustes"), self)
        self.settings_view.grid(row=0, column=0, sticky="nsew", padx=14, pady=12)

    # ---------- helpers de UI ----------

    def toast(self, mensaje: str, tipo: str = "exito") -> None:
        color = ("#1d9a53", "#2fb86d") if tipo == "exito" else ("#c0392b", "#e05d52")
        self.lbl_meta.configure(text=mensaje, text_color=color)
        if getattr(self, "_toast_after", None):
            self.after_cancel(self._toast_after)
        self._toast_after = self.after(
            3500, lambda: self.actualizar_barra_meta()
        )

    def actualizar_barra_meta(self) -> None:
        self.lbl_meta.configure(
            text=f"Meta diaria: {self.meta_diaria // 60} h",
            text_color=ctk.ThemeManager.theme["CTkLabel"]["text_color"],
        )

    def ir_a_fecha(self, fecha_iso: str) -> None:
        self.day_view.seleccionar_fecha(fecha_iso)
        self.tabs.set("Registro del día")

    def toggle_theme(self) -> None:
        nuevo = "light" if ctk.get_appearance_mode().lower() == "dark" else "dark"
        ctk.set_appearance_mode(nuevo)
        db.set_setting(self.conn, "tema", nuevo)
        self.btn_tema.configure(text="☀ Tema" if nuevo == "dark" else "🌙 Tema")

    def _aplicar_geometria(self, geo: str) -> None:
        try:
            w, h = geo.lower().split("x")
            w, h = int(w), int(h)
            if w < MIN_SIZE[0] or h < MIN_SIZE[1]:
                raise ValueError
            x = (self.winfo_screenwidth() - w) // 2
            y = (self.winfo_screenheight() - h) // 3
            self.geometry(f"{w}x{h}+{max(x, 0)}+{max(y, 0)}")
        except (ValueError, tkinter.TclError):
            self.geometry(GEOMETRY_DEFAULT)

    # ---------- ciclo de vida ----------

    def on_close(self) -> None:
        try:
            db.set_setting(self.conn, "geometry", self.geometry())
            fechas.guardar_feriados(self.feriados)
            self.conn.close()
        finally:
            self.destroy()


def main():
    conn = db.get_connection()
    db.migrate(conn)
    app = App(conn)
    app.mainloop()


if __name__ == "__main__":
    main()
