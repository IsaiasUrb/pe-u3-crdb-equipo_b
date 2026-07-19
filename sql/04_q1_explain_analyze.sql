-- =========================================================
-- CONSULTA Q1 DEL BENCHMARK
-- Reportes pendientes ordenados por fecha de reporte
-- Objetivo: analizar el uso del índice por estado y fecha
-- =========================================================
EXPLAIN ANALYZE
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