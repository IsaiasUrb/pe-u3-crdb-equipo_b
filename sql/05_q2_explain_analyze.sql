-- =========================================================
-- CONSULTA Q2 DEL BENCHMARK
-- Reportes en proceso registrados durante los últimos 180 días
-- Objetivo: evaluar el filtrado combinado por estado y fecha
-- =========================================================
EXPLAIN ANALYZE
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