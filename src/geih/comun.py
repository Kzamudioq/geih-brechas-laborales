"""Utilidades comunes: nombres de módulos, meses y lectura de los zips del DANE."""
import io
import re
import unicodedata
import zipfile
from pathlib import Path

# nombre canónico del módulo en los CSV -> tabla en PostgreSQL
MODULOS = {
    "Características generales, seguridad social en salud y educación": "persona",
    "Datos del hogar y la vivienda": "hogar",
    "Fuerza de trabajo": "fuerza_trabajo",
    "Migración": "migracion",
    "No ocupados": "no_ocupados",
    "Ocupados": "ocupados",
    "Otras formas de trabajo": "otras_formas_trabajo",
    "Otros ingresos e impuestos": "otros_ingresos",
}

# columnas que identifican una fila en cada tabla (además de periodo)
LLAVES = {
    "hogar": ("directorio", "secuencia_p", "hogar"),
    "persona": ("directorio", "secuencia_p", "orden"),
    "migracion": ("directorio", "secuencia_p", "orden"),
    "fuerza_trabajo": ("directorio", "secuencia_p", "orden"),
    "ocupados": ("directorio", "secuencia_p", "orden"),
    "no_ocupados": ("directorio", "secuencia_p", "orden"),
    "otras_formas_trabajo": ("directorio", "secuencia_p", "orden"),
    "otros_ingresos": ("directorio", "secuencia_p", "orden"),
}

_MESES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]


def mes_de(nombre_zip):
    """Número de mes (1-12) a partir del nombre del zip: 'Enero', 'Ene_2024', 'Noviembre_ 2024'..."""
    n = unicodedata.normalize("NFKD", nombre_zip.lower()).encode("ascii", "ignore").decode()
    for i, m in enumerate(_MESES, 1):
        if n.startswith(m):
            return i
    raise ValueError(f"No se reconoce el mes en: {nombre_zip}")


def normalizar_modulo(nombre_archivo):
    """Lleva el nombre de archivo CSV al nombre canónico del módulo."""
    n = unicodedata.normalize("NFC", Path(nombre_archivo).name).replace("\xa0", " ")
    while re.search(r"\.csv$", n, flags=re.I):
        n = re.sub(r"\.csv$", "", n, flags=re.I)
    n = re.sub(r"\s+", " ", n).strip()
    if n.lower().startswith("capítulos de "):
        n = n[len("Capítulos de "):]
        n = n[0].upper() + n[1:]
    if n.lower() == "no ocupado":
        n = "No ocupados"
    # comparación sin distinguir mayúsculas/espacios
    for canon in MODULOS:
        if re.sub(r"\s+", " ", canon).lower() == n.lower():
            return canon
    raise ValueError(f"Módulo desconocido: {nombre_archivo!r} -> {n!r}")


def decodificar(raw):
    """Devuelve (texto, codificación). Los CSV del DANE vienen en UTF-8 o cp1252."""
    try:
        return raw.decode("utf-8-sig"), "utf-8"
    except UnicodeDecodeError:
        return raw.decode("cp1252", errors="replace"), "cp1252"


def iterar_csv(zf):
    """Recorre un zip (con zips anidados de CSV) y entrega (módulo canónico, bytes)."""
    for info in zf.infolist():
        if info.is_dir():
            continue
        bajo = info.filename.lower()
        if bajo.endswith(".zip"):
            if "csv" in bajo:
                with zipfile.ZipFile(io.BytesIO(zf.read(info))) as interno:
                    yield from iterar_csv(interno)
            continue
        if bajo.endswith(".csv"):
            yield normalizar_modulo(info.filename), zf.read(info)


def listar_zips(raiz):
    """[(año, mes, ruta)] ordenado, para data/raw/<año>/*.zip."""
    salida = []
    for d in sorted(Path(raiz).iterdir()):
        if d.is_dir() and d.name.isdigit():
            for z in sorted(d.glob("*.zip")):
                salida.append((int(d.name), mes_de(z.stem), z))
    return sorted(salida, key=lambda t: (t[0], t[1]))
