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

**La hoja cierra con un paso a paso, no con propuestas.** Desde la semana 3
(pedido de Ariel: *«pones un paso a paso al final como los proximos pasos pero
mas detallado»*) la última sección es «Los próximos pasos, uno por uno» (ancla
`#pasos`): un paso por acción, numerado por impacto, y cada uno con las mismas
cinco filas —**dónde** tocar en el panel, **qué** poner, **por qué**, qué **no**
hacer y **cómo se verifica** en el informe de la semana siguiente—. Cierra con
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
