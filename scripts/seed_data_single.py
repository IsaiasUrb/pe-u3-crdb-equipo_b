"""
Carga masiva de datos para CockroachDB.

Base de datos: gestion_laboratorios
Objetivo: generar datos coherentes para las pruebas de rendimiento.
"""

from __future__ import annotations

import random
import sys
import uuid
from datetime import date, datetime, time, timedelta
from typing import Any

import psycopg2
from psycopg2.extensions import connection
from psycopg2.extras import execute_values


# ============================================================
# Configuración de conexión
# ============================================================

DB_CONFIG = {
    "host": "localhost",
    "port": 26260,
    "dbname": "gestion_laboratorios",
    "user": "root",
    "sslmode": "disable",
}

SEMILLA_ALEATORIA = 2026
TAMANO_LOTE = 500


# ============================================================
# Cantidades que se insertarán
# ============================================================

TOTAL_LABORATORIOS = 20
TOTAL_DOCENTES = 50
TOTAL_ESTUDIANTES = 1_500
TOTAL_MATERIAS = 60
TOTAL_EQUIPOS = 400
TOTAL_ASIGNACIONES = 600
TOTAL_REGISTROS_ASISTENCIA = 1_200
TOTAL_DETALLES_ASISTENCIA = 9_000
TOTAL_REPORTES_FALLO = 2_500


NOMBRES = [
    "Andy", "José", "Carlos", "María", "Andrea", "Sofía", "Luis",
    "Daniel", "Paola", "Jeremy", "Valentina", "Miguel", "Camila",
    "Jorge", "Fernanda", "David", "Alejandra", "Mateo", "Gabriela",
    "Ricardo",
]

APELLIDOS = [
    "Sánchez", "Lozano", "Urbina", "Morales", "Pilaloa", "Romero",
    "García", "Vera", "Mendoza", "Zambrano", "Cedeño", "Castro",
    "Torres", "Suárez", "Vargas", "Paredes", "Reyes", "Moreira",
    "Salazar", "Álvarez",
]

CARRERAS = [
    "Ingeniería de Software",
    "Tecnologías de la Información",
    "Telemática",
    "Ingeniería Industrial",
    "Administración de Empresas",
]

DEPARTAMENTOS = [
    "Software",
    "Redes",
    "Ciencias Computacionales",
    "Electrónica",
    "Matemáticas",
]

TIPOS_EQUIPO = [
    "Computador",
    "Proyector",
    "Router",
    "Switch",
    "Impresora",
    "Servidor",
]

MARCAS = [
    "Dell",
    "HP",
    "Lenovo",
    "Acer",
    "Asus",
    "Cisco",
    "Epson",
    "Samsung",
]

ESTADOS_EQUIPO = [
    "OPERATIVO",
    "OPERATIVO",
    "OPERATIVO",
    "MANTENIMIENTO",
    "DANADO",
    "BAJA",
]

ESTADOS_REPORTE = [
    "PENDIENTE",
    "EN_PROCESO",
    "RESUELTO",
]

DESCRIPCIONES_FALLO = [
    "El equipo no enciende.",
    "Falla intermitente de conexión a la red.",
    "El sistema operativo presenta errores.",
    "El proyector no muestra imagen.",
    "El equipo genera ruido excesivo.",
    "El periférico no es reconocido.",
    "La conexión eléctrica presenta fallos.",
    "El dispositivo se reinicia inesperadamente.",
    "El equipo presenta sobrecalentamiento.",
    "La velocidad de funcionamiento es demasiado baja.",
]

TEMAS_CLASE = [
    "Introducción a bases de datos",
    "Consultas SQL",
    "Normalización de datos",
    "Bases de datos distribuidas",
    "Transacciones",
    "Índices y optimización",
    "Programación orientada a objetos",
    "Arquitectura de software",
    "Redes de computadores",
    "Seguridad informática",
]


def nuevo_uuid() -> str:
    """Genera un UUID representado como texto."""
    return str(uuid.uuid4())


def fecha_aleatoria(
        inicio: date,
        fin: date,
) -> date:
    """Genera una fecha aleatoria entre dos límites."""
    diferencia = (fin - inicio).days
    return inicio + timedelta(days=random.randint(0, diferencia))


