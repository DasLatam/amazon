#!/usr/bin/python3
"""Frases: cada búsqueda con clics de todas las semanas, con su veredicto.

Nació el 2026-10-22, cuando Ariel pidió un apartado «Frases» dentro de Seguimiento
de Ads para ir poniendo ahí el trabajo fino: qué búsquedas negativizar, cuáles
dejar madurar y cuáles son una oportunidad. Lee los mismos CSV que
`campanas.py` (`datos/semana-N_<desde>_<hasta>_terminos.csv`, reusa su lectura y el
descuento de los días pisados entre informes), junta cada frase en una fila y
escribe `frases-zriceros.html` entera.

    /usr/bin/python3 scripts/frases.py           # imprime el resumen y verifica
    /usr/bin/python3 scripts/frases.py --poner   # además escribe la hoja

Semana nueva: copiar el CSV a datos/ con el nombre de siempre, correr con
--poner, mirar las frases que salen «sin clasificar» (las imprime) y, si hace
falta, sumarlas a FAMILIAS, EXACTAS u OPORTUNIDADES de abajo y volver a correr.
Una nota de la semana va en NOTAS_SEMANA. Después, `scripts/menu.py`.

Las decisiones de criterio viven acá y no en la hoja, para que la tabla, las
cajas para copiar y el cuadro de familias salgan siempre de la misma fuente.
"""
from __future__ import annotations

import html
import math
import re
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from campanas import MANUAL, campana, depurar, num, semanas, tipo  # noqa: E402

BASE = Path(__file__).resolve().parent.parent
HOJA = BASE / "frases-zriceros.html"

CONTRIBUCION = 9.00      # $19,89 − tarifas − producto (CLAUDE.md, «Economía»)
CLICS_DECIDIR = 15       # la regla de la estrategia de PPC: 15 clics sin pedido

# Lo que dicen las hojas semanales, tabla «Las N semanas lado a lado» (la 8 desde el 27-10).
HOJAS_TOTALES = {1: (11, 18.66, 4), 2: (34, 75.19, 5), 3: (53, 92.32, 9), 4: (56, 85.12, 1),
                 5: (91, 87.92, 6), 6: (57, 54.52, 11), 7: (88, 120.17, 17),
                 8: (58, 83.99, 9)}

# Familias: una palabra que describe un producto que no vendemos. Va como
# NEGATIVA DE FRASE en la automática y corta todas las variantes que la contengan.
# Zriceros: 3 raspadores de acero inoxidable 304, negros, con estuche de metal.
FAMILIAS = {
    "copper": "somos de acero, no de cobre",
    "titanium": "somos de acero, no de titanio",
    "disposable": "busca descartables; el nuestro dura años",
    "toothbrush": "busca un cepillo de dientes",
    "palate": "expansor de paladar: otro producto",
    "tongue guard": "protector de lengua: otro producto",
    "uv": "estuche con luz UV: no lo tenemos",
    "sanitizer": "esterilizador: otro producto",
    "rubber": "mango o cepillo de goma: el nuestro es todo acero",
    "non metal": "pide que no sea de metal",
    "hygiene kit": "kit de higiene completo: otro producto",
    "brushing teeth": "kit para cepillarse los dientes",
}

# Palabras que parecen familia pero NO se negativizan (el cuadro las muestra).
NO_FAMILIAS = {
    "electric": "«electric tongue scraper» vendió (1 pedido en 2 clics, el 13-10)",
    "case": "«tongue scraper w case» vendió y «with case» está en la manual",
    "brush": "«tongue brush» vendió 2 unidades; «toothbrush» es otra palabra",
    "kit": "«tongue scraper kit» describe lo nuestro; por eso «hygiene kit» y no «kit»",
    "travel / mini / tiny / smaller mouth / gag": "tenemos dos tamaños, estuche de viaje y la ficha habla del reflejo",
    "marcas (dr tung, mastermedi, equate, grin, gum, elevate)": "tres de seis vendieron: no se cierran",
}

# Frases que no encajan pero cuyas palabras sí aparecen en búsquedas buenas:
# van como NEGATIVA EXACTA (sólo esa frase, letra por letra).
EXACTAS = {
    "tongue scraper with stand": "pide pedestal; traemos estuche",
    "tongue scraper with teeth": "pide dientes o cerdas; el nuestro es liso",
    "very thick tongue scraper": "pide uno grueso; el nuestro es una lámina",
    "tongue scraper it does rough": "pide uno áspero; el nuestro es liso",
    "tongue buddy": "nombre de otro producto",
    "tongue scraper for adults fsa eligible": "pide apto para cuenta FSA; la ficha no lo es",
    "case for tongue scraper": "busca sólo el estuche",
    # semana 8 (27-10)
    "tongue scraper under 3 dollars": "busca algo de $3; el nuestro sale $19,89",
    "tongue scraper pink": "pide rosa; el nuestro es negro",
    "tongue scraper clear plastic": "pide plástico transparente; el nuestro es acero",
    "tongue scraper spiky": "pide púas; el nuestro es liso",
    "tung gel": "busca el gel de Tung, no un raspador",
    "hy1200": "modelo de otro producto",
}

