"""
grafo.py
--------
Estructura de datos y algoritmos del Buscador de Rutas del Campus.

Contiene:
  - Clase Grafo: grafo NO DIRIGIDO con PESO, representado como
    LISTA DE ADYACENCIA (diccionario de listas de tuplas).
  - Algoritmo Dijkstra para la ruta más corta.
  - Búsqueda de nodos alcanzables (DFS iterativo).
  - Carga del grafo desde un archivo de texto.

Se usan ARREGLOS (listas y diccionarios de Python) como estructuras
auxiliares: distancias, previos, visitados, cola de prioridad y pila.
"""

from __future__ import annotations

import heapq
import math
import os
from typing import Dict, List, Optional, Tuple


class Grafo:
    """Grafo no dirigido y ponderado basado en lista de adyacencia."""

    def __init__(self) -> None:
        # adyacencia: { nodo: [(vecino, peso), ...] }
        self.adyacencia: Dict[str, List[Tuple[str, float]]] = {}

    # ---------------------------- Nodos ----------------------------
    def agregar_nodo(self, nombre: str) -> bool:
        """Agrega una ubicación. True si se agregó, False si ya existía."""
        nombre = nombre.strip()
        if not nombre:
            raise ValueError("El nombre de la ubicación no puede estar vacío.")
        if nombre in self.adyacencia:
            return False
        self.adyacencia[nombre] = []
        return True

    def eliminar_nodo(self, nombre: str) -> bool:
        """Elimina una ubicación y todas sus aristas. True si existía."""
        if nombre not in self.adyacencia:
            return False
        del self.adyacencia[nombre]
        for vecinos in self.adyacencia.values():
            vecinos[:] = [(v, p) for (v, p) in vecinos if v != nombre]
        return True

    def existe_nodo(self, nombre: str) -> bool:
        return nombre in self.adyacencia

    def listar_nodos(self) -> List[str]:
        return sorted(self.adyacencia.keys())

    # --------------------------- Aristas ---------------------------
    def agregar_arista(self, origen: str, destino: str, peso: float) -> None:
        """Agrega/actualiza una arista no dirigida con peso."""
        if peso < 0:
            raise ValueError("El peso no puede ser negativo (Dijkstra lo requiere).")
        if origen == destino:
            raise ValueError("No se permiten lazos (origen == destino).")

        self.agregar_nodo(origen)
        self.agregar_nodo(destino)

        self._upsert(origen, destino, peso)
        self._upsert(destino, origen, peso)

    def _upsert(self, a: str, b: str, peso: float) -> None:
        for i, (v, _) in enumerate(self.adyacencia[a]):
            if v == b:
                self.adyacencia[a][i] = (b, peso)
                return
        self.adyacencia[a].append((b, peso))

    def eliminar_arista(self, origen: str, destino: str) -> bool:
        """Elimina la arista entre dos nodos. True si existía."""
        if origen not in self.adyacencia or destino not in self.adyacencia:
            return False
        antes = len(self.adyacencia[origen])
        self.adyacencia[origen] = [
            (v, p) for (v, p) in self.adyacencia[origen] if v != destino
        ]
        self.adyacencia[destino] = [
            (v, p) for (v, p) in self.adyacencia[destino] if v != origen
        ]
        return len(self.adyacencia[origen]) < antes

    def obtener_peso(self, origen: str, destino: str) -> Optional[float]:
        if origen not in self.adyacencia:
            return None
        for v, p in self.adyacencia[origen]:
            if v == destino:
                return p
        return None

    # ---------------------- Representaciones -----------------------
    def representacion_lista(self) -> str:
        """Lista de adyacencia formateada como texto."""
        if not self.adyacencia:
            return "(grafo vacío)"
        lineas = ["Lista de adyacencia:"]
        for nodo in sorted(self.adyacencia):
            vecinos = self.adyacencia[nodo]
            if vecinos:
                vecinos_txt = ", ".join(
                    f"{v}({p:g})" for v, p in sorted(vecinos)
                )
            else:
                vecinos_txt = "(sin conexiones)"
            lineas.append(f"  {nodo} -> {vecinos_txt}")
        return "\n".join(lineas)

    def representacion_matriz(self) -> str:
        """Matriz de adyacencia con pesos. '-' indica sin conexión."""
        nodos = self.listar_nodos()
        if not nodos:
            return "(grafo vacío)"

        ancho = max(8, max(len(n) for n in nodos) + 1)
        encabezado = " " * ancho + "".join(f"{n:>{ancho}}" for n in nodos)
        lineas = ["Matriz de adyacencia:", encabezado]

        for n in nodos:
            fila = f"{n:<{ancho}}"
            for m in nodos:
                if n == m:
                    celda = "0"
                else:
                    p = self.obtener_peso(n, m)
                    celda = "-" if p is None else f"{p:g}"
                fila += f"{celda:>{ancho}}"
            lineas.append(fila)
        return "\n".join(lineas)

    # ----------------------------- Misc ----------------------------
    def numero_nodos(self) -> int:
        return len(self.adyacencia)

    def numero_aristas(self) -> int:
        return sum(len(v) for v in self.adyacencia.values()) // 2

    def __repr__(self) -> str:
        return f"Grafo(nodos={self.numero_nodos()}, aristas={self.numero_aristas()})"


