"""Modelos de dominio y validación."""
from dataclasses import dataclass, field
from datetime import date, datetime

MAX_MINUTOS_TAREA = 24 * 60


@dataclass
class Task:
    fecha: str
    titulo: str
    minutos: int
    descripcion: str = ""
    categoria: str = ""
    id: int | None = None
    creado_en: str = field(default="", repr=False)
    actualizado_en: str = field(default="", repr=False)


@dataclass
class Note:
    titulo: str
    tema: str = ""
    contenido: str = ""
    etiquetas: str = ""
    id: int | None = None
    creado_en: str = field(default="", repr=False)
    actualizado_en: str = field(default="", repr=False)


class ValidationError(Exception):
    pass


def validar_fecha(valor: str) -> str:
    try:
        d = date.fromisoformat(valor)
    except (TypeError, ValueError):
        raise ValidationError("Fecha inválida (formato esperado: AAAA-MM-DD).")
    if d > date.today():
        raise ValidationError("No se pueden registrar tareas en fechas futuras.")
    return valor


def validar_minutos(valor: str) -> int:
    if ":" in (valor or ""):
        minutos = hhmm_a_minutos(valor)
        if minutos is None:
            raise ValidationError("Duración inválida: usa minutos u horas:minutos (1:30).")
        return _rango_minutos(minutos)
    try:
        minutos = int(valor)
    except (TypeError, ValueError):
        raise ValidationError("Los minutos deben ser un número entero.")
    return _rango_minutos(minutos)


def _rango_minutos(minutos: int) -> int:
    if minutos <= 0:
        raise ValidationError("Los minutos deben ser mayores que 0.")
    if minutos > MAX_MINUTOS_TAREA:
        raise ValidationError("Una tarea no puede superar 24 horas (1440 minutos).")
    return minutos


def validar_tarea(titulo: str, minutos: str, fecha: str) -> tuple[str, int, str]:
    titulo = (titulo or "").strip()
    if not titulo:
        raise ValidationError("El título es obligatorio.")
    mins = validar_minutos(minutos)
    validar_fecha(fecha)
    return titulo, mins, fecha


def validar_nota(titulo: str) -> str:
    titulo = (titulo or "").strip()
    if not titulo:
        raise ValidationError("El título de la nota es obligatorio.")
    return titulo


def hhmm_a_minutos(texto: str) -> int | None:
    """Convierte 'H:MM' u horas decimales a minutos; None si no es parseable."""
    texto = (texto or "").strip()
    if not texto:
        return None
    if ":" in texto:
        try:
            h, m = texto.split(":", 1)
            return int(h or 0) * 60 + int(m or 0)
        except ValueError:
            return None
    try:
        return int(round(float(texto) * 60))
    except ValueError:
        return None


def minutos_a_hhmm(minutos: int) -> str:
    return f"{minutos // 60}h {minutos % 60:02d}m"


def validar_meta_diaria(valor: str) -> int:
    try:
        meta = int(valor)
    except (TypeError, ValueError):
        raise ValidationError("La meta diaria debe ser un número entero de minutos.")
    if meta <= 0 or meta > 24 * 60:
        raise ValidationError("La meta diaria debe estar entre 1 y 1440 minutos.")
    return meta
