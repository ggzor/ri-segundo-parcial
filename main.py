from collections import defaultdict
from re import compile
from math import log
from pathlib import Path
from pprint import pprint

# Constantes utilizadas
SIGNOS_PUNTUACION = ".,;:¿?¡!()[]/\\'\"&-_►—%@…|’“”"
NUMEROS = "0123456789"
RE_PALABRA = compile(r"\b[a-zñáéíóú]+\b")

# Función para terminar en caso de error
def exitError(mensaje):
    print(mensaje)
    exit(1)


# Calcular la frecuencia de termino (TF)
def pesoTF(x):
    if x > 0:
        return 1 + log(x, 2)
    else:
        return 0


def imprimir_diccionario(d):
    print("\n".join(f"{p:9} {v:.03f}" for p, v in d.items()))
    print()


def imprimir_diccionario_listas(d, fp=False, file=None):
    fmt = "{:.03f}" if fp else "{}"
    print(
        "\n".join(f'{p:9} {" ".join(map(fmt.format, l))}' for p, l in d.items()),
        file=file,
    )
    print()


# Archivos y carpetas utilizados
originales = Path("Noticias 2P.txt")
archivo_stopwords = Path("PalabrasCerradas.txt")

# Verificación de existencia de archivos
if not originales.exists():
    exitError(
        "No se localizó la carpeta con"
        " los documentos originales: \n" + str(originales.absolute())
    )
if not archivo_stopwords.exists():
    exitError(
        "No se localizó el archivo de palabras cerradas:\n" + str(archivo_stopwords)
    )

# Cargar las palabras cerradas
stopwords = set(archivo_stopwords.read_text("utf-8").split("\n"))

# Procesar cada documento
with open(originales, encoding="utf-8") as archivo:
    vocabulario = set()

    documentos = []
    conteo_palabras = defaultdict(lambda: defaultdict(lambda: 0))

    N = 0
    for i, linea in enumerate(archivo):
        N += 1

        # Obtener contenido
        documento = linea.split("$")[1]

        # Remover signos de puntuación
        for s in SIGNOS_PUNTUACION:
            documento = documento.replace(s, " ")

        # Remover dígitos
        for n in NUMEROS:
            documento = documento.replace(n, "")

        # Convertir a minúsculas
        documento = documento.lower()

        # Obtener las palabras
        documento = RE_PALABRA.findall(documento)

        # Remover las palabras vacías
        documento = [p for p in documento if p not in stopwords]

        # Agregar documento a lista de documentos
        documentos.append(documento)

        # Agregar palabras al conjunto
        for palabra in documento:
            vocabulario.add(palabra)
            conteo_palabras[palabra][i] += 1

    Path("NoticiasProcesadas.txt").write_text(
        "\n".join(f"noticia{i} $ {' '.join(d)}" for i, d in enumerate(documentos, 1)),
        encoding="utf-8",
    )

    vocabulario = sorted(vocabulario)
    Path("vocabulario.txt").write_text("\n".join(vocabulario), encoding="utf-8")
    print("Longitud del vocabulario: ", len(vocabulario))

    # Frecuencias de cada termino por documento
    frecuencias = {p: [v[i] for i in range(N)] for p, v in conteo_palabras.items()}

    # Pesos TF por documento
    tf = {p: [pesoTF(x) for x in l] for p, l in frecuencias.items()}
    Path("tf.csv").write_text(
        "\n".join(f"{p},{','.join(str(x) for x in tf[p])}" for p in sorted(tf.keys())),
        encoding="utf-8",
    )

    # Cantidad de documentos con el término
    ni = {p: len([x for x in l if x > 0]) for p, l in frecuencias.items()}

    # Frecuencia inversa por término
    idf = {p: log(N / x, 2) for p, x in ni.items()}
    Path("idf.csv").write_text(
        "\n".join(f"{p},{idf[p]}" for p in sorted(idf.keys())), encoding="utf-8"
    )

    # Pesos finales por cada término
    wi = {p: [x * idf[p] for x in l] for p, l in tf.items()}
    Path("representacion_documentos.csv").write_text(
        "\n".join(
            f"noticia{i + 1},{','.join(str(wi[p][i]) for p in sorted(wi.keys()))}"
            for i in range(N)
        ),
        encoding="utf-8",
    )

    # Vectores normalizados
    vector = {d: (sum(l[d] ** 2 for _, l in wi.items())) ** 0.5 for d in range(0, N)}

    # Función para rankear los documentos
    def rankear(consulta):
        resultado = {}

        for d in range(N):
            suma = 0
            for t in consulta:
                suma += idf.get(t, 0) * wi.get(t, [0] * N)[d]
            if suma > 0:
                resultado[d + 1] = suma / vector[d]

        return sorted(resultado.items(), key=lambda r: r[1], reverse=True)

    consultas = [
        ["hoy", "telecomunicaciones"],
        ["televisoras", "país", "servicios"],
        ["a"],
        ["narcotráfico", "chapo"],
        ["putin", "rusia"],
    ]

    # Realizar las consultas
    for c in consultas:
        print("Consulta: ", ",".join(c))
        pprint(rankear(c))
        print()
