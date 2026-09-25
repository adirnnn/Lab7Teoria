"""
Motor de expresiones regulares propio.

Sigue el mismo flujo del Proyecto 1 del curso:

    expresion regular (infix)
        -> tokens con concatenacion explicita
        -> postfix (algoritmo Shunting-Yard)
        -> AFN (construccion de Thompson)
        -> simulacion del AFN sobre una cadena

Operadores soportados:
    |        union
    *        cerradura de Kleene
    +        cerradura positiva
    ?        opcional (cero o una vez)
    ( )      agrupacion
    [a-z0-9] clase de caracteres (rangos y caracteres sueltos)
    \\x      escape: el caracter x se toma de forma literal
"""

CONCAT = "·"
UNARIOS = {"*", "+", "?"}
PRECEDENCIA = {"|": 1, CONCAT: 2, "*": 3, "+": 3, "?": 3}


class ErrorRegex(Exception):
    """La expresion regular esta mal formada."""


class Token:
    """Unidad lexica de la expresion regular.

    tipo:
        'SIM' -> simbolo del alfabeto (conjunto de caracteres aceptados)
        'OP'  -> operador ( | · * + ? )
        'PAR' -> parentesis ( ( o ) )
    """

    __slots__ = ("tipo", "valor", "texto")

    def __init__(self, tipo, valor, texto):
        self.tipo = tipo
        self.valor = valor
        self.texto = texto

    def __repr__(self):
        return "Token({}, {!r})".format(self.tipo, self.texto)


# ---------------------------------------------------------------------------
# 1. Analisis lexico
# ---------------------------------------------------------------------------

def _leer_clase(patron, i):
    """Lee una clase [..] que inicia en patron[i] == '['.

    Devuelve (conjunto_de_caracteres, indice_siguiente).
    """
    j = i + 1
    caracteres = set()
    while j < len(patron) and patron[j] != "]":
        if patron[j] == "\\":
            if j + 1 >= len(patron):
                raise ErrorRegex("escape incompleto dentro de la clase en la posicion {}".format(j))
            caracteres.add(patron[j + 1])
            j += 2
        elif j + 2 < len(patron) and patron[j + 1] == "-" and patron[j + 2] != "]":
            inicio, fin = patron[j], patron[j + 2]
            if ord(inicio) > ord(fin):
                raise ErrorRegex("rango invalido '{}-{}' en la clase".format(inicio, fin))
            caracteres.update(chr(k) for k in range(ord(inicio), ord(fin) + 1))
            j += 3
        else:
            caracteres.add(patron[j])
            j += 1
    if j >= len(patron):
        raise ErrorRegex("clase de caracteres sin cerrar desde la posicion {}".format(i))
    if not caracteres:
        raise ErrorRegex("clase de caracteres vacia en la posicion {}".format(i))
    return frozenset(caracteres), j + 1


def tokenizar(patron):
    """Convierte el patron en una lista de tokens (sin concatenacion explicita)."""
    tokens = []
    i = 0
    while i < len(patron):
        c = patron[i]
        if c == "\\":
            if i + 1 >= len(patron):
                raise ErrorRegex("escape incompleto al final del patron")
            tokens.append(Token("SIM", frozenset(patron[i + 1]), patron[i:i + 2]))
            i += 2
        elif c == "[":
            conjunto, siguiente = _leer_clase(patron, i)
            tokens.append(Token("SIM", conjunto, patron[i:siguiente]))
            i = siguiente
        elif c == "]":
            raise ErrorRegex("']' sin '[' correspondiente en la posicion {}".format(i))
        elif c in "|*+?":
            tokens.append(Token("OP", c, c))
            i += 1
        elif c in "()":
            tokens.append(Token("PAR", c, c))
            i += 1
        else:
            tokens.append(Token("SIM", frozenset(c), c))
            i += 1
    return tokens


def insertar_concatenacion(tokens):
    """Agrega el operador de concatenacion explicito entre tokens adyacentes."""
    resultado = []
    for k, actual in enumerate(tokens):
        resultado.append(actual)
        if k + 1 == len(tokens):
            break
        siguiente = tokens[k + 1]
        izquierda_cierra = (
            actual.tipo == "SIM"
            or (actual.tipo == "PAR" and actual.valor == ")")
            or (actual.tipo == "OP" and actual.valor in UNARIOS)
        )
        derecha_abre = siguiente.tipo == "SIM" or (siguiente.tipo == "PAR" and siguiente.valor == "(")
        if izquierda_cierra and derecha_abre:
            resultado.append(Token("OP", CONCAT, CONCAT))
    return resultado


# ---------------------------------------------------------------------------
# 2. Shunting-Yard: infix -> postfix
# ---------------------------------------------------------------------------

