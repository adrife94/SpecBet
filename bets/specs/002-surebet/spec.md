# Spec 002 — Surebet: reparto de stake sobre arbitraje 1X2

## Contexto y objetivo
El comparador (spec 001) ya dice, para cada partido, la mejor cuota de cada
resultado 1/X/2 y su % de pago. Cuando ese % supera el 100 % existe un
**arbitraje** (surebet): repartiendo bien el dinero entre los tres resultados
se gana lo mismo gane quien gane, con beneficio garantizado. Esta funcionalidad
da el siguiente paso hacia el objetivo del proyecto —**decir dónde apostar y
cuánto**—: toma la salida del comparador y una inversión total, y calcula para
cada partido cuánto apostar a cada resultado y en qué casa, además del retorno y
el beneficio garantizados. No apuesta ni recalcula cuotas: solo reparte.

## Usuarios / actores
- **Apostador** (el propio usuario): ya ha ejecutado `compare --json` sobre sus
  cuotas y quiere saber, con un presupuesto dado, cómo repartir la apuesta entre
  resultados y casas para asegurar el resultado.

## Historias de usuario
- H1: Como apostador quiero que, dada una inversión total, el sistema me diga
  cuánto apostar a cada resultado y en qué casa, para no calcularlo a mano.
- H2: Como apostador quiero ver el retorno y el beneficio garantizados de cada
  partido, para saber si el reparto me hace ganar seguro o perder seguro.
- H3: Como apostador quiero ver también los partidos sin arbitraje señalados
  como pérdida garantizada, para descartarlos de un vistazo.
- H4: Como apostador quiero poder encadenar este resultado con las siguientes
  funcionalidades (freebet, bonos), reutilizando su salida sin recalcular.

## Requisitos funcionales (criterios de aceptación en EARS)

- RF-1: CUANDO se ejecuta surebet con la salida JSON del comparador y una
  inversión total, EL SISTEMA calcula, para cada partido con % de pago, cómo
  repartir esa inversión entre los resultados 1, X y 2.
- RF-2: EL SISTEMA reparte la inversión de modo que el retorno (importe de una
  pata multiplicado por su mejor cuota) sea el mismo sea cual sea el resultado
  ganador.
- RF-3: EL SISTEMA aplica la inversión total indicada a cada partido de forma
  independiente: la suma de los importes de las tres patas de un partido
  equivale a esa inversión.
- RF-4: EL SISTEMA muestra, por cada resultado, el importe a apostar, su mejor
  cuota y la casa donde apostarlo.
- RF-5: EL SISTEMA calcula y muestra, por partido, el retorno garantizado (igual
  en los tres resultados) y el beneficio garantizado (retorno menos inversión).
- RF-6: SI el % de pago de un partido es mayor que 100, ENTONCES EL SISTEMA lo
  señala como surebet con beneficio garantizado positivo.
- RF-7: SI el % de pago de un partido es menor o igual que 100, ENTONCES EL
  SISTEMA muestra igualmente su reparto y lo señala como pérdida garantizada
  (beneficio menor o igual que cero).
- RF-8: SI varias casas empatan en la mejor cuota de un resultado, ENTONCES EL
  SISTEMA las lista todas e indica que el importe de esa pata se apuesta íntegro
  en una cualquiera de ellas (no lo divide entre ellas).
- RF-9: SI un partido llega en la entrada marcado como incompleto (sin % de
  pago), ENTONCES EL SISTEMA no calcula su reparto y lo muestra marcado como no
  calculable.
- RF-10: EL SISTEMA ordena los partidos por beneficio garantizado de mayor a
  menor y coloca los no calculables al final.
- RF-11: EL SISTEMA presenta los importes, el retorno y el beneficio en euros
  con dos decimales.
- RF-12: SI la inversión total indicada no es un número mayor que 0, ENTONCES EL
  SISTEMA aborta con un mensaje de error y termina con código de salida distinto
  de 0.
- RF-13: SI la entrada no existe, no es JSON válido o no tiene la estructura de
  la salida del comparador, ENTONCES EL SISTEMA aborta con un mensaje de error
  que identifica el problema y termina con código de salida distinto de 0.
