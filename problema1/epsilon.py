"""
Eliminacion de producciones epsilon, mostrando cada paso del algoritmo.

Paso 1. Encontrar los simbolos anulables (A =>* ε):
        - Base: A es anulable si existe A -> ε.
        - Induccion: A es anulable si existe A -> X1 X2 ... Xk con todos
          los Xi anulables. Se repite por rondas hasta que no cambie.
Paso 2. Por cada produccion A -> α con m ocurrencias de simbolos
        anulables, generar los 2^m casos (cada ocurrencia se conserva o
        se omite).
Paso 3. Construir la nueva gramatica: se agregan todos los cuerpos
        generados excepto ε, y se eliminan las producciones A -> ε.

Todas las funciones reciben `mostrar(texto, estilo)` para imprimir los
pasos; estilo es uno de: 'titulo', 'subtitulo', 'normal', 'ok', 'aviso',
'tenue'.
"""

from gramatica import EPSILON, Gramatica, cuerpo_a_texto


def _sin_salida(texto="", estilo="normal"):
    pass


def _conjunto(simbolos):
    return "{ " + ", ".join(simbolos) + " }" if simbolos else "∅"


# ---------------------------------------------------------------------------
# Paso 1: simbolos anulables
# ---------------------------------------------------------------------------

def calcular_anulables(gramatica, mostrar=_sin_salida):
    mostrar("PASO 1: encontrar los simbolos anulables", "titulo")
    mostrar("Un no terminal A es anulable si A =>* ε.", "tenue")

    anulables = []
    directos = [a for a, cuerpos in gramatica.producciones.items() if () in cuerpos]
    mostrar("Ronda 0 (base: producciones A -> ε):", "subtitulo")
    if directos:
        for a in directos:
            mostrar("  {} es anulable porque existe {} -> {}".format(a, a, EPSILON))
    else:
        mostrar("  No hay producciones A -> ε.")
    anulables.extend(directos)
    mostrar("  Anulables = {}".format(_conjunto(anulables)))

    ronda = 0
    while True:
        ronda += 1
        conocidos = set(anulables)
        nuevos = []
        for a, cuerpos in gramatica.producciones.items():
            if a in conocidos:
                continue
            for cuerpo in cuerpos:
                if cuerpo and all(s in conocidos for s in cuerpo):
                    nuevos.append((a, cuerpo))
                    break
        mostrar("Ronda {} (induccion: A -> X1...Xk con todos los Xi anulables):".format(ronda), "subtitulo")
        if not nuevos:
            mostrar("  No se agregan simbolos nuevos: el conjunto ya no cambia.")
            break
        for a, cuerpo in nuevos:
            mostrar(
                "  {} es anulable porque {} -> {} y {} {} anulable{}".format(
                    a,
                    a,
                    cuerpo_a_texto(cuerpo),
                    ", ".join(dict.fromkeys(cuerpo)),
                    "es" if len(set(cuerpo)) == 1 else "son",
                    "" if len(set(cuerpo)) == 1 else "s",
                )
            )
            anulables.append(a)
        mostrar("  Anulables = {}".format(_conjunto(anulables)))

    mostrar("Simbolos anulables: {}".format(_conjunto(anulables)), "ok")
    return anulables


def _lista_producciones(producciones):
    return ", ".join("{} -> {}".format(a, cuerpo_a_texto(c)) for a, c in producciones) or "(ninguna)"


def mostrar_producciones_anulables(gramatica, anulables, mostrar=_sin_salida):
    mostrar("Producciones anulables (todo su cuerpo deriva ε):", "subtitulo")
    mostrar("  " + _lista_producciones(producciones_anulables(gramatica, anulables)))
    mostrar("Producciones que contienen simbolos anulables (se expanden en el paso 2):", "subtitulo")
    mostrar("  " + _lista_producciones(producciones_con_anulables(gramatica, anulables)))


def producciones_anulables(gramatica, anulables):
    """Producciones A -> α cuyo cuerpo completo puede derivar ε (α = ε o todos sus simbolos anulables)."""
    conjunto = set(anulables)
    return [
        (a, cuerpo)
        for a, cuerpos in gramatica.producciones.items()
        for cuerpo in cuerpos
        if all(s in conjunto for s in cuerpo)
    ]


def producciones_con_anulables(gramatica, anulables):
    """Producciones A -> α (α != ε) que contienen al menos un simbolo anulable."""
    conjunto = set(anulables)
    return [
        (a, cuerpo)
        for a, cuerpos in gramatica.producciones.items()
        for cuerpo in cuerpos
        if cuerpo and any(s in conjunto for s in cuerpo)
    ]


# ---------------------------------------------------------------------------
# Paso 2: los 2^m casos de cada produccion
# ---------------------------------------------------------------------------

def generar_casos(cuerpo, anulables):
    """Genera los 2^m casos de un cuerpo con m ocurrencias anulables.

    Devuelve (posiciones, casos) donde cada caso es (conserva, resultado):
        conserva  -> tupla de booleanos, uno por ocurrencia anulable
                     (True = se conserva, False = se omite)
        resultado -> cuerpo resultante (tupla; () representa ε)
    El primer caso conserva todo y el ultimo omite todas las ocurrencias.
    """
    conjunto = set(anulables)
    posiciones = [i for i, s in enumerate(cuerpo) if s in conjunto]
    m = len(posiciones)
    casos = []
    for mascara in range(2 ** m):
        conserva = tuple(not (mascara >> (m - 1 - j)) & 1 for j in range(m))
        omitidas = {posiciones[j] for j in range(m) if not conserva[j]}
        resultado = tuple(s for i, s in enumerate(cuerpo) if i not in omitidas)
        casos.append((conserva, resultado))
    return posiciones, casos


