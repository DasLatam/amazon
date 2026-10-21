#!/usr/bin/python3
"""Totales por campaña de cada informe de términos, y rastro de la manual exacta.

Nació el 2026-10-20, cuando Ariel preguntó si la campaña manual en exacta estaba
mal creada o si el informe la estaba dejando afuera. El informe de términos de
búsqueda **sólo trae líneas de campañas que tuvieron algo** (clics, y desde la
semana 7 una línea «(Other)» con las impresiones sin clic): una campaña sin
actividad no aparece ni con ceros. Este script lo deja a la vista: cuenta líneas,
impresiones, clics, gasto, ventas y pedidos por campaña y por tipo de línea
(búsqueda tipeada, ficha ajena con ASIN, «(Other)»), y busca las siete palabras de
la manual en todas las semanas.

    /usr/bin/python3 scripts/campanas.py              # imprime y verifica
    /usr/bin/python3 scripts/campanas.py --poner      # además actualiza las hojas

Lee `datos/semana-N_<desde>_<hasta>_terminos.csv` (no se publican: traen el ID de
la cuenta). A las hojas sólo van totales y nombres de campaña, nunca IDs.

Cuando dos informes se pisan un día (el 13-10 está en el de la semana 6 y en el de
la 7), las líneas idénticas en los dos (misma campaña, término, clics, costo y
compras) se descuentan del más nuevo, igual que en la hoja de la semana 7.
"""
from __future__ import annotations

import csv
import re
import sys
from collections import defaultdict
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
DATOS = BASE / "datos"

# Las siete búsquedas de la manual exacta (hoja de la semana 6, paso 2).
MANUAL = ["tongue brush", "tongue scraper stainless steel", "tongue scraper dr tung",
          "tongue scrapper", "tongue scraper black", "tongue scraper with case",
          "tongue scraper travel"]
NOMBRE_MANUAL = "Zriceros - Manual exacta - oct 2026"

# Lo que dice la hoja de la semana 7 (ya descontado el 13-10 repetido).
HOJA_S7 = {"clics": 88, "gasto": 120.17, "pedidos": 17, "ventas": 338.13, "impresiones": 13896}

MARCA = "tabla-campanas"
HOJAS = ["reporte-campanas-zriceros-semana-7.html", "diagnostico-campana-manual.html"]


def num(v: str) -> float:
    v = (v or "").replace("%", "").replace(",", "").strip()
    return float(v) if v else 0.0


def campana(nombre: str) -> str:
    n = nombre.lower()
    if "automatica" in n:
        return "Automática"
    if "primals" in n:
        return "PRIMALS"
    return nombre  # cualquier otra (la manual nueva, si aparece) con su nombre


def tipo(termino: str) -> str:
    t = termino.strip().lower()
    if t.startswith("(other"):
        return "other"
    if re.fullmatch(r"b0[a-z0-9]{8}", t):
        return "ficha"
    return "busqueda"


def semanas() -> list[tuple[int, str, str, list[dict]]]:
    out = []
    for f in DATOS.glob("semana-*_terminos.csv"):
        m = re.match(r"semana-(\d+)_(\S+?)_(\S+?)_terminos\.csv", f.name)
        if not m:
            continue
        with f.open(encoding="utf-8-sig", newline="") as fh:
            filas = list(csv.DictReader(fh))
        out.append((int(m[1]), m[2], m[3], filas))
    return sorted(out)


def clave(x: dict) -> tuple:
    return (x["ID de la campaña"], x["Término de búsqueda"].strip().lower(),
            x["Clics"], x["Coste total"], x["Compras"])


def depurar(lista):
    """Saca del informe más nuevo las líneas idénticas al anterior si se pisan."""
    out, previo = [], None
    for n, desde, hasta, filas in lista:
        repetidas = []
        if previo and previo[2] >= desde:  # fechas AAAA-MM-DD: se comparan como texto
            viejas = {clave(x) for x in previo[3] if num(x["Clics"]) > 0}
            repetidas = [x for x in filas if num(x["Clics"]) > 0 and clave(x) in viejas]
            filas = [x for x in filas if x not in repetidas]
        out.append((n, desde, hasta, filas, repetidas))
        previo = (n, desde, hasta, filas + repetidas)
    return out


def totales(filas: list[dict]) -> dict:
    por = defaultdict(lambda: defaultdict(float))
    for x in filas:
        c = por[campana(x["Nombre de la campaña"])]
        c["lineas"] += 1
        c["l_" + tipo(x["Término de búsqueda"])] += 1
        for k, col in (("impresiones", "Impresiones"), ("clics", "Clics"), ("gasto", "Coste total"),
                       ("ventas", "Ventas"), ("pedidos", "Compras"), ("unidades", "Unidades vendidas")):
            c[k] += num(x[col])
    return por


def pct(a: float, b: float) -> str:
    return f"{a / b * 100:.1f}%".replace(".", ",") if b else "—"


def plata(v: float) -> str:
    return "$" + f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def miles(v: float) -> str:
    return f"{v:,.0f}".replace(",", ".")


