# Diccionario de variables

<p align="justify">
Esta carpeta contiene el diccionario de variables de la GEIH. Los archivos originales del DANE están en <code>fuentes_dane/</code> y no se modifican. Los dos CSV de esta carpeta se generan a partir de ellos con <code>python src/geih/diccionario.py</code> y se cargan a la base con <code>python src/geih/cargar.py --diccionario</code>.
</p>

| Archivo | Qué es | Origen |
|---------|--------|--------|
| `fuentes_dane/diccionario_2023_anonimizadas.xlsx` | Diccionario de las bases anonimizadas de 2023 | DANE |
| `fuentes_dane/diccionario_2023_completa.xlsx` | Diccionario completo de 2023; solo completa vacíos del anterior | DANE |
| `fuentes_dane/diccionario_2025.xlsx` | Diccionario de 2025 | DANE |
| `fuentes_dane/diccionario_2026.xlsx` | Diccionario de 2026 | DANE |
| `dicc_variables.csv` | Una fila por versión y variable: descripción, tipo y longitud | Generado |
| `dicc_valores.csv` | Una fila por versión, variable y código: significado del valor | Generado |

<p align="justify">
El DANE no publicó diccionario para 2024; ese año se cubre con los de 2023 y 2025. En la base, las vistas <code>meta.diccionario</code> y <code>meta.diccionario_valor</code> eligen la versión más reciente disponible de cada variable (2026, luego 2025, luego 2023).
</p>