# Las que se miran con más plata, no con negativas.
OPORTUNIDADES = {
    "tongue scraper for adults": "10 pedidos en 29 clics (34,5%). Pasa a la manual exacta a $1,50 y a negativa exacta en la automática (semana 8, pasos 2 y 3)",
    "tongue cleaner": "2 pedidos en 12 clics. Pasa a la manual exacta a $1,00 y a negativa exacta en la automática (semana 8, pasos 2 y 3)",
}
NUCLEO = {
    "tongue scraper": "la búsqueda principal. CAMBIO (27-10): pasa a la manual exacta a $1,00 y va de negativa exacta en la automática (semana 8, pasos 2 y 3). Nunca de frase",
}

# Lo que ya está cargado. Sólo lo que consta en las hojas o en los pendientes.
YA_NEGATIVAS = {t: "negativa exacta en la automática y exacta en la manual (19-10)" for t in MANUAL}
NOTAS_FRASE = {
    "copper tongue scraper": "dejó de salir el 9-09 en PRIMALS (pausada); en la automática no consta",
    "copper tongue scraper for adults": "propuesta como negativa en la semana 1; en la automática no consta",
    "electric tongue scraper": "vendió el 13-10: no va como negativa",
    "tongue scrapper for smaller mouth": "el mismo clic del 13-10 en dos informes: cuenta una vez",
    "tongue cleaner": "convierte 1 en 11: por debajo de su equilibrio, todavía sin veredicto",
    "zricezos tongue cleaner": "nuestra marca mal escrita",
    "tung scraper": "«tongue» o Dr. Tung mal escrito",
    "tough scraper": "«tongue» mal escrito",
    "raspalenguas": "en español",
    "舌苔刷": "chino: «cepillo de lengua»",
    "شطب اللسان": "árabe: «raspar la lengua»",
}

NOTAS_SEMANA = {
    8: "El presupuesto de $12 cortó todos los días. Seis exactas nuevas (pink, under 3 "
       "dollars, clear plastic, spiky, tung gel, hy1200). «plastictongue scraper for "
       "adults» vendió: «plastic» no va de frase.",
    7: "La puja dinámica llevó el anuncio a muchas búsquedas sueltas. Casi todas las "
       "negativas de frase salen de esta semana.",
    6: "La primera semana sin PRIMALS. «electric tongue scraper» vendió el 13-10.",
    5: "PRIMALS se pausó el 1-10. Aparece «tongue scraper for adults», la mejor frase.",
    4: "Una línea de PRIMALS sin término (2 clics, $4,32): no es una frase.",
    2: "«copper tongue scraper» sale el 8 y el 9 y no vuelve.",
}

ORDEN = ["Negativa de frase", "Negativa exacta", "Madurar", "Oportunidad", "Núcleo", "Ya negativa"]
CLASE = {"Negativa de frase": "v-frase", "Negativa exacta": "v-exacta", "Madurar": "v-madurar",
         "Oportunidad": "v-oport", "Núcleo": "v-nucleo", "Ya negativa": "v-ya"}


def norm(t: str) -> str:
    return re.sub(r"\s+", " ", t.strip().lower())


def palabras(t: str) -> list[str]:
    # Plural simple: Amazon trata plurales como la misma palabra en una negativa de frase.
    return [w[:-1] if len(w) > 3 and w.endswith("s") and not w.endswith("ss") else w
            for w in re.findall(r"[\w']+", t.lower())]


def contiene(termino: str, familia: str) -> bool:
    a, b = palabras(termino), palabras(familia)
    return any(a[i:i + len(b)] == b for i in range(len(a) - len(b) + 1))


def familia_de(t: str) -> str | None:
    return next((f for f in FAMILIAS if contiene(t, f)), None)


def binom_ge(k: int, n: int, p: float) -> float:
    return sum(math.comb(n, i) * p ** i * (1 - p) ** (n - i) for i in range(k, n + 1))


# ---------------------------------------------------------------- datos

def juntar():
    lista = depurar(semanas())
    frases: dict[str, dict] = {}
    fichas = defaultdict(float)
    otros = defaultdict(float)
    por_semana = {}
    repetidas = []
    busq_clics = busq_pedidos = 0
    ultima = defaultdict(float)
    for n, desde, hasta, filas, rep in lista:
        por_semana[n] = (desde, hasta, defaultdict(float))
        repetidas += [(n, x["Término de búsqueda"].strip(), int(num(x["Clics"])), int(num(x["Compras"])))
                      for x in rep]
        for x in filas:
            t = x["Término de búsqueda"]
            k = tipo(t) if t.strip() else "vacio"
            tot = por_semana[n][2]
            for col, c in (("Clics", "clics"), ("Coste total", "gasto"), ("Compras", "pedidos")):
                tot[c] += num(x[col])
            if k != "busqueda":
                d = fichas if k == "ficha" else otros
                for col, c in (("Impresiones", "impr"), ("Clics", "clics"), ("Coste total", "gasto"),
                               ("Compras", "pedidos"), ("Unidades vendidas", "unidades")):
                    d[c] += num(x[col])
                if k == "ficha":
                    fichas["n_lineas"] += 1
                continue
            f = frases.setdefault(norm(t), {"frase": norm(t), "impr": 0.0, "clics": 0.0, "gasto": 0.0,
                                            "pedidos": 0.0, "ventas": 0.0, "unidades": 0.0,
                                            "semanas": {}, "campanas": set(), "concordancia": set()})
            for col, c in (("Impresiones", "impr"), ("Clics", "clics"), ("Coste total", "gasto"),
                           ("Compras", "pedidos"), ("Ventas", "ventas"), ("Unidades vendidas", "unidades")):
                f[c] += num(x[col])
            s = f["semanas"].setdefault(n, [0, 0])
            s[0] += int(num(x["Clics"]))
            s[1] += int(num(x["Compras"]))
            cam = campana(x["Nombre de la campaña"])
            f["campanas"].add(cam)
            conc = (x.get("Tipo de concordancia") or "").strip()
            f["concordancia"].add(conc or {"Automática": "automática", "PRIMALS": "por producto"}.get(cam, "manual"))
            busq_clics += num(x["Clics"])
            busq_pedidos += num(x["Compras"])
            if n == lista[-1][0]:
                ultima["clics"] += num(x["Clics"])
                ultima["gasto"] += num(x["Coste total"])
    p = busq_pedidos / busq_clics
    extra = {"cpc": ultima["gasto"] / ultima["clics"], "base": (int(busq_pedidos), int(busq_clics))}
    return frases, fichas, otros, por_semana, repetidas, p, extra


