# amazon — Zriceros en Amazon USA

Ficha en el tablero: `amazon-listings`. Portal `:8089` (`serve.py`), público en
https://daslatam.github.io/amazon/ vía `scripts/sync_github.sh`, que **corre por
cron cada 5 minutos y commitea todo lo que no esté en `.gitignore`**. Cualquier
archivo que se deje en la carpeta se publica solo, en un repo público.

## El menú de las hojas

Todas las hojas comparten el menú de arriba y el «anterior / siguiente» de abajo,
y los genera `scripts/menu.py` desde la lista `SECCIONES` (Producto → Plan →
Seguimiento de Ads); también pone los `<title>`. El menú tiene dos niveles: las
secciones son links a su hoja principal (Seguimiento abre la última semana) y
debajo aparecen las hojas de la sección actual. La primera versión mostraba los
nombres de sección como rótulos sueltos al lado de los links, parecían botones
y no hacían nada: un rótulo en una barra de navegación tiene que ser un link. **Hoja nueva: sumarla a
`SECCIONES` y correr `/usr/bin/python3 scripts/menu.py`.** Si queda un `.html`
fuera de la lista, el script lo avisa y sale con 1. No editar a mano lo que está
entre `<!-- menu -->` y `<!-- /menu -->`: la próxima corrida lo pisa. Es HTML
estático y no JS porque la hoja de reseñas se sirve también desde el tablero por
https, y un script pedido por http al :8089 se bloquearía.

## El seguimiento semanal de Amazon Ads

Una hoja por semana: `reporte-campanas-zriceros.html` (semana 1),
`reporte-campanas-zriceros-semana-N.html` (las siguientes), enlazadas entre sí y
desde `index.html`. Las hojas viejas no se reescriben: si un número de una semana
anterior resultó mal, se agrega una nota de corrección.

## Cómo se le escribe a Ariel en estas hojas

Tres reglas que puso el 2026-09-21 y que valen para todas las hojas del
proyecto, no sólo para el seguimiento semanal:

1. **La hoja es su informe: no se le hacen preguntas ni se le piden datos.**
   *«tampoco hagamos preguntas como si no supiera, en teoria es un informe mio y
   se lo que esta pasando»*. Se cayó por eso una sección entera («lo que hay que
   anotar del panel: presupuesto configurado, puja de la automática, ¿le
   subieron algo esta semana?»). **Tampoco lleva la sección roja «Lo que esta
   hoja no puede afirmar»** (se sacó en la semana 5, 2026-10-10: *«no suma esas
   aclaraciones solo traen mas preguntas»*). Un límite que cambia la lectura de
   un número va en una línea al lado de ese número (como la nota de los nueve
   días o la de atribución bajo la tabla); el resto no se escribe.
2. **No se recomienda lo que no está disponible.** *«las reseñas en general
   paremos con recomendar cosas que no hay como vine y esas cosas»*. Vine,
   Brand Registry e IP Accelerator salieron de los próximos pasos y del índice.
   `resenas-zriceros.html` los conserva porque es **hoja de referencia**: está
   para consultarla, y el índice ahora lo dice con esas palabras. En un plan de
   acción sólo entra lo que se puede hacer esta semana.
3. **Una recomendación que cambia, se dice que cambió.** La imagen principal
   venía propuesta **cuadrada de 1.600**; desde el 2026-09-21 va **vertical
   1.600×2.000 (4:5)**, *«que sea mas vertical para que funcione en las
   miniaturas»*. Las hojas viejas no se reescriben, así que el pendiente y la
   hoja nueva arrancan diciendo «CAMBIO de la propuesta anterior». Si no, la
   contradicción entre dos hojas parece un error y no una decisión.

## El registro de solicitudes de reseña

`datos/resenas_solicitadas.csv` + `scripts/resenas.py`. Existe porque el botón
«Solicitar una reseña» de Seller Central se habilita entre 5 y 30 días después
de la entrega y **después desaparece**: sin registro se vuelven a abrir los
mismos pedidos cada semana y los que se pasan se pierden sin dejar rastro.

