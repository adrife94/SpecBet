# Spec 003 — Freebet: cobertura que extrae el valor de una o varias apuestas gratis

## Contexto y objetivo
Una casa regala a veces una **freebet** (apuesta gratis) de importe F: si la
apuesta gana, se cobran solo las ganancias `F·(cuota−1)` —el stake gratis no se
devuelve—; si pierde, no se pierde nada. Una freebet solo vale de verdad si se
convierte en dinero seguro: se juega la pata gratis en la casa que la otorga y
se **cubren los otros resultados con dinero real en casas distintas**
(constitución nº 10), de modo que quede el mismo beneficio neto gane quien gane.
Esta funcionalidad, siguiendo el objetivo del proyecto —**decir dónde apostar y
cuánto**—, toma las cuotas por casa (Formato A, el mismo JSON que usa `compare`)
y uno o varios bonos (cada uno con su casa e importe), y calcula para cada uno en
qué resultado jugar la freebet, cómo cubrir los demás y cuánto valor se extrae.
Permite meter **varios bonos en un mismo lote** (p. ej. liberar dos a la vez):
cada bono se calcula de forma independiente y se muestra el valor total. Además
respeta el **plazo** de la freebet (la fecha límite para apostar y saldar,
p. ej. 7 días en Luckia): un partido que se dispute después de esa fecha no
sirve, porque la freebet se perdería aunque ganara. No apuesta ni obtiene cuotas
por su cuenta: solo lee, calcula y muestra.

## Usuarios / actores
- **Apostador** (el propio usuario): tiene una o varias freebets de una o varias
  casas y quiere saber en qué partido y resultado jugar cada una, cómo cubrirlas
  y cuánto gana en total.

## Historias de usuario
- H1: Como apostador quiero que, dada una freebet de una casa, el sistema me diga
  en qué resultado jugarla y cómo cubrir los demás, para asegurar la ganancia.
- H2: Como apostador quiero ver el valor extraído en euros y el % de conversión
  (lo liberado sobre el importe), para saber cuánto vale de verdad la freebet.
- H3: Como apostador quiero poder fijar un partido y un resultado concretos y que
  me calcule lo que ganaría, para evaluar una jugada que ya tengo en mente.
- H4: Como apostador quiero que se respeten los límites de cuota de los términos
  de la freebet, para no proponer una jugada que la casa no aceptaría.
- H5: Como apostador quiero que no me recomiende partidos que se juegan después
  de que caduque la freebet, para no perderla por plazo.
- H6: Como apostador quiero calcular varios bonos en una misma ejecución y ver el
  valor total, para planificar liberar varios a la vez sin repetir el trabajo.

## Requisitos funcionales (criterios de aceptación en EARS)

- RF-1: CUANDO se ejecuta freebet con un JSON de cuotas por casa, la casa que
  otorga la freebet y su importe, EL SISTEMA calcula, para cada partido en el que
  participa esa casa, cómo jugar la freebet y cubrir los otros resultados.
- RF-2: EL SISTEMA juega la pata gratis en la casa del bono y cubre los otros dos
  resultados con dinero real en casas distintas de la del bono (constitución
  nº 10).
- RF-3: EL SISTEMA calcula la cobertura de modo que el beneficio neto sea el
  mismo sea cual sea el resultado ganador, y llama a ese beneficio "valor
  extraído".
- RF-4: EL SISTEMA muestra, por cada jugada, el valor extraído en euros y su
  **% de conversión** (valor extraído dividido entre el importe de la freebet;
  p. ej. una freebet de 100 que deja 70 → 70 %).
- RF-5: EL SISTEMA muestra, por cada pata (la gratis y las de cobertura), el
  resultado, el importe a apostar, la cuota y la casa.
- RF-6: MIENTRAS el usuario no fije el resultado de la pata gratis, EL SISTEMA
  elige, de entre los resultados admitidos, el que deja mayor valor extraído.
- RF-7: CUANDO el usuario fija el resultado de la pata gratis, EL SISTEMA calcula
  la cobertura y el valor extraído solo para ese resultado.
- RF-8: CUANDO el usuario fija un partido concreto, EL SISTEMA calcula solo ese
  partido e ignora los demás.
- RF-9: DONDE el usuario indique una cuota mínima y/o máxima para la pata gratis,
  EL SISTEMA solo juega la freebet en resultados cuya cuota en la casa del bono
  esté dentro de ese rango (constitución nº 11).
- RF-10: SI el resultado que el usuario fija tiene en la casa del bono una cuota
  fuera del rango indicado, ENTONCES EL SISTEMA no propone esa jugada e informa
  del motivo.
- RF-11: EL SISTEMA cubre cada resultado con la mejor cuota disponible entre las
  casas distintas de la del bono.
