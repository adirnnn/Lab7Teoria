"""
Validacion sintactica de las lineas de un archivo de gramatica.

Cada linea se valida con una expresion regular que se compila con el motor
propio (regex_engine.py: Shunting-Yard -> Thompson -> simulacion del AFN).

Estructura que reconoce la expresion regular:

    <espacios> NT <espacios> FLECHA <espacios> CUERPO ( <espacios> | <espacios> CUERPO )* <espacios>

    NT      : una letra mayuscula (simbolo no terminal de la cabeza)
    FLECHA  : "->" o "→"
    CUERPO  : uno o mas simbolos (mayusculas = no terminales,
              minusculas o digitos = terminales), o bien "ε" solo
"""

from regex_engine import compilar

NO_TERMINAL = "[A-Z]"
TERMINAL = "[a-z0-9]"
EPSILON = "ε"
FLECHAS = ("->", "→")
ESPACIOS = "[ \t]*"

CUERPO = "(({nt}|{t})+|{eps})".format(nt=NO_TERMINAL, t=TERMINAL, eps=EPSILON)
FLECHA = "(->|→)"

REGEX_PRODUCCION = (
    "{w}{nt}{w}{flecha}{w}{cuerpo}({w}\\|{w}{cuerpo})*{w}".format(
        w=ESPACIOS, nt=NO_TERMINAL, flecha=FLECHA, cuerpo=CUERPO
    )
)

_AFN = compilar(REGEX_PRODUCCION)


def afn_produccion():
    """AFN usado para validar (se expone para mostrarlo en pantalla)."""
    return _AFN


def _explicar_error(linea, posicion):
    """Da una explicacion legible de por que el AFN rechazo la linea."""
    contenido = linea.strip()
    if not contenido:
        return "la linea esta vacia"
    if posicion >= len(linea):
        if linea.rstrip().endswith("|"):
            return "falta un cuerpo de produccion despues del ultimo '|'"
        if not any(f in linea for f in FLECHAS):
            return "la linea termina sin la flecha de produccion '->'"
        return "la linea termina antes de completar una produccion (falta el cuerpo)"

    caracter = linea[posicion]
    antes = linea[:posicion]
    tiene_flecha = any(f in antes for f in FLECHAS)

    if not antes.strip():
        if caracter.isalpha() and caracter.islower():
            return "la cabeza de la produccion debe ser un no terminal (letra mayuscula), no '{}'".format(caracter)
        return "la linea debe iniciar con un no terminal (letra mayuscula), se encontro '{}'".format(caracter)
    if not tiene_flecha:
        if caracter.isupper() or caracter.islower() or caracter.isdigit():
            return "la cabeza debe ser una sola letra mayuscula seguida de '->'"
        return "se esperaba la flecha '->' y se encontro '{}'".format(caracter)
    if caracter == "|":
        return "alternativa vacia: '|' debe tener un cuerpo a cada lado (use ε para la cadena vacia)"
    if caracter == EPSILON or (antes.endswith(EPSILON) and caracter not in " \t|"):
        return "ε debe aparecer sola como cuerpo de una alternativa"
    if caracter in " \t" or (antes[-1] in " \t" and caracter.isalnum()):
        return "no se permiten espacios dentro de un cuerpo de produccion"
    if caracter in "->→":
        return "la flecha '->' solo puede aparecer una vez por linea"
    return "simbolo invalido '{}' (solo se permiten letras, digitos, ε y '|')".format(caracter)


class ResultadoValidacion:
    __slots__ = ("valida", "posicion", "mensaje")

    def __init__(self, valida, posicion=None, mensaje=None):
        self.valida = valida
        self.posicion = posicion
        self.mensaje = mensaje


def validar_linea(linea):
    """Valida una linea con el AFN construido a partir de la expresion regular."""
    acepta, posicion = _AFN.simular(linea)
    if acepta:
        return ResultadoValidacion(True)
    return ResultadoValidacion(False, posicion, _explicar_error(linea, posicion))
