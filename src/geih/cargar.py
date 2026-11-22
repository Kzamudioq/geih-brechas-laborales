"""Cargador incremental de la GEIH a PostgreSQL (capa raw).

Uso (desde la raíz del repo):
    python src/geih/cargar.py                    # carga solo los meses que faltan
    python src/geih/cargar.py --solo 2025-01     # un mes
    python src/geih/cargar.py --recargar 2025-01 # borra y vuelve a cargar ese mes
    python src/geih/cargar.py --validar          # revisa llaves y relaciones
    python src/geih/cargar.py --diccionario      # carga el diccionario de variables

La conexión se lee de variables de entorno o del archivo .env (ignorado por Git):
    PGHOST=localhost  PGPORT=5432  PGUSER=postgres  PGPASSWORD=...  PGDATABASE=geih
o bien DATABASE_URL.
"""
import argparse
import csv
import io
import os
import sys
import zipfile
from datetime import date
from pathlib import Path

import psycopg

sys.path.insert(0, str(Path(__file__).parent))
from comun import LLAVES, MODULOS, decodificar, iterar_csv, listar_zips  # noqa: E402

RAIZ = Path(__file__).resolve().parents[2]


def leer_env():
    """Carga .env (CLAVE=valor) sin pisar variables ya definidas."""
    ruta = RAIZ / ".env"
    if ruta.exists():
        for linea in ruta.read_text(encoding="utf-8").splitlines():
            linea = linea.strip()
            if linea and not linea.startswith("#") and "=" in linea:
                k, v = linea.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def conectar():
    leer_env()
    if os.environ.get("DATABASE_URL"):
        return psycopg.connect(os.environ["DATABASE_URL"])
    return psycopg.connect(
        host=os.environ.get("PGHOST", "localhost"),
        port=os.environ.get("PGPORT", "5432"),
        user=os.environ.get("PGUSER", "postgres"),
        password=os.environ.get("PGPASSWORD", ""),
        dbname=os.environ.get("PGDATABASE", "geih"),
    )


def asegurar_esquema(conn):
    with conn.cursor() as cur:
        for archivo in ("01_esquema_raw.sql", "02_diccionario.sql"):
            cur.execute((RAIZ / "sql" / archivo).read_text(encoding="utf-8"))
    conn.commit()


def cargar_diccionario(conn):
    """Carga docs/diccionario/dicc_variables.csv y dicc_valores.csv en meta.dicc_*."""
    d = RAIZ / "docs" / "diccionario"
    with conn.cursor() as cur:
        cur.execute("TRUNCATE meta.dicc_variable, meta.dicc_valor")
        for archivo, tabla, cols in (
            ("dicc_variables.csv", "meta.dicc_variable", ["version", "variable", "descripcion", "tipo_dato", "longitud", "tabla_dane"]),
            ("dicc_valores.csv", "meta.dicc_valor", ["version", "variable", "valor", "etiqueta"]),
        ):
            n = 0
            with open(d / archivo, encoding="utf-8", newline="") as f, cur.copy(f"COPY {tabla} ({', '.join(cols)}) FROM STDIN") as copy:
                for fila in csv.DictReader(f):
                    copy.write_row([fila[c] or None for c in cols])
                    n += 1
            print(f"{tabla}: {n} filas")
    conn.commit()


def columnas_de(conn, tabla):
    with conn.cursor() as cur:
        cur.execute(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_schema='raw' AND table_name=%s",
            (tabla,),
        )
        return {r[0] for r in cur.fetchall()}


def cargar_modulo(conn, periodo, modulo, raw, nombre_zip):
    tabla = MODULOS[modulo]
    texto, enc = decodificar(raw)
    lector = csv.reader(io.StringIO(texto, newline=""), delimiter=";")
    encabezado = [c.strip().lower() for c in next(lector)]
    if len(set(encabezado)) != len(encabezado):
        raise ValueError(f"{tabla} {periodo}: columnas repetidas en el encabezado")
    # el 'periodo' del DANE es el año; nuestro periodo (date) lo agregamos aparte
    idx = [i for i, c in enumerate(encabezado) if c != "periodo"]
    cols = [encabezado[i] for i in idx]

    # si el DANE agrega columnas nuevas, la tabla las incorpora (como TEXT)
    existentes = columnas_de(conn, tabla)
    with conn.cursor() as cur:
        for c in cols:
            if c not in existentes:
                cur.execute(f'ALTER TABLE raw.{tabla} ADD COLUMN "{c}" text')
                print(f"    + columna nueva en raw.{tabla}: {c}")

    n = 0
    lista = ", ".join(['periodo'] + [f'"{c}"' for c in cols])
    with conn.cursor() as cur:
        with cur.copy(f"COPY raw.{tabla} ({lista}) FROM STDIN") as copy:
            for fila in lector:
                if not fila:
                    continue
                if len(fila) != len(encabezado):
                    raise ValueError(f"{tabla} {periodo}: fila {n + 2} con {len(fila)} campos, se esperaban {len(encabezado)}")
                copy.write_row([periodo] + [(fila[i].strip() or None) for i in idx])
                n += 1
        cur.execute(
            "INSERT INTO meta.carga (periodo, modulo, tabla, filas, codificacion, archivo_zip) "
            "VALUES (%s,%s,%s,%s,%s,%s)",
            (periodo, modulo, tabla, n, enc, nombre_zip),
        )
    return n


