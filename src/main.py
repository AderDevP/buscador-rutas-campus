"""
main.py
-------
Punto de entrada y menú interactivo del Buscador de Rutas del Campus.

Operaciones (según enunciado):
  1. Cargar ubicaciones y conexiones desde archivo.
  2. Agregar una ubicación.
  3. Eliminar una ubicación.
  4. Agregar una ruta entre dos ubicaciones con su peso.
  5. Eliminar una ruta entre dos ubicaciones.
  6. Calcular la ruta más corta entre dos puntos (Dijkstra).
  7. Listar todas las ubicaciones alcanzables desde un origen.
  8. Mostrar la representación interna del grafo (lista o matriz).
  0. Salir.

El menú usa colores ANSI a través de la librería estándar. En Windows, la
llamada `os.system("")` activa el procesamiento de secuencias ANSI en la
consola sin necesidad de instalar paquetes externos.
"""

from __future__ import annotations

import os
import sys
from typing import Optional

from grafo import (
    Grafo,
    alcanzables_desde,
    cargar_desde_archivo,
    dijkstra,
)


# ============================== Colores =================================
def _activar_colores_windows() -> None:
    """Habilita el procesamiento ANSI en consolas de Windows."""
    if os.name == "nt":
        # Truco estándar: una llamada vacía a la API del sistema activa el
        # Virtual Terminal Processing en cmd.exe y PowerShell modernos.
        os.system("")


_activar_colores_windows()


class C:
    """Códigos ANSI usados por el menú."""
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"

    # Foreground
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"

    # Brillantes
    BRIGHT_CYAN = "\033[96m"
    BRIGHT_GREEN = "\033[92m"
    BRIGHT_YELLOW = "\033[93m"
    BRIGHT_RED = "\033[91m"
    BRIGHT_MAGENTA = "\033[95m"


def _ok(msg: str) -> None:
    print(f"  {C.BRIGHT_GREEN}[OK]{C.RESET} {msg}")


def _err(msg: str) -> None:
    print(f"  {C.BRIGHT_RED}[!]{C.RESET}  {msg}")


def _info(msg: str) -> None:
    print(f"  {C.CYAN}{msg}{C.RESET}")


# ============================== Banner ==================================
BANNER = f"""
{C.BRIGHT_CYAN}╔══════════════════════════════════════════════════════════╗
║         BUSCADOR DE RUTAS DEL CAMPUS                     ║
║         Estructura de Datos · Pascual Bravo · 2026-1     ║
╚══════════════════════════════════════════════════════════╝{C.RESET}
"""


def _construir_menu() -> str:
    """Devuelve el menú coloreado. Se construye dinámico para usar C.*"""
    op = lambda n, t: (
        f" {C.BRIGHT_YELLOW}{n:>2}{C.RESET}. {t}"
    )
    salir = f" {C.BRIGHT_RED} 0{C.RESET}. {C.DIM}Salir{C.RESET}"
    sep = f"{C.DIM}{'─' * 60}{C.RESET}"

    return "\n".join([
        BANNER,
        sep,
        op(1, "Cargar ubicaciones y conexiones desde archivo"),
        op(2, "Agregar ubicación"),
        op(3, "Eliminar ubicación"),
        op(4, "Agregar ruta entre dos ubicaciones (con peso)"),
        op(5, "Eliminar ruta entre dos ubicaciones"),
        op(6, f"{C.BOLD}Ruta más corta{C.RESET} entre dos puntos (Dijkstra)"),
        op(7, "Listar ubicaciones alcanzables desde un origen"),
        op(8, "Mostrar representación interna del grafo"),
        salir,
        sep,
    ])


# =============================== Entrada ================================
def _input_str(msg: str) -> str:
    return input(f"{C.BRIGHT_CYAN}{msg}{C.RESET}").strip()


def _input_float(msg: str) -> Optional[float]:
    raw = input(f"{C.BRIGHT_CYAN}{msg}{C.RESET}").strip()
    try:
        return float(raw)
    except ValueError:
        _err(f"Valor numérico inválido: '{raw}'")
        return None


def _formatear_camino(camino: list) -> str:
    if not camino:
        return f"{C.DIM}(sin camino){C.RESET}"
    flecha = f" {C.BRIGHT_MAGENTA}→{C.RESET} "
    return flecha.join(f"{C.BOLD}{n}{C.RESET}" for n in camino)


def _ruta_default_datos() -> str:
    """Calcula la ruta de data/campus.txt relativa a la raíz del proyecto."""
    aqui = os.path.dirname(os.path.abspath(__file__))
    raiz = os.path.dirname(aqui)
    return os.path.join(raiz, "data", "campus.txt")


def _resumen_estado(grafo: Grafo) -> str:
    return (
        f"  {C.DIM}Estado actual:{C.RESET} "
        f"{C.GREEN}{grafo.numero_nodos()}{C.RESET} nodos, "
        f"{C.GREEN}{grafo.numero_aristas()}{C.RESET} aristas"
    )


