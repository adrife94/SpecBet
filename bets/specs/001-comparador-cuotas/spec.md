# Spec 001 — Comparador de cuotas / % de pago (1X2)

## Contexto y objetivo
Hoy el usuario compara manualmente, abriendo varias pestañas del navegador, las
cuotas 1X2 de un mismo partido en distintas casas de apuestas para saber dónde
está la mejor cuota de cada resultado y cómo de "eficiente" es el mercado
combinado. Esta funcionalidad automatiza ese trabajo: a partir de un archivo
JSON con los partidos y las cuotas de cada casa (recopilado aparte, p. ej. con
Claude en el navegador), calcula para cada partido la mejor cuota de cada
resultado y su **% de pago**, y presenta una tabla ordenada de mayor a menor
eficiencia. Es la base sobre la que se apoyarán las funcionalidades de surebets,
freebets y bonos. No apuesta ni obtiene cuotas por su cuenta: solo lee, calcula
y muestra.

## Usuarios / actores
- **Apostador** (el propio usuario): prepara/actualiza el archivo JSON con las
  cuotas y ejecuta el comparador para decidir dónde hay menos margen en contra.

## Historias de usuario
- H1: Como apostador quiero ver, para cada partido, la mejor cuota disponible de
  cada resultado y qué casa la ofrece, para no tener que cotejar pestañas a mano.
- H2: Como apostador quiero un % de pago por partido y la tabla ordenada por él,
  para identificar de un vistazo los mercados menos desfavorables.
- H3: Como apostador quiero que los partidos con datos incompletos se muestren
  igualmente (marcados), para saber que existen aunque no se hayan podido
  calcular.

## Requisitos funcionales (criterios de aceptación en EARS)

- RF-1: CUANDO se ejecuta el comparador con un archivo JSON válido, EL SISTEMA
  calcula para cada partido la mejor cuota de cada resultado (1, X y 2) y muestra
  una tabla con una fila por partido.
- RF-2: EL SISTEMA define la "mejor cuota" de un resultado como la cuota **más
  alta** ofrecida por alguna casa para ese resultado.
- RF-3: EL SISTEMA define el "% de pago" de un partido como
  `100 / (1/mejor_1 + 1/mejor_X + 1/mejor_2)` y lo muestra en porcentaje con
  dos decimales.
- RF-4: EL SISTEMA muestra, por cada resultado, la mejor cuota y el nombre de la
  casa que la ofrece.
- RF-5: SI dos o más casas ofrecen exactamente la misma mejor cuota para un
  resultado, ENTONCES EL SISTEMA muestra todas esas casas en la celda de ese
  resultado.
- RF-6: EL SISTEMA ordena las filas con % de pago de mayor a menor.
- RF-7: SI una casa no aporta cuota para algún resultado de un partido, ENTONCES
  EL SISTEMA ignora ese hueco y sigue considerando esa casa para los resultados
  que sí aporta.
- RF-8: SI una cuota es inválida (no es un número mayor que 1), ENTONCES EL
  SISTEMA la descarta como si fuera un hueco e informa al usuario de qué cuota
  descartó y en qué partido/casa.
- RF-9: SI algún resultado (1, X o 2) de un partido no tiene ninguna cuota
  válida en ninguna casa, ENTONCES EL SISTEMA no calcula el % de pago de ese
  partido y lo muestra en la tabla marcado como incompleto.
- RF-10: MIENTRAS existan partidos sin % de pago calculable, EL SISTEMA los
  coloca al final de la tabla, después de todos los partidos con % de pago.
- RF-11: SI el archivo no existe, no es JSON válido o no tiene la estructura
  esperada, ENTONCES EL SISTEMA aborta sin calcular, muestra un mensaje de error
  que identifica el problema y termina con código de salida distinto de 0.
- RF-12: CUANDO el archivo es válido pero no contiene ningún partido, EL SISTEMA
  informa de que no hay partidos que comparar y termina con código de salida 0.