def veredicto(f: dict, p: float) -> tuple[str, str]:
    t, c, ped = f["frase"], int(f["clics"]), int(f["pedidos"])
    if t in YA_NEGATIVAS:
        return "Ya negativa", YA_NEGATIVAS[t]
    if t in NUCLEO:
        return "Núcleo", NUCLEO[t]
    if t in OPORTUNIDADES:
        return "Oportunidad", OPORTUNIDADES[t]
    fam = familia_de(t)
    if fam and ped == 0:
        return "Negativa de frase", f"«{fam}»: {FAMILIAS[fam]}"
    if t in EXACTAS and ped == 0:
        return "Negativa exacta", EXACTAS[t]
    if ped == 0 and c >= CLICS_DECIDIR:
        return "Negativa exacta", f"{c} clics sin pedido: con {pct(p)} pasa {pct((1 - p) ** c, 0)} de las veces"
    falta = max(CLICS_DECIDIR - c, 0)
    if ped:
        conv = ped / c
        eq = CONTRIBUCION * conv
        cpc = f["gasto"] / c
        txt = f"vendió {ped} en {c}; " + ("gana a este CPC" if cpc <= eq else "por ahora pierde a este CPC")
        return "Madurar", txt + (f"; decide a los {CLICS_DECIDIR} clics" if falta else "")
    return "Madurar", f"encaja; faltan {falta} clics sin pedido para decidir"


# ---------------------------------------------------------------- formato

def pct(v: float, dec: int = 1) -> str:
    return f"{v * 100:.{dec}f}%".replace(".", ",")


def plata(v: float) -> str:
    s = f"{abs(v):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return ("−$" if v < -0.004 else "$") + s


def signo(v: float) -> str:
    return ("+" if v > 0.004 else "") + plata(v)


def miles(v: float) -> str:
    return f"{v:,.0f}".replace(",", ".")


def e(t: str) -> str:
    return html.escape(t, quote=True)


def fila(f: dict, ver: str, motivo: str) -> str:
    c = f["clics"]
    conv = f["pedidos"] / c if c else 0
    cpc = f["gasto"] / c if c else 0
    acos = f["gasto"] / f["ventas"] if f["ventas"] else None
    neto = f["unidades"] * CONTRIBUCION - f["gasto"]
    ctr = c / f["impr"] if f["impr"] else 0
    sem = " ".join(str(n) for n in sorted(f["semanas"]))
    cam = " + ".join(sorted(f["campanas"]))
    nota = NOTAS_FRASE.get(f["frase"], "")
    return (
        f'<tr data-v="{e(ver)}" data-t="{e(f["frase"])}">'
        f'<td class="fr"><bdi>{e(f["frase"])}</bdi>'
        + (f'<small>{e(nota)}</small>' if nota else "") +
        f'</td><td><span class="vd {CLASE[ver]}">{e(ver)}</span><small>{e(motivo)}</small></td>'
        f'<td data-s="{min(f["semanas"])}">{sem}</td>'
        f'<td>{e(cam)}<small>{e(", ".join(sorted(f["concordancia"])))}</small></td>'
        f'<td class="num" data-s="{f["impr"]:.0f}">{miles(f["impr"])}</td>'
        f'<td class="num" data-s="{c:.0f}">{int(c)}</td>'
        f'<td class="num" data-s="{ctr:.5f}">{pct(ctr, 2) if f["impr"] else "—"}</td>'
        f'<td class="num" data-s="{f["gasto"]:.2f}">{plata(f["gasto"])}</td>'
        f'<td class="num" data-s="{cpc:.2f}">{plata(cpc)}</td>'
        f'<td class="num" data-s="{f["pedidos"]:.0f}">{int(f["pedidos"])}</td>'
        f'<td class="num" data-s="{f["ventas"]:.2f}">{plata(f["ventas"])}</td>'
        f'<td class="num" data-s="{conv:.4f}">{pct(conv) if f["pedidos"] else "—"}</td>'
        f'<td class="num" data-s="{acos if acos is not None else 99:.4f}">{pct(acos) if acos is not None else "—"}</td>'
        f'<td class="num" data-s="{neto:.2f}">{signo(neto)}</td></tr>'
    )


