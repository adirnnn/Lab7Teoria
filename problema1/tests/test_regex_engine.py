import itertools
import os
import random
import re
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from regex_engine import ErrorRegex, compilar, insertar_concatenacion, a_postfix, postfix_a_texto, tokenizar  # noqa: E402


class TestShuntingYard(unittest.TestCase):
    def postfix(self, patron):
        return postfix_a_texto(a_postfix(insertar_concatenacion(tokenizar(patron))))

    def test_concatenacion_y_union(self):
        self.assertEqual(self.postfix("ab|c"), "a b · c |")

    def test_cerraduras(self):
        self.assertEqual(self.postfix("(a|b)*c+"), "a b | * c + ·")

    def test_clase_y_escape(self):
        self.assertEqual(self.postfix("[A-Z]\\|"), "[A-Z] \\| ·")


class TestErrores(unittest.TestCase):
    def test_patrones_mal_formados(self):
        for patron in ["", "(ab", "ab)", "*a", "a|", "[a-", "[z-a]", "a\\"]:
            with self.subTest(patron=patron):
                with self.assertRaises(ErrorRegex):
                    compilar(patron)


class TestContraModuloRe(unittest.TestCase):
    """Compara el motor propio con el modulo re de Python sobre muchas cadenas."""

    PATRONES = [
        "a",
        "ab|c",
        "(a|b)*abb",
        "a+b?c*",
        "(ab)+|c?",
        "[a-c]+[0-9]?",
        "((a|b)(c|d))*",
        "a(b|ε)c",
        "x\\|y",
    ]
    ALFABETO = "abcd0|xyε"

    def test_cadenas_exhaustivas_cortas(self):
        for patron in self.PATRONES:
            afn = compilar(patron)
            esperado = re.compile(patron)
            for n in range(0, 5):
                for letras in itertools.product(self.ALFABETO, repeat=n):
                    cadena = "".join(letras)
                    with self.subTest(patron=patron, cadena=cadena):
                        self.assertEqual(afn.acepta(cadena), esperado.fullmatch(cadena) is not None)

    def test_cadenas_aleatorias_largas(self):
        generador = random.Random(7)
        for patron in self.PATRONES:
            afn = compilar(patron)
            esperado = re.compile(patron)
            for _ in range(300):
                cadena = "".join(generador.choice(self.ALFABETO) for _ in range(generador.randint(5, 12)))
                self.assertEqual(afn.acepta(cadena), esperado.fullmatch(cadena) is not None, (patron, cadena))


class TestPosicionDeError(unittest.TestCase):
    def test_posicion_del_primer_caracter_no_consumible(self):
        afn = compilar("abc")
        self.assertEqual(afn.simular("abc"), (True, None))
        self.assertEqual(afn.simular("axc"), (False, 1))
        self.assertEqual(afn.simular("ab"), (False, 2))


if __name__ == "__main__":
    unittest.main()