- RF-13: EL SISTEMA compara los nombres de casa y de partido ignorando
  mayúsculas/minúsculas y espacios exteriores, tanto para agruparlos como para
  detectar repetidos.
- RF-14: SI un partido tiene cuotas válidas de menos de dos casas distintas,
  ENTONCES EL SISTEMA no calcula su % de pago y lo muestra marcado como
  incompleto.
- RF-15: SI una misma casa (según RF-13) aparece más de una vez dentro del mismo
  partido, ENTONCES EL SISTEMA aborta con un mensaje de error que identifica el
  partido y la casa, y termina con código de salida distinto de 0.
- RF-16: SI un mismo partido (según RF-13) aparece más de una vez en el archivo,
  ENTONCES EL SISTEMA aborta con un mensaje de error que lo identifica y termina
  con código de salida distinto de 0.
- RF-17: EL SISTEMA no destaca ni marca de forma especial los partidos con % de
  pago superior a 100 %: los ordena por su % de pago igual que a cualquier otro.
- RF-18: CUANDO el usuario lo solicite, EL SISTEMA produce el resultado del
  comparador en un formato estructurado reutilizable (JSON), además de la tabla
  legible, para poder encadenarlo con otras funcionalidades sin recalcular.

## Requisitos no funcionales
- Los cálculos de cuotas y % de pago se realizan con precisión decimal, sin
  errores de redondeo de coma flotante (constitución, principio 8). El redondeo
  a dos decimales ocurre solo al presentar.
- Los mensajes al usuario y la tabla se muestran en español (constitución,
  principio 6).
- El sistema no accede a la red ni a las webs de las casas: la única entrada son
  el archivo y sus datos (constitución, principio 7).

## Casos límite
- Casa que solo trae 1 y 2 pero no la X → se usa para 1 y 2 (RF-7).
- Ningún precio para el empate en ningún casa → partido incompleto (RF-9).
- Cuota `"N/A"`, `0`, negativa o ≤ 1 → descartada con aviso (RF-8).
- Archivo vacío de partidos → mensaje y salida 0 (RF-12).
- Archivo corrupto / ruta inexistente / estructura inesperada → error y salida
  ≠ 0 (RF-11).
- Empate de mejor cuota entre varias casas → se listan todas (RF-5).
- Partido con cuotas de una sola casa → incompleto, sin % de pago (RF-14).
- Misma casa repetida dentro de un partido → error y salida ≠ 0 (RF-15).
- Mismo partido repetido en el archivo → error y salida ≠ 0 (RF-16).
- Nombres con distinta caja o espacios exteriores (`"Bet365"` vs `"bet365 "`)
  → se consideran la misma casa/partido (RF-13).

## Fuera de alcance
- Mercados que no sean 1X2 de tres resultados (2 vías sin empate, hándicaps,
  más/menos goles, etc.).
- Obtención automática de cuotas: scraping, login o cualquier interacción con
  las webs de las casas. Las cuotas llegan ya recopiladas en el JSON.
- Detección de surebets y reparto de stakes (spec siguiente).
- Extracción de valor de freebets y liberación de bonos con rollover.
- Persistencia o acumulación de cuotas entre ejecuciones: cada ejecución parte
  del archivo que se le pasa.
- Verificación de licencia DGOJ de las casas y puntuación/ranking de casas.
- Conversión de divisas.

## Criterios de finalización
- Todos los RF con test automático en verde (pytest).
- Demo manual: ejecutar el comparador sobre un JSON de ejemplo con varios
  partidos que muestre (a) la tabla ordenada de mayor a menor % de pago, (b) al
  menos un partido incompleto colocado al final, y (c) el aviso de una cuota
  inválida descartada.
- Verificado el comportamiento ante archivo inexistente/corrupto (mensaje de
  error y salida ≠ 0) y ante archivo sin partidos (mensaje y salida 0).

## Dudas abiertas
- Ninguna pendiente: las dudas iniciales quedaron resueltas en RF-13 a RF-18.