CSS = """
  body { font-family: -apple-system, Segoe UI, Roboto, Arial, sans-serif; max-width: 960px;
    margin: 40px auto; padding: 0 20px; line-height: 1.55; color: #232f3e; background: #f7f7f7; font-size: 17px; }
  p, li { text-align: justify; hyphens: auto; }
  h1 { font-size: 26px; border-bottom: 3px solid #ff9900; padding-bottom: 8px; margin-bottom: 14px; }
  h2 { font-size: 19px; margin: 40px 0 12px; letter-spacing: .5px; }
  h3 { font-size: 17px; margin: 22px 0 8px; }
  .estado { background: #fff; border-left: 6px solid #2e7d32; border-radius: 8px;
    padding: 14px 18px; font-size: 18px; font-weight: 600; margin: 0 0 8px; text-align: left; }
  .paso { display: flex; gap: 16px; background: #fff; border: 1px solid #ddd;
    border-radius: 10px; padding: 16px 18px; margin: 0 0 14px; }
  .n { flex: 0 0 auto; font-size: 40px; font-weight: 800; color: #ff9900; line-height: 1; min-width: 34px; }
  .paso div.t { flex: 1 1 auto; min-width: 0; }
  .paso h3 { margin: 0 0 8px; font-size: 18px; }
  .paso p { margin: 6px 0; hyphens: none; }
  .et { font-weight: 700; display: block; margin-top: 10px; font-size: 14px; text-transform: uppercase; letter-spacing: .4px; }
  .et.ok { color: #2e7d32; } .et.no { color: #b3261e; }
  em { font-style: normal; font-weight: 600; background: #fff3d6; padding: 0 3px; border-radius: 3px; }
  code { background: #eef2f5; padding: 1px 5px; border-radius: 4px; font-size: 15px; word-break: break-word; }
  a { color: #007185; }
  .card { background: #fff; border: 1px solid #e0e0e0; border-radius: 8px; padding: 16px 20px; margin: 12px 0; }
  .regla p { margin: 6px 0; }
  .cajas { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }
  .caja { background: #fff; border: 1px solid #ddd; border-radius: 10px; padding: 12px 14px; }
  .caja h3 { margin: 0 0 6px; font-size: 16px; }
  .caja textarea { width: 100%; box-sizing: border-box; font: 15px/1.5 ui-monospace, Menlo, Consolas, monospace;
    border: 1px solid #cfd8dc; border-radius: 6px; padding: 8px; background: #f6f8fa; resize: vertical; }
  .copiar { margin-top: 8px; background: #ff9900; color: #232f3e; border: 0; border-radius: 6px;
    padding: 9px 16px; font-weight: 700; font-size: 15px; cursor: pointer; }
  .copiar.hecho { background: #2e7d32; color: #fff; }
  .tabla { overflow-x: auto; -webkit-overflow-scrolling: touch; background: #fff; border: 1px solid #e0e0e0; border-radius: 8px; }
  table { width: 100%; border-collapse: collapse; font-size: 13.5px; }
  th, td { border-bottom: 1px solid #eceff1; padding: 7px 9px; text-align: left; vertical-align: top; }
  th { background: #f0f2f4; position: sticky; top: 0; white-space: nowrap; }
  #frases th { cursor: pointer; user-select: none; }
  #frases th[aria-sort="descending"]::after { content: " ▼"; color: #ff9900; }
  #frases th[aria-sort="ascending"]::after { content: " ▲"; color: #ff9900; }
  td.num, th.num { text-align: right; white-space: nowrap; }
  td small { display: block; color: #6b7780; font-size: 12px; line-height: 1.35; margin-top: 2px; }
  td.fr { font-weight: 600; min-width: 150px; }
  #frases td.fr, #frases th:first-child { position: sticky; left: 0; background: #fff; z-index: 1;
    box-shadow: 1px 0 0 #e0e0e0; }
  #frases th:first-child { background: #f0f2f4; z-index: 2; }
  #frases td:nth-child(2) { min-width: 190px; }
  .vd { display: inline-block; font-size: 12px; font-weight: 700; padding: 1px 7px; border-radius: 10px; white-space: nowrap; }
  .v-frase { background: #b3261e; color: #fff; } .v-exacta { background: #f6c9c4; color: #7a1711; }
  .v-madurar { background: #fff0c2; color: #6b4e00; } .v-oport { background: #2e7d32; color: #fff; }
  .v-nucleo { background: #cfe8d2; color: #1b5e20; } .v-ya { background: #e0e4e8; color: #455a64; }
  .filtros { display: flex; flex-wrap: wrap; gap: 6px; align-items: center; margin: 8px 0 10px; }
  .filtros button { border: 1px solid #cfd8dc; background: #fff; border-radius: 16px; padding: 5px 12px;
    font-size: 14px; cursor: pointer; }
  .filtros button[aria-pressed="true"] { background: #232f3e; color: #fff; border-color: #232f3e; }
  .filtros input { flex: 1 1 180px; padding: 6px 10px; border: 1px solid #cfd8dc; border-radius: 6px; font-size: 15px; }
  .meta { font-size: 13px; color: #6b7780; text-align: left; margin: 6px 0; }
  .semana { background: #fff; border: 1px solid #e0e0e0; border-radius: 8px; padding: 12px 16px; margin: 0 0 12px; }
  .semana h3 { margin: 0 0 4px; }
  .semana ul { margin: 6px 0 0; padding-left: 18px; }
  .semana li { text-align: left; margin: 2px 0; }
  details summary { cursor: pointer; color: #007185; }
  @media (max-width: 640px) {
    body { margin: 16px auto; padding: 0 12px; font-size: 16px; }
    .cajas { grid-template-columns: 1fr; }
    .paso { padding: 14px 12px; gap: 10px; }
    .n { font-size: 32px; min-width: 26px; }
    .paso p, .estado, .regla p { text-align: left; }
    table { font-size: 13px; }
  }
""".strip("\n")

