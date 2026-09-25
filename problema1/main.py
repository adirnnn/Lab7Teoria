#!/usr/bin/env python3
"""
Laboratorio 7 - Problema 1
Carga de gramaticas desde archivos de texto, validacion de cada linea con una
expresion regular y eliminacion de producciones epsilon mostrando los pasos.

Uso:
    python main.py gramaticas/gramatica1.txt
    python main.py gramaticas/gramatica1.txt gramaticas/gramatica2.txt
    python main.py --mostrar-regex gramaticas/invalidas/error_cabeza.txt
"""

import argparse
import os
import sys

from epsilon import eliminar_epsilon, notas_resultado
from gramatica import ErrorGramatica, construir_gramatica, cuerpo_a_texto, leer_lineas, validar_lineas
from regex_engine import postfix_a_texto
from validador import REGEX_PRODUCCION, afn_produccion

COLORES = {
    "titulo": "\033[1;36m",
    "subtitulo": "\033[1m",
    "ok": "\033[32m",
    "aviso": "\033[33m",
    "error": "\033[1;31m",
    "tenue": "\033[2m",
    "normal": "",
}
FIN_COLOR = "\033[0m"


class Consola:
    def __init__(self, color):
        self.color = color

    def __call__(self, texto="", estilo="normal"):
        inicio = COLORES.get(estilo, "") if self.color else ""
        fin = FIN_COLOR if inicio else ""
        for linea in texto.split("\n"):
            print("{}{}{}".format(inicio, linea, fin))

    def encabezado(self, texto):
        self("=" * 72, "titulo")
        self(texto, "titulo")
        self("=" * 72, "titulo")


def configurar_consola():
    """Permite imprimir ε y colores ANSI tambien en la consola de Windows."""
    for flujo in (sys.stdout, sys.stderr):
        try:
            flujo.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass
    if os.name == "nt":
        os.system("")


def mostrar_expresion_regular(mostrar):
    afn = afn_produccion()
    mostrar("Expresion regular usada para validar cada linea:", "subtitulo")
    mostrar("  " + REGEX_PRODUCCION.replace("\t", "\\t"))
    mostrar("Postfix (Shunting-Yard):", "subtitulo")
    mostrar("  " + postfix_a_texto(afn.postfix).replace("\t", "\\t"))
    mostrar("AFN de Thompson: {} estados, inicial q{}, aceptacion q{}".format(
        len(afn.estados), afn.inicio.id, afn.aceptacion.id), "subtitulo")
    mostrar("", "normal")


def procesar_archivo(ruta, mostrar, mostrar_regex):
    """Procesa un archivo. Devuelve True si todo salio bien, False si hay que detenerse."""
    mostrar.encabezado("Archivo: {}".format(ruta))

    if not os.path.isfile(ruta):
        mostrar("ERROR: no se encontro el archivo '{}'.".format(ruta), "error")
        return False
    lineas = leer_lineas(ruta)
    if not lineas:
        mostrar("ERROR: el archivo no contiene producciones.", "error")
        return False

    # 1. Validacion sintactica -------------------------------------------------
    mostrar("VALIDACION DE LAS LINEAS", "titulo")
    if mostrar_regex:
        mostrar_expresion_regular(mostrar)

    def al_validar(numero, texto):
        mostrar("  Linea {:>2}: {:<32} valida".format(numero, texto.strip()), "ok")

    try:
        validar_lineas(ruta, lineas, al_validar)
    except ErrorGramatica as error:
        mostrar("  Linea {:>2}: {:<32} INVALIDA".format(error.numero, error.linea.strip()), "error")
        mostrar("", "normal")
        mostrar("ERROR de sintaxis en {}, linea {}, columna {}:".format(
            ruta, error.numero, error.posicion + 1), "error")
        mostrar("    " + error.linea.replace("\t", " "), "normal")
        mostrar("    " + " " * error.posicion + "^", "error")
        mostrar("    " + error.mensaje, "error")
        mostrar("", "normal")
        mostrar("La linea no cumple la expresion regular de producciones. Ejecucion detenida.", "error")
        return False
    mostrar("Todas las lineas son validas.", "ok")
    mostrar("", "normal")

    # 2. Gramatica leida -------------------------------------------------------
    gramatica, repetidas = construir_gramatica(lineas)
    mostrar("GRAMATICA CARGADA", "titulo")
    for linea in gramatica.lineas():
        mostrar("  " + linea)
    mostrar("  Simbolo inicial : {}".format(gramatica.inicial), "tenue")
    mostrar("  No terminales   : {}".format(", ".join(gramatica.no_terminales())), "tenue")
    mostrar("  Terminales      : {}".format(", ".join(gramatica.terminales()) or "(ninguno)"), "tenue")
    for numero, cabeza, cuerpo in repetidas:
        mostrar("  Aviso: linea {}: la produccion {} -> {} esta repetida; se toma una sola vez.".format(
            numero, cabeza, cuerpo_a_texto(cuerpo)), "aviso")
    for simbolo in gramatica.sin_producciones():
        mostrar("  Aviso: el no terminal {} aparece en un cuerpo pero no tiene producciones.".format(
            simbolo), "aviso")
    mostrar("", "normal")

    # 3. Eliminacion de producciones epsilon ------------------------------------
    mostrar("ELIMINACION DE PRODUCCIONES ε", "titulo")
    mostrar("", "normal")
    resultado, anulables = eliminar_epsilon(gramatica, mostrar)

    mostrar("", "normal")
    mostrar("GRAMATICA RESULTANTE (sin producciones ε)", "titulo")
    for linea in resultado.lineas():
        mostrar("  " + linea, "ok")
    for nota in notas_resultado(gramatica, resultado, anulables):
        mostrar("  Nota: " + nota, "aviso")
    mostrar("", "normal")
    return True


def main(argumentos=None):
    configurar_consola()
    parser = argparse.ArgumentParser(
        description="Carga gramaticas, valida cada linea con una expresion regular "
                    "y elimina las producciones epsilon mostrando los pasos.")
    parser.add_argument("archivos", nargs="+", help="archivos .txt con una gramatica cada uno")
    parser.add_argument("--mostrar-regex", action="store_true",
                        help="muestra la expresion regular, su postfix y el tamano del AFN")
    parser.add_argument("--sin-color", action="store_true", help="desactiva los colores ANSI")
    opciones = parser.parse_args(argumentos)

    color = not opciones.sin_color and sys.stdout.isatty() and "NO_COLOR" not in os.environ
    mostrar = Consola(color)

    for ruta in opciones.archivos:
        if not procesar_archivo(ruta, mostrar, opciones.mostrar_regex):
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
