"""Pestaña 'Base de conocimiento': lista + editor."""
import tkinter.messagebox

import customtkinter as ctk

import db
from models import Note, ValidationError, validar_nota
from ui.widgets import styled_button, field_label, entry, multiline


class KnowledgeView(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self.app = app
        self.conn = app.conn
        self.nota_actual_id = None

        self.grid_columnconfigure(0, weight=2, uniform="col")
        self.grid_columnconfigure(1, weight=3, uniform="col")
        self.grid_rowconfigure(1, weight=1)

        self._build_left()
        self._build_editor()
        self.refrescar_lista()

    # ---------- construcción ----------

    def _build_left(self):
        left = ctk.CTkFrame(self, corner_radius=12)
        left.grid(row=0, column=0, rowspan=2, sticky="nsew", padx=(0, 12))
        left.grid_rowconfigure(2, weight=1)
        left.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(left, text="Notas", font=ctk.CTkFont(size=14, weight="bold")
                      ).grid(row=0, column=0, sticky="w", padx=14, pady=(12, 6))

        search_bar = ctk.CTkFrame(left, fg_color="transparent")
        search_bar.grid(row=1, column=0, sticky="ew", padx=14, pady=(0, 8))
        search_bar.grid_columnconfigure(0, weight=1)
        self.in_busqueda = entry(search_bar, "Buscar en tema, título, contenido…")
        self.in_busqueda.grid(row=0, column=0, sticky="ew", padx=(0, 6))
        self.in_busqueda.bind("<Return>", lambda e: self.refrescar_lista())
        styled_button(search_bar, "🔍", self.refrescar_lista, width=36
                      ).grid(row=0, column=1)

        self.lista = ctk.CTkScrollableFrame(left, fg_color="transparent")
        self.lista.grid(row=2, column=0, sticky="nsew", padx=8, pady=(0, 8))
        self.lista.grid_columnconfigure(0, weight=1)

        actions = ctk.CTkFrame(left, fg_color="transparent")
        actions.grid(row=3, column=0, sticky="ew", padx=14, pady=(0, 12))
        actions.grid_columnconfigure(1, weight=1)
        styled_button(actions, "＋ Nueva nota", self.nueva_nota, primary=True
                      ).grid(row=0, column=0, padx=(0, 6))
        styled_button(actions, "🗑 Eliminar", self.eliminar_nota, danger=True
                      ).grid(row=0, column=1)

    def _build_editor(self):
        editor = ctk.CTkFrame(self, corner_radius=12)
        editor.grid(row=0, column=1, rowspan=2, sticky="nsew")
        editor.grid_columnconfigure(0, weight=1)
        editor.grid_rowconfigure(5, weight=1)

        ctk.CTkLabel(editor, text="Editor", font=ctk.CTkFont(size=14, weight="bold")
                      ).grid(row=0, column=0, sticky="w", padx=14, pady=(12, 4))

        row1 = ctk.CTkFrame(editor, fg_color="transparent")
        row1.grid(row=1, column=0, sticky="ew", padx=14)
        row1.grid_columnconfigure(0, weight=1)
        row1.grid_columnconfigure(1, weight=1)
        field_label(row1, "Tema").grid(row=0, column=0, sticky="w", pady=(4, 2))
        self.in_tema = entry(row1, "Ej. Python, recetas…", width=240)
        self.in_tema.grid(row=1, column=0, sticky="ew", padx=(0, 8))
        field_label(row1, "Título *").grid(row=0, column=1, sticky="w", pady=(4, 2))
        self.in_titulo = entry(row1, "Título de la nota", width=240)
        self.in_titulo.grid(row=1, column=1, sticky="ew")

        field_label(editor, "Etiquetas (separadas por comas)").grid(
            row=2, column=0, sticky="w", padx=14, pady=(8, 2))
        self.in_etiquetas = entry(editor, "tip, sql, productividad")
        self.in_etiquetas.grid(row=3, column=0, sticky="ew", padx=14)

        field_label(editor, "Contenido").grid(row=4, column=0, sticky="w",
                                              padx=14, pady=(8, 2))
        self.in_contenido = multiline(editor, height=260)
        self.in_contenido.grid(row=5, column=0, sticky="nsew", padx=14, pady=(0, 4))

        foot = ctk.CTkFrame(editor, fg_color="transparent")
        foot.grid(row=6, column=0, sticky="ew", padx=14, pady=(0, 12))
        foot.grid_columnconfigure(1, weight=1)
        self.lbl_estado = ctk.CTkLabel(foot, text="", font=ctk.CTkFont(size=12))
        self.lbl_estado.grid(row=0, column=0, sticky="w")
        styled_button(foot, "Guardar nota", self.guardar, primary=True
                      ).grid(row=0, column=1, sticky="e")

    # ---------- comportamiento ----------

    def nueva_nota(self):
        self.nota_actual_id = None
        self._limpiar_editor()
        self.in_titulo.focus_set()
        self.lbl_estado.configure(text="Nueva nota.", text_color=("#2563eb", "#3b82f6"))

    def _limpiar_editor(self):
        for w in (self.in_tema, self.in_titulo, self.in_etiquetas):
            w.delete(0, "end")
        self.in_contenido.delete("1.0", "end")
        self.lbl_estado.configure(text="")

    def _cargar_nota(self, note: Note):
        self.nota_actual_id = note.id
        self.in_tema.delete(0, "end")
        self.in_tema.insert(0, note.tema)
        self.in_titulo.delete(0, "end")
        self.in_titulo.insert(0, note.titulo)
        self.in_etiquetas.delete(0, "end")
        self.in_etiquetas.insert(0, note.etiquetas)
        self.in_contenido.delete("1.0", "end")
        self.in_contenido.insert("1.0", note.contenido)
        self.lbl_estado.configure(text=f"Editando nota #{note.id}.")

    def guardar(self):
        try:
            titulo = validar_nota(self.in_titulo.get())
        except ValidationError as e:
            self.lbl_estado.configure(text=str(e), text_color=("#c0392b", "#e05d52"))
            return
        note = Note(
            titulo=titulo,
            tema=self.in_tema.get().strip(),
            contenido=self.in_contenido.get("1.0", "end").strip(),
            etiquetas=self.in_etiquetas.get().strip(),
            id=self.nota_actual_id,
        )
        if self.nota_actual_id is None:
            self.nota_actual_id = db.insert_note(self.conn, note)
            self.lbl_estado.configure(text="Nota guardada.",
                                       text_color=("#1d9a53", "#2fb86d"))
            self.app.toast("Nota guardada en la base de conocimiento.")
        else:
            db.update_note(self.conn, note)
            self.lbl_estado.configure(text="Nota actualizada.",
                                       text_color=("#1d9a53", "#2fb86d"))
            self.app.toast("Nota actualizada.")
        self.refrescar_lista()

    def eliminar_nota(self):
        if self.nota_actual_id is None:
            self.lbl_estado.configure(text="No hay nota seleccionada.",
                                      text_color=("#c0392b", "#e05d52"))
            return
        note = db.get_note(self.conn, self.nota_actual_id)
        if not note:
            return
        if not tkinter.messagebox.askyesno(
            "Confirmar eliminación",
            f"¿Eliminar la nota «{note.titulo}»? Esta acción no se puede deshacer.",
            icon="warning", parent=self,
        ):
            return
        db.delete_note(self.conn, self.nota_actual_id)
        self.nueva_nota()
        self.refrescar_lista()
        self.app.toast("Nota eliminada.")

    def refrescar_lista(self):
        for w in self.lista.winfo_children():
            w.destroy()
        query = self.in_busqueda.get().strip()
        notas = db.list_notes(self.conn, query)
        if not notas:
            ctk.CTkLabel(self.lista, text="Sin resultados." if query else "Sin notas aún.",
                         text_color=("gray60", "gray50")
                         ).grid(row=0, column=0, sticky="w", padx=6, pady=4)
        for i, n in enumerate(notas):
            card = ctk.CTkFrame(self.lista, corner_radius=8,
                                fg_color=("gray88", "gray17"))
            card.grid(row=i, column=0, sticky="ew", pady=3)
            card.grid_columnconfigure(0, weight=1)
            ctk.CTkLabel(card, text=n.titulo, font=ctk.CTkFont(size=13, weight="bold"),
                         anchor="w").grid(row=0, column=0, sticky="ew", padx=10,
                                          pady=(6, 0))
            sub = n.tema if n.tema else "Sin tema"
            ctk.CTkLabel(card, text=sub, font=ctk.CTkFont(size=11),
                         text_color=("gray45", "gray55"), anchor="w"
                         ).grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 6))
            card.bind("<Button-1>", lambda e, n=n: self._cargar_nota(n))
            for child in card.winfo_children():
                child.bind("<Button-1>", lambda e, n=n: self._cargar_nota(n))
