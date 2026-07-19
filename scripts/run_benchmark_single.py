"""
Benchmark de consultas para el clúster CockroachDB.

Ejecuta cinco consultas sobre los tres nodos del clúster,
mide los tiempos y genera un archivo CSV con los resultados.
"""

from __future__ import annotations

import csv
import statistics
import sys
import time
from pathlib import Path
from typing import Any

import psycopg2
from psycopg2.extensions import connection


DB_NAME = "gestion_laboratorios"
DB_USER = "root"
DB_HOST = "localhost"
SSL_MODE = "disable"

REPETICIONES = 10

NODOS = {
    "single": 26260,
}

RUTA_SALIDA = Path("evidencia") / "resultados_single.csv"


CONSULTAS: dict[str, str] = {
    "Q1_reportes_pendientes": """
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
                              """,

    "Q2_reportes_en_proceso": """
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
                              """,

    "Q3_reportes_resueltos_join": """
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
                                  """,

    "Q4_reportes_por_laboratorio": """
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
                                   """,

    "Q5_equipos_con_mas_fallos": """
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
                                 """,
}


def conectar(puerto: int) -> connection:
    """Crea una conexión hacia uno de los nodos."""
    return psycopg2.connect(
        host=DB_HOST,
        port=puerto,
        dbname=DB_NAME,
        user=DB_USER,
        sslmode=SSL_MODE,
        connect_timeout=10,
    )


def ejecutar_consulta(
        conexion: connection,
        consulta: str,
) -> tuple[float, int]:
    """
    Ejecuta una consulta y devuelve:
    - tiempo en milisegundos;
    - cantidad de filas retornadas.
    """
    with conexion.cursor() as cursor:
        inicio = time.perf_counter()
        cursor.execute(consulta)
        filas = cursor.fetchall()
        fin = time.perf_counter()

    tiempo_ms = (fin - inicio) * 1000
    return tiempo_ms, len(filas)


def verificar_conexion(
        nombre_nodo: str,
        puerto: int,
) -> bool:
    """Comprueba que un nodo esté disponible."""
    try:
        conexion = conectar(puerto)

        with conexion.cursor() as cursor:
            cursor.execute("SELECT 1;")
            cursor.fetchone()

        conexion.close()
        print(f"[OK] {nombre_nodo} disponible en puerto {puerto}.")
        return True

    except psycopg2.Error as error:
        print(
            f"[ERROR] No se pudo conectar con "
            f"{nombre_nodo} en el puerto {puerto}."
        )
        print(error)
        return False


def ejecutar_benchmark() -> list[dict[str, Any]]:
    """Ejecuta todas las consultas en todos los nodos."""
    resultados: list[dict[str, Any]] = []

    for nombre_nodo, puerto in NODOS.items():
        print()
        print("=" * 60)
        print(f"PROBANDO {nombre_nodo.upper()} - PUERTO {puerto}")
        print("=" * 60)

        conexion = conectar(puerto)
        conexion.autocommit = True

        try:
            for nombre_consulta, consulta in CONSULTAS.items():
                tiempos: list[float] = []

                print(f"\nConsulta: {nombre_consulta}")

                # Ejecución de calentamiento.
                ejecutar_consulta(conexion, consulta)

                for repeticion in range(1, REPETICIONES + 1):
                    tiempo_ms, filas = ejecutar_consulta(
                        conexion,
                        consulta,
                    )

                    tiempos.append(tiempo_ms)

                    resultados.append(
                        {
                            "nodo": nombre_nodo,
                            "puerto": puerto,
                            "consulta": nombre_consulta,
                            "repeticion": repeticion,
                            "tiempo_ms": round(tiempo_ms, 4),
                            "filas": filas,
                        }
                    )

                    print(
                        f"  Repetición {repeticion:02d}: "
                        f"{tiempo_ms:.4f} ms | "
                        f"{filas} filas"
                    )

                print(
                    f"  Promedio: {statistics.mean(tiempos):.4f} ms"
                )
                print(
                    f"  Mínimo:   {min(tiempos):.4f} ms"
                )
                print(
                    f"  Máximo:   {max(tiempos):.4f} ms"
                )

        finally:
            conexion.close()

    return resultados


def guardar_csv(
        resultados: list[dict[str, Any]],
) -> None:
    """Guarda los resultados brutos del benchmark."""
    RUTA_SALIDA.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    columnas = [
        "nodo",
        "puerto",
        "consulta",
        "repeticion",
        "tiempo_ms",
        "filas",
    ]

    with RUTA_SALIDA.open(
            mode="w",
            newline="",
            encoding="utf-8-sig",
    ) as archivo:
        escritor = csv.DictWriter(
            archivo,
            fieldnames=columnas,
        )
        escritor.writeheader()
        escritor.writerows(resultados)

    print()
    print(
        f"[OK] Resultados guardados en: "
        f"{RUTA_SALIDA.resolve()}"
    )


def mostrar_resumen(
        resultados: list[dict[str, Any]],
) -> None:
    """Muestra un resumen por nodo y consulta."""
    print()
    print("=" * 80)
    print("RESUMEN DEL BENCHMARK")
    print("=" * 80)

    for nombre_nodo in NODOS:
        for nombre_consulta in CONSULTAS:
            tiempos = [
                float(resultado["tiempo_ms"])
                for resultado in resultados
                if resultado["nodo"] == nombre_nodo
                   and resultado["consulta"] == nombre_consulta
            ]

            if not tiempos:
                continue

            print(
                f"{nombre_nodo:5} | "
                f"{nombre_consulta:30} | "
                f"promedio={statistics.mean(tiempos):8.4f} ms | "
                f"mínimo={min(tiempos):8.4f} ms | "
                f"máximo={max(tiempos):8.4f} ms"
            )


def main() -> None:
    print("=" * 60)
    print("BENCHMARK DEL CLÚSTER COCKROACHDB")
    print("=" * 60)
    print(f"Nodos: {len(NODOS)}")
    print(f"Consultas: {len(CONSULTAS)}")
    print(f"Repeticiones por consulta: {REPETICIONES}")
    print(
        "Total de ejecuciones medidas: "
        f"{len(NODOS) * len(CONSULTAS) * REPETICIONES}"
    )

    for nombre_nodo, puerto in NODOS.items():
        if not verificar_conexion(nombre_nodo, puerto):
            print(
                "[ERROR] El benchmark fue cancelado "
                "porque uno de los nodos no está disponible."
            )
            sys.exit(1)

    try:
        resultados = ejecutar_benchmark()
        guardar_csv(resultados)
        mostrar_resumen(resultados)

    except psycopg2.Error as error:
        print("[ERROR] El benchmark fue cancelado.")
        print(error)
        sys.exit(1)

    print()
    print("=" * 60)
    print("BENCHMARK COMPLETADO")
    print("=" * 60)


if __name__ == "__main__":
    main()