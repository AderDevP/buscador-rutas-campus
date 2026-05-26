# Documento Técnico — Buscador de Rutas del Campus

| | |
|---|---|
| **Asignatura** | Estructura de Datos |
| **Institución** | Institución Universitaria Pascual Bravo |
| **Programa** | Ingeniería de Software |
| **Período** | 2026‑1 |
| **Problema escogido** | Problema 1 — Buscador de rutas del campus |
| **Repositorio** | <https://github.com/AderDevP/buscador-rutas-campus> |

**Integrantes:**

- Sara Ríos Vélez — modelado del grafo, casos de prueba, documentación.
- Ader Eliecer Quintana Herrera — algoritmo Dijkstra, DFS de alcanzables, menú interactivo.

## 1. Descripción del problema y motivación

Los campus universitarios suelen tener decenas de bloques, salones y puntos de interés (biblioteca, cafetería, auditorio, laboratorios). Para un estudiante o visitante nuevo, decidir qué camino tomar para llegar de un punto a otro en el menor tiempo o con la menor distancia recorrida no siempre es trivial.

El objetivo del proyecto es construir una herramienta que permita:

- Modelar el campus como una red de ubicaciones conectadas.
- Calcular la ruta más corta entre dos puntos.
- Conocer qué ubicaciones son alcanzables desde un origen.
- Mantener la información actualizada (agregar y eliminar ubicaciones y rutas).

La motivación pedagógica es aplicar dos estructuras vistas en clase: **grafos** y **arreglos**, integrándolas en una solución funcional.

## 2. Modelado del problema

Se modela el campus como un **grafo no dirigido y ponderado** `G = (V, E, w)` donde:

- `V` = conjunto de ubicaciones (bloques, salones, puntos de interés).
- `E` = conjunto de caminos transitables entre dos ubicaciones.
- `w(e)` = peso de la arista `e`, en metros (también podría ser segundos).

Es **no dirigido** porque los caminos del campus se recorren en ambos sentidos. Es **ponderado** porque cada camino tiene una distancia distinta y se busca la ruta de menor costo total.

### 2.1 Diagrama del grafo de ejemplo

```
                          (40)
          [Entrada] ───────────────── [Parqueadero]
              │                              │
            (60)                          (150)
              │                              │
          [BloqueA] ── (50) ── [BloqueB] ── (45) ── [BloqueC]
              │                  │                    │
            (80)               (65)                (70)
              │                  │                    │
        [Biblioteca]      [Laboratorios]         [Auditorio]
              │                  │                    │
            (30)               (75)                 (90)
              │                  │                    │
              └── [Cafeteria] ───┘               [Coliseo]
                       │
                     (55)
                       │
                   [BloqueC]   (mismo nodo, ciclo en el grafo)
```

Versión ASCII más detallada en [`diagrama_grafo.txt`](diagrama_grafo.txt).

### 2.2 Conjunto de aristas (datos `data/campus.txt`)

| Origen | Destino | Peso (m) |
|---|---|---|
| Entrada | Parqueadero | 40 |
| Entrada | BloqueA | 60 |
| BloqueA | BloqueB | 50 |
| BloqueB | BloqueC | 45 |
| BloqueA | Biblioteca | 80 |
| Biblioteca | Cafeteria | 30 |
| Cafeteria | BloqueC | 55 |
| BloqueC | Auditorio | 70 |
| Auditorio | Coliseo | 90 |
| Laboratorios | BloqueB | 65 |
| Laboratorios | Cafeteria | 75 |
| Parqueadero | Coliseo | 150 |

## 3. Estructuras de datos utilizadas

### 3.1 Representación principal: lista de adyacencia

Implementada como un `dict` cuyo valor es una `list` de tuplas `(vecino, peso)`:

```python
adyacencia: Dict[str, List[Tuple[str, float]]] = {
    "Entrada":     [("Parqueadero", 40), ("BloqueA", 60)],
    "Parqueadero": [("Entrada", 40),     ("Coliseo", 150)],
    "BloqueA":     [("Entrada", 60),     ("BloqueB", 50), ("Biblioteca", 80)],
    ...
}
```

Como el grafo es no dirigido, **cada arista aparece dos veces**: una en la lista del origen y otra en la del destino.

**Justificación de la elección:**

| Criterio | Lista de adyacencia | Matriz de adyacencia |
|---|---|---|
| Memoria | `O(V + E)` | `O(V²)` |
| Buscar vecinos de `v` | `O(grado(v))` | `O(V)` |
| Verificar arista `(u, v)` | `O(grado(u))` | `O(1)` |
| Insertar/eliminar arista | `O(grado(v))` | `O(1)` |

