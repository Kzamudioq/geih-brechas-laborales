# Estructura de la base de datos (GEIH 2023-01 a 2026-08)

Analizado sobre los 44 zips (352 CSV, 8 módulos por mes). Las cifras de filas son de enero de 2025.

## Modelo relacional

```
periodo ──< hogar ──< persona ──┬── fuerza_trabajo (PET) ──┬── ocupados
                                │                          └── no_ocupados
                                ├── migracion
                                ├── otras_formas_trabajo   (solo PET)
                                └── otros_ingresos         (solo PET)
```

| Tabla | Llave primaria | Filas (ene-2025) | Columnas (unión 2023-26) |
|---|---|---|---|
| `hogar` | periodo, DIRECTORIO, SECUENCIA_P, HOGAR | 24.109 | 50 |
| `persona` (características generales, salud, educación) | periodo, DIRECTORIO, SECUENCIA_P, ORDEN | 67.857 | 74 |
| `migracion` | igual que persona | 67.857 | 43 |
| `fuerza_trabajo` | igual que persona | 54.070 | 43 |
| `ocupados` | igual que persona | 28.317 | 211 |
| `no_ocupados` | igual que persona | 25.753 | 39 |
| `otras_formas_trabajo` | igual que persona | 54.070 | 112 |
| `otros_ingresos` | igual que persona | 54.070 | 64 |

Verificado en enero de 2025:
- Las llaves son únicas en todas las tablas.
- Todas las filas de cada módulo existen en `persona`, y toda persona existe en `hogar`.
- Ocupados (28.317) + No ocupados (25.753) = Fuerza de trabajo (54.070). Fuerza de trabajo, Otras formas de trabajo y Otros ingresos cubren a la misma población (la PET).

Todas las tablas incluyen `PERIODO`, `MES`, `PER`, `REGIS`, `AREA`, `CLASE`, `DPTO` y el factor `FEX_C18`. El periodo (año-mes) entra en la llave porque `DIRECTORIO` puede repetirse entre meses.

## Variables clave para los indicadores

| Necesidad | Variable | Tabla |
|---|---|---|
| Sexo / edad | P3271 / P6040 | persona |
| Condición migratoria | P3373, P3375, P3376, P3378 | migracion |
| PET, desempleo | PET, FFT, DSI | fuerza_trabajo, no_ocupados |
| Ocupación, ingreso laboral | OCI, INGLABO | ocupados |
| Región | DPTO, AREA, CLASE | todas |
| Informalidad | **no viene calculada** (no existe `INFORMAL`) | se construye desde ocupados (pendiente definir) |

## Columnas que cambian entre años

Cada tabla guarda la **unión** de columnas; si un mes no la trae queda en `NULL`. El detalle por columna está en `columnas_por_modulo.csv`.

- **ocupados:** 14 columnas parciales (3 solo 2023-24, 5 solo desde 2025, 6 solo en 2026).
- **persona:** las 11 variables `P3147S*` solo existen en 2023-24. Las variables de orientación (`LGB_*`, `LGBT_*`, `Trans_numerica`), `Discapacidad`, `Dificultad` y `Campesina` solo vienen en enero y febrero de 2023, por lo que **no sirven para brechas en toda la serie**.
- **otros_ingresos:** 9 parciales (`P1661*` cambia en 2025, `P750S4` solo en 2026).
- **hogar:** `P4000` solo 2023-24; `P4005` y `P5222S11` solo desde 2025.
- **fuerza_trabajo:** `P6290` solo 2023-24. **no_ocupados:** 4 parciales.
- **migracion** y **otras_formas_trabajo:** sin cambios en los 44 meses.

## Reglas de carga

- Separador `;`. Codificación **mixta**: 201 de 352 archivos están en cp1252 y 151 en UTF-8; se detecta por archivo.
- Los nombres de módulo varían (espacios no separables, `.CSV` en el nombre, `Capítulos de…`, `No ocupado`); se normalizan al nombre canónico.
- Algunos meses traen `CSV.zip` anidado; la carpeta de DTA se llama `DTA` o `DAT`.
- Registro en `meta.carga` de qué periodo y módulo ya se cargó, para la actualización incremental.

## Pendientes antes de crear tablas

1. Definir informalidad (criterio DANE) y construirla desde `ocupados`.
2. Extraer las etiquetas de valores de los DTA para el diccionario.
3. Validar 2023 y 2024 con las mismas pruebas de llaves que enero de 2025.
