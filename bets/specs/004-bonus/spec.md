# Spec 004 — Bonus: apuesta de menor coste para cumplir el rollover

## Contexto y objetivo
Un bono de depósito con **rollover** obliga a apostar mucho dinero en la casa del
bono antes de poder retirar. Para no depender de la suerte, cada apuesta que
cuenta para el rollover se **cubre en otras casas** (como en surebet/freebet), de
modo que el ciclo quede cerrado y solo se pierda un pequeño **margen**. Esta
funcionalidad, siguiendo el objetivo del proyecto —**decir dónde apostar y
cuánto**—, toma las cuotas por casa (Formato A, el mismo JSON que usa `compare`),
la casa del bono, el importe que quieres apostar con el bono y la cuota mínima
exigida, y calcula, partido a partido, las apuestas válidas que cumplen el
rollover con su coste, ordenadas de la más barata a la más cara. Anclar en una
cuota más alta cuesta más (hay que cubrir más dinero), pero es más probable que
la apuesta del bono pierda —lo que interesa, porque ganarla obliga a seguir
apostando—; por eso el coste no lo decide todo. No apuesta ni obtiene cuotas por
su cuenta: solo lee, calcula y muestra. Cubre el caso sin máximo de conversión.

## Usuarios / actores
- **Apostador** (el propio usuario): tiene un bono con rollover en una casa y
  quiere saber, para el importe que va a apostar, en qué partido y resultado
  hacerlo y cómo cubrirlo para cumplir el rollover al menor coste.

## Historias de usuario
- H1: Como apostador quiero que, dado el importe a apostar con el bono, el sistema
  me diga en qué partido y resultado apostar en la casa del bono y cómo cubrir los
  demás, para cumplir el rollover perdiendo lo mínimo.
- H2: Como apostador quiero ver el coste de cada apuesta ordenado de menor a mayor,
  para grindear primero por las más baratas.
- H3: Como apostador quiero ver la cuota del resultado anclado de cada opción,
  para preferir, entre costes parecidos, la más alta (más probable que pierda).
- H4: Como apostador quiero que no me proponga partidos que se juegan después de
  que caduque el bono, para no perderlo por plazo.

## Requisitos funcionales (criterios de aceptación en EARS)

- RF-1: CUANDO se ejecuta bonus con el JSON de cuotas por casa, la casa del bono,
  el importe a apostar y la cuota mínima, EL SISTEMA calcula, para cada partido en
  el que participa esa casa, las opciones de apuesta válidas.
- RF-2: EL SISTEMA genera una opción por cada resultado cuya cuota en la casa del
  bono sea mayor o igual que la cuota mínima.
- RF-3: EL SISTEMA ancla el importe indicado en la casa del bono al resultado de
  la opción.
- RF-4: EL SISTEMA cubre los otros dos resultados con dinero normal (no con otro
  bono) en casas distintas de la del bono (constitución nº 10).
- RF-5: EL SISTEMA dimensiona la cobertura de modo que el retorno sea el mismo
  gane quien gane (la opción queda cerrada, sin riesgo).
- RF-6: EL SISTEMA cubre cada resultado con la mejor cuota entre las casas
  distintas de la del bono; ante empate, la primera por orden de entrada.
- RF-7: EL SISTEMA calcula el coste de cada opción como lo apostado (importe del
  bono más coberturas) menos el retorno garantizado, en euros.
- RF-8: EL SISTEMA muestra, por cada opción, el partido, el resultado anclado con
  su cuota, el importe en la casa del bono, y la casa, el importe y la cuota de
  cada cobertura.
- RF-9: EL SISTEMA ordena las opciones por coste de menor a mayor.
- RF-10: SI el coste de una opción es negativo (existe arbitraje), ENTONCES EL
  SISTEMA la muestra igualmente con coste negativo, sin trato especial, ordenada
  por su coste.
- RF-11: SI la cuota de un resultado en la casa del bono es menor que la cuota
  mínima, ENTONCES EL SISTEMA no genera la opción de ese resultado.
- RF-12: SI un resultado a cubrir no tiene ninguna casa distinta de la del bono
  con cuota válida, ENTONCES EL SISTEMA no genera esa opción e informa del motivo.
- RF-13: SI la casa del bono no participa en un partido, ENTONCES EL SISTEMA no
  genera opciones de ese partido e informa del motivo.
- RF-14: EL SISTEMA lee la fecha de cada partido como un campo opcional del
  archivo; su ausencia no impide el cálculo (compatible con compare, surebet y
  freebet).
- RF-15: DONDE el usuario indique una fecha límite, EL SISTEMA descarta los
  partidos que se juegan después de ella.
- RF-16: SI el usuario indica una fecha límite y un partido no trae fecha,
  ENTONCES EL SISTEMA lo incluye pero avisa de que no ha podido comprobar su plazo.
- RF-17: MIENTRAS el usuario no indique una fecha límite, EL SISTEMA ignora las
  fechas de los partidos.
- RF-18: SI el importe a apostar no es un número mayor que 0, ENTONCES EL SISTEMA
  aborta con un mensaje de error y termina con código de salida distinto de 0.
- RF-19: SI la cuota mínima no es un número mayor que 1, ENTONCES EL SISTEMA
  aborta con un mensaje de error y termina con código de salida distinto de 0.