def _vista(cuerpo, posiciones, conserva):
    """Muestra el cuerpo con las ocurrencias omitidas reemplazadas por '_'."""
    omitidas = {posiciones[j] for j, c in enumerate(conserva) if not c}
    return " ".join("_" if i in omitidas else s for i, s in enumerate(cuerpo))


def _subindices(cuerpo, posiciones):
    """Etiqueta cada ocurrencia anulable: B1, B2, ... cuando un simbolo se repite."""
    conteo = {}
    for i in posiciones:
        conteo[cuerpo[i]] = conteo.get(cuerpo[i], 0) + 1
    vistos = {}
    etiquetas = []
    for i in posiciones:
        s = cuerpo[i]
        vistos[s] = vistos.get(s, 0) + 1
        etiquetas.append("{}{}".format(s, vistos[s]) if conteo[s] > 1 else s)
    return etiquetas


# ---------------------------------------------------------------------------
# Paso 3: nueva gramatica
# ---------------------------------------------------------------------------

def eliminar_epsilon(gramatica, mostrar=_sin_salida):
    """Devuelve (gramatica_sin_epsilon, anulables) mostrando todos los pasos."""
    anulables = calcular_anulables(gramatica, mostrar)
    mostrar_producciones_anulables(gramatica, anulables, mostrar)
    conjunto = set(anulables)

    mostrar("", "normal")
    mostrar("PASO 2: generar las alternativas de cada produccion (2^m casos)", "titulo")
    mostrar(
        "Para A -> α con m ocurrencias de simbolos anulables se prueban los 2^m casos:\n"
        "cada ocurrencia se conserva (1) o se omite (0). El caso que deja ε se descarta.",
        "tenue",
    )

    nueva = Gramatica(gramatica.inicial)
    for a, cuerpos in gramatica.producciones.items():
        # Se registra la cabeza aunque quede sin producciones, para conservar el orden.
        nueva.producciones.setdefault(a, [])
        for cuerpo in cuerpos:
            if not cuerpo:
                continue
            posiciones = [i for i, s in enumerate(cuerpo) if s in conjunto]
            if not posiciones:
                nueva.agregar(a, cuerpo)
                continue

            m = len(posiciones)
            etiquetas = _subindices(cuerpo, posiciones)
            mostrar("", "normal")
            mostrar(
                "{} -> {}   (m = {}: {}; 2^{} = {} casos)".format(
                    a, cuerpo_a_texto(cuerpo), m, ", ".join(etiquetas), m, 2 ** m
                ),
                "subtitulo",
            )
            _, casos = generar_casos(cuerpo, anulables)
            w1 = max(len(" ".join(etiquetas)), len("caso"))
            w2 = max(len(" ".join(cuerpo)), len("cuerpo"))
            w3 = max(len(cuerpo), len("resultado"))
            mostrar(
                "  {:>4}  {:<{w1}}  {:<{w2}}  {:<{w3}}  {}".format(
                    "caso", " ".join(etiquetas), "cuerpo", "resultado", "observacion",
                    w1=w1, w2=w2, w3=w3,
                ),
                "tenue",
            )
            for numero, (conserva, resultado) in enumerate(casos, start=1):
                bits = " ".join(
                    "{:<{w}}".format("1" if c else "0", w=len(e)) for c, e in zip(conserva, etiquetas)
                )
                if not resultado:
                    observacion, estilo = "es ε: se descarta", "aviso"
                elif not nueva.agregar(a, resultado):
                    observacion, estilo = "repetida: ya se agrego", "tenue"
                elif resultado == (a,):
                    observacion, estilo = "nueva (unitaria {} -> {}, no aporta)".format(a, a), "normal"
                else:
                    observacion, estilo = "nueva", "normal"
                mostrar(
                    "  {:>4}  {:<{w1}}  {:<{w2}}  {:<{w3}}  {}".format(
                        numero, bits, _vista(cuerpo, posiciones, conserva), cuerpo_a_texto(resultado),
                        observacion,
                        w1=w1, w2=w2, w3=w3,
                    ),
                    estilo,
                )

    mostrar("", "normal")
    mostrar("PASO 3: eliminar las producciones ε y armar la nueva gramatica", "titulo")
    eliminadas = [a for a, cuerpos in gramatica.producciones.items() if () in cuerpos]
    if eliminadas:
        for a in eliminadas:
            mostrar("  Se elimina {} -> {}".format(a, EPSILON))
    else:
        mostrar("  La gramatica no tenia producciones ε.")
    mostrar("  Las producciones sin simbolos anulables se copian sin cambios.")

    return nueva, anulables


def notas_resultado(original, resultado, anulables):
    """Observaciones sobre la gramatica resultante (se muestran junto al resultado)."""
    notas = []
    if original.inicial in anulables:
        notas.append(
            "El simbolo inicial {} es anulable, por lo que ε ∈ L(G). La gramatica "
            "resultante genera L(G) - {{ε}}.".format(original.inicial)
        )
    vacios = [a for a, cuerpos in resultado.producciones.items() if not cuerpos]
    for a in vacios:
        notas.append(
            "{} solo producia ε: se queda sin producciones. Los cuerpos que aun lo "
            "contienen no generan cadenas y se quitan al eliminar simbolos inutiles.".format(a)
        )
    for a in original.sin_producciones():
        notas.append(
            "{} aparece en los cuerpos pero no tiene producciones en el archivo; por "
            "eso no es anulable y se conserva tal cual.".format(a)
        )
    unitarias = [a for a, cuerpos in resultado.producciones.items() if (a,) in cuerpos]
    for a in unitarias:
        notas.append(
            "Se genero la produccion {} -> {}; no cambia el lenguaje y desaparece al "
            "eliminar producciones unitarias.".format(a, a)
        )
    return notas