JS = r"""
(function () {
  function copiar(b) {
    var ta = document.getElementById(b.getAttribute('data-de'));
    var listo = function () { b.textContent = 'Copiado'; b.classList.add('hecho');
      setTimeout(function () { b.textContent = 'Copiar'; b.classList.remove('hecho'); }, 2000); };
    if (navigator.clipboard && window.isSecureContext) {
      navigator.clipboard.writeText(ta.value).then(listo, function () { ta.select(); document.execCommand('copy'); listo(); });
    } else { ta.focus(); ta.select(); ta.setSelectionRange(0, ta.value.length); document.execCommand('copy'); listo(); }
  }
  Array.prototype.forEach.call(document.querySelectorAll('.copiar'), function (b) {
    b.addEventListener('click', function () { copiar(b); });
  });
  var tabla = document.getElementById('frases');
  if (!tabla) return;
  var cuerpo = tabla.tBodies[0], filtro = 'todas', texto = '';
  var cuenta = document.getElementById('cuenta');
  function aplicar() {
    var n = 0;
    Array.prototype.forEach.call(cuerpo.rows, function (r) {
      var ok = (filtro === 'todas' || r.getAttribute('data-v') === filtro) &&
               (!texto || r.getAttribute('data-t').indexOf(texto) >= 0);
      r.style.display = ok ? '' : 'none'; if (ok) n++;
    });
    cuenta.textContent = n + (n === 1 ? ' frase' : ' frases');
  }
  Array.prototype.forEach.call(document.querySelectorAll('.filtros button'), function (b) {
    b.addEventListener('click', function () {
      Array.prototype.forEach.call(document.querySelectorAll('.filtros button'), function (o) { o.setAttribute('aria-pressed', 'false'); });
      b.setAttribute('aria-pressed', 'true'); filtro = b.getAttribute('data-f'); aplicar();
    });
  });
  document.getElementById('buscar').addEventListener('input', function (ev) { texto = ev.target.value.trim().toLowerCase(); aplicar(); });
  Array.prototype.forEach.call(tabla.tHead.rows[0].cells, function (th, i) {
    th.addEventListener('click', function () {
      var desc = th.getAttribute('aria-sort') !== 'descending';
      Array.prototype.forEach.call(tabla.tHead.rows[0].cells, function (o) { o.removeAttribute('aria-sort'); });
      th.setAttribute('aria-sort', desc ? 'descending' : 'ascending');
      var filas = Array.prototype.slice.call(cuerpo.rows);
      filas.sort(function (a, b) {
        var x = a.cells[i], y = b.cells[i];
        var nx = x.getAttribute('data-s'), ny = y.getAttribute('data-s');
        var r = (nx !== null && ny !== null) ? parseFloat(nx) - parseFloat(ny)
                : x.textContent.localeCompare(y.textContent, 'es');
        return desc ? -r : r;
      });
      filas.forEach(function (f) { cuerpo.appendChild(f); });
    });
  });
  aplicar();
})();
""".strip("\n")


