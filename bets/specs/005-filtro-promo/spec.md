# Spec 005 — Filtro de promo "ventaja de 2 goles"

## Contexto y objetivo
Bet365 y otras casas ofrecen la promo **"ventaja de 2 goles"**: si el equipo al
que apuestas a ganar va 2 goles arriba y no acaba ganando, la casa te paga la
apuesta como ganada igualmente. Eso convierte una pata de ganar (resultado 1 o 2)
colocada en una de esas casas en un **posible pago doble**: cobrarías en la casa
con promo **y** en la cobertura del resultado que realmente salió. Esta
funcionalidad añade un **filtro global opcional** que, cuando se activa, obliga a
que las patas de ganar se cojan de una lista de casas con promo y muestra, de
forma **determinista** (sin probabilidades), la decisión: cuánto **cuesta** usar
esa casa en vez de la que mejor paga, y cuánto sería el **windfall** si salta la
ventaja. Es un extra combinable con `compare`, `surebet`, `freebet` y `bonus`; el
usuario decide si le compensa. No calcula la probabilidad de que salte la promo:
solo magnitudes.

## Usuarios / actores
- **Apostador** (el propio usuario): quiere posicionar sus patas de ganar en
  casas con la promo de 2 goles y ver el coste y el posible premio para decidir si
  activarla en cada cálculo.

## Historias de usuario
- H1: Como apostador quiero indicar una lista de casas con promo y que el sistema
  ponga mis patas de ganar en ellas, para poder cobrar la ventaja de 2 goles.
- H2: Como apostador quiero ver cuánto retorno pierdo por usar la casa con promo
  en vez de la que mejor paga, para saber el coste de la decisión.
- H3: Como apostador quiero ver el windfall (pago extra) si salta la ventaja, para
  sopesarlo contra ese coste.
- H4: Como apostador quiero elegir asegurar una o las dos patas de ganar, para
  ajustar cuánto pago y cuántas oportunidades de windfall tengo.
- H5: Como apostador quiero que el filtro funcione con compare, surebet, freebet y
  bonus, para no depender del comando que use.

## Requisitos funcionales (criterios de aceptación en EARS)

### Activación y entrada
- RF-1: DONDE el usuario active el filtro de promo, EL SISTEMA recibe una lista de
  casas con promo.
- RF-2: MIENTRAS el filtro de promo esté desactivado, EL SISTEMA se comporta
  exactamente igual que sin esta funcionalidad.
- RF-3: SI se activa el filtro sin ninguna casa en la lista, ENTONCES EL SISTEMA
  aborta con un mensaje de error y termina con código de salida distinto de 0.
- RF-4: CUANDO el filtro está activo, EL SISTEMA presenta, por partido, tres
  opciones de posicionamiento —asegurar el 1, asegurar el 2 y asegurar ambos—,
  cada una con su coste (y su windfall donde aplique).
- RF-5: EL SISTEMA compara los nombres de las casas de la lista ignorando
  mayúsculas/minúsculas y espacios exteriores (igual que el resto del proyecto).

### Selección de patas
- RF-6: CUANDO el filtro está activo, EL SISTEMA elige la mejor cuota de cada pata
  de ganar asegurada solo entre las casas de la lista, no entre todas.
- RF-7: EL SISTEMA nunca restringe el resultado X: su mejor cuota se elige entre
  todas las casas (que una casa de la lista salga también en la X no penaliza).
- RF-8: CUANDO se posiciona una pata de ganar, EL SISTEMA usa la mejor cuota de
  ese resultado entre las casas de la lista.
- RF-9: CUANDO se posicionan ambas patas de ganar, EL SISTEMA usa casas de la
  lista en el 1 y en el 2.
- RF-10: SI en un partido ninguna casa de la lista ofrece cuota válida en una pata
  de ganar que se iba a asegurar, ENTONCES EL SISTEMA no aplica la promo en esa
  pata, usa su mejor cuota normal y avisa.

### Coste y windfall
- RF-11: EL SISTEMA muestra, por cada pata de ganar asegurada, el coste relativo:
  la diferencia de retorno entre usar la casa con promo y usar la mejor cuota
  disponible sin la restricción para ese resultado.
- RF-12: EL SISTEMA nombra la casa de mejor cuota sin la restricción que usa como
  referencia del coste.
- RF-13: SI la mejor cuota disponible de un resultado ya es de una casa de la
  lista, ENTONCES el coste relativo de esa pata es 0 (seguro sin coste).
- RF-14: DONDE el comando maneja importes (surebet, freebet, bonus), EL SISTEMA
  muestra el windfall de cada pata asegurada, igual al importe apostado en esa
  pata multiplicado por su cuota.
- RF-15: EL SISTEMA advierte de que los windfalls de las dos patas de ganar pueden
  acumularse (caso de doble remontada que acaba en empate).
