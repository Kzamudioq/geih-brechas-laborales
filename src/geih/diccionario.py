"""Lee los diccionarios de datos del DANE (XLSX) y genera dos CSV:

    docs/diccionario/dicc_variables.csv  -> una fila por (version, variable)
    docs/diccionario/dicc_valores.csv    -> una fila por (version, variable, valor)

Uso:  python src/geih/diccionario.py        (requiere openpyxl)

Versiones: 2023 (bases anonimizadas), 2023_completa (solo rellena huecos), 2025, 2026.
No hay diccionario de 2024 publicado; esa información se cubre con 2023 y 2025.
"""
import csv
import re
import sys
from pathlib import Path

import openpyxl

RAIZ = Path(__file__).resolve().parents[2]
DIR = RAIZ / "docs" / "diccionario"

ARCHIVOS = {
    "2023": DIR / "diccionario_2023_anonimizadas.xlsx",
    "2023_completa": DIR / "diccionario_2023_completa.xlsx",
    "2025": DIR / "diccionario_2025.xlsx",
    "2026": DIR / "diccionario_2026.xlsx",
}


def limpia(x):
    if x is None:
        return None
    if isinstance(x, float) and x.is_integer():
        x = int(x)
    s = re.sub(r"\s+", " ", str(x).replace("\xa0", " ")).strip()
    return s or None


def hoja_principal(wb):
    """La hoja que contiene el encabezado de variables."""
    for ws in wb.worksheets:
        for fila in ws.iter_rows(min_row=1, max_row=8, values_only=True):
            textos = [str(c).lower() for c in fila if c]
            if any("variable" in t and ("nombre" in t or "id." in t) for t in textos):
                return ws
    raise ValueError("No se encontró la hoja del diccionario")


def columnas(fila):
    """Ubica cada columna por el texto del encabezado."""
    m = {}
    for i, c in enumerate(fila):
        t = (limpia(c) or "").lower()
        if ("nombre de la variable" in t or "id. de la variable" in t) and "nom" not in m:
            m["nom"] = i
        elif ("descripción de la variable" in t or "descipción de la variable" in t) and "desc" not in m:
            m["desc"] = i
        elif t.startswith("tipo de dato") and "tipo" not in m:
            m["tipo"] = i
        elif t.startswith("longitud") and "lon" not in m:
            m["lon"] = i
        elif t.startswith("dominios") and "dom" not in m:
            m["dom"] = i
    faltan = {"nom", "desc", "tipo", "lon", "dom"} - set(m)
    if faltan:
        raise ValueError(f"Encabezados no encontrados: {faltan}")
    return m


def leer(version, ruta):
    ws = hoja_principal(openpyxl.load_workbook(ruta, read_only=True, data_only=True))
    filas = list(ws.iter_rows(values_only=True))
    for i, f in enumerate(filas[:10]):
        try:
            m = columnas(f)
            inicio = i + 1
            break
        except ValueError:
            continue
    else:
        raise ValueError(f"{ruta.name}: sin fila de encabezados")
    variables, valores = {}, {}
    tabla_id = tabla_nom = None
    for f in filas[inicio:]:
        f = list(f) + [None] * 25
        if limpia(f[0]) is not None:  # nueva tabla del DANE
            tabla_id, tabla_nom = limpia(f[0]), limpia(f[1])
        nom = limpia(f[m["nom"]])
        if not nom or nom.lower() in ("nombre de la variable o la columna",):
            continue
        nom = nom.lower()
        v = variables.setdefault(nom, {"descripcion": None, "tipo_dato": None, "longitud": None,
                                       "tabla_dane": tabla_id})
        v["descripcion"] = v["descripcion"] or limpia(f[m["desc"]])
        v["tipo_dato"] = v["tipo_dato"] or limpia(f[m["tipo"]])
        v["longitud"] = v["longitud"] or limpia(f[m["lon"]])
        val, eti = limpia(f[m["dom"]]), limpia(f[m["dom"] + 1])
        if val is not None and eti is not None:
            valores.setdefault((nom, val), eti)
    return variables, valores


def main():
    todas_vars, todos_vals = [], []
    cubiertas = set()
    for version, ruta in ARCHIVOS.items():
        variables, valores = leer(version, ruta)
        for nom, d in variables.items():
            if version == "2023_completa" and nom in cubiertas:
                continue
            todas_vars.append({"version": version, "variable": nom, **d})
        for (nom, val), eti in valores.items():
            if version == "2023_completa" and nom in cubiertas:
                continue
            todos_vals.append({"version": version, "variable": nom, "valor": val, "etiqueta": eti})
        if version == "2023":
            cubiertas = set(variables)
        print(f"{version:<14} {len(variables):>5} variables  {len(valores):>6} valores")

    with open(DIR / "dicc_variables.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["version", "variable", "descripcion", "tipo_dato", "longitud", "tabla_dane"])
        w.writeheader()
        w.writerows(todas_vars)
    with open(DIR / "dicc_valores.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["version", "variable", "valor", "etiqueta"])
        w.writeheader()
        w.writerows(todos_vals)


if __name__ == "__main__":
    main()
