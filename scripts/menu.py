#!/usr/bin/env python3
"""Menú común de las hojas de Zriceros.

Dos niveles: arriba las secciones (Producto, Plan, Seguimiento de Ads), que son
links de verdad y llevan a la hoja principal de cada una; abajo, las hojas de la
sección en la que se está, con la actual resaltada. Al pie, «anterior / siguiente».
El <title> también sale de acá.

Es HTML estático y no JS a propósito: las hojas se ven en el portal :8089, en
GitHub Pages y en https://192.168.1.71/reseñas, y desde esa página https un
script pedido por http al portal se bloquea.

Hoja nueva (la semana 3, por ejemplo): sumarla a SECCIONES y correr
    /usr/bin/python3 scripts/menu.py
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent

# (sección, hojas, cuál abre la pestaña). El orden es el de la vida del producto:
# qué se vende, cómo se planeó, cómo va. Seguimiento abre la última semana (-1).
SECCIONES = [
    ("Producto", [
        ("listing-zriceros-tongue-scraper.html", "Listing"),
        ("panorama-competitivo.html", "Competencia"),
    ], 0),
    ("Plan", [
        ("estrategia-inversion-zriceros.html", "Inversión"),
        ("estrategia-ppc-zriceros.html", "PPC"),
        ("resenas-zriceros.html", "Reseñas"),
    ], 0),
    ("Seguimiento de Ads", [
        ("reporte-campanas-zriceros.html", "Semana 1"),
        ("reporte-campanas-zriceros-semana-2.html", "Semana 2"),
        ("reporte-campanas-zriceros-semana-3.html", "Semana 3"),
    ], -1),
]
PORTADA = ("index.html", "Inicio", "")
MARCA = "Zriceros en Amazon"

CSS = """
.zm{position:sticky;top:0;z-index:50;margin:0 0 26px;border-radius:10px;overflow:hidden;
  box-shadow:0 2px 10px rgba(0,0,0,.18);font:14px/1.3 -apple-system,Segoe UI,Roboto,Arial,sans-serif}