El grafo del campus es **disperso** (`E ≪ V²`): cada ubicación solo está conectada con 2–4 vecinos. Por eso conviene la lista de adyacencia: ahorra memoria y los recorridos típicos (Dijkstra, DFS) iteran sobre vecinos, donde la lista es óptima.

La matriz se ofrece solo como **vista derivada** en la opción 8b para visualización.

### 3.2 Arreglos auxiliares

Los algoritmos usan los siguientes arreglos. En Python se modelan como `dict` cuando se indexan por nombre de nodo, o como `list` cuando se indexan por posición.

| Arreglo | Tipo | Tamaño | Uso |
|---|---|---|---|
| `distancias` | `Dict[str, float]` | `O(V)` | Distancia mínima conocida desde el origen |
| `previos` | `Dict[str, str]` | `O(V)` | Predecesor en la ruta óptima (para reconstruir el camino) |
| `visitados` | `Dict[str, bool]` | `O(V)` | Marca si un nodo ya fue procesado (DFS) |
| `cola` (heap) | `List[Tuple[float, str]]` | hasta `O(V + E)` | Cola de prioridad de Dijkstra (`heapq`) |
| `pila` | `List[str]` | `O(V)` | Pila de DFS iterativo (alcanzables) |
| `camino` | `List[str]` | `O(V)` | Reconstrucción de la ruta final |

`distancias` y `previos` son los arreglos clásicos para reconstruir caminos óptimos. `visitados` evita reprocesar nodos. La cola de prioridad `heapq` da las operaciones logarítmicas que necesita Dijkstra.

## 4. Operaciones implementadas

| # | Operación | Función | Complejidad temporal | Complejidad espacial |
|---|---|---|---|---|
| 1 | Cargar desde archivo | `cargar_desde_archivo` | `O(V + E)` | `O(V + E)` |
| 2 | Agregar ubicación | `Grafo.agregar_nodo` | `O(1)` promedio | `O(1)` |
| 3 | Eliminar ubicación | `Grafo.eliminar_nodo` | `O(V + E)` | `O(1)` |
| 4 | Agregar ruta con peso | `Grafo.agregar_arista` | `O(grado(v))` | `O(1)` |
| 5 | Eliminar ruta | `Grafo.eliminar_arista` | `O(grado(v))` | `O(1)` |
| 6 | Ruta más corta (Dijkstra) | `dijkstra` | `O((V + E) log V)` | `O(V)` |
| 7 | Alcanzables (DFS) | `alcanzables_desde` | `O(V + E)` | `O(V)` |
| 8a | Lista de adyacencia | `representacion_lista` | `O(V + E)` | `O(V + E)` |
| 8b | Matriz de adyacencia | `representacion_matriz` | `O(V²)` | `O(V²)` |

### 4.1 Algoritmo Dijkstra

#### Pseudocódigo

```
función Dijkstra(grafo, origen, destino):
    para cada v en V:
        distancias[v] = ∞
        previos[v] = nulo
    distancias[origen] = 0

    heap = cola de prioridad
    push(heap, (0, origen))

    mientras heap no esté vacío:
        (d, u) = pop_mínimo(heap)
        si d > distancias[u]:           # entrada obsoleta
            continuar
        si u == destino:                # corte temprano
            romper
        para cada (v, peso) en adyacencia[u]:
            nueva = d + peso
            si nueva < distancias[v]:
                distancias[v] = nueva
                previos[v] = u
                push(heap, (nueva, v))

    devolver (distancias[destino], reconstruir(previos, origen, destino))
```

#### Traza paso a paso: `Entrada → Auditorio`

| Paso | Pop del heap | Relajaciones efectivas | Estado relevante de `distancias` |
|---|---|---|---|
| 0 | — | inicial: `distancias[Entrada]=0` | Entrada=0, resto=∞ |
| 1 | `(0, Entrada)` | Parqueadero ← 40, BloqueA ← 60 | Parqueadero=40, BloqueA=60 |
| 2 | `(40, Parqueadero)` | Coliseo ← 190 | Coliseo=190 |
| 3 | `(60, BloqueA)` | BloqueB ← 110, Biblioteca ← 140 | BloqueB=110, Biblioteca=140 |
| 4 | `(110, BloqueB)` | BloqueC ← 155, Laboratorios ← 175 | BloqueC=155, Laboratorios=175 |
| 5 | `(140, Biblioteca)` | Cafeteria ← 170 | Cafeteria=170 |
| 6 | `(155, BloqueC)` | Auditorio ← 225 (no mejora Cafeteria, 170<210) | Auditorio=225 |
| 7 | `(170, Cafeteria)` | nada mejora | — |
| 8 | `(175, Laboratorios)` | nada mejora | — |
| 9 | `(190, Coliseo)` | (Auditorio 280 no mejora 225) | — |
| 10 | `(225, Auditorio)` | **destino alcanzado**, corte | — |

