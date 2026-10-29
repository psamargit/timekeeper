"""Utilidades de fecha: jornada, feriados y semanas."""
import json
import os
from dataclasses import dataclass, field, asdict
from datetime import date, timedelta

import db

DEFAULT_META_MINUTOS = 480
FERIADOS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             "data", "feriados.json")

DIAS_ES = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes",
           "Sábado", "Domingo"]
MESES_ES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
            "agosto", "septiembre", "octubre", "noviembre", "diciembre"]


@dataclass
class DayInfo:
    fecha: str
    es_hoy: bool = False
    tipo: str = "laborable"  # laborable | fin_semana | feriado
    etiqueta: str = ""
    tareas: list = field(default_factory=list)
    total_minutos: int = 0
    meta_minutos: int = 0

    @property
    def meta_efectiva(self) -> int:
        return 0 if self.tipo != "laborable" else self.meta_minutos


def format_fecha_larga(fecha: date) -> str:
    return f"{DIAS_ES[fecha.weekday()]}, {fecha.day} de {MESES_ES[fecha.month - 1]} de {fecha.year}"


def lunes_de_semana(ref: date) -> date:
    return ref - timedelta(days=ref.weekday())


def week_dates(ref: date) -> list[date]:
    lunes = lunes_de_semana(ref)
    return [lunes + timedelta(days=i) for i in range(7)]


def parse_fecha(texto: str) -> date:
    return date.fromisoformat(texto)


def cargar_feriados() -> set[str]:
    try:
        with open(FERIADOS_FILE, encoding="utf-8") as f:
            return set(json.load(f))
    except (OSError, json.JSONDecodeError):
        return set()


def guardar_feriados(feriados: set[str]) -> None:
    os.makedirs(os.path.dirname(FERIADOS_FILE), exist_ok=True)
    with open(FERIADOS_FILE, "w", encoding="utf-8") as f:
        json.dump(sorted(feriados), f, indent=2, ensure_ascii=False)


def tipo_de_dia(d: date, feriados: set[str]) -> str:
    if d.isoformat() in feriados:
        return "feriado"
    if d.weekday() >= 5:
        return "fin_semana"
    return "laborable"


def etiqueta_de_dia(d: date, feriados: set[str]) -> str:
    t = tipo_de_dia(d, feriados)
    if t == "feriado":
        return "Feriado"
    if t == "fin_semana":
        return "Fin de semana"
    return ""


def get_meta_diaria(conn) -> int:
    raw = db.get_setting(conn, "meta_diaria", str(DEFAULT_META_MINUTOS))
    try:
        meta = int(raw)
        return meta if 0 < meta <= 24 * 60 else DEFAULT_META_MINUTOS
    except ValueError:
        return DEFAULT_META_MINUTOS
