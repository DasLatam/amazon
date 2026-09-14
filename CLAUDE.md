# amazon — Zriceros en Amazon USA

Ficha en el tablero: `amazon-listings`. Portal `:8089` (`serve.py`), público en
https://daslatam.github.io/amazon/ vía `scripts/sync_github.sh`, que **corre por
cron cada 5 minutos y commitea todo lo que no esté en `.gitignore`**. Cualquier
archivo que se deje en la carpeta se publica solo, en un repo público.

## El seguimiento semanal de Amazon Ads

Una hoja por semana: `reporte-campanas-zriceros.html` (semana 1),
`reporte-campanas-zriceros-semana-N.html` (las siguientes), enlazadas entre sí y
desde `index.html`. Las hojas viejas no se reescriben: si un número de una semana
anterior resultó mal, se agrega una nota de corrección.

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

## Pendientes

Las acciones que sólo puede hacer Ariel en Seller Central van a
`tablero/storage/pendientes.json` con `"grupo": "zriceros"` (sin `peso`: es una
bitácora de un caso real, no compite en prioridad). Actualizarlas con cada semana:
una propuesta basada en datos viejos que queda en la lista se ejecuta igual.
