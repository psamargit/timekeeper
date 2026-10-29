"""SQLite local: conexión, migraciones y acceso a datos."""
import os
import sqlite3
from datetime import datetime

from models import Task, Note

DB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
DB_PATH = os.path.join(DB_DIR, "app.db")

MIGRATIONS = [
    """
    CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fecha TEXT NOT NULL,
        titulo TEXT NOT NULL,
        descripcion TEXT DEFAULT '',
        minutos INTEGER NOT NULL,
        categoria TEXT DEFAULT '',
        creado_en TEXT NOT NULL,
        actualizado_en TEXT NOT NULL
    )
    """,
    "CREATE INDEX IF NOT EXISTS idx_tasks_fecha ON tasks(fecha)",
    """
    CREATE TABLE IF NOT EXISTS notes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tema TEXT NOT NULL DEFAULT '',
        titulo TEXT NOT NULL,
        contenido TEXT NOT NULL DEFAULT '',
        etiquetas TEXT DEFAULT '',
        creado_en TEXT NOT NULL,
        actualizado_en TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS settings (
        clave TEXT PRIMARY KEY,
        valor TEXT NOT NULL
    )
    """,
]


def get_connection() -> sqlite3.Connection:
    os.makedirs(DB_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def migrate(conn: sqlite3.Connection) -> None:
    # Migraciones aditivas e idempotentes: nunca se borran tablas ni datos.
    conn.executescript(
        "CREATE TABLE IF NOT EXISTS schema_migration_log ("
        "version INTEGER PRIMARY KEY, aplicada_en TEXT NOT NULL)"
    )
    applied = {
        r["version"] for r in conn.execute("SELECT version FROM schema_migration_log")
    }
    with conn:
        for i, script in enumerate(MIGRATIONS, start=1):
            if i not in applied:
                conn.executescript(script)
                conn.execute(
                    "INSERT INTO schema_migration_log (version, aplicada_en) "
                    "VALUES (?, ?)",
                    (i, datetime.now().isoformat(timespec="seconds")),
                )


def _table_exists(conn: sqlite3.Connection, name: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (name,)
    ).fetchone()
    return row is not None


# ---------- settings ----------

def get_setting(conn: sqlite3.Connection, clave: str, default: str = "") -> str:
    row = conn.execute("SELECT valor FROM settings WHERE clave = ?", (clave,)).fetchone()
    return row["valor"] if row else default


def set_setting(conn: sqlite3.Connection, clave: str, valor: str) -> None:
    with conn:
        conn.execute(
            "INSERT INTO settings (clave, valor) VALUES (?, ?) "
            "ON CONFLICT(clave) DO UPDATE SET valor = excluded.valor",
            (clave, valor),
        )


def delete_setting(conn: sqlite3.Connection, clave: str) -> None:
    with conn:
        conn.execute("DELETE FROM settings WHERE clave = ?", (clave,))


# ---------- tasks ----------

def _row_to_task(row: sqlite3.Row) -> Task:
    return Task(
        id=row["id"],
        fecha=row["fecha"],
        titulo=row["titulo"],
        descripcion=row["descripcion"] or "",
        minutos=row["minutos"],
        categoria=row["categoria"] or "",
        creado_en=row["creado_en"],
        actualizado_en=row["actualizado_en"],
    )


def list_tasks(conn: sqlite3.Connection, fecha: str) -> list[Task]:
    rows = conn.execute(
        "SELECT * FROM tasks WHERE fecha = ? ORDER BY creado_en, id", (fecha,)
    ).fetchall()
    return [_row_to_task(r) for r in rows]


def get_task(conn: sqlite3.Connection, task_id: int) -> Task | None:
    row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    return _row_to_task(row) if row else None


def insert_task(conn: sqlite3.Connection, task: Task) -> int:
    now = datetime.now().isoformat(timespec="seconds")
    with conn:
        cur = conn.execute(
            "INSERT INTO tasks (fecha, titulo, descripcion, minutos, categoria, "
            "creado_en, actualizado_en) VALUES (?,?,?,?,?,?,?)",
            (task.fecha, task.titulo, task.descripcion, task.minutos,
             task.categoria, now, now),
        )
        return cur.lastrowid


def update_task(conn: sqlite3.Connection, task: Task) -> None:
    with conn:
        conn.execute(
            "UPDATE tasks SET fecha=?, titulo=?, descripcion=?, minutos=?, "
            "categoria=?, actualizado_en=? WHERE id=?",
            (task.fecha, task.titulo, task.descripcion, task.minutos,
             task.categoria, datetime.now().isoformat(timespec="seconds"), task.id),
        )


def delete_task(conn: sqlite3.Connection, task_id: int) -> None:
    with conn:
        conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))


def minutes_by_day(conn: sqlite3.Connection, desde: str, hasta: str) -> dict[str, int]:
    rows = conn.execute(
        "SELECT fecha, SUM(minutos) AS total FROM tasks "
        "WHERE fecha BETWEEN ? AND ? GROUP BY fecha",
        (desde, hasta),
    ).fetchall()
    return {r["fecha"]: r["total"] or 0 for r in rows}


# ---------- notes ----------

def _row_to_note(row: sqlite3.Row) -> Note:
    return Note(
        id=row["id"],
        tema=row["tema"] or "",
        titulo=row["titulo"],
        contenido=row["contenido"] or "",
        etiquetas=row["etiquetas"] or "",
        creado_en=row["creado_en"],
        actualizado_en=row["actualizado_en"],
    )


def list_notes(conn: sqlite3.Connection, query: str = "") -> list[Note]:
    if query:
        like = f"%{query}%"
        rows = conn.execute(
            "SELECT * FROM notes WHERE tema LIKE ? OR titulo LIKE ? OR "
            "contenido LIKE ? ORDER BY actualizado_en DESC, id DESC",
            (like, like, like),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM notes ORDER BY actualizado_en DESC, id DESC"
        ).fetchall()
    return [_row_to_note(r) for r in rows]


def get_note(conn: sqlite3.Connection, note_id: int) -> Note | None:
    row = conn.execute("SELECT * FROM notes WHERE id = ?", (note_id,)).fetchone()
    return _row_to_note(row) if row else None


def insert_note(conn: sqlite3.Connection, note: Note) -> int:
    now = datetime.now().isoformat(timespec="seconds")
    with conn:
        cur = conn.execute(
            "INSERT INTO notes (tema, titulo, contenido, etiquetas, creado_en, "
            "actualizado_en) VALUES (?,?,?,?,?,?)",
            (note.tema, note.titulo, note.contenido, note.etiquetas, now, now),
        )
        return cur.lastrowid


def update_note(conn: sqlite3.Connection, note: Note) -> None:
    with conn:
        conn.execute(
            "UPDATE notes SET tema=?, titulo=?, contenido=?, etiquetas=?, "
            "actualizado_en=? WHERE id=?",
            (note.tema, note.titulo, note.contenido, note.etiquetas,
             datetime.now().isoformat(timespec="seconds"), note.id),
        )


def delete_note(conn: sqlite3.Connection, note_id: int) -> None:
    with conn:
        conn.execute("DELETE FROM notes WHERE id = ?", (note_id,))