def fecha_hora_aleatoria(
        inicio: datetime,
        fin: datetime,
) -> datetime:
    """Genera una fecha y hora aleatoria entre dos límites."""
    diferencia = int((fin - inicio).total_seconds())
    return inicio + timedelta(seconds=random.randint(0, diferencia))


def insertar_lotes(
        conexion: connection,
        consulta: str,
        registros: list[tuple[Any, ...]],
        descripcion: str,
) -> None:
    """Inserta registros utilizando lotes para mejorar el rendimiento."""
    if not registros:
        return

    with conexion.cursor() as cursor:
        for inicio in range(0, len(registros), TAMANO_LOTE):
            lote = registros[inicio:inicio + TAMANO_LOTE]
            execute_values(cursor, consulta, lote, page_size=TAMANO_LOTE)

    conexion.commit()
    print(f"[OK] {descripcion}: {len(registros):,}")


def limpiar_datos(conexion: connection) -> None:
    """Limpia las tablas respetando el orden de las claves foráneas."""
    tablas = [
        "detalle_asistencia",
        "reporte_fallo",
        "registro_asistencia",
        "asignacion_laboratorio",
        "equipo",
        "estudiante",
        "docente",
        "materia",
        "laboratorio",
        "persona",
    ]

    with conexion.cursor() as cursor:
        for tabla in tablas:
            cursor.execute(f"DELETE FROM {tabla};")

    conexion.commit()
    print("[OK] Datos anteriores eliminados.")


def generar_personas(
        cantidad: int,
        prefijo_correo: str,
) -> tuple[list[tuple[Any, ...]], list[str]]:
    registros: list[tuple[Any, ...]] = []
    ids: list[str] = []

    for numero in range(1, cantidad + 1):
        identificador = nuevo_uuid()
        nombre = random.choice(NOMBRES)
        apellido = random.choice(APELLIDOS)
        correo = (
            f"{prefijo_correo}.{numero}."
            f"{identificador[:8]}@uteq.edu.ec"
        )
        telefono = f"09{random.randint(10_000_000, 99_999_999)}"

        registros.append(
            (
                identificador,
                nombre,
                apellido,
                correo.lower(),
                telefono,
            )
        )
        ids.append(identificador)

    return registros, ids


