CREATE DATABASE IF NOT EXISTS gestion_laboratorios;

USE gestion_laboratorios;

CREATE TABLE persona (
                         id_persona UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                         nombres STRING NOT NULL,
                         apellidos STRING NOT NULL,
                         correo STRING NOT NULL UNIQUE,
                         telefono STRING,
                         fecha_registro TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE laboratorio (
                             id_laboratorio UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                             codigo STRING NOT NULL UNIQUE,
                             nombre STRING NOT NULL,
                             capacidad INT NOT NULL CHECK (capacidad > 0),
                             estado STRING NOT NULL DEFAULT 'ACTIVO'
                                 CHECK (estado IN ('ACTIVO', 'INACTIVO', 'MANTENIMIENTO')),
                             ubicacion STRING
);

CREATE TABLE docente (
                         id_docente UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                         id_persona UUID NOT NULL UNIQUE,
                         departamento STRING,
                         titulo_academico STRING,
                         CONSTRAINT fk_docente_persona
                             FOREIGN KEY (id_persona)
                                 REFERENCES persona(id_persona)
);

CREATE TABLE estudiante (
                            id_estudiante UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                            id_persona UUID NOT NULL UNIQUE,
                            matricula STRING NOT NULL UNIQUE,
                            nivel STRING,
                            carrera STRING,
                            CONSTRAINT fk_estudiante_persona
                                FOREIGN KEY (id_persona)
                                    REFERENCES persona(id_persona)
);

CREATE TABLE equipo (
                        id_equipo UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        id_laboratorio UUID NOT NULL,
                        codigo STRING NOT NULL UNIQUE,
                        tipo STRING NOT NULL,
                        marca STRING,
                        modelo STRING,
                        estado STRING NOT NULL DEFAULT 'OPERATIVO'
                            CHECK (estado IN ('OPERATIVO', 'MANTENIMIENTO', 'DANADO', 'BAJA')),
                        fecha_registro TIMESTAMPTZ NOT NULL DEFAULT now(),
                        CONSTRAINT fk_equipo_laboratorio
                            FOREIGN KEY (id_laboratorio)
                                REFERENCES laboratorio(id_laboratorio)
);

CREATE TABLE materia (
                         id_materia UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                         codigo STRING NOT NULL UNIQUE,
                         nombre STRING NOT NULL,
                         carrera STRING,
                         semestre INT CHECK (semestre BETWEEN 1 AND 10)
);

CREATE TABLE asignacion_laboratorio (
                                        id_asignacion UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                                        id_laboratorio UUID NOT NULL,
                                        id_docente UUID NOT NULL,
                                        id_materia UUID NOT NULL,
                                        fecha_asignacion DATE NOT NULL,
                                        hora_inicio TIME NOT NULL,
                                        hora_fin TIME NOT NULL,
                                        jornada STRING NOT NULL
                                            CHECK (jornada IN ('MATUTINA', 'VESPERTINA', 'NOCTURNA')),
                                        CONSTRAINT ck_rango_horario
                                            CHECK (hora_fin > hora_inicio),
                                        CONSTRAINT fk_asignacion_laboratorio
                                            FOREIGN KEY (id_laboratorio)
                                                REFERENCES laboratorio(id_laboratorio),
                                        CONSTRAINT fk_asignacion_docente
                                            FOREIGN KEY (id_docente)
                                                REFERENCES docente(id_docente),
                                        CONSTRAINT fk_asignacion_materia
                                            FOREIGN KEY (id_materia)
                                                REFERENCES materia(id_materia)
);

CREATE TABLE registro_asistencia (
                                     id_registro UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                                     id_asignacion UUID NOT NULL,
                                     fecha_clase DATE NOT NULL,
                                     tema_clase STRING,
                                     fecha_registro TIMESTAMPTZ NOT NULL DEFAULT now(),
                                     CONSTRAINT fk_registro_asignacion
                                         FOREIGN KEY (id_asignacion)
                                             REFERENCES asignacion_laboratorio(id_asignacion)
);

CREATE TABLE detalle_asistencia (
                                    id_detalle UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                                    id_registro UUID NOT NULL,
                                    id_estudiante UUID NOT NULL,
                                    presente BOOL NOT NULL DEFAULT false,
                                    observacion STRING,
                                    CONSTRAINT fk_detalle_registro
                                        FOREIGN KEY (id_registro)
                                            REFERENCES registro_asistencia(id_registro),
                                    CONSTRAINT fk_detalle_estudiante
                                        FOREIGN KEY (id_estudiante)
                                            REFERENCES estudiante(id_estudiante),
                                    CONSTRAINT uq_asistencia_estudiante
                                        UNIQUE (id_registro, id_estudiante)
);

CREATE TABLE reporte_fallo (
                               id_reporte UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                               id_equipo UUID NOT NULL,
                               id_docente UUID NOT NULL,
                               descripcion STRING NOT NULL,
                               estado STRING NOT NULL DEFAULT 'PENDIENTE'
                                   CHECK (estado IN ('PENDIENTE', 'EN_PROCESO', 'RESUELTO')),
                               fecha_reporte TIMESTAMPTZ NOT NULL DEFAULT now(),
                               CONSTRAINT fk_reporte_equipo
                                   FOREIGN KEY (id_equipo)
                                       REFERENCES equipo(id_equipo),
                               CONSTRAINT fk_reporte_docente
                                   FOREIGN KEY (id_docente)
                                       REFERENCES docente(id_docente)
);

CREATE INDEX idx_equipo_laboratorio
    ON equipo(id_laboratorio);

CREATE INDEX idx_asignacion_fecha
    ON asignacion_laboratorio(fecha_asignacion);

CREATE INDEX idx_asignacion_laboratorio
    ON asignacion_laboratorio(id_laboratorio);

CREATE INDEX idx_registro_fecha
    ON registro_asistencia(fecha_clase);

CREATE INDEX idx_detalle_estudiante
    ON detalle_asistencia(id_estudiante);

CREATE INDEX idx_reporte_estado
    ON reporte_fallo(estado);

CREATE INDEX idx_reporte_fecha
    ON reporte_fallo(fecha_reporte);