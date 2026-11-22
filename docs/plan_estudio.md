# Plan del estudio: priorización de preguntas, variables y fuentes

Documento de trabajo. Fija qué se estudia, con qué variables y con qué fuentes, antes de construir la capa tipada. Referencia metodológica: Orjuela (2024), *Calidad laboral en Colombia, 2016-2019: efectos del choque migratorio venezolano* (FLACSO México).

## 1. Pregunta central

¿Cómo han evolucionado entre 2023 y 2026 las brechas laborales (participación, ocupación, desempleo, informalidad, calidad del empleo e ingresos) según sexo, condición migratoria, edad y territorio, y cuánto de esas brechas se explica por la composición de los grupos (educación, edad, sector) frente a una diferencia que persiste?

Alcance: **descriptivo y de brechas**. La tesis de referencia estima efectos causales para 2016-2019 con un instrumento basado en el censo de 2005; ese diseño no se replica aquí. Con 2023-2026 el choque migratorio ya ocurrió y no hay una fuente exógena de variación equivalente.

## 2. Tipos de estudio (en orden de prioridad)

| # | Tipo | Qué responde | Dato requerido | Estado |
|---|------|--------------|----------------|--------|
| 1 | Series de indicadores con factor de expansión | TGP, TO, TD, informalidad por grupo y mes | GEIH | Listo para construir |
| 2 | Brechas y su variación | Diferencia en puntos porcentuales entre grupos y su cambio en el tiempo | GEIH | Listo para construir |
| 3 | Calidad del empleo (IMCT) | Calidad multidimensional, separando asalariados e independientes | GEIH (ocupados) | Listo para construir |
| 4 | Distribución del ingreso | Deciles, Gini, ingreso relativo al salario mínimo | GEIH + salario mínimo + IPC | Falta cargar salario mínimo e IPC |
| 5 | Descomposición de brechas | Cuánto de la brecha es composición y cuánto es diferencia no explicada (Oaxaca-Blinder, Kitagawa) | GEIH | Segunda fase |
| 6 | Presión migratoria territorial | Relación entre la proporción de migrantes en la ciudad y los indicadores de los nativos | GEIH + Migración Colombia + proyecciones | Segunda fase, correlacional |

Se descarta como alcance base cualquier estimación causal y cualquier análisis a nivel de municipio (ver sección 5).

## 3. Variables priorizadas

La GEIH trae cientos de columnas. Estas son las que sostienen el estudio. Todas existen en los 44 meses cargados (2023-01 a 2026-08), salvo donde se indica.

### Prioridad 1: indispensables (sin ellas no hay indicadores)

| Variable | Qué mide | Tabla |
|----------|----------|-------|
| `directorio`, `secuencia_p`, `orden`, `hogar` | Llaves de unión | todas |
| `periodo` | Mes de la encuesta (columna propia del repo) | todas |
| `fex_c18` | Factor de expansión | persona |
| `pet`, `ft`, `fft`, `oci`, `dsi` | Indicadores de población en edad de trabajar, fuerza de trabajo, ocupados, desocupados e inactivos | fuerza de trabajo y ocupados |
| `p3271` | Sexo al nacer | persona |
| `p6040` | Edad | persona |
| `dpto`, `area`, `clase` | Departamento, ciudad o área metropolitana, cabecera o resto | persona |
| `p3374`, `p3373`, `p3382`, `p3384` | Nacionalidad, lugar de nacimiento, residencia hace 5 años y hace 12 meses | migración |
| `inglabo` | Ingreso laboral | ocupados |

### Prioridad 2: calidad del empleo e informalidad

Dimensiones del IMCT de la tesis y variable de la GEIH que las alimenta:

| Dimensión | Variable(s) |
|-----------|-------------|
| Posición ocupacional (asalariado o independiente) | `p6430` |
| Ingresos frente al salario mínimo | `inglabo`, `p6500` |
| Jornada y subocupación | `p6800`, `p6850`, `p7090`, `p7110` |
| Salud | `p6090`, `p6100` |
| Pensiones | `p6920`, `p6930` |
| Riesgos laborales | `p6990` |
| Estabilidad (contrato) | `p6440`, `p6450`, `p6460` |
| Tamaño de la empresa (insumo de informalidad) | `p3069` |
| Sector, oficio | `rama2d_r4`, `oficio_c8` |

Cesantías y vacaciones (dimensiones solo para asalariados en la tesis) requieren confirmar la variable exacta en el diccionario; aún no está identificada.