def pagina(frases, fichas, otros, por_semana, repetidas, p, extra) -> tuple[str, dict]:
    cpc_ult = extra["cpc"]
    base_ped, base_clics = extra["base"]
    clasif = {t: veredicto(f, p) for t, f in frases.items()}
    cuenta = defaultdict(int)
    for v, _ in clasif.values():
        cuenta[v] += 1
    ult = max(por_semana)
    desde_u, hasta_u, _ = por_semana[ult]
    eq = CONTRIBUCION * p
    cero = (1 - p) ** CLICS_DECIDIR
    cinco = (1 - p) ** 5

    neg_frase = sorted({familia_de(t) for t, (v, _) in clasif.items() if v == "Negativa de frase"},
                       key=lambda f: list(FAMILIAS).index(f))
    neg_exacta = sorted(t for t, (v, _) in clasif.items() if v == "Negativa exacta")

    # Tabla: por clics y después gasto.
    orden = sorted(frases.values(), key=lambda f: (-f["clics"], -f["gasto"], f["frase"]))
    filas_html = "\n".join(fila(f, *clasif[f["frase"]]) for f in orden)
    botones = ['<button type="button" data-f="todas" aria-pressed="true">Todas</button>'] + [
        f'<button type="button" data-f="{e(v)}" aria-pressed="false">{e(v)} ({cuenta[v]})</button>'
        for v in ORDEN if cuenta[v]]

    # Cuadro de familias.
    fam_filas = []
    for fam, motivo in FAMILIAS.items():
        miembros = [f for t, f in frases.items() if familia_de(t) == fam]
        if not miembros:
            continue
        cl = sum(f["clics"] for f in miembros)
        ga = sum(f["gasto"] for f in miembros)
        pe = sum(f["pedidos"] for f in miembros)
        fam_filas.append(
            f'<tr><td><code>{e(fam)}</code></td><td>{e(motivo)}<small>{e(", ".join(sorted(f["frase"] for f in miembros)))}</small></td>'
            f'<td class="num">{int(cl)}</td><td class="num">{plata(ga)}</td><td class="num">{int(pe)}</td></tr>')
    no_fam = "".join(f"<tr><td>{e(k)}</td><td colspan=\"4\">{e(v)}</td></tr>" for k, v in NO_FAMILIAS.items())

    # Semanas, la última arriba.
    primeras = {t: min(f["semanas"]) for t, f in frases.items()}
    bloques = []
    for n in sorted(por_semana, reverse=True):
        desde, hasta, tot = por_semana[n]
        nuevas = sorted((frases[t] for t in frases if primeras[t] == n), key=lambda f: (-f["clics"], f["frase"]))
        con_clic = sum(1 for f in frases.values() if n in f["semanas"])
        items = "".join(
            f'<li><strong><bdi>{e(f["frase"])}</bdi></strong> · {f["semanas"][n][0]} clic{"s" if f["semanas"][n][0] != 1 else ""}'
            f'{" · " + str(f["semanas"][n][1]) + " pedido" + ("s" if f["semanas"][n][1] != 1 else "") if f["semanas"][n][1] else ""}'
            f' · <span class="vd {CLASE[clasif[f["frase"]][0]]}">{e(clasif[f["frase"]][0])}</span></li>'
            for f in nuevas)
        nota = NOTAS_SEMANA.get(n, "")
        bloques.append(
            f'<div class="semana" id="semana-{n}"><h3>Semana {n} · {fecha(desde)} al {fecha(hasta)}</h3>'
            f'<p class="meta">{con_clic} frases con clics, {len(nuevas)} nuevas · semana entera: '
            f'{int(tot["clics"])} clics, {int(tot["pedidos"])} pedidos, {plata(tot["gasto"])}</p>'
            + (f"<p>{e(nota)}</p>" if nota else "") + f"<ul>{items}</ul></div>")

    # Repetidas.
    multi = sorted((f for f in frases.values() if len(f["semanas"]) > 1), key=lambda f: (-f["clics"], f["frase"]))
    rep_items = "".join(
        f'<li><strong><bdi>{e(f["frase"])}</bdi></strong>: semanas {", ".join(str(n) for n in sorted(f["semanas"]))} · '
        f'{int(f["clics"])} clics, {int(f["pedidos"])} pedidos</li>' for f in multi)
    pisadas = "".join(f"<li>{e(t)} ({c} clic{'s' if c != 1 else ''}, {ped} pedido{'s' if ped != 1 else ''})</li>"
                      for _, t, c, ped in repetidas)

    nfichas = int(fichas["n_lineas"])
    oport = "".join(f"<li><strong>{e(t)}</strong>: {e(m)}.</li>" for t, m in OPORTUNIDADES.items())
    fadult = frases.get("tongue scraper for adults")
    p_adult = binom_ge(int(fadult["pedidos"]), int(fadult["clics"]), p) if fadult else None

    cuerpo = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Frases — Seguimiento de Ads · Zriceros en Amazon</title>
<style>
{CSS}
</style>
</head>
<body>
<!-- menu --><!-- /menu -->

<h1>Frases: qué búsqueda sí, cuál no</h1>

<p class="estado">{len(frases)} frases con clics en {len(por_semana)} semanas. {len(neg_frase)} negativas de frase y {len(neg_exacta)} exactas, listas para pegar en la automática.</p>
<p class="meta">Datos hasta el informe de la semana {ult} ({fecha(desde_u)} al {fecha(hasta_u)}). Hoja generada el {fecha_hoy()} con <code>scripts/frases.py</code>.</p>

<h2 id="pasos">ESTA SEMANA</h2>

<div class="paso"><span class="n">1</span><div class="t">
<h3>Cuándo</h3>
<p>Ahora: tocaba el 27-10, con el informe de la semana 8.</p>
<p>Va junto con «solo reducir» (<a href="reporte-campanas-zriceros-semana-8.html#pasos">semana 8, paso 1</a>).</p>
</div></div>

<div class="paso"><span class="n">2</span><div class="t">
<h3>Entrar a las negativas de la automática</h3>
<p><a href="https://advertising.amazon.com/cm/campaigns">advertising.amazon.com/cm/campaigns</a>, cuenta <em>lombardi company</em>, <em>Estados Unidos</em>.</p>
<p>Clic en <em>Campaña - 9/1/2026 automatica</em> → <em>Grupo RASPADOR - 9/1/2026</em>.</p>
<p>Menú de la izquierda → <em>Segmentación negativa</em> (o <em>Palabras clave negativas</em>).</p>
<span class="et no">Si no está así</span>
<p>Ves ASIN en vez de palabras: es <em>Productos negativos</em>. Volver y elegir la otra.</p>
</div></div>

<div class="paso"><span class="n">3</span><div class="t">
<h3>Las de frase</h3>
<p><em>Añadir palabras clave negativas</em> → concordancia <em>Frase negativa</em>.</p>
<p>Pegar la caja 1 (botón <em>Copiar</em>, <a href="#cajas">abajo</a>) → <em>Añadir</em> → <em>Guardar</em>.</p>
<span class="et ok">Tiene que decir</span>
<p>{len(neg_frase)} filas nuevas, todas <em>Frase negativa</em>.</p>
</div></div>

