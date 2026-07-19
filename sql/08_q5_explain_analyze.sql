-- =========================================================
-- CONSULTA Q5 DEL BENCHMARK
-- Equipos con mayor cantidad de fallos registrados
-- Objetivo: analizar JOIN, agregaciones, HAVING y ORDER BY
-- =========================================================
EXPLAIN ANALYZE
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