- RF-12: EL SISTEMA reparte la cobertura en una o dos casas distintas de la del
  bono (las dos patas de cobertura pueden coincidir en la misma casa) y nunca
  cubre en la casa del bono.
- RF-13: SI un resultado a cubrir no tiene ninguna casa distinta de la del bono
  con cuota válida, ENTONCES EL SISTEMA marca esa jugada como no cubrible y no la
  propone.
- RF-14: SI la casa del bono no aporta ninguna cuota válida (dentro del rango) a
  ningún resultado de un partido, ENTONCES EL SISTEMA señala ese partido como no
  jugable con esa freebet.
- RF-15: EL SISTEMA presenta, por cada bono, un partido por fila con el valor
  extraído de su mejor jugada, ordenados de mayor a menor valor extraído y con
  los no jugables al final.
- RF-16: EL SISTEMA compara el nombre de la casa del bono con los del archivo
  ignorando mayúsculas/minúsculas y espacios exteriores (igual que `compare`).
- RF-17: SI el importe de la freebet no es un número mayor que 0, ENTONCES EL
  SISTEMA aborta con un mensaje de error y termina con código de salida distinto
  de 0.
- RF-18: SI no se indica la casa del bono, ENTONCES EL SISTEMA aborta con un
  mensaje de error y termina con código de salida distinto de 0.
- RF-19: SI el archivo no existe, no es JSON válido, no tiene la estructura
  esperada o repite casa/partido (mismas reglas que `compare`), ENTONCES EL
  SISTEMA aborta con un mensaje de error que identifica el problema y termina con
  código de salida distinto de 0.
- RF-20: CUANDO el archivo es válido pero no contiene partidos, EL SISTEMA
  informa de que no hay partidos que analizar y termina con código de salida 0.
- RF-21: CUANDO el usuario lo solicite, EL SISTEMA emite el resultado (pata
  gratis, cobertura por pata con casa e importe, valor extraído) en un formato
  JSON reutilizable, además de la tabla legible; con varios bonos incluye el plan
  de cada uno y el valor total del lote.
- RF-22: EL SISTEMA recuerda al usuario que las cuotas pueden haber cambiado y
  que debe verificarlas justo antes de apostar (constitución nº 9).
- RF-23: EL SISTEMA lee la fecha en que se juega cada partido como un campo
  opcional del archivo; su ausencia no impide el resto del cálculo (así el mismo
  archivo sigue valiendo para `compare` y `surebet`).
- RF-24: DONDE el usuario indique una fecha límite para la freebet, EL SISTEMA
  solo propone partidos cuya fecha sea igual o anterior a ese límite, asumiendo
  que la apuesta se hace en el momento del cálculo.
- RF-25: SI el usuario indica una fecha límite y un partido se juega después de
  ella, ENTONCES EL SISTEMA lo marca como fuera de plazo y lo trata como no
  jugable (no lo propone y lo coloca al final, RF-15).
- RF-26: SI el usuario indica una fecha límite y un partido no trae fecha,
  ENTONCES EL SISTEMA lo incluye igualmente en el cálculo pero avisa de que no ha
  podido comprobar su plazo.
- RF-27: MIENTRAS el usuario no indique una fecha límite, EL SISTEMA ignora las
  fechas de los partidos y los considera todos.
- RF-28: EL SISTEMA acepta uno o varios bonos en la misma ejecución (un lote);
  cada bono lleva su propia casa, importe, rango de cuota opcional, fecha límite
  opcional y, si el usuario lo indica, su partido y/o resultado fijados.
- RF-29: EL SISTEMA calcula cada bono del lote de forma independiente (aplicando
  RF-1 a RF-27) y presenta todos los planes en el mismo resultado.
- RF-30: EL SISTEMA muestra el valor extraído total del lote como la suma de los
  valores extraídos de cada bono, junto con su % de conversión total (valor
  extraído total dividido entre la suma de los importes de los bonos).
- RF-31: SI dos bonos del lote proponen apostar en el mismo partido, resultado y
  casa, ENTONCES EL SISTEMA lo avisa para que el usuario pueda consolidar esa
  apuesta (es solo un aviso: no cambia el cálculo).
- RF-32: SI un bono del lote no tiene ninguna jugada válida (su casa no participa
  en ningún partido, todo queda fuera de plazo o de rango, o ningún resultado es
  cubrible), ENTONCES EL SISTEMA marca ese bono como sin plan y sigue calculando
  el resto del lote.
- RF-33: EL SISTEMA señala como jugada recomendada de cada bono el partido con
  mayor valor extraído (la primera fila de su listado).
- RF-34: EL SISTEMA detalla, para cada partido del listado, la pata gratis y las
  de cobertura (resultado, importe, cuota y casa), no solo la jugada recomendada.

