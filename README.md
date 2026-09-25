# Laboratorio 7 - Teoría de la Computación

Simplificación de gramáticas libres de contexto.

| Problema | Contenido | Carpeta |
|---|---|---|
| Problema 1 (50%) | Programa que carga gramáticas, valida cada línea con una expresión regular y elimina producciones ε mostrando los pasos | [`problema1/`](problema1/) |
| Problema 2 (50%) | Resolución manual de las tres CFGs (incisos a-d) en PDF | `problema2/` |

## Video de demostración

> **Enlace (YouTube, no listado):** _pendiente de agregar_

---

## Problema 1

Programa escrito en **Python 3** (versión 3.8 o superior). Solo usa la biblioteca
estándar, no hay que instalar dependencias.

### Estructura

```text
problema1/
├── main.py              # Programa principal (línea de comandos)
├── regex_engine.py      # Motor de regex: Shunting-Yard -> AFN de Thompson -> simulación
├── validador.py         # Expresión regular de producciones y mensajes de error
├── gramatica.py         # Lectura del archivo y representación de la gramática
├── epsilon.py           # Algoritmo de eliminación de producciones ε
├── gramaticas/
│   ├── gramatica1.txt   # Gramática 1 del enunciado
│   ├── gramatica2.txt   # Gramática 2 del enunciado
│   ├── gramatica3.txt   # Gramática 3 del enunciado (archivo adicional)
│   └── invalidas/       # Copias con errores introducidos a propósito (demostración)
└── tests/               # Pruebas unitarias
```

### Ejecución

Desde la carpeta `problema1/`:

```bash
# Una gramática
python main.py gramaticas/gramatica1.txt

# Varias gramáticas en la misma ejecución
python main.py gramaticas/gramatica1.txt gramaticas/gramatica2.txt

# Mostrar además la expresión regular, su forma postfix y el tamaño del AFN
python main.py --mostrar-regex gramaticas/gramatica2.txt

# Archivos con errores: la ejecución se detiene en la línea inválida
python main.py gramaticas/invalidas/error_flecha.txt
```

Opciones:

| Opción | Descripción |
|---|---|
| `--mostrar-regex` | Imprime la expresión regular, su postfix (Shunting-Yard) y el número de estados del AFN de Thompson |
| `--sin-color` | Desactiva los colores de la consola |

Código de salida: `0` si todo se procesó, `1` si algún archivo tiene una línea inválida
(o no existe). Si se pasan varios archivos, al primer error ya no se procesan los siguientes.

Pruebas:

```bash
python -m unittest discover -s tests -v
```

### 1. Formato de los archivos de gramática

- Cada línea es una producción; varias alternativas se separan con `|`.
- La cabeza de la primera línea es el símbolo inicial.
- Letra mayúscula individual: **no terminal**. Letra minúscula individual: **terminal**.
- La cadena vacía se escribe `ε`.
- La flecha puede escribirse `->` o `→`. Se permiten espacios alrededor de la flecha y de `|`.
- Las líneas vacías se ignoran.

```text
S -> 0A0 | 1B1 | BB
A -> C
B -> S | A
C -> S | ε
```

### 2. Validación de cada línea

Cada línea se valida **antes** de procesar la gramática. La validación usa una expresión
regular que se compila con un motor propio (`regex_engine.py`), siguiendo el mismo flujo del
Proyecto 1: infix → postfix (**Shunting-Yard**) → **AFN de Thompson** → **simulación del AFN**.

```text
[ \t]*[A-Z][ \t]*(->|→)[ \t]*(([A-Z]|[a-z0-9])+|ε)([ \t]*\|[ \t]*(([A-Z]|[a-z0-9])+|ε))*[ \t]*
```

| Parte | Qué reconoce |
|---|---|
| `[A-Z]` | Símbolo de la cabeza (una mayúscula) |
| `(->\|→)` | Flecha de producción |
| `(([A-Z]\|[a-z0-9])+\|ε)` | Un cuerpo: uno o más símbolos, o bien `ε` sola |
| `([ \t]*\|[ \t]*CUERPO)*` | Alternativas adicionales separadas por `\|` |
| `[ \t]*` | Espacios opcionales |

Si una línea no es aceptada por el AFN, el programa indica el archivo, la línea, la columna
donde falló la simulación, una explicación del error y **detiene la ejecución**:

```text
  Linea  3: B - S | A                        INVALIDA

ERROR de sintaxis en gramaticas/invalidas/error_flecha.txt, linea 3, columna 4:
    B - S | A
       ^
    se esperaba la flecha '->' y se encontro ' '

La linea no cumple la expresion regular de producciones. Ejecucion detenida.
```