# ======================================================================
# Algoritmos sobre el grafo
# ======================================================================
def _reconstruir_camino(
    previos: Dict[str, Optional[str]], origen: str, destino: str
) -> List[str]:
    """Reconstruye la ruta origen -> destino usando el arreglo previos[]."""
    if destino not in previos:
        return []
    camino: List[str] = []
    actual: Optional[str] = destino
    while actual is not None:
        camino.append(actual)
        if actual == origen:
            break
        actual = previos.get(actual)
    if not camino or camino[-1] != origen:
        return []
    camino.reverse()
    return camino


def dijkstra(
    grafo: Grafo, origen: str, destino: str
) -> Tuple[Optional[float], List[str]]:
    """
    Ruta de menor peso entre origen y destino.
    Retorna (distancia_total, camino) o (None, []) si no hay ruta.
    Complejidad: O((V + E) log V).
    """
    if not grafo.existe_nodo(origen) or not grafo.existe_nodo(destino):
        return None, []

    distancias: Dict[str, float] = {n: math.inf for n in grafo.adyacencia}
    previos: Dict[str, Optional[str]] = {n: None for n in grafo.adyacencia}
    distancias[origen] = 0.0

    cola: List[Tuple[float, str]] = [(0.0, origen)]

    while cola:
        d_actual, u = heapq.heappop(cola)
        if d_actual > distancias[u]:
            continue
        if u == destino:
            break
        for vecino, peso in grafo.adyacencia[u]:
            nueva = d_actual + peso
            if nueva < distancias[vecino]:
                distancias[vecino] = nueva
                previos[vecino] = u
                heapq.heappush(cola, (nueva, vecino))

    if math.isinf(distancias[destino]):
        return None, []

    return distancias[destino], _reconstruir_camino(previos, origen, destino)


def alcanzables_desde(grafo: Grafo, origen: str) -> List[str]:
    """
    Lista todas las ubicaciones alcanzables desde un origen
    (no incluye al propio origen). DFS iterativo con pila.
    Complejidad: O(V + E).
    """
    if not grafo.existe_nodo(origen):
        return []

    visitados: Dict[str, bool] = {n: False for n in grafo.adyacencia}
    pila: List[str] = [origen]
    visitados[origen] = True
    resultado: List[str] = []

    while pila:
        u = pila.pop()
        if u != origen:
            resultado.append(u)
        for vecino, _ in grafo.adyacencia[u]:
            if not visitados[vecino]:
                visitados[vecino] = True
                pila.append(vecino)

    return sorted(resultado)


# ======================================================================
# Carga desde archivo
# ======================================================================
def cargar_desde_archivo(ruta: str) -> Tuple[Grafo, int, int]:
    """
    Carga un grafo desde un archivo de texto.

    Formato:
      # comentario
      NODO <nombre>
      ARISTA <origen> <destino> <peso>

    Retorna (grafo, nodos_cargados, aristas_cargadas).
    """
    if not os.path.isfile(ruta):
        raise FileNotFoundError(f"No existe el archivo: {ruta}")

    grafo = Grafo()
    nodos_cargados = 0
    aristas_cargadas = 0

    with open(ruta, "r", encoding="utf-8") as f:
        for num_linea, linea_cruda in enumerate(f, start=1):
            linea = linea_cruda.strip()
            if not linea or linea.startswith("#"):
                continue
            partes = linea.split()
            tipo = partes[0].upper()

            if tipo == "NODO":
                if len(partes) != 2:
                    raise ValueError(
                        f"Línea {num_linea}: formato esperado 'NODO <nombre>'"
                    )
                if grafo.agregar_nodo(partes[1]):
                    nodos_cargados += 1

            elif tipo == "ARISTA":
                if len(partes) != 4:
                    raise ValueError(
                        f"Línea {num_linea}: formato esperado "
                        f"'ARISTA <origen> <destino> <peso>'"
                    )
                origen, destino, peso_txt = partes[1], partes[2], partes[3]
                try:
                    peso = float(peso_txt)
                except ValueError:
                    raise ValueError(
                        f"Línea {num_linea}: peso inválido '{peso_txt}'"
                    )
                grafo.agregar_arista(origen, destino, peso)
                aristas_cargadas += 1

            else:
                raise ValueError(
                    f"Línea {num_linea}: instrucción desconocida '{tipo}'"
                )

    return grafo, nodos_cargados, aristas_cargadas
