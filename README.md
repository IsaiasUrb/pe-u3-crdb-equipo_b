# PE-U3 — Clúster distribuido con CockroachDB

Implementación y verificación de una base de datos distribuida de tres nodos con CockroachDB, aplicada al PFC **FUVV — Laboratorios Informáticos: reserva y monitoreo distribuido de laboratorios**.

Repositorio público: [https://github.com/JoseLozanoMorales/pe-u3-crdb-equipo_b](https://github.com/JoseLozanoMorales/pe-u3-crdb-equipo_b)

## Índice

- [Descripción](#descripción)
- [PFC de referencia](#pfc-de-referencia)
- [Integrantes y roles](#integrantes-y-roles)
- [Arquitectura implementada](#arquitectura-implementada)
- [Tecnologías y versiones](#tecnologías-y-versiones)
- [Estructura del repositorio](#estructura-del-repositorio)
- [Requisitos previos](#requisitos-previos)
- [Ejecución reproducible del clúster](#ejecución-reproducible-del-clúster)
- [Prueba de tolerancia a fallos](#prueba-de-tolerancia-a-fallos)
- [Benchmark del clúster](#benchmark-del-clúster)
- [Benchmark de nodo único](#benchmark-de-nodo-único)
- [Resultados principales](#resultados-principales)
- [Documento LaTeX](#documento-latex)
- [Evidencias](#evidencias)
- [Detención y limpieza](#detención-y-limpieza)
- [Declaración de uso de IA generativa](#declaración-de-uso-de-ia-generativa)
- [Aclaración sobre fuentes bibliográficas](#aclaración-sobre-fuentes-bibliográficas)

## Descripción

El proyecto despliega tres nodos CockroachDB en contenedores Docker conectados mediante una red `bridge`. Cada nodo posee almacenamiento persistente, un puerto SQL, una interfaz web y una localidad lógica diferente. El esquema `gestion_laboratorios` contiene diez tablas relacionadas para usuarios, docentes, estudiantes, laboratorios, equipos, materias, asignaciones, asistencias y reportes de fallos.

La tabla principal `reporte_fallo` utiliza fragmentación horizontal mediante `PARTITION BY LIST` sobre el atributo `estado`. Se definieron las particiones `PENDIENTE`, `EN_PROCESO` y `RESUELTO`, cada una con tres réplicas y una preferencia de leaseholder distinta. El experimento incluye carga sintética reproducible, validación de rangos, cinco consultas de rendimiento, planes `EXPLAIN ANALYZE`, comparación con nodo único y una prueba de tolerancia a fallos al detener el nodo 2.

## PFC de referencia

- **Código:** FUVV
- **Título:** Laboratorios Informáticos: reserva y monitoreo distribuido de laboratorios.

Este PFC fue seleccionado porque combina reservas, recursos físicos, usuarios y eventos de monitoreo que pueden originarse simultáneamente desde diferentes laboratorios. El dominio permite aplicar fragmentación, replicación, consistencia serializable, control de concurrencia y tolerancia a fallos sobre reglas funcionales concretas. La distribución busca mantener disponibles las reservas y los reportes operativos aun cuando un nodo deje de responder.

## Integrantes y roles

| Integrante | PFC de origen | Rol principal |
|---|---|---|
| José Alejandro Lozano Morales | AGLS | Diseño del esquema, fragmentación, consultas y revisión bibliográfica. |
| Andy Paul Sanchez Pilaloa | AGLS | Configuración del clúster, documentación LaTeX y organización de evidencias. |
| Isaias Romero Abraham Urbina | FUVV | Generación de datos, benchmarks, nodo único y prueba de tolerancia a fallos. |

Las responsabilidades describen el aporte principal de cada integrante; la revisión del código, los resultados y el informe se realizó de manera colaborativa.

## Arquitectura implementada

| Servicio | Localidad | Puerto SQL | Dashboard | Almacenamiento |
|---|---|---:|---:|---|
| `crdb-node1` | `region=uteq,zone=nodo1` | `26257` | [http://localhost:8080](http://localhost:8080) | Volumen `crdb-node1-data` |
| `crdb-node2` | `region=uteq,zone=nodo2` | `26258` | [http://localhost:8081](http://localhost:8081) | Volumen `crdb-node2-data` |
| `crdb-node3` | `region=uteq,zone=nodo3` | `26259` | [http://localhost:8082](http://localhost:8082) | Volumen `crdb-node3-data` |
| `cockroach-single` | Nodo único independiente | `26260` | [http://localhost:8083](http://localhost:8083) | Volumen `cockroach-single-data` |

Los nodos distribuidos utilizan el puerto interno `26357` para la comunicación del clúster y el puerto interno `26257` para SQL. El servicio auxiliar `crdb-init` ejecuta la inicialización contra `crdb-node1:26357`.

## Tecnologías y versiones

- CockroachDB `v25.2.3`.
- Docker Desktop 4.x con Docker Compose Plugin.
- Python 3.10 o superior.
- `psycopg2-binary` para las conexiones desde Python.
- LaTeX con `pdflatex`, `biber`, `biblatex` y estilo IEEE.

## Estructura del repositorio

```text
pe-u3-crdb-equipo_b/
├── README.md
├── docker-compose.yml
├── docker-compose.single.yml
├── docs/
│   ├── PE_U3_Informe.tex
│   └── referencias.bib
├── sql/
│   ├── 01_schema.sql
│   ├── 02_partitions.sql
│   ├── 03_queries.sql
│   ├── 04_q1_explain_analyze.sql
│   ├── 05_q2_explain_analyze.sql
│   ├── 06_q3_explain_analyze.sql
│   ├── 07_q4_explain_analyze.sql
│   └── 08_q5_explain_analyze.sql
├── scripts/
│   ├── seed_data.py
│   ├── run_benchmark.py
│   ├── seed_data_single.py
│   └── run_benchmark_single.py
└── evidencia/
    ├── imagenes/
    ├── resultados.csv
    ├── resultados_single.csv
    └── video_tolerancia.mp4
```

## Requisitos previos

1. Instalar Docker Desktop y comprobar que el motor esté iniciado.
2. Instalar Python 3.10 o superior.
3. Clonar el repositorio y entrar en su carpeta.
4. Instalar la dependencia de Python.

```powershell
git clone https://github.com/JoseLozanoMorales/pe-u3-crdb-equipo_b.git
cd pe-u3-crdb-equipo_b
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install psycopg2-binary
```

En Linux o macOS, la activación equivalente es `source .venv/bin/activate`.

## Ejecución reproducible del clúster

### 1. Levantar los tres nodos

```powershell
docker compose up -d
docker compose ps
```

El servicio `crdb-init` inicializa automáticamente el clúster. Si la inicialización ya fue realizada sobre los volúmenes existentes, el contenedor auxiliar puede finalizar indicando que el clúster ya estaba inicializado.

### 2. Verificar el estado

```powershell
docker compose exec crdb-node1 cockroach node status --insecure --host=crdb-node1:26257
```

La salida esperada debe mostrar tres nodos disponibles y vivos. El dashboard principal puede consultarse en [http://localhost:8080](http://localhost:8080).

### 3. Crear el esquema

```powershell
Get-Content -Raw .\sql\01_schema.sql | docker compose exec -T crdb-node1 cockroach sql --insecure --host=crdb-node1:26257
```

### 4. Aplicar la fragmentación y replicación

```powershell
Get-Content -Raw .\sql\02_partitions.sql | docker compose exec -T crdb-node1 cockroach sql --insecure --host=crdb-node1:26257
```

### 5. Cargar los datos sintéticos

```powershell
python .\scripts\seed_data.py
```

El script utiliza la semilla `2026` y genera 15 330 registros, incluidos 2 500 reportes de fallos.

### 6. Ejecutar las consultas de validación

```powershell
Get-Content -Raw .\sql\03_queries.sql | docker compose exec -T crdb-node1 cockroach sql --insecure --host=crdb-node1:26257
```

### 7. Verificar particiones, zonas y rangos

```powershell
docker compose exec crdb-node1 cockroach sql --insecure --host=crdb-node1:26257 --database=gestion_laboratorios -e "SHOW PARTITIONS FROM TABLE reporte_fallo;"
docker compose exec crdb-node1 cockroach sql --insecure --host=crdb-node1:26257 --database=gestion_laboratorios -e "SHOW ZONE CONFIGURATIONS;"
docker compose exec crdb-node1 cockroach sql --insecure --host=crdb-node1:26257 --database=gestion_laboratorios -e "SHOW RANGES FROM TABLE reporte_fallo;"
```

## Prueba de tolerancia a fallos

La prueba utiliza `reporte_fallo` como tabla principal. Debe ejecutarse de forma continua mientras se graba la pantalla.

### 1. Estado inicial y consulta base

```powershell
docker compose exec crdb-node1 cockroach node status --insecure --host=crdb-node1:26257
docker compose exec crdb-node1 cockroach sql --insecure --host=crdb-node1:26257 --database=gestion_laboratorios -e "SELECT COUNT(*) FROM reporte_fallo;"
docker compose exec crdb-node1 cockroach sql --insecure --host=crdb-node1:26257 --database=gestion_laboratorios -e "SHOW RANGES FROM TABLE reporte_fallo;"
```

### 2. Detener el nodo 2 y repetir la consulta

```powershell
docker stop crdb-node2
docker compose exec crdb-node1 cockroach sql --insecure --host=crdb-node1:26257 --database=gestion_laboratorios -e "SELECT COUNT(*) FROM reporte_fallo;"
Start-Sleep -Seconds 30
docker compose exec crdb-node1 cockroach sql --insecure --host=crdb-node1:26257 --database=gestion_laboratorios -e "SHOW RANGES FROM TABLE reporte_fallo;"
```

La consulta debe continuar devolviendo `2500` porque los nodos 1 y 3 conservan la mayoría de dos réplicas.

### 3. Reiniciar y verificar la reintegración

```powershell
docker start crdb-node2
docker compose exec crdb-node1 cockroach node status --insecure --host=crdb-node1:26257
```

El video continuo de la prueba se encuentra en [`evidencia/video_tolerancia.mp4`](evidencia/video_tolerancia.mp4).

## Benchmark del clúster

El benchmark abre conexiones independientes a los puertos `26257`, `26258` y `26259`. Ejecuta cinco consultas, realiza un calentamiento y registra diez repeticiones por consulta y nodo, para un total de 150 observaciones.

```powershell
python .\scripts\run_benchmark.py
```

Los resultados se guardan en [`evidencia/resultados.csv`](evidencia/resultados.csv).

Para ejecutar los cinco planes de análisis desde PowerShell:

```powershell
Get-ChildItem .\sql\0[4-8]_*.sql | Sort-Object Name | ForEach-Object { Get-Content -Raw $_.FullName | docker compose exec -T crdb-node1 cockroach sql --insecure --host=crdb-node1:26257 --database=gestion_laboratorios }
```

## Benchmark de nodo único

La instancia independiente utiliza el puerto SQL `26260` y el dashboard `8083`. El esquema y los datos se cargan por separado para evitar que el benchmark se conecte al clúster distribuido.

### 1. Levantar la instancia

```powershell
docker compose -f docker-compose.single.yml up -d
docker compose -f docker-compose.single.yml ps
```

### 2. Crear el esquema y cargar los datos

```powershell
Get-Content -Raw .\sql\01_schema.sql | docker compose -f docker-compose.single.yml exec -T cockroach-single cockroach sql --insecure --host=localhost:26257
python .\scripts\seed_data_single.py
```

No se aplica `02_partitions.sql` a esta instancia porque sus restricciones requieren las tres localidades del clúster.

### 3. Ejecutar el benchmark

```powershell
python .\scripts\run_benchmark_single.py
```

Los resultados se guardan en [`evidencia/resultados_single.csv`](evidencia/resultados_single.csv).

## Resultados principales

El factor se define como `tiempo_nodo_único / tiempo_clúster`. Un valor superior a `1` favorece al clúster; un valor inferior a `1` favorece al nodo único.

| Consulta | Clúster (ms) | Nodo único (ms) | Factor |
|---|---:|---:|---:|
| Q1 — Reportes pendientes | 5.2904 | 5.4985 | 1.039 |
| Q2 — Reportes en proceso | 9.2761 | 6.3010 | 0.679 |
| Q3 — Reportes resueltos con uniones | 7.5935 | 12.7959 | 1.685 |
| Q4 — Reportes agrupados por laboratorio | 9.3320 | 7.9940 | 0.857 |
| Q5 — Equipos con más fallos | 10.4981 | 15.2845 | 1.456 |

El clúster obtuvo menor latencia en Q1, Q3 y Q5, mientras que el nodo único fue más rápido en Q2 y Q4. El promedio no ponderado fue `8.3980 ms` para el clúster y `9.5750 ms` para el nodo único. Estos resultados corresponden al entorno experimental utilizado y no deben generalizarse sin repetir las mediciones bajo cargas y configuraciones equivalentes.

## Documento LaTeX

- Fuente principal: [`docs/PE_U3_Informe.tex`](docs/PE_U3_Informe.tex).
- Bibliografía: [`docs/referencias.bib`](docs/referencias.bib).
- Estilo bibliográfico: IEEE mediante `biblatex` y `biber`.

Secuencia habitual de compilación:

```text
pdflatex PE_U3_Informe.tex
biber PE_U3_Informe
pdflatex PE_U3_Informe.tex
pdflatex PE_U3_Informe.tex
```

El proyecto fue preparado para su compilación final en Overleaf, donde las imágenes se organizan en las carpetas indicadas por las rutas del archivo `.tex`. El PDF compilado debe guardarse finalmente como `docs/PE_U3_Informe.pdf` en el repositorio de entrega.

## Evidencias

La carpeta [`evidencia/`](evidencia/) contiene:

- Capturas de inicialización, dashboard, esquema, particiones, zonas y carga de datos.
- Planes `EXPLAIN ANALYZE` de Q1 a Q5.
- Capturas de la caída y reintegración del nodo 2.
- Diagrama de secuencia de la prueba de tolerancia a fallos.
- Mediciones brutas del clúster y del nodo único.
- Video continuo de tolerancia a fallos.

## Detención y limpieza

Detener los servicios sin eliminar los datos:

```powershell
docker compose down
docker compose -f docker-compose.single.yml down
```

Eliminar también los volúmenes y reiniciar el experimento desde cero:

```powershell
docker compose down -v
docker compose -f docker-compose.single.yml down -v
```

> **Advertencia:** la opción `-v` elimina permanentemente los datos almacenados en los volúmenes de CockroachDB.

## Declaración de uso de IA generativa

El equipo utilizó **ChatGPT** como herramienta de apoyo para realizar comprobaciones y proponer arreglos durante el desarrollo del trabajo. La asistencia se aplicó a la revisión de código SQL, Python, Docker Compose y LaTeX; la detección de errores de rutas, sintaxis, estructura y compilación; la organización y comprobación de referencias bibliográficas, DOI, metadatos y formato IEEE; la revisión de coherencia entre la rúbrica y el informe; la comprobación conceptual y visual del diagrama de secuencia; y la mejora de redacción, tablas, pies de figura y referencias cruzadas.

ChatGPT no ejecutó por cuenta propia el experimento ni sustituyó las decisiones académicas del equipo. Los integrantes configuraron el entorno, ejecutaron las pruebas, verificaron las fuentes disponibles, revisaron las propuestas y asumieron la responsabilidad final por el código, los resultados, el análisis y el contenido entregado.

## Aclaración sobre fuentes bibliográficas

Durante la verificación manual de las fuentes recomendadas en la rúbrica se identificaron problemas de acceso en las referencias originales [1], [2] y [7]:

- **[1] D. J. Abadi, _Consistency Tradeoffs in Modern Distributed Database System Design: CAP Is Only Part of the Story_.** No fue posible acceder al artículo mediante el DOI proporcionado por la rúbrica.
- **[2] E. Brewer, _CAP Twelve Years Later: How the “Rules” Have Changed_.** Tampoco fue posible acceder al artículo mediante el DOI proporcionado por la rúbrica.
- **[7] D. Ongaro y J. Ousterhout, _In Search of an Understandable Consensus Algorithm_.** Al comprobar el ISBN proporcionado se obtuvo un libro diferente del artículo señalado por la rúbrica.

Estas entradas no se presentan como fuentes consultadas dentro del informe. La aclaración conserva el resultado de la comprobación realizada por el equipo y evita atribuir contenido académico a documentos que no pudieron verificarse mediante los datos suministrados.