**Reconstrucción del camino** siguiendo `previos` desde el destino:

```
Auditorio ← BloqueC ← BloqueB ← BloqueA ← Entrada
```

Invertido: `Entrada → BloqueA → BloqueB → BloqueC → Auditorio` con distancia total **225 m**.

### 4.2 DFS iterativo (alcanzables)

#### Pseudocódigo

```
función alcanzables(grafo, origen):
    visitados[v] = falso para todo v
    pila = [origen]
    visitados[origen] = verdadero
    resultado = []
    mientras pila no esté vacía:
        u = pop(pila)
        si u != origen:
            resultado.añadir(u)
        para cada (v, _) en adyacencia[u]:
            si no visitados[v]:
                visitados[v] = verdadero
                push(pila, v)
    devolver ordenar(resultado)
```

#### Traza desde `Entrada`

| Iter | `pop` | Estado de la pila al terminar | Visitados nuevos |
|---|---|---|---|
| 1 | Entrada | `[Parqueadero, BloqueA]` | Parqueadero, BloqueA |
| 2 | BloqueA | `[Parqueadero, Biblioteca, BloqueB]` (ordén depende del listado) | Biblioteca, BloqueB |
| 3 | BloqueB | `[Parqueadero, Biblioteca, BloqueC, Laboratorios]` | BloqueC, Laboratorios |
| 4 | Laboratorios | `[Parqueadero, Biblioteca, BloqueC, Cafeteria]` | Cafeteria |
| 5 | Cafeteria | `[Parqueadero, Biblioteca, BloqueC]` | (todos visitados) |
| 6 | BloqueC | `[Parqueadero, Biblioteca, Auditorio]` | Auditorio |
| 7 | Auditorio | `[Parqueadero, Biblioteca, Coliseo]` | Coliseo |
| 8 | Coliseo | `[Parqueadero, Biblioteca]` | — |
| 9 | Biblioteca | `[Parqueadero]` | — |
| 10 | Parqueadero | `[]` | — |

Resultado ordenado: `[Auditorio, Biblioteca, BloqueA, BloqueB, BloqueC, Cafeteria, Coliseo, Laboratorios, Parqueadero]` (9 nodos).

### 4.3 Eliminar ubicación

```
función eliminar_nodo(nombre):
    si nombre no está en adyacencia: devolver falso
    eliminar adyacencia[nombre]
    para cada lista de vecinos en adyacencia.values():
        filtrar tuplas cuyo vecino sea 'nombre'
    devolver verdadero
```

Coste: visita los `V−1` nodos restantes y filtra cada lista. En total, recorre todas las aristas: `O(V + E)`.

### 4.4 Carga desde archivo

Lectura línea por línea:

```
NODO <nombre>                    → grafo.agregar_nodo(nombre)
ARISTA <origen> <destino> <peso> → grafo.agregar_arista(origen, destino, peso)
# comentario                     → ignorar
```

Validaciones: número correcto de campos, peso convertible a `float`, instrucción reconocida. Mensajes de error indican el número de línea.

## 5. Casos de prueba

> Las capturas referenciadas están en `docs/imagenes/`.

### Caso 1 — Ruta más corta (Dijkstra)

- **Acción:** opción 6 con `Entrada → Auditorio`.
- **Salida esperada:**
  - Distancia mínima: `225`
  - Camino: `Entrada -> BloqueA -> BloqueB -> BloqueC -> Auditorio`
- **Verificación manual:** `60 + 50 + 45 + 70 = 225` (vía bloques), frente a `60 + 80 + 30 + 55 + 70 = 295` (vía biblioteca). 225 < 295 ✔.
- **Captura:** ![Dijkstra Entrada → Auditorio](imagenes/04_dijkstra_entrada_auditorio.png)

### Caso 2 — Alcanzables

- **Acción:** opción 7 con origen `Entrada`.
- **Salida esperada:** las 9 ubicaciones restantes (grafo conexo).
- **Captura:** ![Alcanzables desde Entrada](imagenes/05_alcanzables_entrada.png)

### Caso 3 — Agregar y eliminar nodo

- **Acción:** opción 2 para crear `Polideportivo`, luego opción 3 para eliminarlo.
- **Salida esperada:** confirmaciones `[OK] Ubicación 'Polideportivo' agregada.` y `[OK] Ubicación 'Polideportivo' eliminada.`
- **Captura:** ![Agregar y eliminar Polideportivo](imagenes/07_agregar_eliminar_polideportivo.png)

### Caso 4 — Eliminar arista

- **Acción:** opción 5 con `BloqueB` y `BloqueC`.
- **Salida esperada:** Dijkstra `Entrada → Auditorio` deja de dar `225` y pasa a `280` por `Entrada → Parqueadero → Coliseo → Auditorio` (`40 + 150 + 90`). Tiene sentido: cualquier ruta vía bloques debe rodear el corte por `Cafeteria` o por `Coliseo`, y la más corta resulta ser por el Coliseo.
- **Captura:** ![Eliminar BloqueB-BloqueC y recálculo](imagenes/06_eliminar_arista_y_recalculo.png)

