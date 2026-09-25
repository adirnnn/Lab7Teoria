import glob
import io
import os
import re
import sys
import unittest
from contextlib import redirect_stdout

RAIZ = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, RAIZ)

import main  # noqa: E402
from epsilon import calcular_anulables, eliminar_epsilon, generar_casos  # noqa: E402
from gramatica import ErrorGramatica, cargar_gramatica  # noqa: E402
from validador import REGEX_PRODUCCION, validar_linea  # noqa: E402


def ruta(nombre):
    return os.path.join(RAIZ, "gramaticas", nombre)


class TestValidador(unittest.TestCase):
    VALIDAS = [
        "S -> 0A0 | 1B1 | BB",
        "C -> S | ε",
        "S->aAa|bBb|ε",
        "  A  ->  C  |  a  ",
        "S → ε",
        "D -> A | B | ab",
    ]
    INVALIDAS = [
        "s -> a",
        "SA -> a",
        "S - > a",
        "S => a",
        "S -> a b",
        "S -> a||b",
        "S -> | a",
        "S -> a |",
        "S ->",
        "S",
        "S -> aε",
        "S -> εa",
        "S -> a$",
        "S -> a -> b",
        "-> a",
        "",
    ]

    def test_lineas_validas(self):
        for linea in self.VALIDAS:
            with self.subTest(linea=linea):
                self.assertTrue(validar_linea(linea).valida)

    def test_lineas_invalidas(self):
        for linea in self.INVALIDAS:
            with self.subTest(linea=linea):
                resultado = validar_linea(linea)
                self.assertFalse(resultado.valida)
                self.assertTrue(resultado.mensaje)

    def test_equivalente_al_modulo_re(self):
        esperado = re.compile(REGEX_PRODUCCION)
        for linea in self.VALIDAS + self.INVALIDAS:
            with self.subTest(linea=linea):
                self.assertEqual(validar_linea(linea).valida, esperado.fullmatch(linea) is not None)


def como_texto(gramatica):
    return {a: sorted("".join(c) for c in cuerpos) for a, cuerpos in gramatica.producciones.items() if cuerpos}


class TestEliminacionEpsilon(unittest.TestCase):
    def test_gramatica_1(self):
        g = cargar_gramatica(ruta("gramatica1.txt"))
        self.assertEqual(calcular_anulables(g), ["C", "A", "B", "S"])
        resultado, _ = eliminar_epsilon(g)
        self.assertEqual(como_texto(resultado), {
            "S": sorted(["0A0", "00", "1B1", "11", "BB", "B"]),
            "A": ["C"],
            "B": ["A", "S"],
            "C": ["S"],
        })

    def test_gramatica_2(self):
        g = cargar_gramatica(ruta("gramatica2.txt"))
        self.assertEqual(g.sin_producciones(), ["E"])
        self.assertEqual(set(calcular_anulables(g)), {"S", "A", "B", "C", "D"})
        resultado, _ = eliminar_epsilon(g)
        self.assertEqual(como_texto(resultado), {
            "S": sorted(["aAa", "aa", "bBb", "bb"]),
            "A": ["C", "a"],
            "B": ["C", "b"],
            "C": sorted(["CDE", "CE", "DE", "E"]),
            "D": sorted(["A", "B", "ab"]),
        })

    def test_gramatica_3(self):
        g = cargar_gramatica(ruta("gramatica3.txt"))
        self.assertEqual(calcular_anulables(g), ["B", "A"])
        resultado, _ = eliminar_epsilon(g)
        self.assertEqual(como_texto(resultado), {
            "S": sorted(["ASA", "AS", "SA", "S", "aB", "a"]),
            "A": sorted(["B", "S"]),
            "B": ["b"],
        })

    def test_dos_a_la_m_casos(self):
        posiciones, casos = generar_casos(tuple("ABaB"), ["A", "B"])
        self.assertEqual(posiciones, [0, 1, 3])
        self.assertEqual(len(casos), 8)
        resultados = ["".join(r) for _, r in casos]
        self.assertEqual(resultados, ["ABaB", "ABa", "AaB", "Aa", "BaB", "Ba", "aB", "a"])

    def test_resultado_sin_producciones_epsilon(self):
        for archivo in ("gramatica1.txt", "gramatica2.txt", "gramatica3.txt"):
            resultado, _ = eliminar_epsilon(cargar_gramatica(ruta(archivo)))
            for cuerpos in resultado.producciones.values():
                self.assertNotIn((), cuerpos)


def cadenas_hasta(gramatica, n):
    """Todas las cadenas de longitud <= n que genera la gramatica (punto fijo)."""
    lenguaje = {a: set() for a in gramatica.no_terminales()}
    cambio = True
    while cambio:
        cambio = False
        for a, cuerpos in gramatica.producciones.items():
            for cuerpo in cuerpos:
                parciales = {""}
                for simbolo in cuerpo:
                    opciones = lenguaje[simbolo] if simbolo in lenguaje else {simbolo}
                    parciales = {p + o for p in parciales for o in opciones if len(p + o) <= n}
                nuevas = parciales - lenguaje[a]
                if nuevas:
                    lenguaje[a] |= nuevas
                    cambio = True
    return lenguaje[gramatica.inicial]


class TestEquivalencia(unittest.TestCase):
    def test_mismo_lenguaje_sin_epsilon(self):
        for archivo in ("gramatica1.txt", "gramatica2.txt", "gramatica3.txt"):
            with self.subTest(archivo=archivo):
                original = cargar_gramatica(ruta(archivo))
                resultado, _ = eliminar_epsilon(original)
                antes = cadenas_hasta(original, 7)
                despues = cadenas_hasta(resultado, 7)
                self.assertTrue(antes)
                self.assertEqual(despues, antes - {""})


class TestPrograma(unittest.TestCase):
    def ejecutar(self, *archivos):
        salida = io.StringIO()
        with redirect_stdout(salida):
            codigo = main.main(["--sin-color"] + list(archivos))
        return codigo, salida.getvalue()

    def test_archivos_validos(self):
        codigo, salida = self.ejecutar(ruta("gramatica1.txt"), ruta("gramatica2.txt"))
        self.assertEqual(codigo, 0)
        self.assertIn("GRAMATICA RESULTANTE", salida)

    def test_archivos_invalidos_detienen_la_ejecucion(self):
        invalidos = sorted(glob.glob(ruta(os.path.join("invalidas", "*.txt"))))
        self.assertTrue(invalidos)
        for archivo in invalidos:
            with self.subTest(archivo=os.path.basename(archivo)):
                with self.assertRaises(ErrorGramatica):
                    cargar_gramatica(archivo)
                # El archivo valido que va despues no debe procesarse.
                codigo, salida = self.ejecutar(archivo, ruta("gramatica1.txt"))
                self.assertEqual(codigo, 1)
                self.assertIn("Ejecucion detenida", salida)
                self.assertNotIn("gramatica1.txt", salida)
                self.assertNotIn("ELIMINACION", salida)


if __name__ == "__main__":
    unittest.main()
