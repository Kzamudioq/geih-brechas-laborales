-- Diccionario de variables de la GEIH (generado desde los XLSX del DANE con src/geih/diccionario.py)
CREATE SCHEMA IF NOT EXISTS meta;

CREATE TABLE IF NOT EXISTS meta.dicc_variable (
    version     text NOT NULL,   -- 2023, 2023_completa, 2025, 2026
    variable    text NOT NULL,   -- código de columna, en minúscula (p6040, inglabo...)
    descripcion text,
    tipo_dato   text,
    longitud    text,
    tabla_dane  text,
    PRIMARY KEY (version, variable)
);

CREATE TABLE IF NOT EXISTS meta.dicc_valor (
    version  text NOT NULL,
    variable text NOT NULL,
    valor    text NOT NULL,      -- código tal como aparece en los datos
    etiqueta text NOT NULL,      -- significado
    PRIMARY KEY (version, variable, valor)
);

-- Descripción vigente de cada variable: se prefiere la versión más reciente
CREATE OR REPLACE VIEW meta.diccionario AS
SELECT DISTINCT ON (variable) variable, descripcion, tipo_dato, longitud, version
FROM meta.dicc_variable
ORDER BY variable, CASE version WHEN '2026' THEN 1 WHEN '2025' THEN 2 WHEN '2023' THEN 3 ELSE 4 END;

-- Valores vigentes de cada variable
CREATE OR REPLACE VIEW meta.diccionario_valor AS
SELECT DISTINCT ON (variable, valor) variable, valor, etiqueta, version
FROM meta.dicc_valor
ORDER BY variable, valor, CASE version WHEN '2026' THEN 1 WHEN '2025' THEN 2 WHEN '2023' THEN 3 ELSE 4 END;