- RF-14: CUANDO la entrada es válida pero no contiene partidos, EL SISTEMA
  informa de que no hay partidos que analizar y termina con código de salida 0.
- RF-15: CUANDO el usuario lo solicite, EL SISTEMA emite el resultado (reparto
  por pata, casas, retorno y beneficio) en un formato JSON reutilizable, además
  de la tabla legible, para encadenarlo con las funcionalidades de freebet y
  bonos.
- RF-16: EL SISTEMA recuerda al usuario que las cuotas pueden haber cambiado y
  que debe verificarlas justo antes de apostar (constitución nº 9).

## Requisitos no funcionales
- El reparto se calcula con precisión decimal, sin `float`; el redondeo a dos
  decimales ocurre solo al presentar (constitución nº 8). Como consecuencia, la
  suma de los tres importes mostrados puede diferir de la inversión total como
  mucho en un céntimo, aunque el reparto interno es exacto.
- Los mensajes y la tabla se muestran en español (constitución nº 6).
- El sistema no accede a la red ni recalcula cuotas desde las cuotas crudas por
  casa: su única entrada es la salida del comparador y la inversión total
  (constitución nº 7).

## Casos límite
- % de pago exactamente 100 → beneficio garantizado 0, señalado como sin
  ganancia (RF-7).
- % de pago > 100 → surebet con beneficio positivo (RF-6).
- Partido marcado como incompleto en la entrada → no calculable, al final
  (RF-9, RF-10).
- Empate de casas en la mejor cuota de un resultado → se listan todas, el
  importe va a una (RF-8).
- Suma de importes redondeados distinta de la inversión → cálculo interno
  exacto, diferencia mostrada ≤ 1 céntimo (RNF).
- Inversión total 0, negativa o no numérica → error y salida ≠ 0 (RF-12).
- Las tres mejores cuotas en la misma casa → reparto válido igualmente (aunque
  rara vez dará surebet); no se trata de forma especial.
- Entrada sin partidos → mensaje y salida 0 (RF-14).
- Entrada inexistente, corrupta o que no es la salida del comparador → error y
  salida ≠ 0 (RF-13).

## Fuera de alcance
- Modo de "pata fija": anclar el reparto en un importe y una casa concretos
  (p. ej. un bono de 100 € que hay que jugar en una casa). Se aborda entero en
  las specs de freebet y bonos.
- Valor específico de una freebet (stake no retornado) y liberación de bonos con
  rollover: specs siguientes.
- Redondeo de los importes a un paso configurable (euro entero, etc.) y el
  reparto del retorno mínimo/máximo derivado.
- Repartir o optimizar un presupuesto global entre varios partidos a la vez:
  aquí la inversión se aplica a cada partido por separado.
- Recalcular o comparar cuotas desde las cuotas crudas por casa (eso es
  `compare`, spec 001).
- Mercados que no sean 1X2 de tres resultados.
- Comisiones de la casa, límites de stake por casa y redondeos impuestos por la
  casa.

## Criterios de finalización
- Todos los RF con test automático en verde (pytest), incluida una comprobación
  numérica a mano del reparto (importes que suman la inversión y retorno igual en
  los tres resultados) sobre un caso con % de pago > 100.
- Demo manual: ejecutar surebet sobre la salida `compare --json` de un JSON de
  ejemplo con (a) al menos un partido surebet (beneficio positivo) mostrando el
  reparto y las casas, (b) al menos un partido con pérdida garantizada señalado
  como tal, y (c) un partido incompleto no calculable al final.
- Verificado el comportamiento ante inversión no válida (error y salida ≠ 0),
  entrada corrupta/ajena al comparador (error y salida ≠ 0) y entrada sin
  partidos (mensaje y salida 0), más la salida `--json` reutilizable.

## Dudas abiertas
- Ninguna pendiente: las decisiones de entrada, modo de stake, alcance,
  redondeo y empate de casas quedaron cerradas en la entrevista y recogidas en
  RF-1 a RF-16.