<div class="paso"><span class="n">4</span><div class="t">
<h3>Las exactas</h3>
<p>Otra vez <em>Añadir palabras clave negativas</em> → <em>Negativa exacta</em>.</p>
<p>Pegar la caja 2 → <em>Añadir</em> → <em>Guardar</em>.</p>
<span class="et ok">Tiene que decir</span>
<p>{len(neg_exacta)} filas nuevas <em>Negativa exacta</em>, más las siete de la manual.</p>
<span class="et no">Si no está así</span>
<p>Amazon avisa que una ya existe: seguir, no es un error.</p>
</div></div>

<div class="paso"><span class="n">5</span><div class="t">
<h3>Lo que no se agrega</h3>
<p>Nada que no esté en las cajas.</p>
<p>Nunca de frase <code>tongue scraper</code>, <code>electric</code>, <code>case</code> ni <code>kit</code> solas.</p>
<p>La manual, sus tres exactas nuevas y el presupuesto van en la <a href="reporte-campanas-zriceros-semana-8.html#pasos">semana 8, pasos 2 y 3</a>.</p>
</div></div>

<div class="paso"><span class="n">6</span><div class="t">
<h3>Cómo se verifica</h3>
<p>En el informe de la semana 9 no sale ninguna frase de las cajas.</p>
<p>Si sale una, la negativa no se guardó: repetir el paso 3 o 4.</p>
</div></div>

<p class="meta">CAMBIO de la semana 7: decía que las búsquedas sueltas no se cortaban de a una. Por familia de palabra, sí.</p>

<h2 id="cajas">PARA COPIAR Y PEGAR</h2>
<div class="cajas">
<div class="caja"><h3>Caja 1 · Frase negativa ({len(neg_frase)})</h3>
<textarea id="caja-frase" rows="{len(neg_frase)}" readonly>{e(chr(10).join(neg_frase))}</textarea>
<button type="button" class="copiar" data-de="caja-frase">Copiar</button></div>
<div class="caja"><h3>Caja 2 · Negativa exacta ({len(neg_exacta)})</h3>
<textarea id="caja-exacta" rows="{len(neg_exacta)}" readonly>{e(chr(10).join(neg_exacta))}</textarea>
<button type="button" class="copiar" data-de="caja-exacta">Copiar</button></div>
</div>

<h2 id="regla">LA REGLA</h2>
<div class="card regla">
<p><strong>1.</strong> No encaja con el producto: negativa ya, sin esperar clics.</p>
<p><strong>2.</strong> Encaja y no vendió: esperar {CLICS_DECIDIR} clics. Con 5 clics, cero pedidos pasa {pct(cinco, 0)} de las veces.</p>
<p><strong>3.</strong> {CLICS_DECIDIR} clics sin pedido: negativa exacta. Le pasa sólo al {pct(cero, 0)} de las frases que convierten {pct(p)}.</p>
<p><strong>4.</strong> Vendió: gana si convierte más que CPC ÷ $9,00. Hoy, a {plata(cpc_ult)}, eso es {pct(cpc_ult / CONTRIBUCION)}.</p>
</div>
<p class="meta">{pct(p)} es la conversión de todas las búsquedas tipeadas: {base_ped} pedidos en {base_clics} clics, {len(por_semana)} semanas. La semana 7 decía 17,8% porque sumaba 2 clics sin término. Equilibrio por clic: $9,00 × {pct(p)} = {plata(eq)}. {plata(cpc_ult)} es el CPC de búsqueda de la semana {ult}.</p>
<p><strong>Frase o exacta.</strong> De frase cuando una palabra sola describe otro producto: corta todas sus variantes. Exacta cuando la frase entera no encaja pero sus palabras sí salen en búsquedas que venden. Las negativas van sólo en la automática: la manual puja por sus siete exactas y PRIMALS está pausada, así que ninguna otra campaña hereda esas subastas.</p>

<h3>Las familias</h3>
<div class="tabla"><table>
<thead><tr><th>Negativa de frase</th><th>Por qué · qué frases corta</th><th class="num">Clics</th><th class="num">Gasto</th><th class="num">Pedidos</th></tr></thead>
<tbody>
{chr(10).join(fam_filas)}
<tr><th colspan="5">No van como negativa</th></tr>
{no_fam}
</tbody></table></div>

<h2 id="oportunidades">OPORTUNIDADES</h2>
<ul>{oport}</ul>
<p>«tongue scraper for adults»: {int(fadult["pedidos"]) if fadult else 0} pedidos en {int(fadult["clics"]) if fadult else 0} clics. Si convirtiera como el promedio ({pct(p)}), eso pasaría {pct(p_adult or 0, 1)} de las veces: convierte más, de verdad.</p>

<h2 id="tabla">TODAS LAS FRASES</h2>
<div class="filtros">{"".join(botones)}<input id="buscar" type="search" placeholder="Buscar una frase" aria-label="Buscar una frase"></div>
<p class="meta"><span id="cuenta">{len(frases)} frases</span>. Clic en un título para ordenar. Las impresiones son un piso: el informe sólo trae búsquedas con clic.</p>
<div class="tabla"><table id="frases">
<thead><tr><th>Frase</th><th>Veredicto</th><th>Semanas</th><th>Campaña</th><th class="num">Impr.</th><th class="num">Clics</th><th class="num">CTR</th><th class="num">Gasto</th><th class="num">CPC</th><th class="num">Pedidos</th><th class="num">Ventas</th><th class="num">Conv.</th><th class="num">ACoS</th><th class="num">Neto</th></tr></thead>
<tbody>
{filas_html}
</tbody></table></div>
<p class="meta">Neto = unidades × $9,00 − gasto. Las compras llegan hasta 7 días después del clic: los últimos días de cada informe pueden sumar.</p>
<p class="meta">Fuera de la tabla: {nfichas} líneas de fichas ajenas (ASIN, no son frases: {int(fichas["clics"])} clics, {int(fichas["pedidos"])} pedidos, {plata(fichas["gasto"])}; se manejan con la puja de Sustitutos y Complementos) y {int(otros["clics"])} clics sin término.</p>

