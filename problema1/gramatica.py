"""
Representacion de una gramatica libre de contexto y carga desde archivo.

Convenciones (segun el enunciado del laboratorio):
    - Letra mayuscula individual  -> no terminal.
    - Letra minuscula individual  -> terminal.
    - Digito individual           -> terminal (la Gramatica 1 usa 0 y 1).
    - ε                           -> cadena vacia (solo como cuerpo completo).
    - La cabeza de la primera linea es el simbolo inicial.

Un cuerpo de produccion se guarda como una tupla de simbolos; ε se guarda
como la tupla vacia ().
"""

from validador import EPSILON, FLECHAS, validar_linea


class ErrorGramatica(Exception):
    """Una linea del archivo no cumple la expresion regular de producciones."""

    def __init__(self, archivo, numero, linea, resultado):
        self.archivo = archivo
        self.numero = numero
        self.linea = linea
        self.posicion = resultado.posicion
        self.mensaje = resultado.mensaje
        super().__init__(
            "{}:{}: {} -> {!r}".format(archivo, numero, resultado.mensaje, linea)
        )


def es_no_terminal(simbolo):
    return len(simbolo) == 1 and "A" <= simbolo <= "Z"


def cuerpo_a_texto(cuerpo):
    return "".join(cuerpo) if cuerpo else EPSILON


class Gramatica:
    def __init__(self, inicial):
        self.inicial = inicial
        self.producciones = {}  # no terminal -> lista de cuerpos (tuplas), sin repetidos

    def agregar(self, cabeza, cuerpo):
        """Agrega A -> cuerpo. Devuelve False si la produccion ya existia."""
        cuerpos = self.producciones.setdefault(cabeza, [])
        if cuerpo in cuerpos:
            return False
        cuerpos.append(cuerpo)
        return True

    def no_terminales(self):
        """No terminales en orden de aparicion (cabezas primero, luego los de los cuerpos)."""
        vistos = list(self.producciones)
        for cuerpos in self.producciones.values():
            for cuerpo in cuerpos:
                for simbolo in cuerpo:
                    if es_no_terminal(simbolo) and simbolo not in vistos:
                        vistos.append(simbolo)
        return vistos

    def terminales(self):
        vistos = []
        for cuerpos in self.producciones.values():
            for cuerpo in cuerpos:
                for simbolo in cuerpo:
                    if not es_no_terminal(simbolo) and simbolo not in vistos:
                        vistos.append(simbolo)
        return vistos

    def sin_producciones(self):
        """No terminales que aparecen en algun cuerpo pero no tienen producciones."""
        return [x for x in self.no_terminales() if not self.producciones.get(x)]

    def lineas(self):
        """Representacion textual: una linea por no terminal con producciones."""
        return [
            "{} -> {}".format(cabeza, " | ".join(cuerpo_a_texto(c) for c in cuerpos))
            for cabeza, cuerpos in self.producciones.items()
            if cuerpos
        ]

    def __str__(self):
        return "\n".join(self.lineas())


def separar_linea(linea):
    """Separa una linea ya validada en (cabeza, [cuerpos])."""
    for flecha in FLECHAS:
        if flecha in linea:
            cabeza, resto = linea.split(flecha, 1)
            break
    cuerpos = []
    for alternativa in resto.split("|"):
        alternativa = alternativa.strip()
        cuerpos.append(() if alternativa == EPSILON else tuple(alternativa))
    return cabeza.strip(), cuerpos


def leer_lineas(ruta):
    """Lee el archivo y devuelve [(numero_de_linea, texto)] sin saltos de linea.

    Las lineas completamente vacias se omiten (no representan producciones).
    """
    with open(ruta, encoding="utf-8-sig") as archivo:
        contenido = archivo.read()
    return [
        (numero, texto)
        for numero, texto in enumerate(contenido.splitlines(), start=1)
        if texto.strip()
    ]


def validar_lineas(ruta, lineas, al_validar=None):
    """Valida todas las lineas; al primer error lanza ErrorGramatica.

    al_validar(numero, texto) se invoca por cada linea valida (para mostrar el progreso).
    """
    for numero, texto in lineas:
        resultado = validar_linea(texto)
        if not resultado.valida:
            raise ErrorGramatica(ruta, numero, texto, resultado)
        if al_validar:
            al_validar(numero, texto)


def construir_gramatica(lineas):
    """Construye la gramatica a partir de lineas ya validadas.

    Devuelve (gramatica, repetidas) donde repetidas es una lista de
    (numero_de_linea, cabeza, cuerpo) de producciones que ya existian.
    """
    gramatica = None
    repetidas = []
    for numero, texto in lineas:
        cabeza, cuerpos = separar_linea(texto)
        if gramatica is None:
            gramatica = Gramatica(cabeza)
        for cuerpo in cuerpos:
            if not gramatica.agregar(cabeza, cuerpo):
                repetidas.append((numero, cabeza, cuerpo))
    return gramatica, repetidas


def cargar_gramatica(ruta):
    """Lee, valida y construye la gramatica de un archivo (sin imprimir nada)."""
    lineas = leer_lineas(ruta)
    validar_lineas(ruta, lineas)
    return construir_gramatica(lineas)[0]