- RF-20: SI no se indica la casa del bono, ENTONCES EL SISTEMA aborta con un
  mensaje de error y termina con código de salida distinto de 0.
- RF-21: SI el archivo no existe, no es JSON válido, no tiene la estructura
  esperada o repite casa/partido (mismas reglas que compare), ENTONCES EL SISTEMA
  aborta con un mensaje de error y termina con código de salida distinto de 0.
- RF-22: CUANDO el archivo es válido pero no contiene partidos, EL SISTEMA informa
  y termina con código de salida 0.
- RF-23: SI ningún partido produce opciones válidas, ENTONCES EL SISTEMA informa
  de que no hay opciones y termina con código de salida 0.
- RF-24: EL SISTEMA compara el nombre de la casa del bono ignorando
  mayúsculas/minúsculas y espacios exteriores (igual que compare).
- RF-25: CUANDO el usuario lo solicite, EL SISTEMA emite las opciones (partido,
  resultado anclado, importe y cuota del bono, coberturas y coste) en un formato
  JSON reutilizable, además de la tabla legible.
- RF-26: EL SISTEMA presenta los importes, las cuotas y el coste con dos decimales.
- RF-27: EL SISTEMA recuerda al usuario que las cuotas pueden haber cambiado y que
  debe verificarlas justo antes de apostar (constitución nº 9).

## Requisitos no funcionales
- Los importes de cobertura y el coste se calculan con precisión decimal, sin
  `float`; el redondeo a dos decimales ocurre solo al presentar (constitución
  nº 8).
- Los mensajes y la tabla se muestran en español (constitución nº 6).
- El sistema no accede a la red ni obtiene cuotas por su cuenta: su única entrada
  son el archivo, la casa del bono, el importe, la cuota mínima y la fecha límite
  opcional (constitución nº 7).
- Las fechas (de partido y límite) se interpretan como instantes comparables
  cronológicamente, sin gestión de zonas horarias (se asume la misma).

## Casos límite
- Partido con los tres resultados en cuota ≥ mínima → hasta tres opciones (RF-2).
- Resultado con cuota bajo la mínima → sin opción de ese resultado (RF-11).
- Resultado a cubrir solo ofrecido por la casa del bono → opción no generada, con
  motivo (RF-12).
- Casa del bono ausente del partido → sin opciones de ese partido (RF-13).
- Empate en la mejor cuota de cobertura → la primera por orden de entrada (RF-6).
- Coste negativo (el conjunto es un arbitraje) → se muestra como coste negativo,
  ordenado por su coste (RF-10).
- Fecha límite indicada y partido posterior → fuera de plazo, descartado (RF-15).
- Fecha límite indicada y partido sin fecha → incluido con aviso (RF-16).
- Importe ≤ 0, cuota mínima ≤ 1 o casa del bono no indicada → error y salida ≠ 0
  (RF-18, RF-19, RF-20).
- Archivo inexistente/corrupto/estructura inesperada o con casa/partido repetido
  → error y salida ≠ 0 (RF-21).
- Archivo sin partidos → mensaje y salida 0 (RF-22); ningún partido con opciones →
  mensaje y salida 0 (RF-23).

## Fuera de alcance
- **Caso 2 — máximo de conversión**: bonos que limitan lo retirable (p. ej. 2× el
  bono) y la estrategia de no asegurar y jugársela a que la apuesta del bono
  pierda. Se aborda en una spec aparte.
- Tope de rollover por partido y seguimiento del total del rollover (cuánto llevas
  liberado): lo lleva el usuario por su cuenta.
- Procesar varios bonos en un mismo lote: un bono por ejecución.
- Combinar varios bonos a la vez (p. ej. cubrir cada uno de los tres resultados
  con el bono de otra casa): la cobertura es siempre con dinero normal; el uso
  simultáneo de bonos queda fuera.
- Freebets (stake no retornado): spec 003.
- Cobertura mediante casas de intercambio (lay en exchange).
- Mercados que no sean 1X2 de tres resultados.
- Comisiones de la casa y límites de stake por casa.
- Gestión de zonas horarias y descarte de partidos ya disputados.
- Conversión de divisas.

## Criterios de finalización
- Todos los RF con test automático en verde (pytest), incluida una comprobación
  numérica a mano de una opción (coberturas que dejan el mismo retorno en los tres
  resultados y su coste).
- Demo manual sobre un JSON de ejemplo: (a) opciones válidas ordenadas por coste
  con la cuota anclada visible, (b) un resultado descartado por cuota bajo la
  mínima y otro por no ser cubrible, (c) un partido con la casa del bono ausente,
  (d) una fecha límite que deja fuera un partido posterior y avisa de uno sin
  fecha, y (e) la salida `--json`.
- Verificado el comportamiento ante importe/cuota mínima/casa no válidos (error y
  salida ≠ 0), archivo corrupto (error y salida ≠ 0), archivo sin partidos y sin
  opciones (mensaje y salida 0).

## Dudas abiertas
- Ninguna pendiente: entrada, generación de opciones por resultado, cobertura en
  casas distintas, métrica de coste en euros, orden, plazo (fecha opcional y
  límite) y el recorte de alcance al Caso 1 (sin máximo de conversión) quedaron
  cerrados en la entrevista y recogidos en RF-1 a RF-27.
