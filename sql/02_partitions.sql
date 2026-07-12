-- ============================================================
-- Estrategia de fragmentación para CockroachDB
-- Tabla: reporte_fallo
--
-- Fragmentación horizontal por estado:
--   PENDIENTE  -> nodo1
--   EN_PROCESO -> nodo2
--   RESUELTO   -> nodo3
--
-- Cada partición conserva 3 réplicas, una en cada nodo.
-- La preferencia de leaseholder permite que las operaciones
-- se atiendan principalmente desde el nodo asignado.
-- ============================================================

USE gestion_laboratorios;

-- CockroachDB exige que la columna utilizada para particionar
-- sea el prefijo de la clave primaria.
--
-- Primero se conserva la unicidad individual de id_reporte y
-- luego se transforma la clave primaria en una clave compuesta.

ALTER TABLE reporte_fallo
    ADD CONSTRAINT uq_reporte_fallo_id
        UNIQUE (id_reporte);

ALTER TABLE reporte_fallo
ALTER PRIMARY KEY USING COLUMNS (estado, id_reporte);

-- ============================================================
-- Fragmentación horizontal por lista
-- ============================================================

ALTER TABLE reporte_fallo
    PARTITION BY LIST (estado) (
    PARTITION reporte_pendiente
    VALUES IN ('PENDIENTE'),

    PARTITION reporte_en_proceso
    VALUES IN ('EN_PROCESO'),

    PARTITION reporte_resuelto
    VALUES IN ('RESUELTO')
    );

-- ============================================================
-- Configuración de zona de las particiones de la tabla
--
-- Cada partición conserva una réplica en cada nodo, pero utiliza
-- un leaseholder preferido diferente.
-- ============================================================

ALTER PARTITION reporte_pendiente
OF TABLE reporte_fallo
CONFIGURE ZONE USING
    num_replicas = 3,
    constraints = '{"+zone=nodo1": 1, "+zone=nodo2": 1, "+zone=nodo3": 1}',
    lease_preferences = '[[+zone=nodo1]]';

ALTER PARTITION reporte_en_proceso
OF TABLE reporte_fallo
CONFIGURE ZONE USING
    num_replicas = 3,
    constraints = '{"+zone=nodo1": 1, "+zone=nodo2": 1, "+zone=nodo3": 1}',
    lease_preferences = '[[+zone=nodo2]]';

ALTER PARTITION reporte_resuelto
OF TABLE reporte_fallo
CONFIGURE ZONE USING
    num_replicas = 3,
    constraints = '{"+zone=nodo1": 1, "+zone=nodo2": 1, "+zone=nodo3": 1}',
    lease_preferences = '[[+zone=nodo3]]';

-- ============================================================
-- Índice complementario particionado
--
-- Este índice optimiza las consultas que filtran por estado y
-- ordenan o restringen por fecha de reporte.
-- ============================================================

CREATE INDEX idx_reporte_estado_fecha
    ON reporte_fallo (estado, fecha_reporte DESC)
    PARTITION BY LIST (estado) (
        PARTITION idx_reporte_pendiente
            VALUES IN ('PENDIENTE'),

        PARTITION idx_reporte_en_proceso
            VALUES IN ('EN_PROCESO'),

        PARTITION idx_reporte_resuelto
            VALUES IN ('RESUELTO')
    );

-- ============================================================
-- Configuración de zona de las particiones del índice
-- ============================================================

ALTER PARTITION idx_reporte_pendiente
OF INDEX reporte_fallo@idx_reporte_estado_fecha
CONFIGURE ZONE USING
    num_replicas = 3,
    constraints = '{"+zone=nodo1": 1, "+zone=nodo2": 1, "+zone=nodo3": 1}',
    lease_preferences = '[[+zone=nodo1]]';

ALTER PARTITION idx_reporte_en_proceso
OF INDEX reporte_fallo@idx_reporte_estado_fecha
CONFIGURE ZONE USING
    num_replicas = 3,
    constraints = '{"+zone=nodo1": 1, "+zone=nodo2": 1, "+zone=nodo3": 1}',
    lease_preferences = '[[+zone=nodo2]]';

ALTER PARTITION idx_reporte_resuelto
OF INDEX reporte_fallo@idx_reporte_estado_fecha
CONFIGURE ZONE USING
    num_replicas = 3,
    constraints = '{"+zone=nodo1": 1, "+zone=nodo2": 1, "+zone=nodo3": 1}',
    lease_preferences = '[[+zone=nodo3]]';

-- ============================================================
-- Consultas de verificación de la tabla
-- ============================================================

SHOW PARTITIONS FROM TABLE reporte_fallo;

SHOW ZONE CONFIGURATION
FROM PARTITION reporte_pendiente
OF TABLE reporte_fallo;

SHOW ZONE CONFIGURATION
FROM PARTITION reporte_en_proceso
OF TABLE reporte_fallo;

SHOW ZONE CONFIGURATION
FROM PARTITION reporte_resuelto
OF TABLE reporte_fallo;

-- ============================================================
-- Consultas de verificación del índice particionado
-- ============================================================

SHOW PARTITIONS
FROM INDEX reporte_fallo@idx_reporte_estado_fecha;

SHOW ZONE CONFIGURATION
FROM PARTITION idx_reporte_pendiente
OF INDEX reporte_fallo@idx_reporte_estado_fecha;

SHOW ZONE CONFIGURATION
FROM PARTITION idx_reporte_en_proceso
OF INDEX reporte_fallo@idx_reporte_estado_fecha;

SHOW ZONE CONFIGURATION
FROM PARTITION idx_reporte_resuelto
OF INDEX reporte_fallo@idx_reporte_estado_fecha;