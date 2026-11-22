# Inventario de archivos

<p align="justify">
Resultado del recorrido inicial de los zips del DANE. <code>inventario_archivos.csv</code> lista filas, columnas y codificación por mes y módulo. <code>columnas_por_modulo.csv</code> indica en qué meses aparece cada columna y de ella se genera el esquema <code>sql/01_esquema_raw.sql</code>. Se regeneran con <code>python src/geih/inventario.py</code>.
</p>