<h2 id="semanas">SEMANA POR SEMANA</h2>
<p>Cada semana suma las frases que aparecieron por primera vez.</p>
{chr(10).join(bloques)}

<h2 id="repetidas">LAS REPETIDAS</h2>
<p>Cada frase es una sola fila en la tabla, con todas sus semanas sumadas.</p>
<ul>{rep_items}</ul>
<p>Estas líneas del 13-10 estaban en el informe de la semana 6 y en el de la 7: el mismo clic, contado una vez.</p>
<ul>{pisadas}</ul>

<p class="meta">Fuentes: informes de términos de búsqueda de Sponsored Products, semanas 1 a {ult}. Contribución $9,00 por unidad y equilibrio 45,2%, de la hoja de la semana 1.</p>

<!-- pie-menu --><!-- /pie-menu -->
<script>
{JS}
</script>
</body>
</html>
"""
    return cuerpo, {"cuenta": dict(cuenta), "frase": neg_frase, "exacta": neg_exacta, "clasif": clasif}


MESES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]


def fecha(iso: str) -> str:
    a, m, d = iso.split("-")
    return f"{int(d)} {MESES[int(m) - 1]}"


def fecha_hoy() -> str:
    return date.today().isoformat()


def conservar_menu(nuevo: str) -> str:
    """Deja el menú y el pie que ya tenía la hoja (los pone menu.py)."""
    if not HOJA.exists():
        return nuevo
    viejo = HOJA.read_text(encoding="utf-8")
    for marca in ("menu", "pie-menu"):
        m = re.search(rf"<!-- {marca} -->.*?<!-- /{marca} -->", viejo, re.S)
        if m:
            nuevo = re.sub(rf"<!-- {marca} -->.*?<!-- /{marca} -->", lambda _: m.group(0), nuevo, count=1, flags=re.S)
    return nuevo


def main() -> int:
    frases, fichas, otros, por_semana, repetidas, p, extra = juntar()
    ok = True

    print(f"Conversión de búsquedas: {pct(p)} · equilibrio por clic {plata(CONTRIBUCION * p)}"
          f" · {CLICS_DECIDIR} clics sin pedido: {pct((1 - p) ** CLICS_DECIDIR)}")
    for n, (desde, hasta, tot) in sorted(por_semana.items()):
        esperado = HOJAS_TOTALES.get(n)
        txt = f"  semana {n}: {int(tot['clics'])} clics, {plata(tot['gasto'])}, {int(tot['pedidos'])} pedidos"
        if esperado:
            igual = (int(tot["clics"]), round(tot["gasto"], 2), int(tot["pedidos"])) == esperado
            ok &= igual
            txt += " · hoja " + ("OK" if igual else f"NO COINCIDE {esperado}")
        print(txt)

    cuerpo, res = pagina(frases, fichas, otros, por_semana, repetidas, p, extra)
    print("Veredictos:", ", ".join(f"{v} {res['cuenta'].get(v, 0)}" for v in ORDEN))
    print("Frase negativa:", ", ".join(res["frase"]))
    print("Negativa exacta:", ", ".join(res["exacta"]))

    # Controles: una negativa nunca puede tapar una frase que vendió ni las de la manual.
    vendieron = [t for t, f in frases.items() if f["pedidos"]] + list(MANUAL) + list(NUCLEO) + list(OPORTUNIDADES)
    for fam in res["frase"]:
        for t in vendieron:
            if contiene(t, fam):
                ok = False
                print(f"  OJO: la negativa de frase «{fam}» taparía «{t}»", file=sys.stderr)
    for t in res["exacta"]:
        if frases[t]["pedidos"]:
            ok = False
            print(f"  OJO: «{t}» vendió y está como negativa exacta", file=sys.stderr)
    for t in list(EXACTAS) + list(OPORTUNIDADES) + list(NOTAS_FRASE):
        if t not in frases:
            print(f"  aviso: «{t}» está en las listas pero no en ningún informe", file=sys.stderr)
    sin = [t for t, (v, m) in res["clasif"].items() if v == "Madurar" and m.startswith("encaja")
           and min(frases[t]["semanas"]) == max(por_semana)]
    if sin:
        print(f"Nuevas de la semana {max(por_semana)} que quedaron en «Madurar» por defecto (revisar si alguna no encaja):")
        for t in sorted(sin):
            print("   ", t)

    if "--poner" in sys.argv:
        nuevo = conservar_menu(cuerpo)
        viejo = HOJA.read_text(encoding="utf-8") if HOJA.exists() else ""
        # La fecha de generación no cuenta como cambio.
        if re.sub(r"generada el \S+", "", nuevo) != re.sub(r"generada el \S+", "", viejo):
            HOJA.write_text(nuevo, encoding="utf-8")
            print(f"actualizada: {HOJA.name}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