.zm a{text-decoration:none;white-space:nowrap}
.zm-f1{display:flex;flex-wrap:wrap;align-items:center;gap:4px;background:#232f3e;padding:7px 10px}
.zm-f1 a{color:#fff;padding:7px 13px;border-radius:6px}
.zm-f1 a:hover{background:rgba(255,255,255,.14)}
.zm-f1 .zm-marca{font-weight:700;margin-right:8px}
.zm-f1 .zm-aqui{background:#37475a;box-shadow:inset 0 -3px 0 #ff9900;font-weight:700}
.zm-f2{display:flex;flex-wrap:wrap;align-items:center;gap:4px;background:#37475a;padding:6px 10px}
.zm-f2 .zm-rot{color:#b8c4cf;font-size:12px;padding:0 6px 0 3px}
.zm-f2 a{color:#e8edf2;padding:5px 11px;border-radius:6px}
.zm-f2 a:hover{background:rgba(255,255,255,.14)}
.zm-f2 a[aria-current]{background:#ff9900;color:#232f3e;font-weight:700}
.zp{display:flex;flex-wrap:wrap;gap:12px;margin:48px 0 0;padding-top:18px;border-top:1px solid #e0e0e0}
.zp a{flex:0 1 46%;text-decoration:none;color:#007185;background:#fff;border:1px solid #e0e0e0;
  border-radius:8px;padding:10px 14px;font-size:15px;font-weight:600}
.zp a:hover{border-color:#ff9900}
.zp small{display:block;color:#888;font-size:11px;font-weight:400;text-transform:uppercase;letter-spacing:.4px}
.zp .zp-sig{margin-left:auto;text-align:right}
@media (max-width:640px){
  .zm{position:static}
  .zp a{flex:1 1 100%}
  table{display:block;max-width:100%;overflow-x:auto}
}
""".strip()


def hojas() -> list[tuple[str, str, str]]:
    return [PORTADA] + [(a, t, s) for s, items, _ in SECCIONES for a, t in items]


def menu(actual: str) -> str:
    marca_aqui = ' class="zm-marca zm-aqui" aria-current="page"' if actual == "index.html" else ' class="zm-marca"'
    pestañas, subhojas = [], ""
    for seccion, items, principal in SECCIONES:
        adentro = any(a == actual for a, _ in items)
        clase = ' class="zm-aqui"' if adentro else ""
        contenido = ", ".join(t for _, t in items)
        pestañas.append(f'<a href="{items[principal][0]}"{clase} title="{contenido}">{seccion}</a>')
        if adentro:
            links = "".join(
                f'<a href="{a}"{" aria-current=\"page\"" if a == actual else ""}>{t}</a>' for a, t in items)
            subhojas = f'<div class="zm-f2"><span class="zm-rot">{seccion} ›</span>{links}</div>'
    return (
        f"<!-- menu -->\n<style>{CSS}</style>\n"
        f'<nav class="zm" aria-label="Hojas del proyecto">'
        f'<div class="zm-f1"><a href="index.html"{marca_aqui}>{MARCA}</a>{"".join(pestañas)}</div>'
        f"{subhojas}</nav>\n<!-- /menu -->"
    )


def pie(actual: str) -> str:
    orden = hojas()
    i = next(k for k, h in enumerate(orden) if h[0] == actual)
    partes = []
    if i > 0:
        a, t, s = orden[i - 1]
        partes.append(f'<a href="{a}"><small>← Anterior</small>{s + " · " if s else ""}{t}</a>')
    if i < len(orden) - 1:
        a, t, s = orden[i + 1]
        partes.append(f'<a class="zp-sig" href="{a}"><small>Siguiente →</small>{s} · {t}</a>')
    return f'<!-- pie-menu -->\n<nav class="zp" aria-label="Hoja anterior y siguiente">{"".join(partes)}</nav>\n<!-- /pie-menu -->'


def poner(texto: str, bloque: str, marca: str, antes_de: re.Pattern | None, despues_de: re.Pattern | None) -> str:
    """Reemplaza el bloque si ya está; si no, lo inserta en su lugar."""
    viejo = re.compile(rf"<!-- {marca} -->.*?<!-- /{marca} -->", re.S)
    if viejo.search(texto):
        return viejo.sub(lambda _: bloque, texto, count=1)
    if despues_de and (m := despues_de.search(texto)):
        return texto[: m.end()] + "\n" + bloque + "\n" + texto[m.end():]
    if antes_de and (m := antes_de.search(texto)):
        return texto[: m.start()] + bloque + "\n\n" + texto[m.start():]
    raise ValueError(f"no encontré dónde poner <!-- {marca} -->")


def main() -> int:
    for archivo, titulo, seccion in hojas():
        ruta = BASE / archivo
        texto = ruta.read_text(encoding="utf-8")
        nuevo = poner(texto, menu(archivo), "menu", None, re.compile(r"<body[^>]*>"))
        if archivo != "index.html":
            nuevo = poner(nuevo, pie(archivo), "pie-menu", re.compile(r"<footer|</body>"), None)
        nombre = f"{titulo} — {seccion} · {MARCA}" if seccion else f"{MARCA} — Documentación del proyecto"
        nuevo = re.sub(r"<title>.*?</title>", f"<title>{nombre}</title>", nuevo, count=1, flags=re.S)
        if nuevo != texto:
            ruta.write_text(nuevo, encoding="utf-8")
            print(f"actualizada: {archivo}")

    en_menu = {a for a, _, _ in hojas()}
    sueltas = sorted(p.name for p in BASE.glob("*.html") if p.name not in en_menu)
    if sueltas:
        print("OJO, hojas que no están en el menú:", ", ".join(sueltas), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
