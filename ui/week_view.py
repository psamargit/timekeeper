"""Pestaña 'Calendario semanal': lunes a domingo, navegable."""
from datetime import date, timedelta

import customtkinter as ctk

import db
import fechas
from models import minutos_a_hhmm
from ui.widgets import styled_button

DIA_CORTO = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]


class WeekView(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self.app = app
        self.conn = app.conn
        self.ref = date.today()

        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self._build_header()
        self._build_grid()
        self.refrescar()

    def _build_header(self):
        head = ctk.CTkFrame(self, fg_color="transparent")
        head.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        head.grid_columnconfigure(1, weight=1)

        styled_button(head, "◀ Semana anterior",
                      lambda: self.mover_semana(-1), width=140
                      ).grid(row=0, column=0, padx=(0, 8))
        self.lbl_semana = ctk.CTkLabel(head, text="",
                                       font=ctk.CTkFont(size=16, weight="bold"))
        self.lbl_semana.grid(row=0, column=1, sticky="w")
        styled_button(head, "Semana siguiente",
                      lambda: self.mover_semana(1), width=140
                      ).grid(row=0, column=2, padx=(8, 8))
        styled_button(head, "Hoy", self.ir_hoy, width=70, primary=True
                      ).grid(row=0, column=3, padx=(8, 0))

    def _build_grid(self):
        self.cuadricula = ctk.CTkFrame(self, fg_color="transparent")
        self.cuadricula.grid(row=1, column=0, sticky="nsew")
        for c in range(4):
            self.cuadricula.grid_columnconfigure(c, weight=1, uniform="dia")
        for r in range(2):
            self.cuadricula.grid_rowconfigure(r, weight=1, uniform="sem")

    def mover_semana(self, delta: int):
        self.ref += timedelta(days=7 * delta)
        self.refrescar()

    def ir_hoy(self):
        self.ref = date.today()
        self.refrescar()

    def refrescar(self):
        for w in self.cuadricula.winfo_children():
            w.destroy()
        dias = fechas.week_dates(self.ref)
        lunes, domingo = dias[0], dias[-1]
        self.lbl_semana.configure(
            text=f"Semana del {lunes.day} de {fechas.MESES_ES[lunes.month - 1]} al "
                 f"{domingo.day} de {fechas.MESES_ES[domingo.month - 1]} de {domingo.year}"
        )
        totales = db.minutes_by_day(self.conn, lunes.isoformat(), domingo.isoformat())
        hoy = date.today()

        for i, d in enumerate(dias):
            row, col = divmod(i, 4)
            self._add_day_card(d, row, col, totales.get(d.isoformat(), 0), d == hoy)

    def _add_day_card(self, d: date, row: int, col: int, total: int, es_hoy: bool):
        tipo = fechas.tipo_de_dia(d, self.app.feriados)
        tareas = db.list_tasks(self.conn, d.isoformat())

        border = ("#2563eb", "#3b82f6") if es_hoy else ("gray78", "gray28")
        card = ctk.CTkFrame(self.cuadricula, corner_radius=12, border_width=2 if es_hoy else 1,
                            border_color=border)
        card.grid(row=row, column=col, sticky="nsew", padx=6, pady=6)
        card.grid_columnconfigure(0, weight=1)
        card.grid_rowconfigure(2, weight=1)

        head = ctk.CTkFrame(card, fg_color="transparent",
                            corner_radius=0)
        head.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 0))
        head.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(head, text=f"{DIA_CORTO[d.weekday()]} {d.day}",
                     font=ctk.CTkFont(size=14, weight="bold")
                     ).grid(row=0, column=0, sticky="w")

        if es_hoy:
            tag = "Hoy"
            color = ("#2563eb", "#3b82f6")
        elif tipo == "feriado":
            tag = "Feriado"
            color = ("#d97706", "#f59e0b")
        elif tipo == "fin_semana":
            tag = "Fin de semana"
            color = ("#9ca3af", "#6b7280")
        else:
            tag = ""
            color = None
        if tag:
            ctk.CTkLabel(head, text=tag, font=ctk.CTkFont(size=11),
                         text_color=color).grid(row=0, column=1, sticky="e")

        ctk.CTkLabel(card, text=f"{minutos_a_hhmm(total)}",
                     font=ctk.CTkFont(size=20, weight="bold"),
                     text_color=(("#9ca3af", "#6b7280") if total == 0 else None)
                     ).grid(row=1, column=0, sticky="w", padx=10, pady=(2, 2))

        lista = ctk.CTkScrollableFrame(card, fg_color="transparent", height=120)
        lista.grid(row=2, column=0, sticky="nsew", padx=6, pady=(0, 4))
        lista.grid_columnconfigure(0, weight=1)
        if tareas:
            for j, t in enumerate(tareas):
                ctk.CTkLabel(lista, text=f"• {t.titulo} ({t.minutos} m)",
                             font=ctk.CTkFont(size=11), anchor="w", justify="left"
                             ).grid(row=j, column=0, sticky="ew", padx=4, pady=1)
        else:
            ctk.CTkLabel(lista, text="Sin tareas", font=ctk.CTkFont(size=11),
                         text_color=("gray60", "gray50")
                         ).grid(row=0, column=0, sticky="w", padx=4, pady=1)

        meta = self.app.meta_diaria if tipo == "laborable" else 0
        if meta:
            pct = min(total / meta, 1.0)
            bar = ctk.CTkProgressBar(card, height=8)
            bar.grid(row=3, column=0, sticky="ew", padx=10, pady=(2, 6))
            bar.set(pct)
        else:
            sp = ctk.CTkFrame(card, fg_color="transparent", height=14)
            sp.grid(row=3, column=0, sticky="ew", padx=10, pady=(2, 6))

        styled_button(card, "Abrir día",
                      lambda d=d: self.app.ir_a_fecha(d.isoformat()),
                      width=90).grid(row=4, column=0, padx=10, pady=(0, 10))
