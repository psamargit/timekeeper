"""Pestaña 'Registro del día': formulario, lista y progreso."""
import tkinter.messagebox
from datetime import date, timedelta

import customtkinter as ctk

import db
import fechas
from models import (Task, ValidationError, validar_tarea, validar_hora_inicio,
                    minutos_a_hhmm, hhmm_a_minutos, hora_a_minutos,
                    minutos_a_hora, HORA_MIN, HORA_MAX,
                    TIPOS_COMUNICACION, SIN_TIPO, validar_tipo_comunicacion)
from ui.widgets import styled_button, field_label, entry, multiline


ESCALA = 1.5          # píxeles por minuto en el horario
ANCHO_BLOQUES = 190
SIN_HORA = "Sin hora"
HORAS = [SIN_HORA] + [minutos_a_hora(m) for m in range(HORA_MIN, HORA_MAX + 1, 15)]
COLORES = ["#3b82f6", "#10b981", "#8b5cf6", "#f59e0b", "#ef4444", "#14b8a6"]


class DayView(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self.app = app
        self.conn = app.conn
        self.fecha = date.today()
        self.editando_id = None

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=0)
        self.grid_rowconfigure(2, weight=1)

        self._build_header()
        self._build_form()
        self._build_list()
        self._build_progress()
        self.refrescar()

    # ---------- construcción ----------

    def _build_header(self):
        head = ctk.CTkFrame(self, fg_color="transparent")
        head.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        head.grid_columnconfigure(1, weight=1)

        styled_button(head, "◀", lambda: self.mover_dia(-1), width=36
                      ).grid(row=0, column=0, padx=(0, 6))
        self.lbl_fecha = ctk.CTkLabel(head, text="", font=ctk.CTkFont(size=16, weight="bold"))
        self.lbl_fecha.grid(row=0, column=1, sticky="w")
        styled_button(head, "▶", lambda: self.mover_dia(1), width=36
                      ).grid(row=0, column=2, padx=(6, 6))
        styled_button(head, "Hoy", self.ir_hoy, width=60
                      ).grid(row=0, column=3, padx=(0, 10))

        self.lbl_tipo = ctk.CTkLabel(head, text="", font=ctk.CTkFont(size=12))
        self.lbl_tipo.grid(row=0, column=4)

    def _build_form(self):
        form = ctk.CTkFrame(self, corner_radius=12)
        form.grid(row=1, column=0, sticky="nsew", padx=(0, 12), pady=(0, 12))
        for i in range(6):
            form.grid_columnconfigure(i, weight=1)
        ctk.CTkLabel(form, text="Nueva tarea", font=ctk.CTkFont(size=13, weight="bold")
                      ).grid(row=0, column=0, columnspan=6, sticky="w", padx=12, pady=(10, 4))

        field_label(form, "Título *").grid(row=1, column=0, columnspan=2, sticky="ew",
                                           padx=12, pady=(4, 2))
        self.in_titulo = entry(form, "¿Qué hiciste?")
        self.in_titulo.grid(row=2, column=0, columnspan=2, sticky="ew", padx=12)

        field_label(form, "Hora de inicio").grid(row=1, column=2, padx=12,
                                                 pady=(4, 2), sticky="w")
        self.in_hora = ctk.CTkComboBox(form, values=HORAS, width=110)
        self.in_hora.set(SIN_HORA)
        self.in_hora.grid(row=2, column=2, padx=12, sticky="w")

        field_label(form, "Duración (min u h:mm) *").grid(row=1, column=3, padx=12,
                                                         pady=(4, 2), sticky="w")
        self.in_minutos = entry(form, "90 o 1:30", width=140)
        self.in_minutos.grid(row=2, column=3, padx=12, sticky="w")

        field_label(form, "Categoría").grid(row=1, column=4, padx=12, pady=(4, 2), sticky="w")
        self.in_categoria = entry(form, "Trabajo, personal…", width=160)
        self.in_categoria.grid(row=2, column=4, padx=12, sticky="w")

        styled_button(form, "Guardar", self.guardar, primary=True
                      ).grid(row=2, column=5, padx=12, sticky="ew")

        field_label(form, "Tipo de comunicación").grid(row=3, column=0, columnspan=2,
                                                       sticky="w", padx=12, pady=(8, 2))
        self.in_tipo = ctk.CTkComboBox(form, values=TIPOS_COMUNICACION, width=180,
                                       state="readonly")
        self.in_tipo.set(SIN_TIPO)
        self.in_tipo.grid(row=4, column=0, columnspan=2, sticky="w", padx=12)

        field_label(form, "Usuario solicitante").grid(row=3, column=2, columnspan=3,
                                                      sticky="w", padx=12, pady=(8, 2))
        self.in_solicitante = entry(form, "Nombre o usuario de quien lo pidió")
        self.in_solicitante.grid(row=4, column=2, columnspan=3, sticky="ew", padx=12)

        field_label(form, "Nota breve").grid(row=5, column=0, columnspan=6, sticky="ew",
                                             padx=12, pady=(8, 2))
        self.in_descripcion = multiline(form, height=60)
        self.in_descripcion.grid(row=6, column=0, columnspan=6, sticky="ew",
                                 padx=12, pady=(0, 4))
        self.in_descripcion.grid_columnconfigure(0, weight=1)

        self.lbl_form_state = ctk.CTkLabel(form, text="", font=ctk.CTkFont(size=12))
        self.lbl_form_state.grid(row=7, column=0, columnspan=6, sticky="e", padx=12,
                                 pady=(0, 10))

    def _build_list(self):
        wrap = ctk.CTkFrame(self, fg_color="transparent")
        wrap.grid(row=2, column=0, sticky="nsew")
        wrap.grid_rowconfigure(1, weight=1)
        wrap.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(wrap, text="Tareas del día", font=ctk.CTkFont(size=13, weight="bold")
                      ).grid(row=0, column=0, sticky="w", pady=(0, 6))
        self.scroll = ctk.CTkScrollableFrame(wrap, corner_radius=12)
        self.scroll.grid(row=1, column=0, sticky="nsew")
        self.scroll.grid_columnconfigure(0, weight=1)

    def _build_progress(self):
        panel = ctk.CTkFrame(self, corner_radius=12, width=300)
        panel.grid(row=1, column=1, rowspan=2, sticky="nsew", pady=(0, 12))
        panel.grid_columnconfigure(0, weight=1)
        panel.grid_rowconfigure(6, weight=1)
        ctk.CTkLabel(panel, text="Progreso del día",
                      font=ctk.CTkFont(size=13, weight="bold")
                      ).grid(row=0, column=0, sticky="w", padx=16, pady=(12, 6))
        self.lbl_total = ctk.CTkLabel(panel, text="", font=ctk.CTkFont(size=22, weight="bold"))
        self.lbl_total.grid(row=1, column=0, sticky="w", padx=16)
        self.lbl_vs_meta = ctk.CTkLabel(panel, text="", font=ctk.CTkFont(size=12))
        self.lbl_vs_meta.grid(row=2, column=0, sticky="w", padx=16, pady=(0, 8))
        self.barra = ctk.CTkProgressBar(panel, height=14)
        self.barra.grid(row=3, column=0, sticky="ew", padx=16)
        self.lbl_pct = ctk.CTkLabel(panel, text="", font=ctk.CTkFont(size=12))
        self.lbl_pct.grid(row=4, column=0, sticky="w", padx=16, pady=(6, 8))

        ctk.CTkLabel(panel, text="Horario 08:30 – 16:30",
                     font=ctk.CTkFont(size=13, weight="bold")
                     ).grid(row=5, column=0, sticky="w", padx=16, pady=(4, 4))
        self.horario = ctk.CTkScrollableFrame(panel, fg_color="transparent", width=270)
        self.horario.grid(row=6, column=0, sticky="nsew", padx=8, pady=(0, 10))
        self.lienzo = ctk.CTkFrame(self.horario, fg_color="transparent", width=260,
                                   height=int((HORA_MAX - HORA_MIN) * ESCALA) + 12)
        self.lienzo.grid(row=0, column=0, sticky="w")

    # ---------- comportamiento ----------

    def mover_dia(self, delta: int):
        self.seleccionar_fecha((self.fecha + timedelta(days=delta)).isoformat())

    def ir_hoy(self):
        self.seleccionar_fecha(date.today().isoformat())

    def seleccionar_fecha(self, fecha_iso: str):
        self.fecha = fechas.parse_fecha(fecha_iso)
        self.editando_id = None
        self._limpiar_form()
        self.refrescar()

    def _limpiar_form(self):
        self.in_titulo.delete(0, "end")
        self.in_minutos.delete(0, "end")
        self.in_categoria.delete(0, "end")
        self.in_descripcion.delete("1.0", "end")
        self.in_hora.set(SIN_HORA)
        self.in_tipo.set(SIN_TIPO)
        self.in_solicitante.delete(0, "end")
        self.lbl_form_state.configure(text="")

    def guardar(self):
        try:
            titulo, minutos, fecha = validar_tarea(
                self.in_titulo.get(), self.in_minutos.get(), self.fecha.isoformat()
            )
            hora = validar_hora_inicio(self.in_hora.get())
            tipo = validar_tipo_comunicacion(self.in_tipo.get())
        except ValidationError as e:
            self.lbl_form_state.configure(text=str(e), text_color=("#c0392b", "#e05d52"))
            return

        task = Task(
            fecha=fecha, titulo=titulo, minutos=minutos,
            descripcion=self.in_descripcion.get("1.0", "end").strip(),
            categoria=self.in_categoria.get().strip(),
            hora_inicio=hora,
            tipo_comunicacion=tipo,
            usuario_solicitante=self.in_solicitante.get().strip(),
            id=self.editando_id,
        )
        if self.editando_id is None:
            db.insert_task(self.conn, task)
            msg = "Tarea guardada."
        else:
            db.update_task(self.conn, task)
            msg = "Tarea actualizada."
        self.editando_id = None
        self._limpiar_form()
        self.refrescar()
        self.app.refrescar_calendario()
        self.app.toast(msg)

    def _cargar_para_editar(self, task: Task):
        self.editando_id = task.id
        self.in_titulo.delete(0, "end")
        self.in_titulo.insert(0, task.titulo)
        self.in_minutos.delete(0, "end")
        self.in_minutos.insert(0, f"{task.minutos // 60}:{task.minutos % 60:02d}")
        self.in_categoria.delete(0, "end")
        self.in_categoria.insert(0, task.categoria)
        self.in_descripcion.delete("1.0", "end")
        self.in_descripcion.insert("1.0", task.descripcion)
        self.in_hora.set(task.hora_inicio or SIN_HORA)
        self.in_tipo.set(task.tipo_comunicacion or SIN_TIPO)
        self.in_solicitante.delete(0, "end")
        self.in_solicitante.insert(0, task.usuario_solicitante)
        self.lbl_form_state.configure(text="Editando tarea — guarda para aplicar.",
                                      text_color=("#2563eb", "#3b82f6"))
        self.in_titulo.focus_set()

    def _eliminar(self, task: Task):
        if not tkinter.messagebox.askyesno(
            "Confirmar eliminación",
            f"¿Eliminar la tarea «{task.titulo}» ({minutos_a_hhmm(task.minutos)})?",
            icon="warning", parent=self,
        ):
            return
        db.delete_task(self.conn, task.id)
        if self.editando_id == task.id:
            self.editando_id = None
            self._limpiar_form()
        self.refrescar()
        self.app.refrescar_calendario()
        self.app.toast("Tarea eliminada.")

    def refrescar(self):
        fecha_iso = self.fecha.isoformat()
        tipo = fechas.tipo_de_dia(self.fecha, self.app.feriados)
        etiqueta = fechas.etiqueta_de_dia(self.fecha, self.app.feriados)
        self.lbl_fecha.configure(text=fechas.format_fecha_larga(self.fecha))
        color = ("#d97706", "#f59e0b") if tipo != "laborable" else None
        texto = etiqueta or "Jornada laboral"
        self.lbl_tipo.configure(text=texto, text_color=color or
                                ctk.ThemeManager.theme["CTkLabel"]["text_color"])

        for w in self.scroll.winfo_children():
            w.destroy()

        tareas = db.list_tasks(self.conn, fecha_iso)
        total = sum(t.minutos for t in tareas)
        for i, t in enumerate(tareas):
            self._add_task_row(t, i)
        self._dibujar_horario(tareas)
        if self.editando_id is None:
            self.in_hora.set(self._siguiente_hora(tareas))

        meta = self.app.meta_diaria if tipo == "laborable" else 0
        self.lbl_total.configure(text=minutos_a_hhmm(total))
        if meta:
            pct = min(total / meta, 1.0)
            self.barra.set(pct)
            restante = meta - total
            detalle = (f"Te sobran {minutos_a_hhmm(max(restante, 0))} para la meta"
                       if restante > 0 else f"¡Meta cumplida! +{minutos_a_hhmm(total - meta)}")
            self.lbl_vs_meta.configure(text=f"Meta: {minutos_a_hhmm(meta)} — {detalle}")
            self.lbl_pct.configure(text=f"{int(pct * 100)}%")
        else:
            self.barra.set(0)
            self.lbl_vs_meta.configure(
                text=f"{etiqueta} — la meta visual es 0, puedes registrar igual.")
            self.lbl_pct.configure(text="—")

    def _add_task_row(self, t: Task, i: int):
        row = ctk.CTkFrame(self.scroll, corner_radius=8)
        row.grid(row=i, column=0, sticky="ew", pady=3)
        row.grid_columnconfigure(0, weight=1)

        color = "#3b82f6" if i % 2 == 0 else "#10b981"
        badge = ctk.CTkFrame(row, fg_color=color, corner_radius=6, width=4, height=24)
        badge.grid(row=0, column=0, padx=(8, 0), pady=6)

        info = ctk.CTkFrame(row, fg_color="transparent")
        info.grid(row=0, column=1, sticky="ew", padx=8, pady=6)
        info.grid_columnconfigure(0, weight=1)
        if t.hora_inicio:
            ini = hora_a_minutos(t.hora_inicio)
            rango = f"{t.hora_inicio}–{minutos_a_hora((ini + t.minutos) % 1440)}"
            titulo = f"{rango} · {minutos_a_hhmm(t.minutos)} · {t.titulo}"
        else:
            titulo = f"⏱ {minutos_a_hhmm(t.minutos)} · {t.titulo}"
        if t.categoria:
            titulo += f"   [{t.categoria}]"
        ctk.CTkLabel(info, text=titulo, font=ctk.CTkFont(size=13, weight="bold"),
                     anchor="w").grid(row=0, column=0, sticky="ew")
        detalle = []
        if t.tipo_comunicacion:
            detalle.append(f"Vía {t.tipo_comunicacion}")
        if t.usuario_solicitante:
            detalle.append(f"Solicita: {t.usuario_solicitante}")
        if detalle:
            ctk.CTkLabel(info, text=" · ".join(detalle), font=ctk.CTkFont(size=12),
                         anchor="w", text_color=("#2563eb", "#60a5fa")
                         ).grid(row=1, column=0, sticky="ew")
        if t.descripcion:
            ctk.CTkLabel(info, text=t.descripcion, font=ctk.CTkFont(size=12),
                         anchor="w", text_color=("gray40", "gray60")
                         ).grid(row=2, column=0, sticky="ew")
        styled_button(row, "✏", lambda: self._cargar_para_editar(t), width=34
                      ).grid(row=0, column=2, padx=(4, 4), pady=6)
        styled_button(row, "🗑", lambda: self._eliminar(t), width=34, danger=True
                      ).grid(row=0, column=3, padx=(0, 8), pady=6)

    # ---------- horario del día ----------

    def _siguiente_hora(self, tareas) -> str:
        """Sugiere iniciar cuando termina la última tarea con hora (múltiplo de 15)."""
        fin = HORA_MIN
        for t in tareas:
            ini = hora_a_minutos(t.hora_inicio) if t.hora_inicio else None
            if ini is not None:
                fin = max(fin, ini + t.minutos)
        fin = -(-fin // 15) * 15
        return minutos_a_hora(fin) if fin <= HORA_MAX else SIN_HORA

    def _dibujar_horario(self, tareas):
        for w in self.lienzo.winfo_children():
            w.destroy()
        gris = ("gray60", "gray45")
        for m in range(HORA_MIN, HORA_MAX + 1, 30):
            y = int((m - HORA_MIN) * ESCALA)
            ctk.CTkLabel(self.lienzo, text=minutos_a_hora(m), font=ctk.CTkFont(size=10),
                         text_color=gris, width=40, height=12).place(x=0, y=max(y - 6, 0))
            ctk.CTkFrame(self.lienzo, width=ANCHO_BLOQUES + 8, height=1,
                         fg_color=("gray80", "gray28")).place(x=46, y=y)

        bloques = []  # (inicio, fin, inicio real, tarea) recortados al horario visible
        for t in tareas:
            if not t.hora_inicio:
                continue
            ini = hora_a_minutos(t.hora_inicio)
            ini_c, fin_c = max(ini, HORA_MIN), min(ini + t.minutos, HORA_MAX)
            if fin_c > ini_c:
                bloques.append((ini_c, fin_c, ini, t))
        bloques.sort(key=lambda b: b[0])

        # carriles para tareas que se solapan
        carriles, fines = [], []
        for ini_c, fin_c, _, _ in bloques:
            for k, f in enumerate(fines):
                if f <= ini_c:
                    fines[k] = fin_c
                    carriles.append(k)
                    break
            else:
                fines.append(fin_c)
                carriles.append(len(fines) - 1)
        n = max(len(fines), 1)
        ancho = ANCHO_BLOQUES // n

        for i, ((ini_c, fin_c, ini, t), carril) in enumerate(zip(bloques, carriles)):
            alto = max(int((fin_c - ini_c) * ESCALA), 16)
            bloque = ctk.CTkFrame(self.lienzo, width=ancho - 2, height=alto,
                                  corner_radius=6, fg_color=COLORES[i % len(COLORES)])
            bloque.place(x=48 + carril * ancho, y=int((ini_c - HORA_MIN) * ESCALA))
            texto = t.titulo
            if alto >= 34:
                texto += f"\n{minutos_a_hora(ini)}–{minutos_a_hora(ini + t.minutos)}"
            lbl = ctk.CTkLabel(bloque, text=texto, font=ctk.CTkFont(size=11),
                               text_color="white", anchor="w", justify="left",
                               wraplength=max(ancho - 14, 30))
            lbl.place(x=6, y=1)
            for w in (bloque, lbl):
                w.bind("<Button-1>", lambda e, t=t: self._cargar_para_editar(t))
