"""Pestaña 'Ajustes': meta diaria y feriados."""
from datetime import date

import customtkinter as ctk

import db
import fechas
from models import ValidationError, validar_meta_diaria
from ui.widgets import styled_button, field_label, entry


class SettingsView(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self.app = app
        self.conn = app.conn

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        self._build_meta()
        self._build_feriados()

    def _build_meta(self):
        card = ctk.CTkFrame(self, corner_radius=12)
        card.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        card.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(card, text="Meta diaria", font=ctk.CTkFont(size=14, weight="bold")
                      ).grid(row=0, column=0, sticky="w", padx=14, pady=(12, 4))
        ctk.CTkLabel(card, text="Minutos objetivo para días laborables (lunes a viernes). "
                                 "En fin de semana y feriados la meta visual es 0.",
                     font=ctk.CTkFont(size=12), text_color=("gray40", "gray60")
                     ).grid(row=1, column=0, sticky="w", padx=14)

        row = ctk.CTkFrame(card, fg_color="transparent")
        row.grid(row=2, column=0, sticky="ew", padx=14, pady=(6, 12))
        self.in_meta = entry(row, "480", width=110)
        self.in_meta.insert(0, str(self.app.meta_diaria))
        self.in_meta.grid(row=0, column=0, padx=(0, 8))
        styled_button(row, "Guardar meta", self.guardar_meta, primary=True
                      ).grid(row=0, column=1)
        self.lbl_meta_estado = ctk.CTkLabel(row, text="", font=ctk.CTkFont(size=12))
        self.lbl_meta_estado.grid(row=0, column=2, padx=10)

    def _build_feriados(self):
        card = ctk.CTkFrame(self, corner_radius=12)
        card.grid(row=1, column=0, sticky="nsew", pady=(0, 12))
        card.grid_columnconfigure(0, weight=1)
        card.grid_rowconfigure(2, weight=1)
        ctk.CTkLabel(card, text="Feriados", font=ctk.CTkFont(size=14, weight="bold")
                      ).grid(row=0, column=0, sticky="w", padx=14, pady=(12, 4))
        ctk.CTkLabel(card, text="Marca días como feriado para distinguirlos en el "
                                 "calendario. Puedes registrar tareas igualmente.",
                     font=ctk.CTkFont(size=12), text_color=("gray40", "gray60")
                     ).grid(row=1, column=0, sticky="w", padx=14)

        row = ctk.CTkFrame(card, fg_color="transparent")
        row.grid(row=2, column=0, sticky="ew", padx=14, pady=(6, 4))
        field_label(row, "Fecha (AAAA-MM-DD)").grid(row=0, column=0, sticky="w",
                                                    pady=(4, 2))
        self.in_feriado = entry(row, "2025-12-25", width=130)
        self.in_feriado.grid(row=1, column=0, padx=(0, 8))
        styled_button(row, "Añadir feriado", self.agregar_feriado
                      ).grid(row=1, column=1)

        self.lbl_feriado_estado = ctk.CTkLabel(card, text="", font=ctk.CTkFont(size=12))
        self.lbl_feriado_estado.grid(row=3, column=0, sticky="w", padx=14, pady=(2, 4))

        wrap = ctk.CTkFrame(card, fg_color="transparent")
        wrap.grid(row=4, column=0, sticky="nsew", padx=14, pady=(0, 12))
        wrap.grid_rowconfigure(1, weight=1)
        wrap.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(wrap, text="Feriados marcados:", font=ctk.CTkFont(size=12)
                      ).grid(row=0, column=0, sticky="w", pady=(4, 4))
        self.lista_feriados = ctk.CTkScrollableFrame(wrap, fg_color="transparent",
                                                     height=140)
        self.lista_feriados.grid(row=1, column=0, sticky="nsew")
        self.lista_feriados.grid_columnconfigure(0, weight=1)
        self.refrescar_feriados()

    # ---------- comportamiento ----------

    def guardar_meta(self):
        try:
            meta = validar_meta_diaria(self.in_meta.get())
        except ValidationError as e:
            self.lbl_meta_estado.configure(text=str(e), text_color=("#c0392b", "#e05d52"))
            return
        db.set_setting(self.conn, "meta_diaria", str(meta))
        self.app.meta_diaria = meta
        self.app.actualizar_barra_meta()
        self.app.day_view.refrescar()
        self.app.week_view.refrescar()
        self.lbl_meta_estado.configure(text="Meta actualizada.",
                                       text_color=("#1d9a53", "#2fb86d"))

    def agregar_feriado(self):
        raw = self.in_feriado.get().strip()
        try:
            d = date.fromisoformat(raw)
        except ValueError:
            self.lbl_feriado_estado.configure(text="Fecha inválida (usa AAAA-MM-DD).",
                                              text_color=("#c0392b", "#e05d52"))
            return
        self.app.feriados.add(d.isoformat())
        self._post_feriados(f"«{d.isoformat()}» marcado como feriado.")

    def quitar_feriado(self, fecha_iso: str):
        self.app.feriados.discard(fecha_iso)
        self._post_feriados(f"«{fecha_iso}» dejado de ser feriado.")

    def _post_feriados(self, msg: str):
        self.lbl_feriado_estado.configure(text=msg, text_color=("#1d9a53", "#2fb86d"))
        self.refrescar_feriados()
        self.app.week_view.refrescar()
        self.app.day_view.refrescar()

    def refrescar_feriados(self):
        for w in self.lista_feriados.winfo_children():
            w.destroy()
        if not self.app.feriados:
            ctk.CTkLabel(self.lista_feriados, text="Ninguno.",
                         text_color=("gray60", "gray50")
                         ).grid(row=0, column=0, sticky="w", padx=6, pady=4)
            return
        for i, fecha_iso in enumerate(sorted(self.app.feriados)):
            row = ctk.CTkFrame(self.lista_feriados, fg_color="transparent")
            row.grid(row=i, column=0, sticky="ew", pady=2)
            row.grid_columnconfigure(0, weight=1)
            d = date.fromisoformat(fecha_iso)
            ctk.CTkLabel(row, text=f"{fecha_iso} — {fechas.format_fecha_larga(d)}"
                           ).grid(row=0, column=0, sticky="w")
            styled_button(row, "Quitar", lambda f=fecha_iso: self.quitar_feriado(f),
                         width=60, danger=True).grid(row=0, column=1, padx=4)
