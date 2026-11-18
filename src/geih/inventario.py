"""Inventario de los zips GEIH: filas y columnas por mes y modulo (solo CSV)."""
import csv, io, json, re, sys, unicodedata, zipfile
from pathlib import Path

RAW = Path(sys.argv[1])
OUT = Path(sys.argv[2])
MESES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]


def mes_de(nombre):
    n = unicodedata.normalize("NFKD", nombre.lower()).encode("ascii", "ignore").decode()
    for i, m in enumerate(MESES, 1):
        if n.startswith(m):
            return i
    raise ValueError(nombre)


def modulo_de(path):
    n = Path(path).stem
    return n


filas = []
cols = {}  # (modulo, mes) -> lista columnas
def norm_mod(path):
    n = unicodedata.normalize("NFC", Path(path).name)
    n = re.sub(r"\.csv$", "", n, flags=re.I).replace("\xa0", " ")
    n = re.sub(r"\s+", " ", n).strip()
    if n.lower().startswith("cap\u00edtulos de "):
        n = n[len("Cap\u00edtulos de "):]
        n = n[0].upper() + n[1:]
    return n


def procesar(zf, ym, zipname):
    for info in zf.infolist():
        if info.is_dir():
            continue
        low = info.filename.lower()
        if low.endswith(".zip"):
            if "csv" in low:  # zip anidado con los CSV
                with zipfile.ZipFile(io.BytesIO(zf.read(info))) as inner:
                    procesar(inner, ym, zipname)
            continue
        if not low.endswith(".csv"):
            continue
        mod = norm_mod(info.filename)
        raw = zf.read(info)
        try:
            txt = raw.decode("utf-8-sig"); enc = "utf-8"
        except UnicodeDecodeError:
            txt = raw.decode("cp1252", errors="replace"); enc = "cp1252"
        rd = csv.reader(io.StringIO(txt, newline=""), delimiter=";")
        header = next(rd)
        n = sum(1 for _ in rd)
        cols[(mod, ym)] = header
        filas.append({"anio_mes": ym, "zip": zipname, "modulo": mod, "filas": n, "columnas": len(header), "codificacion": enc})


for anio_dir in sorted(RAW.iterdir()):
    if not (anio_dir.is_dir() and anio_dir.name.isdigit()):
        continue
    anio = int(anio_dir.name)
    for z in sorted(anio_dir.glob("*.zip")):
        ym = f"{anio}-{mes_de(z.stem):02d}"
        with zipfile.ZipFile(z) as zf:
            procesar(zf, ym, z.name)
        print(ym, "ok", flush=True)

OUT.mkdir(parents=True, exist_ok=True)
with open(OUT / "inventario_archivos.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=["anio_mes", "zip", "modulo", "filas", "columnas", "codificacion"])
    w.writeheader()
    w.writerows(sorted(filas, key=lambda r: (r["anio_mes"], r["modulo"])))

meses = sorted({k[1] for k in cols})
mods = sorted({k[0] for k in cols})
resumen = {}
with open(OUT / "columnas_por_modulo.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["modulo", "columna", "primer_mes", "ultimo_mes", "n_meses", "en_todos"])
    for mod in mods:
        ms = [m for m in meses if (mod, m) in cols]
        todas = []
        for m in ms:
            for c in cols[(mod, m)]:
                if c not in todas:
                    todas.append(c)
        parciales = []
        for c in todas:
            pres = [m for m in ms if c in cols[(mod, m)]]
            w.writerow([mod, c, pres[0], pres[-1], len(pres), len(pres) == len(ms)])
            if len(pres) != len(ms):
                parciales.append((c, pres[0], pres[-1], len(pres)))
        resumen[mod] = {"meses": len(ms), "columnas_union": len(todas), "parciales": parciales}

json.dump(resumen, open(OUT / "resumen_columnas.json", "w"), ensure_ascii=False, indent=1)
print(json.dumps({m: {k: (v if k != "parciales" else len(v)) for k, v in d.items()} for m, d in resumen.items()}, ensure_ascii=False, indent=1))
