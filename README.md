# geih-brechas-laborales

<p align="justify">
Pipeline reproducible para analizar las brechas del mercado laboral colombiano con los microdatos de la Gran Encuesta Integrada de Hogares (GEIH) del DANE. El repositorio consolida los archivos mensuales en una base relacional PostgreSQL, calcula indicadores laborales con factores de expansión, y publica los resultados en un tablero estático y en reportes técnicos reproducibles. Está diseñado para actualizarse cada vez que el DANE publica un mes nuevo.
</p>

## Qué responde

<p align="justify">
La pregunta central es cómo evolucionan la participación, la ocupación, el desempleo, la informalidad, la calidad del empleo y los ingresos según sexo, condición migratoria, edad y territorio, y qué parte de las brechas persiste una vez se controla la composición de los grupos. El análisis es descriptivo y de brechas, no causal. La referencia metodológica es Orjuela (2024), tesis de maestría sobre calidad laboral y migración venezolana. El plan completo, con variables y fuentes priorizadas, está en <a href="docs/plan_estudio.md">docs/plan_estudio.md</a>.
</p>

## Indicadores

<p align="justify">
Tasa global de participación (TGP), tasa de ocupación (TO), tasa de desempleo (TD), informalidad, índice multidimensional de calidad del trabajo (IMCT), distribución del ingreso laboral (deciles y coeficiente de Gini) y sus variaciones entre periodos. Cada indicador se reporta como total expandido y como proporción, con su medida de precisión.
</p>

## Arquitectura

```
data/raw/<año>/*.zip   zips mensuales del DANE (no se versionan)
        │
        ▼  src/geih/cargar.py        carga incremental, un mes entra completo o no entra
PostgreSQL  raw.*  (texto, todas las columnas de todos los años)
        │             meta.carga · meta.diccionario
        ▼  sql/                      capa tipada y tablas agregadas
PostgreSQL  staging.* → core.* → marts.*
        │
        ▼
dashboard/   (HTML estático, sin servidor)      reports/   (Quarto)
```

<p align="justify">
El modelo es relacional: hogar, persona, fuerza de trabajo, migración, ocupados, no ocupados, otras formas de trabajo y otros ingresos, unidos por las llaves <code>directorio</code>, <code>secuencia_p</code> y <code>orden</code> más el mes. La descripción completa de tablas, llaves y reglas de carga está en <a href="docs/estructura_bd.md">docs/estructura_bd.md</a>.
</p>

## Estructura del repositorio

| Carpeta | Contenido |
|---------|-----------|
| `data/raw/` | Zips mensuales del DANE, una carpeta por año. No se versionan |
| `docs/` | Modelo de datos, plan del estudio, diccionario de variables (`diccionario/`), inventario de archivos (`inventario/`) y boletines del DANE para validar (`boletines_dane/`) |
| `sql/` | Creación de la base, esquema crudo, diccionario y capas posteriores |
| `src/geih/` | Carga, diccionario, inventario y utilidades comunes |
| `notebooks/` | Exploración |
| `dashboard/` | Tablero HTML estático |
| `reports/` | Reportes Quarto con nota metodológica |
| `tests/` | Pruebas de validación |

## Instalación

<p align="justify">
Requiere Python 3.11 o superior y PostgreSQL 16 o superior. Los microdatos se descargan manualmente desde el catálogo de microdatos del DANE, porque el sitio exige verificación humana, y se guardan sin descomprimir en <code>data/raw/&lt;año&gt;/</code>.
</p>

```bash
pip install -r requirements.txt
copy .env.example .env        # editar PGPASSWORD
```

Crear la base `geih` (UTF8) con `sql/00_crear_bd.sql` o desde pgAdmin.

## Uso

```bash
python src/geih/cargar.py                      # carga solo los meses nuevos
python src/geih/cargar.py --solo 2026-09       # un mes
python src/geih/cargar.py --recargar 2026-09   # rehace un mes
python src/geih/cargar.py --validar            # revisa llaves, huérfanos y consistencia
python src/geih/cargar.py --diccionario        # carga el diccionario de variables
```

### Actualización mensual

<p align="justify">
Cuando el DANE publica un mes nuevo, se guarda el zip en la carpeta del año y se ejecuta <code>python src/geih/cargar.py</code>. El cargador registra en <code>meta.carga</code> qué mes y módulo ya procesó, omite los existentes y agrega automáticamente cualquier columna nueva que el DANE incorpore. Si un mes falla, se revierte completo.
</p>

## Fuentes

<p align="justify">
Microdatos de la GEIH publicados por el DANE (2023 a 2026) y sus diccionarios de datos. Las fuentes complementarias previstas son los informes de Migración Colombia, la Encuesta Pulso de la Migración, las proyecciones de población del DANE, el salario mínimo y el IPC; se unen por territorio, mes y sexo, nunca por persona.
</p>

## Limitaciones

<p align="justify">
La GEIH es representativa a nivel nacional, departamental y para las 23 ciudades principales con sus áreas metropolitanas; no permite análisis municipal. No es un panel, por lo que las variaciones se leen entre cortes transversales. No pregunta por el estatus migratorio (PEP o PPT). Algunas variables cambian de codificación entre años y se armonizan antes de comparar. Discapacidad y orientación sexual solo existen en enero y febrero de 2023.
</p>

## Referencia

Orjuela Triviño, C. A. (2024). *Calidad laboral en Colombia, 2016-2019: efectos del choque migratorio venezolano*. Tesis de maestría, FLACSO México.

## Licencia

<p align="justify">
El código se publica bajo licencia MIT. Los microdatos pertenecen al DANE y no se redistribuyen en este repositorio.
</p>