# ================================ Menú ==================================
def ejecutar(grafo: Grafo, ruta_default: str) -> None:
    menu = _construir_menu()

    while True:
        print(menu)
        print(_resumen_estado(grafo))
        opcion = _input_str("Seleccione una opción: ")

        if opcion == "1":
            ruta = _input_str(
                f"Ruta del archivo [{C.DIM}{ruta_default}{C.RESET}]: "
            ) or ruta_default
            try:
                nuevo, n, e = cargar_desde_archivo(ruta)
                grafo.adyacencia = nuevo.adyacencia
                _ok(f"Cargado: {C.BOLD}{n}{C.RESET} nodos y "
                    f"{C.BOLD}{e}{C.RESET} aristas.")
            except (FileNotFoundError, ValueError) as ex:
                _err(f"Error al cargar: {ex}")

        elif opcion == "2":
            nombre = _input_str("Nombre de la ubicación: ")
            try:
                if grafo.agregar_nodo(nombre):
                    _ok(f"Ubicación '{C.BOLD}{nombre}{C.RESET}' agregada.")
                else:
                    _err(f"La ubicación '{nombre}' ya existía.")
            except ValueError as ex:
                _err(str(ex))

        elif opcion == "3":
            nombre = _input_str("Nombre de la ubicación a eliminar: ")
            if grafo.eliminar_nodo(nombre):
                _ok(f"Ubicación '{C.BOLD}{nombre}{C.RESET}' eliminada.")
            else:
                _err(f"La ubicación '{nombre}' no existe.")

        elif opcion == "4":
            origen = _input_str("Origen: ")
            destino = _input_str("Destino: ")
            peso = _input_float("Peso (metros o segundos): ")
            if peso is None:
                continue
            try:
                grafo.agregar_arista(origen, destino, peso)
                _ok(f"Ruta {C.BOLD}{origen}{C.RESET} ↔ "
                    f"{C.BOLD}{destino}{C.RESET} con peso "
                    f"{C.BRIGHT_YELLOW}{peso:g}{C.RESET}.")
            except ValueError as ex:
                _err(str(ex))

        elif opcion == "5":
            origen = _input_str("Origen: ")
            destino = _input_str("Destino: ")
            if grafo.eliminar_arista(origen, destino):
                _ok(f"Ruta {C.BOLD}{origen}{C.RESET} ↔ "
                    f"{C.BOLD}{destino}{C.RESET} eliminada.")
            else:
                _err("No existe esa ruta.")

        elif opcion == "6":
            origen = _input_str("Origen: ")
            destino = _input_str("Destino: ")
            distancia, camino = dijkstra(grafo, origen, destino)
            if distancia is None:
                _err(f"No hay ruta entre '{origen}' y '{destino}'.")
            else:
                _ok(f"Distancia mínima: "
                    f"{C.BRIGHT_YELLOW}{distancia:g}{C.RESET}")
                print(f"       Camino: {_formatear_camino(camino)}")

        elif opcion == "7":
            origen = _input_str("Origen: ")
            if not grafo.existe_nodo(origen):
                _err(f"La ubicación '{origen}' no existe.")
                continue
            res = alcanzables_desde(grafo, origen)
            if not res:
                _info(f"No hay ubicaciones alcanzables desde '{origen}'.")
            else:
                _ok(f"Alcanzables desde '{C.BOLD}{origen}{C.RESET}' "
                    f"({C.BRIGHT_YELLOW}{len(res)}{C.RESET}):")
                for n in res:
                    print(f"    {C.BRIGHT_MAGENTA}•{C.RESET} {n}")

        elif opcion == "8":
            print(f"  {C.CYAN}¿Qué representación desea ver?{C.RESET}")
            print(f"    {C.BRIGHT_YELLOW}a{C.RESET}) Lista de adyacencia")
            print(f"    {C.BRIGHT_YELLOW}b{C.RESET}) Matriz de adyacencia")
            sub = _input_str("Opción [a/b]: ").lower()
            print()
            if sub == "a":
                print(f"{C.BRIGHT_CYAN}{grafo.representacion_lista()}{C.RESET}")
            elif sub == "b":
                print(f"{C.BRIGHT_CYAN}{grafo.representacion_matriz()}{C.RESET}")
            else:
                _err(f"Opción no válida: '{sub}'")

        elif opcion == "0":
            print(f"  {C.BRIGHT_GREEN}Hasta luego.{C.RESET}")
            return

        else:
            _err(f"Opción no válida: '{opcion}'")


# ============================ Entry point ==============================
def main() -> int:
    ruta_default = _ruta_default_datos()
    grafo = Grafo()

    if os.path.isfile(ruta_default):
        try:
            grafo, n, e = cargar_desde_archivo(ruta_default)
            print(f"{C.DIM}[Inicio]{C.RESET} Cargado "
                  f"'{ruta_default}': {C.BOLD}{n}{C.RESET} nodos y "
                  f"{C.BOLD}{e}{C.RESET} aristas.")
        except (FileNotFoundError, ValueError) as ex:
            _err(f"No se pudo cargar el archivo por defecto: {ex}")
            grafo = Grafo()
    else:
        _info(f"No se encontró '{ruta_default}'. Iniciando con grafo vacío.")

    try:
        ejecutar(grafo, ruta_default)
    except (KeyboardInterrupt, EOFError):
        print(f"\n{C.DIM}[Salida]{C.RESET} Interrumpido por el usuario.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