def main() -> None:
    random.seed(SEMILLA_ALEATORIA)

    try:
        conexion = psycopg2.connect(**DB_CONFIG)
        conexion.autocommit = False
    except psycopg2.Error as error:
        print("[ERROR] No se pudo conectar con CockroachDB.")
        print(error)
        sys.exit(1)

    try:
        print("=" * 60)
        print("CARGA MASIVA DE DATOS")
        print("=" * 60)

        limpiar_datos(conexion)

        # --------------------------------------------------------
        # Laboratorios
        # --------------------------------------------------------

        laboratorios: list[tuple[Any, ...]] = []
        ids_laboratorios: list[str] = []

        for numero in range(1, TOTAL_LABORATORIOS + 1):
            identificador = nuevo_uuid()
            ids_laboratorios.append(identificador)

            laboratorios.append(
                (
                    identificador,
                    f"LAB-{numero:03d}",
                    f"Laboratorio de Cómputo {numero}",
                    random.randint(20, 45),
                    random.choice(["ACTIVO", "ACTIVO", "MANTENIMIENTO"]),
                    f"Bloque {random.choice(['A', 'B', 'C'])}, "
                    f"piso {random.randint(1, 3)}",
                )
            )

        insertar_lotes(
            conexion,
            """
            INSERT INTO laboratorio (
                id_laboratorio,
                codigo,
                nombre,
                capacidad,
                estado,
                ubicacion
            ) VALUES %s
            """,
            laboratorios,
            "Laboratorios insertados",
        )

        # --------------------------------------------------------
        # Personas, docentes y estudiantes
        # --------------------------------------------------------

        personas_docentes, ids_personas_docentes = generar_personas(
            TOTAL_DOCENTES,
            "docente",
        )
        personas_estudiantes, ids_personas_estudiantes = generar_personas(
            TOTAL_ESTUDIANTES,
            "estudiante",
        )

        insertar_lotes(
            conexion,
            """
            INSERT INTO persona (
                id_persona,
                nombres,
                apellidos,
                correo,
                telefono
            ) VALUES %s
            """,
            personas_docentes + personas_estudiantes,
            "Personas insertadas",
            )

        docentes: list[tuple[Any, ...]] = []
        ids_docentes: list[str] = []

        for id_persona in ids_personas_docentes:
            id_docente = nuevo_uuid()
            ids_docentes.append(id_docente)

            docentes.append(
                (
                    id_docente,
                    id_persona,
                    random.choice(DEPARTAMENTOS),
                    random.choice(
                        [
                            "Ingeniero",
                            "Magíster",
                            "Doctor",
                        ]
                    ),
                )
            )

        insertar_lotes(
            conexion,
            """
            INSERT INTO docente (
                id_docente,
                id_persona,
                departamento,
                titulo_academico
            ) VALUES %s
            """,
            docentes,
            "Docentes insertados",
        )

        estudiantes: list[tuple[Any, ...]] = []
        ids_estudiantes: list[str] = []

        for numero, id_persona in enumerate(
                ids_personas_estudiantes,
                start=1,
        ):
            id_estudiante = nuevo_uuid()
            ids_estudiantes.append(id_estudiante)

            estudiantes.append(
                (
                    id_estudiante,
                    id_persona,
                    f"2026-{numero:06d}",
                    f"{random.randint(1, 10)} semestre",
                    random.choice(CARRERAS),
                )
            )

        insertar_lotes(
            conexion,
            """
            INSERT INTO estudiante (
                id_estudiante,
                id_persona,
                matricula,
                nivel,
                carrera
            ) VALUES %s
            """,
            estudiantes,
            "Estudiantes insertados",
        )

        # --------------------------------------------------------
        # Materias
        # --------------------------------------------------------

        materias: list[tuple[Any, ...]] = []
        ids_materias: list[str] = []

        for numero in range(1, TOTAL_MATERIAS + 1):
            identificador = nuevo_uuid()
            ids_materias.append(identificador)

            materias.append(
                (
                    identificador,
                    f"MAT-{numero:03d}",
                    f"Materia tecnológica {numero}",
                    random.choice(CARRERAS),
                    random.randint(1, 10),
                )
            )

        insertar_lotes(
            conexion,
            """
            INSERT INTO materia (
                id_materia,
                codigo,
                nombre,
                carrera,
                semestre
            ) VALUES %s
            """,
            materias,
            "Materias insertadas",
        )

        # --------------------------------------------------------
        # Equipos
        # --------------------------------------------------------

        equipos: list[tuple[Any, ...]] = []
        ids_equipos: list[str] = []

        for numero in range(1, TOTAL_EQUIPOS + 1):
            identificador = nuevo_uuid()
            ids_equipos.append(identificador)

            equipos.append(
                (
                    identificador,
                    random.choice(ids_laboratorios),
                    f"EQ-{numero:05d}",
                    random.choice(TIPOS_EQUIPO),
                    random.choice(MARCAS),
                    f"Modelo-{random.randint(100, 999)}",
                    random.choice(ESTADOS_EQUIPO),
                )
            )

        insertar_lotes(
            conexion,
            """
            INSERT INTO equipo (
                id_equipo,
                id_laboratorio,
                codigo,
                tipo,
                marca,
                modelo,
                estado
            ) VALUES %s
            """,
            equipos,
            "Equipos insertados",
        )

        # --------------------------------------------------------
        # Asignaciones
        # --------------------------------------------------------

        asignaciones: list[tuple[Any, ...]] = []
        ids_asignaciones: list[str] = []

        horarios = [
            (time(7, 30), time(9, 30), "MATUTINA"),
            (time(9, 30), time(11, 30), "MATUTINA"),
            (time(13, 0), time(15, 0), "VESPERTINA"),
            (time(15, 0), time(17, 0), "VESPERTINA"),
            (time(18, 0), time(20, 0), "NOCTURNA"),
        ]

        for _ in range(TOTAL_ASIGNACIONES):
            identificador = nuevo_uuid()
            ids_asignaciones.append(identificador)
            hora_inicio, hora_fin, jornada = random.choice(horarios)

            asignaciones.append(
                (
                    identificador,
                    random.choice(ids_laboratorios),
                    random.choice(ids_docentes),
                    random.choice(ids_materias),
                    fecha_aleatoria(
                        date(2025, 1, 1),
                        date(2026, 7, 15),
                    ),
                    hora_inicio,
                    hora_fin,
                    jornada,
                )
            )

        insertar_lotes(
            conexion,
            """
            INSERT INTO asignacion_laboratorio (
                id_asignacion,
                id_laboratorio,
                id_docente,
                id_materia,
                fecha_asignacion,
                hora_inicio,
                hora_fin,
                jornada
            ) VALUES %s
            """,
            asignaciones,
            "Asignaciones insertadas",
        )

        # --------------------------------------------------------
        # Registros de asistencia
        # --------------------------------------------------------

        registros_asistencia: list[tuple[Any, ...]] = []
        ids_registros: list[str] = []

        for _ in range(TOTAL_REGISTROS_ASISTENCIA):
            identificador = nuevo_uuid()
            ids_registros.append(identificador)

            registros_asistencia.append(
                (
                    identificador,
                    random.choice(ids_asignaciones),
                    fecha_aleatoria(
                        date(2025, 1, 1),
                        date(2026, 7, 15),
                    ),
                    random.choice(TEMAS_CLASE),
                )
            )

        insertar_lotes(
            conexion,
            """
            INSERT INTO registro_asistencia (
                id_registro,
                id_asignacion,
                fecha_clase,
                tema_clase
            ) VALUES %s
            """,
            registros_asistencia,
            "Registros de asistencia insertados",
        )

        # --------------------------------------------------------
        # Detalles de asistencia
        # --------------------------------------------------------

        detalles_asistencia: list[tuple[Any, ...]] = []
        parejas_utilizadas: set[tuple[str, str]] = set()

        while len(detalles_asistencia) < TOTAL_DETALLES_ASISTENCIA:
            id_registro = random.choice(ids_registros)
            id_estudiante = random.choice(ids_estudiantes)
            pareja = (id_registro, id_estudiante)

            if pareja in parejas_utilizadas:
                continue

            parejas_utilizadas.add(pareja)
            presente = random.random() < 0.85

            detalles_asistencia.append(
                (
                    nuevo_uuid(),
                    id_registro,
                    id_estudiante,
                    presente,
                    None if presente else "Inasistencia registrada",
                )
            )

        insertar_lotes(
            conexion,
            """
            INSERT INTO detalle_asistencia (
                id_detalle,
                id_registro,
                id_estudiante,
                presente,
                observacion
            ) VALUES %s
            """,
            detalles_asistencia,
            "Detalles de asistencia insertados",
        )

        # --------------------------------------------------------
        # Reportes de fallos
        # --------------------------------------------------------

        reportes: list[tuple[Any, ...]] = []

        inicio_reportes = datetime(2025, 1, 1, 7, 0)
        fin_reportes = datetime(2026, 7, 15, 22, 0)

        for _ in range(TOTAL_REPORTES_FALLO):
            reportes.append(
                (
                    nuevo_uuid(),
                    random.choice(ids_equipos),
                    random.choice(ids_docentes),
                    random.choice(DESCRIPCIONES_FALLO),
                    random.choice(ESTADOS_REPORTE),
                    fecha_hora_aleatoria(
                        inicio_reportes,
                        fin_reportes,
                    ),
                )
            )

        insertar_lotes(
            conexion,
            """
            INSERT INTO reporte_fallo (
                id_reporte,
                id_equipo,
                id_docente,
                descripcion,
                estado,
                fecha_reporte
            ) VALUES %s
            """,
            reportes,
            "Reportes de fallos insertados",
        )

        total_generado = (
                TOTAL_LABORATORIOS
                + TOTAL_DOCENTES
                + TOTAL_ESTUDIANTES
                + TOTAL_MATERIAS
                + TOTAL_EQUIPOS
                + TOTAL_ASIGNACIONES
                + TOTAL_REGISTROS_ASISTENCIA
                + TOTAL_DETALLES_ASISTENCIA
                + TOTAL_REPORTES_FALLO
        )

        print("=" * 60)
        print(f"CARGA COMPLETADA: {total_generado:,} REGISTROS")
        print("=" * 60)

    except psycopg2.Error as error:
        conexion.rollback()
        print("[ERROR] La carga fue cancelada.")
        print(error)
        sys.exit(1)

    finally:
        conexion.close()


if __name__ == "__main__":
    main()