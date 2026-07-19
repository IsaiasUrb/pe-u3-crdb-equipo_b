-- =========================================================
-- CONSULTA Q4 DEL BENCHMARK
-- Cantidad de reportes agrupados por laboratorio y estado
-- Objetivo: evaluar operaciones de JOIN, GROUP BY y COUNT
-- =========================================================
EXPLAIN ANALYZE
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