### Caso 5 — Sin ruta

- **Acción:** opción 2 para crear `Polideportivo` aislado y opción 6 con `Entrada → Polideportivo`.
- **Salida esperada:** `[!] No hay ruta entre 'Entrada' y 'Polideportivo'.`

### Caso 6 — Peso negativo

- **Acción:** opción 4 con `BloqueA`, `BloqueB`, peso `-3`.
- **Salida esperada:** `[!] El peso no puede ser negativo (Dijkstra lo requiere).`

### Caso 7 — Lazo

- **Acción:** opción 4 con `BloqueA`, `BloqueA`, peso `5`.
- **Salida esperada:** `[!] No se permiten lazos (origen == destino).`

### Caso 8 — Actualización de peso

- **Acción:** opción 4 con `BloqueA`, `BloqueB`, peso `25`.
- **Salida esperada:** `[OK]`. Una nueva consulta `Entrada → Auditorio` da `60 + 25 + 45 + 70 = 200`.

### Vista general del menú y representación interna

- ![Menú principal](imagenes/01_menu_principal.png)
- ![Lista de adyacencia](imagenes/02_lista_adyacencia.png)
- ![Matriz de adyacencia](imagenes/03_matriz_adyacencia.png)

## 6. Diagramas

- **Modelado del grafo:** sección 2.1 y archivo [`diagrama_grafo.txt`](diagrama_grafo.txt).
- **Diagrama de flujo de Dijkstra:**

```
        ┌──────────────┐
        │   Inicio     │
        └──────┬───────┘
               │
               ▼
   distancias[origen] = 0
   distancias[v ≠ origen] = ∞
   heap = [(0, origen)]
               │
               ▼
   ┌──────────────────────────┐
   │   ¿heap vacío?           │── sí ──► reconstruir(previos, origen, destino)
   └──────────────┬───────────┘
                  │ no
                  ▼
         (d, u) = heappop(heap)
                  │
                  ▼
        ¿d > distancias[u]?  ── sí ──► descartar y volver al check
                  │ no
                  ▼
        ¿u == destino? ── sí ──► reconstruir y salir
                  │ no
                  ▼
         para cada (v, w) vecino de u:
            nueva = d + w
            si nueva < distancias[v]:
               distancias[v] = nueva
               previos[v] = u
               heappush(heap, (nueva, v))
                  │
                  └── volver al check
```

- **Capturas del demo:** disponibles en `docs/imagenes/` y referenciadas en la sección 5 (Casos de prueba) de este documento.

## 7. Instrucciones de ejecución

1. Tener Python 3.9 o superior instalado.
2. Clonar el repositorio:

   ```bash
   git clone https://github.com/AderDevP/buscador-rutas-campus.git
   cd buscador-rutas-campus
   ```

3. Ejecutar:

   ```bash
   python src/main.py
   ```

4. Al iniciar se carga `data/campus.txt`. Use el menú para probar las operaciones según la guía del [`README`](../README.md).

## 8. Limitaciones

- **Grafo no dirigido únicamente:** no se modelan calles de un solo sentido.
- **Pesos no negativos:** para soportar pesos negativos sería necesario Bellman‑Ford.
- **Sin interfaz gráfica:** la representación es textual (lista o matriz) en consola.
- **Sin coordenadas físicas:** no se calculan distancias euclidianas, solo las del archivo.
- **Sin persistencia automática:** los cambios hechos por el menú se pierden al salir.
- **Validación básica del archivo:** detecta errores sintácticos (campos, peso) pero no inconsistencias semánticas (p. ej. arista duplicada con peso distinto se sobrescribe).

## 9. Posibles mejoras

- Soportar **grafos dirigidos** con sentido único.
- Añadir **interfaz gráfica** (Tkinter, o web con Flask + D3.js) para dibujar el campus.
- **Importar y exportar** desde JSON, CSV o GeoJSON con coordenadas reales.
- Implementar **A\*** usando coordenadas como heurística.
- Calcular **árbol de expansión mínima** (Prim o Kruskal).
- Ponderar las aristas según congestión por hora.
- Persistir los cambios del menú en un archivo `data/campus_actual.txt`.

## 10. Referencias

- Cormen, T., Leiserson, C., Rivest, R., Stein, C. *Introduction to Algorithms*, 3.ª edición. MIT Press, 2009. Capítulos 22 (búsqueda en grafos) y 24 (caminos más cortos).
- Documentación oficial de Python: módulo [`heapq`](https://docs.python.org/3/library/heapq.html).