- RF-16: MIENTRAS el comando no maneje importes (compare), EL SISTEMA muestra solo
  el impacto en el % de pago, sin windfall en euros.
- RF-17: EL SISTEMA muestra las tres opciones de posicionamiento (asegurar 1,
  asegurar 2 y asegurar ambos) juntas para que el usuario compare y decida cuál
  colocar.

### Aplicación por comando
- RF-18: DONDE se use en `compare`, EL SISTEMA calcula el % de pago con las cuotas
  de las patas aseguradas y muestra su coste relativo.
- RF-19: DONDE se use en `surebet`, EL SISTEMA reparte el stake con las cuotas de
  las patas aseguradas y muestra su coste y su windfall.
- RF-20: DONDE se use en `freebet`, EL SISTEMA elige las coberturas de resultados
  de ganar aseguradas entre las casas de la lista y muestra su coste y windfall.
- RF-21: DONDE se use en `bonus`, EL SISTEMA elige las coberturas de resultados de
  ganar aseguradas entre las casas de la lista y muestra su coste y windfall.

### Salida y recordatorio
- RF-22: CUANDO el usuario solicite la salida JSON, EL SISTEMA incluye, por cada
  pata asegurada, la casa, el coste relativo (con la casa de referencia) y el
  windfall donde aplique.
- RF-23: EL SISTEMA recuerda al usuario que las cuotas pueden haber cambiado y que
  debe verificarlas justo antes de apostar (constitución nº 9).

## Requisitos no funcionales
- Para usar el filtro se parte de las cuotas por casa (Formato A): el filtro
  necesita el detalle por casa para posicionar patas, no basta el resumen de
  mejores cuotas.
- El coste y el windfall se calculan con precisión decimal, sin `float`; el
  redondeo a dos decimales ocurre solo al presentar (constitución nº 8).
- Los mensajes y las tablas se muestran en español (constitución nº 6).
- El sistema no accede a la red: la lista de casas y el número de patas son
  entrada del usuario (constitución nº 7).

## Casos límite
- Filtro desactivado → los comandos se comportan como antes (RF-2).
- Lista vacía → error y salida ≠ 0 (RF-3).
- Las tres opciones (asegurar 1, asegurar 2, asegurar ambos) se muestran juntas
  con su coste para comparar (RF-4, RF-17).
- Casa de la lista que no aparece en el archivo → simplemente no se usa.
- Ninguna casa de la lista cotiza una pata asegurada en un partido → no se aplica
  ahí, con aviso (RF-10).
- La mejor cuota de un resultado ya es de una casa de la lista → coste 0, seguro
  gratis (RF-13).
- `compare` (sin importes) → solo coste relativo, sin windfall en euros (RF-16).
- Doble remontada que acaba en empate → los dos windfalls se suman (RF-15).

## Fuera de alcance
- Calcular la **probabilidad** de que salte la ventaja de 2 goles: el filtro solo
  da magnitudes (coste y windfall) y el usuario decide.
- La estrategia de **combinada con aumento** (acca boost) y su cobertura
  secuencial: pospuesta a una spec posterior.
- Aplicar la promo a la **pata gratis** de freebet o a la **pata anclada** de
  bonus cuando coincidan con una casa de la lista: el filtro solo posiciona las
  patas cuya cuota elige el sistema (mejores cuotas y coberturas).
- Elegir automáticamente si "compensa" activar la promo: la herramienta muestra
  las cifras; la decisión es del usuario.
- Mercados que no sean 1X2 de tres resultados.
- Otras promociones distintas de la ventaja de 2 goles.

## Criterios de finalización
- Todos los RF con test automático en verde (pytest), incluida una comprobación
  numérica del coste relativo (retorno con casa de promo vs mejor casa) y del
  windfall (importe × cuota) en un comando con importes.
- Demo manual: (a) `compare` con el filtro que baja el % de pago y muestra el
  coste relativo nombrando la casa de referencia, (b) un caso donde la casa con
  promo ya es la que mejor paga → coste 0, (c) `surebet` (o freebet/bonus) con el
  windfall en euros, (d) asegurar 1 vs 2 patas, (e) un partido donde ninguna casa
  de la lista cotiza una pata → aviso y cuota normal, y (f) la salida `--json`.
- Verificado el comportamiento con el filtro desactivado (idéntico a antes),
  lista vacía y número de patas inválido (error y salida ≠ 0).

## Dudas abiertas
- Ninguna pendiente: entrada (lista de casas), las tres opciones de
  posicionamiento (asegurar 1, 2 y ambos) con su coste, X libre, fallback sin casa
  de promo, coste relativo, windfall, aplicación a los cuatro comandos y alcance
  (magnitudes, no probabilidades) quedaron cerrados en el debate previo y en la
  entrevista, y recogidos en RF-1 a RF-23.
