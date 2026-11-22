"""Genera sql/01_esquema_raw.sql a partir de docs/inventario/columnas_por_modulo.csv.

Uso:  python src/geih/generar_esquema.py
Cada tabla raw guarda la UNIÓN de columnas de todos los meses como TEXT; los meses que
no traen una columna quedan en NULL. El tipado numérico se hace en la capa staging.
"""
import csv
import re
import sys
from collections import OrderedDict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from comun import LLAVES, MODULOS  # noqa: E402

RAIZ = Path(__file__).resolve().parents[2]
ENTRADA = RAIZ / "docs" / "inventario" / "columnas_por_modulo.csv"
SALIDA = RAIZ / "sql" / "01_esquema_raw.sql"

columnas = OrderedDict((t, []) for t in MODULOS.values())
with open(ENTRADA, encoding="utf-8") as f:
    for fila in csv.DictReader(f):
        tabla = MODULOS[fila["modulo"]]
        col = fila["columna"].strip().lower()
        if not re.fullmatch(r"[a-z_][a-z0-9_]*", col):
            raise SystemExit(f"Nombre de columna no válido: {fila['columna']!r}")
        if col not in columnas[tabla]:
            columnas[tabla].append(col)

lineas = [
    "-- Generado por src/geih/generar_esquema.py. No editar a mano.",
    "-- Capa raw: una tabla por módulo de la GEIH, columnas en TEXT, particionable por periodo.",
    "",
    "CREATE SCHEMA IF NOT EXISTS raw;",
    "CREATE SCHEMA IF NOT EXISTS meta;",
    "",
    "-- Registro de qué periodo y módulo ya se cargó (permite la carga incremental)",
    "CREATE TABLE IF NOT EXISTS meta.carga (",
    "    periodo      date        NOT NULL,",
    "    modulo       text        NOT NULL,",
    "    tabla        text        NOT NULL,",
    "    filas        integer     NOT NULL,",
    "    codificacion text        NOT NULL,",
    "    archivo_zip  text        NOT NULL,",
    "    cargado_en   timestamptz NOT NULL DEFAULT now(),",
    "    PRIMARY KEY (periodo, modulo)",
    ");",
    "",
]
for tabla, cols in columnas.items():
    cols = [c for c in cols if c != "periodo"]  # 'periodo' del DANE es el año; usamos periodo (date)
    lineas.append(f"CREATE TABLE IF NOT EXISTS raw.{tabla} (")
    lineas.append("    periodo date NOT NULL,  -- primer día del mes de la encuesta")
    lineas.append(",\n".join(f"    {c} text" for c in cols))
    lineas.append(");")
    llave = ", ".join(("periodo",) + LLAVES[tabla])
    lineas.append(f"CREATE INDEX IF NOT EXISTS ix_{tabla}_llave ON raw.{tabla} ({llave});")
    lineas.append("")

SALIDA.parent.mkdir(exist_ok=True)
SALIDA.write_text("\n".join(lineas), encoding="utf-8")
print(f"{SALIDA} escrito: " + ", ".join(f"{t}={len(c)}" for t, c in columnas.items()))