## Requisitos no funcionales
- El valor extraído, los importes de cobertura y las cuotas se calculan con
  precisión decimal, sin `float`; el redondeo a dos decimales ocurre solo al
  presentar (constitución nº 8).
- Los mensajes y la tabla se muestran en español (constitución nº 6).
- El sistema no accede a la red ni obtiene cuotas por su cuenta: su única entrada
  son el archivo, la casa del bono, el importe, el rango opcional y la fecha
  límite opcional (constitución nº 7).
- Las fechas (de partido y límite) se interpretan como instantes comparables
  cronológicamente, sin gestión de zonas horarias (se asume la misma).

## Casos límite
- Freebet jugable en varios resultados del mismo partido → se elige el de mayor
  valor extraído (RF-6).
- Resultado de la pata gratis con cuota fuera del rango → no se propone (RF-9,
  RF-10).
- Un resultado a cubrir solo lo ofrece la casa del bono → jugada no cubrible
  (RF-13).
- Casa del bono ausente del partido → partido no jugable, al final (RF-14, RF-15).
- Las dos coberturas comparten casa (una casa distinta de la del bono ofrece los
  dos resultados a cubrir) → permitido (RF-12).
- Nombre de la casa del bono con distinta caja o espacios (`"Sportium "` vs
  `"sportium"`) → se considera la misma casa (RF-16).
- Importe 0, negativo o no numérico → error y salida ≠ 0 (RF-17).
- Archivo sin partidos → mensaje y salida 0 (RF-20).
- Archivo inexistente/corrupto/estructura inesperada o con casa/partido repetido
  → error y salida ≠ 0 (RF-19).
- Fecha límite indicada y partido posterior a ella → fuera de plazo, no propuesto,
  al final (RF-24, RF-25).
- Fecha límite indicada y partido sin fecha → se incluye con aviso (RF-26).
- Sin fecha límite → las fechas se ignoran y se consideran todos los partidos
  (RF-27).
- Lote de un solo bono → se comporta igual que calcular ese bono suelto (RF-28).
- Un bono del lote sin jugada válida → se marca sin plan y no tumba el resto
  (RF-32).
- Dos bonos del lote que caen en la misma apuesta (partido+resultado+casa) → se
  avisa para consolidar (RF-31).

## Fuera de alcance
- Rollover de bonos (obligación de apostar Nx antes de retirar): spec siguiente
  (`bonus`).
- Freebets que SÍ devuelven el stake ("bonus bet" con reembolso del importe): se
  asume el caso estándar en que el stake gratis no se devuelve.
- Cobertura mediante casas de intercambio (lay en exchange): aquí solo se cubre
  con apuestas normales a los otros resultados 1X2.
- Rango de cuota mín/máx en las patas de cobertura: el rango solo aplica a la
  pata gratis.
- Descartar partidos ya disputados o comprobar que "hoy" está dentro del plazo:
  se asume que la apuesta se hace en el momento del cálculo; solo se compara la
  fecha del partido con la fecha límite.
- Gestión de zonas horarias en las fechas.
- Optimización conjunta o coordinada de varios bonos (evitar solapes entre bonos,
  repartir entre partidos para maximizar el valor combinado más allá de la suma,
  o respetar límites de stake por casa al acumular apuestas de varios bonos): el
  lote trata cada bono de forma independiente.
- Mercados que no sean 1X2 de tres resultados.
- Comisiones de la casa, límites de stake por casa y redondeos impuestos por la
  casa.
- Conversión de divisas.

## Criterios de finalización
- Todos los RF con test automático en verde (pytest), incluida una comprobación
  numérica a mano de una conversión de freebet (cobertura que deja el mismo
  beneficio neto en los tres resultados y su valor extraído en % de F).
- Demo manual sobre un JSON de ejemplo: (a) modo automático que recomienda
  partido y resultado con mayor valor extraído y su cobertura, (b) modo manual
  fijando partido y resultado, (c) un partido con la casa del bono ausente
  señalado como no jugable, (d) una fecha límite que deja fuera de plazo un
  partido posterior y avisa de uno sin fecha, (e) un lote de dos bonos con su
  valor total, y (f) la salida `--json`.
- Verificado el comportamiento ante importe no válido, casa del bono no indicada,
  archivo corrupto/repetido (error y salida ≠ 0) y archivo sin partidos (mensaje
  y salida 0).

## Dudas abiertas
- Ninguna pendiente: entrada, elección de la pata gratis (auto o fijando
  partido/resultado), rango de cuota, regla de casas de cobertura, plazo (fecha
  de partido y fecha límite), lote de varios bonos independientes, listado por
  partido y % de conversión quedaron cerrados en la entrevista y recogidos en
  RF-1 a RF-34.
