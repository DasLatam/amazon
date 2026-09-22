#!/usr/bin/python3
"""Registro de solicitudes de reseña: lee el CSV y lo resume en la hoja.

Ariel lo pidió el 2026-09-21: *«agreguemos solicitar la reseña a los que ya
compraron (llevar el registro de a quienes se le solicito)»*. El botón
«Solicitar una reseña» de Seller Central se habilita entre 5 y 30 días después
de la entrega y **después desaparece**: sin registro, cada semana se vuelven a
abrir los mismos pedidos sin saber cuáles ya se hicieron y los que se pasan de
los 30 días se pierden sin dejar rastro.

El registro es `datos/resenas_solicitadas.csv`, que **no se publica** porque
lleva números de pedido (`datos/` está en `.gitignore`). De la hoja sale sólo el
resumen: cuántos pedidos, cuántos solicitados, cuántos por vencer y cuántas
reseñas llegaron. Eso es lo único que hace falta para saber cuántas reseñas da
cada diez solicitudes, que es el número que decide si vale la pena seguir.

    /usr/bin/python3 scripts/resenas.py            # resume y actualiza la hoja
    /usr/bin/python3 scripts/resenas.py --solo-ver # no toca el HTML

Columnas: pedido · fecha_pedido · fecha_entrega · solicitada · vencido ·
resena · notas. Las fechas van en AAAA-MM-DD; `solicitada` vacío es «todavía
no», `vencido=si` es «el botón ya no estaba».
"""
from __future__ import annotations

import csv
import html
import re
import sys
from datetime import date, datetime
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
REGISTRO = BASE / "datos" / "resenas_solicitadas.csv"
MARCA_INI, MARCA_FIN = "<!-- registro-resenas -->", "<!-- /registro-resenas -->"

# Ventana del botón en Seller Central, contada desde la entrega.
DESDE_DIAS, HASTA_DIAS = 5, 30
POR_VENCER_DIAS = 5  # avisar cuando quedan estos días o menos


def _fecha(valor: str) -> date | None:
    valor = (valor or "").strip()
    if not valor:
        return None
    try:
        return datetime.strptime(valor, "%Y-%m-%d").date()
    except ValueError:
        return None


def leer() -> list[dict]:
    if not REGISTRO.exists():
        return []
    with REGISTRO.open(encoding="utf-8-sig", newline="") as fh:
        return [f for f in csv.DictReader(fh) if (f.get("pedido") or "").strip()]


def resumir(filas: list[dict], hoy: date | None = None) -> dict:
    hoy = hoy or date.today()
    r = {
        "pedidos": len(filas), "solicitados": 0, "resenas": 0, "vencidos": 0,
        "sin_entrega": 0, "esperando": 0, "listos": [], "por_vencer": [],
    }
    for f in filas:
        solicitada = _fecha(f.get("solicitada"))
        entrega = _fecha(f.get("fecha_entrega"))
        if solicitada:
            r["solicitados"] += 1
        if _fecha(f.get("resena")):
            r["resenas"] += 1
        if (f.get("vencido") or "").strip().lower() in ("si", "sí", "1", "true"):
            r["vencidos"] += 1
            continue
        if solicitada:
            continue
        if not entrega:
            r["sin_entrega"] += 1
            continue
        dias = (hoy - entrega).days
        if dias < DESDE_DIAS:
            r["esperando"] += 1
        elif dias <= HASTA_DIAS:
            r["listos"].append(f["pedido"])
            if HASTA_DIAS - dias <= POR_VENCER_DIAS:
                r["por_vencer"].append((f["pedido"], HASTA_DIAS - dias))
        else:
            r["vencidos"] += 1
    return r


def bloque_html(r: dict) -> str:
    if not r["pedidos"]:
        return ('<p class="meta">Registro de solicitudes: todavía vacío. '
                '<code>datos/resenas_solicitadas.csv</code> está creado con las '
                'columnas; se llena con los pedidos de Seller Central.</p>')
    tasa = (f'{r["resenas"] / r["solicitados"] * 100:.0f}%'
            if r["solicitados"] else "&mdash;")
    filas = [
        ("Pedidos en el registro", r["pedidos"]),
        ("Reseña ya solicitada", r["solicitados"]),
        ("Listos para pedir hoy", len(r["listos"])),
        ("Esperando los 5 días", r["esperando"]),
        ("Se pasaron de los 30 días", r["vencidos"]),
        ("Reseñas que llegaron", r["resenas"]),
        ("Reseñas por solicitud", tasa),
    ]
    cuerpo = "".join(
        f'<tr><th>{html.escape(str(k))}</th>'
        f'<td class="num">{v}</td></tr>' for k, v in filas)
    aviso = ""
    if r["por_vencer"]:
        cuantos = len(r["por_vencer"])
        minimo = min(d for _, d in r["por_vencer"])
        dias = f'{minimo} día' + ("s" if minimo != 1 else "")
        aviso = ('<p class="meta warn">'
                 + (f'{cuantos} pedidos sin solicitar a los que les quedan '
                    f'{dias} o menos' if cuantos > 1 else
                    f'Un pedido sin solicitar al que le quedan {dias}')
                 + ' antes de que el botón desaparezca.</p>')
    sin_entrega = ""
    if r["sin_entrega"]:
        sin_entrega = (f'<p class="meta">{r["sin_entrega"]} pedido(s) sin fecha '
                       f'de entrega en el registro: no se pueden contar.</p>')
    return (f'<table class="p-mini">{cuerpo}</table>{aviso}{sin_entrega}')


def escribir(bloque: str) -> list[str]:
    tocadas = []
    for ruta in sorted(BASE.glob("*.html")):
        texto = ruta.read_text(encoding="utf-8")
        if MARCA_INI not in texto:
            continue
        nuevo = re.sub(
            re.escape(MARCA_INI) + r".*?" + re.escape(MARCA_FIN),
            MARCA_INI + "\n" + bloque + "\n" + MARCA_FIN,
            texto, flags=re.S)
        if nuevo != texto:
            ruta.write_text(nuevo, encoding="utf-8")
            tocadas.append(ruta.name)
    return tocadas


def main() -> int:
    filas = leer()
    r = resumir(filas)
    print(f"{r['pedidos']} pedidos · {r['solicitados']} solicitados · "
          f"{len(r['listos'])} listos para pedir hoy · {r['esperando']} esperando · "
          f"{r['vencidos']} vencidos · {r['resenas']} reseñas")
    for pedido, dias in r["por_vencer"]:
        print(f"  ⚠ {pedido}: quedan {dias} días para pedirle la reseña")
    for pedido in r["listos"]:
        print(f"  → {pedido}: se puede pedir ya")
    if "--solo-ver" in sys.argv:
        return 0
    tocadas = escribir(bloque_html(r))
    print("hojas actualizadas:", ", ".join(tocadas) if tocadas else "ninguna")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