- El CSV lleva números de pedido, así que vive en `datos/` y **no se publica**.
- `resenas.py` lo resume en el bloque `<!-- registro-resenas -->` de la hoja
  (sólo conteos, nunca los IDs), lista a cuáles se les puede pedir hoy y avisa a
  cuáles les quedan cinco días o menos. Correrlo después de cargar el CSV.
- Para qué: en unas semanas contesta **cuántas reseñas llegan por cada diez
  solicitudes**. Ese número decide si vale seguir haciéndolo a mano, y hoy sólo
  se puede estimar.

**La hoja cierra con un paso a paso, no con propuestas.** Desde la semana 3
(pedido de Ariel: *«pones un paso a paso al final como los proximos pasos pero
mas detallado»*) la última sección es «Los próximos pasos, uno por uno» (ancla
`#pasos`): un paso por acción, numerado por impacto, y cada uno con las mismas
cinco filas —**dónde** tocar en el panel, **qué** poner, **por qué**, qué **no**
hacer y **cómo se verifica** en el informe de la semana siguiente—. Van en orden
de impacto, y los que se arrastran de semanas anteriores lo dicen en el título. Cierra con
una tabla de predicción: qué tendría que dar la semana próxima si el plan sirve,
y qué significa cada número si no da. Una propuesta que no dice cómo se comprueba
vuelve a discutirse entera la semana que viene.

**Cómo llegan los datos:** Ariel deja el CSV del informe de términos de búsqueda en
el compartido SMB de srvnvidia (`smb://SRVNVIDIA._smb._tcp.local/shared/amazon/`),
que en el server es **`/home/hpp/shared/amazon/`**. Se copia a `datos/` con nombre
`semana-N_<desde>_<hasta>_terminos.csv`. `datos/` está en `.gitignore`: el CSV
trae el ID de la cuenta de anunciante y los de las campañas.

Trampas del informe de términos:

- **Sólo lista búsquedas con al menos un clic.** Los clics están completos; las
  impresiones son un piso. Sin los totales del panel de Campaign Manager no hay
  CTR: pedirlos por campaña.
- **Un ASIN en la columna «Término de búsqueda»** es la ficha de otro producto
  donde salió el anuncio, no algo que alguien tipeó.
- **El «Rango de fechas» es por fila** (primer y último día con actividad de ese
  término), no el de todo el informe. Sirve para fechar cambios: `copper` dejó de
  aparecer el 9-09, que es cuando entró la negativa.
- Amazon atribuye compras **hasta 7 días después del clic**: los últimos días de un
  informe bajado al día siguiente todavía pueden sumar ventas.
- Un mismo CPC repetido en muchas filas de una campaña es su puja (PRIMALS: $2,84).

## Las dos campañas convierten igual: lo que cambia es el precio del clic

Es el hallazgo de la semana 3 y **corrige la lectura de la semana 2**, que había
leído la caída de conversión de PRIMALS (50% → 11,5%) como un problema de
público. Con 69 clics acumulados PRIMALS convierte 18,8% y la automática 17,2%:
lo mismo, y PRIMALS arriba. El 11,5% eran 26 clics.

Toda la diferencia entre perder $34,62 y ganar $19,45 está en el CPC: $2,33
contra $0,88. **La conclusión práctica no es apagar PRIMALS —trae dos de cada
tres ventas— sino ponerle el precio bien.** Vale como regla para la próxima vez:
antes de culpar al público de una campaña, comparar su conversión con la de al
lado sobre el acumulado, no sobre la semana.

Corolario del mismo tipo: **antes de dar por mala una ficha ajena, mirar su
precio**. Las cuatro fichas que convirtieron en la semana 3 promedian $14,49 y
las cinco que no, $7,88. Nadie que esté mirando un raspador de $4,99 paga
$19,89.

## Cuando la conversión cae en las dos campañas a la vez, no es de las campañas

