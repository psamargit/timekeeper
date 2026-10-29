# TimeKeeper — Registro de tiempo y base de conocimiento

Aplicación de escritorio en Python (CustomTkinter + SQLite) para registrar el tiempo
que dedicas a tus tareas cada día y mantener una base de conocimiento personal con
notas. Una sola ventana, tema claro/oscuro, y todos los datos en un archivo local.

## Requisitos

- Python 3.10 o superior (Windows, macOS o Linux)
- Tkinter (incluido en los instaladores oficiales de Python; en Linux puede requerir
  `sudo apt install python3-tk`)

## Instalación

```bash
pip install -r requirements.txt
```

## Ejecución

```bash
python main.py
```

## Dónde están los datos

- Base de datos SQLite: `data/app.db` (junto a la app; se crea al iniciar).
- Feriados marcados: `data/feriados.json`.
- Tamaño/posición de ventana, tema y meta diaria se guardan en la tabla `settings`.

Para respaldar tus datos copia la carpeta `data/`.

## Decisiones de diseño

- Jornada de referencia: 8 h (480 min), lunes a viernes; configurable en Ajustes.
- Sábados, domingos y feriados se pueden registrar igual; su meta visual es 0.
- Duración: acepta minutos (`90`) u horas:minutos (`1:30`); máximo 24 h por tarea.
- No se permiten fechas futuras.
- Migraciones aditivas e idempotentes (tabla `schema_migration_log`); nunca borran datos.