Archivos de demostración en `gramaticas/invalidas/` (cada uno es una de las gramáticas
del enunciado con una producción modificada ligeramente):

| Archivo | Modificación |
|---|---|
| `error_cabeza_minuscula.txt` | `s -> 0A0 \| 1B1 \| BB` (cabeza en minúscula) |
| `error_flecha.txt` | `B - S \| A` (flecha incompleta) |
| `error_epsilon.txt` | `C -> S \| aε` (ε mezclada con otros símbolos) |
| `error_alternativa_vacia.txt` | `S -> aAa \| bBb \|` (falta el cuerpo después de `\|`) |
| `error_simbolo_invalido.txt` | `D -> A \| B \| a$b` (símbolo fuera del alfabeto) |
| `error_espacio_en_cuerpo.txt` | `C -> C DE \| ε` (espacio dentro de un cuerpo) |

### 3. Eliminación de producciones ε

El programa muestra en pantalla cada paso:

1. **Símbolos anulables.** Ronda 0: los `A` con `A -> ε`. En cada ronda siguiente se agrega
   `A` si tiene una producción cuyos símbolos son todos anulables; se repite hasta que el
   conjunto no cambia. Luego se listan las producciones anulables y las que contienen
   símbolos anulables.
2. **Los 2^m casos.** Para cada producción `A -> α` con `m` ocurrencias de símbolos
   anulables se imprime una tabla con los `2^m` casos (cada ocurrencia se conserva `1` o se
   omite `0`), el cuerpo resultante y si es nuevo, repetido o ε (se descarta).
3. **Nueva gramática.** Se eliminan las producciones `A -> ε` y se imprime la gramática
   resultante, con notas cuando corresponde.

Ejemplo (Gramática 1, producción `S -> BB`):

```text
S -> BB   (m = 2: B1, B2; 2^2 = 4 casos)
  caso  B1 B2  cuerpo  resultado  observacion
     1  1  1   B B     BB         nueva
     2  1  0   B _     B          nueva
     3  0  1   _ B     B          repetida: ya se agrego
     4  0  0   _ _     ε          es ε: se descarta
```

Resultados que produce el programa:

| Gramática | Anulables | Resultado sin producciones ε |
|---|---|---|
| 1 | C, A, B, S | `S -> 0A0 \| 00 \| 1B1 \| 11 \| BB \| B`, `A -> C`, `B -> S \| A`, `C -> S` |
| 2 | S, C, A, B, D | `S -> aAa \| aa \| bBb \| bb`, `A -> C \| a`, `B -> C \| b`, `C -> CDE \| CE \| DE \| E`, `D -> A \| B \| ab` |
| 3 | B, A | `S -> ASA \| AS \| SA \| S \| aB \| a`, `A -> B \| S`, `B -> b` |

Las pruebas (`tests/test_gramaticas.py`) comprueban, además, que para cada gramática el
resultado genera exactamente las mismas cadenas que la original (hasta longitud 7) excepto ε.

### Decisiones y ambigüedades del enunciado

- **Gramáticas del Ejercicio No. 2.** El enunciado pide dos archivos, uno por cada gramática
  del Ejercicio 2 indicada para esta parte. Se usaron las **Gramáticas 1 y 2** del Problema 2
  (`gramatica1.txt` y `gramatica2.txt`). También se incluye `gramatica3.txt` como archivo
  adicional, sin que afecte a los dos requeridos.
- **Dígitos como terminales.** La convención del enunciado solo menciona letras minúsculas
  como terminales, pero la Gramática 1 usa `0` y `1`. Por eso la expresión regular acepta
  también dígitos (`[a-z0-9]`) como terminales.
- **No terminal `E` de la Gramática 2.** El documento fuente usa `E` en `C -> CDE` pero no da
  producciones para `E`. La gramática se conserva tal cual: el programa avisa que `E` no
  tiene producciones y, por eso, `E` no es anulable.
- **Símbolo inicial anulable.** En las Gramáticas 1 y 2 el símbolo inicial es anulable
  (ε ∈ L(G)). Como se pide una gramática sin producciones ε, el resultado genera
  L(G) − {ε} y el programa lo indica con una nota. No se agrega un nuevo símbolo inicial.
- **Producción `S -> S` en la Gramática 3.** Aparece al omitir las dos `A` de `S -> ASA`.
  Se muestra porque es uno de los 2^m casos; no cambia el lenguaje y se elimina en el paso
  de producciones unitarias (Problema 2, inciso b), que no forma parte de este programa.
- **Espacios.** Se permiten alrededor de `->` y `|`, pero no dentro de un cuerpo
  (`0 A 0` es inválido), porque cada símbolo es un solo carácter.