def a_postfix(tokens):
    """Algoritmo Shunting-Yard. Recibe tokens con concatenacion explicita."""
    salida = []
    pila = []
    for token in tokens:
        if token.tipo == "SIM":
            salida.append(token)
        elif token.tipo == "PAR" and token.valor == "(":
            pila.append(token)
        elif token.tipo == "PAR" and token.valor == ")":
            while pila and not (pila[-1].tipo == "PAR" and pila[-1].valor == "("):
                salida.append(pila.pop())
            if not pila:
                raise ErrorRegex("parentesis ')' sin pareja")
            pila.pop()
        elif token.valor in UNARIOS:
            # Operador unario posfijo con la mayor precedencia: va directo a la salida.
            salida.append(token)
        else:
            while (
                pila
                and pila[-1].tipo == "OP"
                and PRECEDENCIA[pila[-1].valor] >= PRECEDENCIA[token.valor]
            ):
                salida.append(pila.pop())
            pila.append(token)
    while pila:
        token = pila.pop()
        if token.tipo == "PAR":
            raise ErrorRegex("parentesis '(' sin cerrar")
        salida.append(token)
    return salida


def postfix_a_texto(postfix):
    return " ".join(t.texto for t in postfix)


# ---------------------------------------------------------------------------
# 3. Construccion de Thompson: postfix -> AFN
# ---------------------------------------------------------------------------

class Estado:
    __slots__ = ("id", "transiciones", "epsilon")

    def __init__(self, identificador):
        self.id = identificador
        self.transiciones = []  # lista de (conjunto_de_caracteres, Estado)
        self.epsilon = []       # lista de Estado


class AFN:
    def __init__(self, inicio, aceptacion, estados, postfix):
        self.inicio = inicio
        self.aceptacion = aceptacion
        self.estados = estados
        self.postfix = postfix

    # -- simulacion ---------------------------------------------------------

    def _cerradura(self, estados):
        pila = list(estados)
        visitados = set(estados)
        while pila:
            estado = pila.pop()
            for destino in estado.epsilon:
                if destino not in visitados:
                    visitados.add(destino)
                    pila.append(destino)
        return visitados

    def _mover(self, estados, caracter):
        destinos = set()
        for estado in estados:
            for conjunto, destino in estado.transiciones:
                if caracter in conjunto:
                    destinos.add(destino)
        return destinos

    def simular(self, cadena):
        """Simula el AFN sobre la cadena completa.

        Devuelve (acepta, posicion_error):
            acepta          -> True si la cadena completa es aceptada.
            posicion_error  -> None si acepta; si no, el indice del primer
                               caracter que el AFN no pudo consumir, o
                               len(cadena) si la cadena termino antes de
                               llegar a un estado de aceptacion.
        """
        actuales = self._cerradura({self.inicio})
        for indice, caracter in enumerate(cadena):
            actuales = self._cerradura(self._mover(actuales, caracter))
            if not actuales:
                return False, indice
        if self.aceptacion in actuales:
            return True, None
        return False, len(cadena)

    def acepta(self, cadena):
        return self.simular(cadena)[0]


def construir_afn(postfix):
    contador = [0]
    estados = []

    def nuevo():
        estado = Estado(contador[0])
        contador[0] += 1
        estados.append(estado)
        return estado

    pila = []
    for token in postfix:
        if token.tipo == "SIM":
            inicio, fin = nuevo(), nuevo()
            inicio.transiciones.append((token.valor, fin))
            pila.append((inicio, fin))
            continue

        operador = token.valor
        requeridos = 1 if operador in UNARIOS else 2
        if len(pila) < requeridos:
            raise ErrorRegex("faltan operandos para el operador '{}'".format(operador))

        if operador == CONCAT:
            (i2, f2), (i1, f1) = pila.pop(), pila.pop()
            f1.epsilon.append(i2)
            pila.append((i1, f2))
        elif operador == "|":
            (i2, f2), (i1, f1) = pila.pop(), pila.pop()
            inicio, fin = nuevo(), nuevo()
            inicio.epsilon.extend([i1, i2])
            f1.epsilon.append(fin)
            f2.epsilon.append(fin)
            pila.append((inicio, fin))
        elif operador == "*":
            i1, f1 = pila.pop()
            inicio, fin = nuevo(), nuevo()
            inicio.epsilon.extend([i1, fin])
            f1.epsilon.extend([i1, fin])
            pila.append((inicio, fin))
        elif operador == "+":
            i1, f1 = pila.pop()
            inicio, fin = nuevo(), nuevo()
            inicio.epsilon.append(i1)
            f1.epsilon.extend([i1, fin])
            pila.append((inicio, fin))
        elif operador == "?":
            i1, f1 = pila.pop()
            inicio, fin = nuevo(), nuevo()
            inicio.epsilon.extend([i1, fin])
            f1.epsilon.append(fin)
            pila.append((inicio, fin))

    if len(pila) != 1:
        raise ErrorRegex("expresion regular incompleta (sobran operandos)")
    inicio, fin = pila.pop()
    return AFN(inicio, fin, estados, postfix)


def compilar(patron):
    """Compila un patron completo a un AFN listo para simular."""
    if not patron:
        raise ErrorRegex("el patron esta vacio")
    tokens = insertar_concatenacion(tokenizar(patron))
    postfix = a_postfix(tokens)
    return construir_afn(postfix)