def cargar(conn, raiz, solo=None, recargar=None):
    with conn.cursor() as cur:
        cur.execute("SELECT periodo, modulo FROM meta.carga")
        hechos = {(p, m) for p, m in cur.fetchall()}
    for anio, mes, ruta in listar_zips(raiz):
        ym = f"{anio}-{mes:02d}"
        if solo and ym != solo and ym != recargar:
            continue
        if recargar and ym != recargar:
            continue
        periodo = date(anio, mes, 1)
        if recargar:
            with conn.cursor() as cur:
                for tabla in MODULOS.values():
                    cur.execute(f"DELETE FROM raw.{tabla} WHERE periodo=%s", (periodo,))
                cur.execute("DELETE FROM meta.carga WHERE periodo=%s", (periodo,))
            conn.commit()
            hechos = {(p, m) for p, m in hechos if p != periodo}
        pendientes = [m for m in MODULOS if (periodo, m) not in hechos]
        if not pendientes:
            print(f"{ym}: ya cargado")
            continue
        print(f"{ym}: cargando {ruta.name}")
        try:
            with zipfile.ZipFile(ruta) as zf:
                vistos = set()
                for modulo, raw in iterar_csv(zf):
                    if modulo in vistos or modulo not in pendientes:
                        continue
                    vistos.add(modulo)
                    n = cargar_modulo(conn, periodo, modulo, raw, ruta.name)
                    print(f"    {MODULOS[modulo]:<22}{n:>9,} filas".replace(",", "."))
                faltan = set(pendientes) - vistos
                if faltan:
                    raise ValueError(f"{ym}: faltan módulos en el zip: {sorted(faltan)}")
            conn.commit()  # un mes se confirma completo o no se carga
        except Exception:
            conn.rollback()
            print(f"    ERROR en {ym}; el mes se revirtió completo.")
            raise


def validar(conn):
    """Prueba llaves únicas, relaciones y que ocupados + no ocupados = fuerza de trabajo."""
    problemas = 0
    with conn.cursor() as cur:
        print("== Llaves únicas (periodos con duplicados)")
        for tabla, llave in LLAVES.items():
            k = ", ".join(("periodo",) + llave)
            cur.execute(
                f"SELECT periodo, count(*) FROM (SELECT {k} FROM raw.{tabla} GROUP BY {k} HAVING count(*)>1) d GROUP BY periodo ORDER BY periodo"
            )
            filas = cur.fetchall()
            problemas += len(filas)
            print(f"  {tabla:<22}", "OK" if not filas else f"DUPLICADOS en {[(str(p)[:7], n) for p, n in filas]}")

        print("== Huérfanos: filas de un módulo sin su persona")
        on = "m.periodo=p.periodo AND m.directorio=p.directorio AND m.secuencia_p=p.secuencia_p AND m.orden=p.orden"
        for tabla in ("migracion", "fuerza_trabajo", "ocupados", "no_ocupados", "otras_formas_trabajo", "otros_ingresos"):
            cur.execute(f"SELECT count(*) FROM raw.{tabla} m LEFT JOIN raw.persona p ON {on} WHERE p.directorio IS NULL")
            n = cur.fetchone()[0]
            problemas += n
            print(f"  {tabla:<22}", "OK" if n == 0 else f"{n} huérfanos")

        print("== Persona sin hogar")
        cur.execute(
            "SELECT count(*) FROM raw.persona p LEFT JOIN raw.hogar h ON p.periodo=h.periodo "
            "AND p.directorio=h.directorio AND p.secuencia_p=h.secuencia_p AND p.hogar=h.hogar WHERE h.directorio IS NULL"
        )
        n = cur.fetchone()[0]
        problemas += n
        print("  persona -> hogar      ", "OK" if n == 0 else f"{n} sin hogar")

        print("== Fuerza de trabajo = ocupados + no ocupados (periodos que no cuadran)")
        cur.execute(
            """
            SELECT f.periodo, f.n, coalesce(o.n,0), coalesce(d.n,0)
            FROM (SELECT periodo, count(*) n FROM raw.fuerza_trabajo GROUP BY 1) f
            LEFT JOIN (SELECT periodo, count(*) n FROM raw.ocupados GROUP BY 1) o USING (periodo)
            LEFT JOIN (SELECT periodo, count(*) n FROM raw.no_ocupados GROUP BY 1) d USING (periodo)
            WHERE f.n <> coalesce(o.n,0) + coalesce(d.n,0) ORDER BY 1
            """
        )
        filas = cur.fetchall()
        problemas += len(filas)
        if not filas:
            print("  OK en todos los periodos cargados")
        for p, ft, o, d in filas:
            print(f"  {str(p)[:7]}: fuerza_trabajo={ft} ocupados={o} no_ocupados={d}")
    print("\nRESULTADO:", "sin problemas" if problemas == 0 else f"{problemas} problemas por revisar")
    return problemas


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--raw", default=str(RAIZ / "data" / "raw"), help="carpeta con <año>/*.zip")
    ap.add_argument("--solo", metavar="AAAA-MM", help="cargar solo ese mes")
    ap.add_argument("--recargar", metavar="AAAA-MM", help="borrar y volver a cargar ese mes")
    ap.add_argument("--validar", action="store_true", help="validar llaves y relaciones y salir")
    ap.add_argument("--diccionario", action="store_true", help="cargar el diccionario de variables y salir")
    a = ap.parse_args()
    with conectar() as conn:
        asegurar_esquema(conn)
        if a.diccionario:
            cargar_diccionario(conn)
            return
        if a.validar:
            sys.exit(1 if validar(conn) else 0)
        cargar(conn, a.raw, solo=a.solo, recargar=a.recargar)


if __name__ == "__main__":
    main()
