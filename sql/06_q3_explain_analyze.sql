-- =========================================================
-- CONSULTA Q3 DEL BENCHMARK
-- Reportes resueltos relacionados con equipos y laboratorios
-- Objetivo: analizar el rendimiento de los JOIN entre tres tablas
-- =========================================================
EXPLAIN ANALYZE
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