Semana 4 (2026-09-28): 56 clics y un pedido, con el CPC más bajo que nunca. Con
la conversión acumulada (18,4%), eso pasa 1,5 veces cada diez mil; y la
automática, que nadie tocó, cayó igual (0 en 21). **Antes de discutir pujas,
calcular la probabilidad binomial de lo observado con la conversión acumulada, por
campaña.** Si las dos caen juntas, el problema está en lo que comparten (ficha,
stock, Buy Box, precio, competidores al lado) y la única fuente es el informe
comercial de Seller Central (sesiones, % de sesiones con unidades, % de Buy Box):
la ficha pública sólo muestra cómo está hoy.

Con esa semana cambió la recomendación: la semana 3 decía no apagar PRIMALS; la 4
dice pausarla. Con cuatro semanas convierte 13,5% (no 18,8%), su equilibrio es
$1,21 y es toda la pérdida (−$91,96 contra +$0,67 de la automática). La campaña
manual queda en espera hasta que vuelva la conversión: no se lanza una campaña
nueva la semana en que se cayó.

**`bsr` de `leer_asin.extraer()` es el ranking general** (Health & Household), no
el de la categoría: el de Tongue Brushes, Scrapers & Cleaners hay que sacarlo del
texto de la ficha. Y **apareció el producto copiado**: B0C8ZCY2WM, tres
raspadores con estuche a $5,99 (y B0CFDCYPF3, 3 pack a $3,99).

## La pérdida está en las fichas ajenas, no en una campaña

Semana 5 (2026-10-10). Separando cada línea del informe por **dónde salió el
anuncio** —búsqueda tipeada o ASIN (ficha ajena)— y no por campaña, las cinco
semanas dan: búsquedas 100 clics, 16,0%, −$1,06 (empate); fichas ajenas 145
clics, 6,2%, −$124,15, que es **toda** la pérdida acumulada (−$125,21). En la
automática, 13,8% contra 2,9%. Corrige a la semana 4 («PRIMALS es toda la
pérdida»): PRIMALS perdía porque salía sobre todo en fichas ajenas y pagaba más.

**Antes de culpar a una campaña, cortar por tipo de línea** (ASIN contra
término). En la automática las fichas ajenas vienen de los grupos *Sustitutos* y
*Complementos*, que se apagan por separado: eso reemplaza a ir negativizando ASIN
de a uno (en la semana 5 aparecieron 28 fichas distintas). Y cuando se pausa una
campaña, la otra hereda sus subastas: la automática triplicó el gasto con la
misma puja.

## Una semana buena no da vuelta un veredicto, pero corrige la cuenta (semana 6)

Semana 6 (2026-10-14): 11 pedidos, +$44,48, sin haber hecho el paso 1 (apagar
Sustitutos y Complementos). Las fichas ajenas bajaron solas de 48 a 12 clics y
vendieron 3. Con 12 clics no se cambia de opinión (regla de los ~40), pero el
acumulado sí se mueve: las fichas ajenas de la automática pasaron de 2,9% a 6,1%
de conversión, y con eso el equilibrio sube de $0,26 a $0,55. **Cuando el
equilibrio de algo que se iba a apagar pasa a ser una puja que se gana, la
recomendación cambia de apagar a bajar la puja** ($0,50), y se dice que cambió.

La imagen principal corregida apareció en la ficha entre el 10 y el 14-10
(`61QDX1XG2oL`, 1278×1600, producto en 86% del alto; copia en
`images/main-2026-10-14.jpg`). Nadie avisa cuándo cambia la ficha: **leerla
siempre** con cada informe (los `hiRes` del HTML dan todas las imágenes) y comparar
el ID de la principal con el de la semana anterior. El CTR de «tongue scraper» en la
automática es la medida: 0,45% (semanas 3–5), 0,76% en la 6.

**Una campaña que no aparece en el informe de términos no prueba que no exista**:
el informe sólo trae términos con clics. Por eso el paso de la manual empieza
mirando si ya está creada.

## La imagen del diseñador (2026-10-10)