### Prioridad 3: contexto y desagregación

| Variable | Uso |
|----------|-----|
| `p3042`, `p3043` | Nivel educativo, para controlar composición |
| `p6070` | Estado civil |
| `p6080`, `p3039` | Pertenencia étnica |
| `p6310` | Motivo de no buscar trabajo (desalentados) |
| `p6240`, `p6250`, `p6260` | Actividad principal de los inactivos |
| `p7180` | Afiliación sindical |
| `p6880` | Lugar de trabajo (local, domicilio, vía pública) |
| `p6426` | Antigüedad en el empleo |

### Lo que no existe en el periodo completo

Discapacidad y orientación sexual solo aparecen en enero y febrero de 2023. No se pueden usar como eje de brechas en una serie 2023-2026. Las variables `p3147s*` solo existen en 2023 y 2024.

### Decisiones abiertas (bloquean la capa tipada)

1. **Informalidad:** definición oficial del DANE, IMCT, o ambas. Recomendado: ambas, porque la tesis argumenta que se complementan.
2. **Condición migratoria:** nacionalidad (`p3374`) como criterio principal; residencia hace 5 años y 12 meses (`p3382`, `p3384`, Venezuela = 862) para marcar llegada reciente.
3. 44 de 391 variables con categorías cambian de codificación entre 2023, 2025 y 2026. Se comparan código por código antes de usarlas.

## 4. Fuentes externas

Todas se unen **por territorio, mes y sexo**, nunca por persona (no hay llave común).

| Prioridad | Fuente | Aporta | Formato | Uso |
|-----------|--------|--------|---------|-----|
| Alta | Migración Colombia, informes de migrantes venezolanos | Estimación mensual de venezolanos por departamento y municipio; PPT autorizados | PDF y tableros; no son microdatos | Presión migratoria y estatus de regularización |
| Alta | DANE, Encuesta Pulso de la Migración (rondas 1 a 8) | Situación migratoria, salud y mercado laboral de migrantes | Microdatos en el catálogo de microdatos | Validar y complementar el estatus que la GEIH no pregunta |
| Alta | DANE, proyecciones de población (actualización 2025) | Población por departamento, sexo y edad | Excel | Denominador de tasas y contraste de expandidos |
| Media | Salario mínimo e IPC | Deflactar ingresos y calcular ingresos relativos | Series cortas | Cargar a mano con fuente y fecha |
| Media | DANE, cuentas nacionales departamentales | Valor agregado como control de tamaño económico | Excel | Control en la fase 6 |
| Media | DANE, Censo 2018, caracterización de inmigrantes | Línea base territorial previa al periodo | PDF y anexos | Contexto en el reporte |

Regla para fuentes que son PDF o tableros: se transcriben las cifras a un CSV en `data/external/` con la fecha de publicación, el enlace y el nombre del informe de origen.

## 5. Límites que el estudio debe declarar

- **Representatividad:** la GEIH es representativa a nivel nacional, por departamento y para las 23 ciudades principales con sus áreas metropolitanas. No hay municipio en los archivos públicos. Para el resto del país solo se publican cifras nacionales y departamentales, con intervalo de confianza visible.
- **No es un panel:** la GEIH no sigue a las mismas personas. Las variaciones son entre cortes transversales (pseudo-panel agregado por grupo y territorio).
- **Muestra pequeña:** en ciudades con pocos migrantes las estimaciones tienen error alto. Cada cifra se acompaña de su coeficiente de variación y se suprime por debajo de un mínimo de observaciones.
- **Sin estatus migratorio:** la GEIH no pregunta por PEP, PPT ni situación irregular. Por eso el cruce con Migración Colombia y la Encuesta Pulso de la Migración.
- **Cambio de marco:** variables con categorías distintas entre años deben armonizarse antes de comparar.

## 6. Orden de construcción

1. Capa tipada (staging): conversión de texto a número y nombres claros para las variables de prioridad 1 y 2.
2. Validación de TGP, TO y TD contra los boletines del DANE (carpeta `docs/boletines_dane/`).
3. Indicadores agregados por mes, sexo, condición migratoria, edad y territorio.
4. IMCT y definición de informalidad elegida.
5. Ingresos: deciles y Gini, con salario mínimo e IPC.
6. Fuentes externas (Migración Colombia, proyecciones) y fase 6.
7. Tablero estático y reportes Quarto con nota metodológica.
