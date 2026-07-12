-- ============================================================
-- Consultas de rendimiento para CockroachDB
-- Base de datos: gestion_laboratorios
--
-- Estas consultas permiten evaluar:
--   1. Lectura de una partición específica.
--   2. Filtrado por estado y rango de fechas.
--   3. Relaciones entre reportes, equipos y laboratorios.
--   4. Agregaciones distribuidas.
--   5. Análisis de equipos con mayor cantidad de fallos.
-- ============================================================

USE gestion_laboratorios;

-- ============================================================
-- CONSULTA 1
-- Reportes pendientes ordenados desde el más reciente.
--
-- Objetivo:
-- Comprobar la poda de particiones al consultar únicamente
-- la partición asociada al estado PENDIENTE.
-- ============================================================

SELECT
    id_reporte,
    id_equipo,
    id_docente,
    descripcion,
    estado,
    fecha_reporte
FROM reporte_fallo
WHERE estado = 'PENDIENTE'
ORDER BY fecha_reporte DESC
    LIMIT 100;


-- ============================================================
-- CONSULTA 2
-- Reportes en proceso registrados durante los últimos 180 días.
--
-- Objetivo:
-- Evaluar el índice compuesto por estado y fecha_reporte.
-- ============================================================

SELECT
    id_reporte,
    id_equipo,
    descripcion,
    estado,
    fecha_reporte
FROM reporte_fallo
WHERE estado = 'EN_PROCESO'
  AND fecha_reporte >= now() - INTERVAL '180 days'
ORDER BY fecha_reporte DESC
    LIMIT 200;


-- ============================================================
-- CONSULTA 3
-- Detalle de reportes junto con el equipo y laboratorio.
--
-- Objetivo:
-- Evaluar operaciones JOIN entre tres tablas relacionadas.
-- ============================================================

SELECT
    rf.id_reporte,
    rf.estado,
    rf.descripcion,
    rf.fecha_reporte,
    e.codigo AS codigo_equipo,
    e.tipo AS tipo_equipo,
    e.marca,
    e.modelo,
    l.codigo AS codigo_laboratorio,
    l.nombre AS nombre_laboratorio
FROM reporte_fallo AS rf
         INNER JOIN equipo AS e
                    ON e.id_equipo = rf.id_equipo
         INNER JOIN laboratorio AS l
                    ON l.id_laboratorio = e.id_laboratorio
WHERE rf.estado = 'RESUELTO'
ORDER BY rf.fecha_reporte DESC
    LIMIT 250;


-- ============================================================
-- CONSULTA 4
-- Cantidad de reportes agrupados por laboratorio y estado.
--
-- Objetivo:
-- Evaluar JOIN, GROUP BY, COUNT y ordenamiento de resultados.
-- ============================================================

SELECT
    l.id_laboratorio,
    l.codigo AS codigo_laboratorio,
    l.nombre AS nombre_laboratorio,
    rf.estado,
    COUNT(*) AS total_reportes
FROM reporte_fallo AS rf
         INNER JOIN equipo AS e
                    ON e.id_equipo = rf.id_equipo
         INNER JOIN laboratorio AS l
                    ON l.id_laboratorio = e.id_laboratorio
GROUP BY
    l.id_laboratorio,
    l.codigo,
    l.nombre,
    rf.estado
ORDER BY
    total_reportes DESC,
    l.codigo ASC,
    rf.estado ASC;


-- ============================================================
-- CONSULTA 5
-- Equipos con mayor cantidad de fallos registrados.
--
-- Objetivo:
-- Evaluar una consulta analítica con múltiples agregaciones,
-- JOIN, filtro mediante HAVING y ordenamiento.
-- ============================================================

SELECT
    e.id_equipo,
    e.codigo AS codigo_equipo,
    e.tipo AS tipo_equipo,
    e.marca,
    e.modelo,
    l.codigo AS codigo_laboratorio,
    l.nombre AS nombre_laboratorio,
    COUNT(rf.id_reporte) AS total_fallos,
    COUNT(*) FILTER (
        WHERE rf.estado = 'PENDIENTE'
    ) AS fallos_pendientes,
    COUNT(*) FILTER (
        WHERE rf.estado = 'EN_PROCESO'
    ) AS fallos_en_proceso,
    COUNT(*) FILTER (
        WHERE rf.estado = 'RESUELTO'
    ) AS fallos_resueltos,
    MAX(rf.fecha_reporte) AS ultimo_reporte
FROM equipo AS e
         INNER JOIN laboratorio AS l
                    ON l.id_laboratorio = e.id_laboratorio
         INNER JOIN reporte_fallo AS rf
                    ON rf.id_equipo = e.id_equipo
GROUP BY
    e.id_equipo,
    e.codigo,
    e.tipo,
    e.marca,
    e.modelo,
    l.codigo,
    l.nombre
HAVING COUNT(rf.id_reporte) >= 1
ORDER BY
    total_fallos DESC,
    ultimo_reporte DESC
    LIMIT 100;