Llegó cuadrada, 1787×1787 (`images/propuestas/disenador-2026-10.jpg`): fondo 254
con piso gris y reflejo, hojas de menta, producto en 71% del alto. **En la casilla
del celular (152×224 pt, medida en `images/resultados-busqueda-celular.jpg`) una
cuadrada achica el producto** respecto de la vertical de hoy (−25%); en la grilla
de PC lo agranda. Simulación: `images/propuestas/miniaturas-semana-5.png`. Va como
imagen 2; para la principal hay que pedirle seis correcciones (pendiente `zri-ctr`).
Base del CTR para medirla: «tongue scraper» en la automática, 0,45% (semanas 3–5).

## Un CTR que cae no siempre es mala noticia sobre el anuncio

Semana 3: con «tongue scraper» negativa en PRIMALS, la automática heredó esa
subasta. Las impresiones de esa búsqueda pasaron de 170 a 1.480 y los clics de 4
a 6: el CTR cayó de 2,4% a 0,41%. **No es que el anuncio empeoró; es que ganó
subastas peores.** El informe de términos no trae la ubicación, así que la
confirmación sale del informe de ubicación del panel. De paso, es el argumento
más fuerte que hay para la imagen principal: el anuncio ahora se muestra y no lo
miran.

## Economía (no cambia mientras no cambien precio ni costos)

Precio $19,89 − tarifas $7,44 − producto $3,45 = **$9,00 de contribución**,
equilibrio **ACoS 45,2%**. Neto de una semana = unidades × $9,00 − gasto.

**Puja máxima = precio × ACoS × conversión.** La semana 1 proyectó con 36% de
conversión y eran 11 clics; con 45 clics fue 20% (techo $1,80, objetivo 30% →
$1,20). No sacar conclusiones de conversión con menos de ~40 clics.

## Leer la ficha viva

`/home/hpp/hiox/scripts/leer_asin.py` (importable: `bajar()` + `extraer()`).

- Las **estrellas y reseñas que devuelve pueden ser de un carrusel**. Las propias
  están en el bloque `id="averageCustomerReviews"` con `data-csa-c-asin` del ASIN;
  vacío = 0 reseñas (así estaba el 2026-09-14, con BSR #191 en la categoría).
- La imagen principal es el `data-old-hires` de `id="landingImage"`. El 2026-09-14
  era `51MqYyt1dBL`, **896×1195 (vertical)**; `images/main-actual.jpg` es una
  captura recortada de 350×289 y no sirve para medir.

## Reseñas y marca (verificado 2026-09-14)

Hoja: `resenas-zriceros.html`. El tablero la sirve en `https://192.168.1.71/reseñas`
leyendo el archivo en cada pedido, así que editarla no pide reiniciar nada.

- **Una solicitud directa en la USPTO no habilita Brand Registry mientras está
  pendiente.** Sólo sirve la presentada por **IP Accelerator** (tope de $700 de
  honorarios + $350 de tasa por clase). Por la vía directa hay que esperar el
  registro, unos 10 meses.
- Vine acepta marcas en Brand Registry **o productos genéricos**. Zriceros tiene
  marca: volver a «Generic» para entrar a Vine desharía la corrección de la ficha.
- New Seller Incentives (10% sobre ventas de marca, crédito de Vine) exige Brand
  Registry **dentro de los 6 meses del primer ASIN a la venta**. El de prueba
  (`B0GVZF1GN7`) ya estaba publicado el 2026-06-22.
- El inserto con QR que se decidió el 2026-06-23 armaba el enlace con el ASIN de
  **prueba**: si se imprimió así, las reseñas van a la ficha equivocada.

## Pendientes

Las acciones que sólo puede hacer Ariel en Seller Central van a
`tablero/storage/pendientes.json` con `"grupo": "zriceros"` (sin `peso`: es una
bitácora de un caso real, no compite en prioridad). Actualizarlas con cada semana:
una propuesta basada en datos viejos que queda en la lista se ejecuta igual.
