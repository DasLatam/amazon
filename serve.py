#!/usr/bin/env python3
"""Listings de Amazon (drafts internos) — portal web. Puerto 8089."""
import sys
from pathlib import Path

from flask import Flask, abort, send_from_directory

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8089
BASE = Path(__file__).parent
app = Flask(__name__)


@app.route("/")
def index():
    """La raiz sirve index.html, la portada navegable del proyecto.

    Antes devolvia un listado crudo de los .html de la carpeta: servia para
    encontrar un archivo, no para entender el proyecto. Si algun dia falta
    index.html, se cae al listado como respaldo en vez de dar 404.
    """
    portada = BASE / "index.html"
    if portada.exists():
        return send_from_directory(BASE, "index.html")
    listings = sorted(p.name for p in BASE.glob("*.html"))
    items = "\n".join(f'<li><a href="/{name}">{name}</a></li>' for name in listings)
    return f"""<!DOCTYPE html>
<html lang="es"><head><meta charset="UTF-8"><title>Amazon Listings</title></head>
<body><h1>Amazon Listings</h1><ul>{items}</ul></body></html>"""


# Las hojas ahora muestran imágenes —la comparación de la principal a 200 px, por
# ejemplo— y hasta el 2026-09-08 esta ruta sólo servía `.html` de la raíz: la hoja
# se veía bien en GitHub Pages y con la foto rota en el portal. De ahí que se
# acepten también subcarpetas y formatos de imagen.
EXTENSIONES = (".html", ".png", ".jpg", ".jpeg", ".webp", ".svg", ".gif")


@app.route("/<path:name>")
def listing(name):
    if not name.lower().endswith(EXTENSIONES):
        abort(404)
    # `send_from_directory` ya bloquea el salto de directorio, pero la ruta se
    # normaliza igual antes de tocar el disco: es una línea y cierra la duda.
    destino = (BASE / name).resolve()
    if not destino.is_file() or BASE.resolve() not in destino.parents:
        abort(404)
    return send_from_directory(BASE, name)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)