def tabla_html(n: int, desde: str, hasta: str, por: dict, nombres_pasadas: set[str]) -> str:
    filas = []
    orden = ["Automática", NOMBRE_MANUAL, "PRIMALS"] + sorted(set(por) - {"Automática", "PRIMALS", NOMBRE_MANUAL})
    for nom in orden:
        c = por.get(nom)
        etiqueta = {"Automática": "Campaña - 9/1/2026 automatica",
                    "PRIMALS": "Campaña - 9/1/2026 PRIMALS (pausada el 1-10)"}.get(nom, nom)
        if not c:
            motivo = ("ninguna línea: ningún clic ni impresiones agrupadas en el informe"
                      if nom == NOMBRE_MANUAL else "ninguna línea (pausada)")
            filas.append(f'<tr><td>{etiqueta}</td><td colspan="8" class="tbd">{motivo}</td></tr>')
            continue
        lineas = f'{int(c["lineas"])} ({int(c["l_busqueda"])} búsq. · {int(c["l_ficha"])} fichas' + \
                 (f' · {int(c["l_other"])} «(Other)»' if c["l_other"] else "") + ")"
        filas.append(
            f'<tr><td>{etiqueta}</td><td class="num">{lineas}</td><td class="num">{miles(c["impresiones"])}</td>'
            f'<td class="num">{int(c["clics"])}</td><td class="num">{pct(c["clics"], c["impresiones"])}</td>'
            f'<td class="num">{plata(c["gasto"])}</td><td class="num">{plata(c["ventas"])}</td>'
            f'<td class="num">{int(c["pedidos"])}</td><td class="num">{pct(c["gasto"], c["ventas"])}</td></tr>')
    return (f"<!-- {MARCA} -->\n<div class=\"tabla\"><table>\n"
            "<tr><th>Campaña</th><th class=\"num\">Líneas del informe</th><th class=\"num\">Impr.</th>"
            "<th class=\"num\">Clics</th><th class=\"num\">CTR</th><th class=\"num\">Gasto</th>"
            "<th class=\"num\">Ventas</th><th class=\"num\">Pedidos</th><th class=\"num\">ACoS</th></tr>\n"
            + "\n".join(filas) +
            f"\n</table></div>\n<p class=\"meta\">Semana {n} ({desde} a {hasta}), salido de "
            "<code>scripts/campanas.py</code> sobre el informe de términos, con las líneas del 13-10 "
            "repetidas de la semana 6 descontadas. Las impresiones incluyen la línea «(Other)».</p>\n"
            f"<!-- /{MARCA} -->")


def poner(ruta: Path, bloque: str) -> bool:
    texto = ruta.read_text(encoding="utf-8")
    nuevo = re.sub(rf"<!-- {MARCA} -->.*?<!-- /{MARCA} -->", lambda _: bloque, texto, count=1, flags=re.S)
    if nuevo == texto:
        return False
    ruta.write_text(nuevo, encoding="utf-8")
    return True


def main() -> int:
    lista = depurar(semanas())
    if not lista:
        print("no hay CSV en datos/", file=sys.stderr)
        return 1
    nombres = set()
    for n, desde, hasta, filas, rep in lista:
        por = totales(filas)
        nombres |= set(por)
        print(f"\n== Semana {n} ({desde} a {hasta}): {len(filas)} líneas"
              + (f" + {len(rep)} repetidas del informe anterior, descontadas" if rep else ""))
        for nom, c in por.items():
            print(f"  {nom:<12} líneas {int(c['lineas']):>3} (búsq {int(c['l_busqueda'])}, fichas {int(c['l_ficha'])},"
                  f" other {int(c['l_other'])}) · impr {miles(c['impresiones'])} · clics {int(c['clics'])}"
                  f" · CTR {pct(c['clics'], c['impresiones'])} · gasto {plata(c['gasto'])}"
                  f" · ventas {plata(c['ventas'])} · pedidos {int(c['pedidos'])} · ACoS {pct(c['gasto'], c['ventas'])}")
        ids = {x["ID de la campaña"] for x in filas}
        print(f"  campañas distintas (por ID): {len(ids)}")

    print("\n== Las siete de la manual, en todas las semanas (cualquier campaña)")
    total_c = total_i = 0
    for n, _, _, filas, _ in lista:
        for x in filas:
            if x["Término de búsqueda"].strip().lower() in MANUAL:
                total_c += num(x["Clics"]); total_i += num(x["Impresiones"])
                cpc = num(x["Coste total"]) / num(x["Clics"]) if num(x["Clics"]) else 0
                print(f"  sem {n}: {x['Término de búsqueda']:<32} {campana(x['Nombre de la campaña']):<11}"
                      f" impr {int(num(x['Impresiones'])):>3} clics {int(num(x['Clics']))} CPC {plata(cpc)}"
                      f" pedidos {int(num(x['Compras']))}")
    print(f"  total: {int(total_i)} impresiones (piso), {int(total_c)} clics")
    print(f"  ¿apareció alguna campaña que no sea Automática ni PRIMALS?: "
          f"{sorted(nombres - {'Automática', 'PRIMALS'}) or 'no'}")

    # Verificación contra la hoja de la semana 7.
    n, desde, hasta, filas, _ = lista[-1]
    ok = True
    if n == 7:
        t = defaultdict(float)
        for c in totales(filas).values():
            for k in HOJA_S7:
                t[k] += c[k]
        for k, v in HOJA_S7.items():
            igual = abs(t[k] - v) < 0.005
            ok &= igual
            print(f"  hoja semana 7, {k}: hoja {v} · CSV {round(t[k], 2)} · {'OK' if igual else 'NO COINCIDE'}")

    if "--poner" in sys.argv:
        bloque = tabla_html(n, desde, hasta, totales(filas), nombres)
        for h in HOJAS:
            ruta = BASE / h
            if ruta.exists() and poner(ruta, bloque):
                print(f"actualizada: {h}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
