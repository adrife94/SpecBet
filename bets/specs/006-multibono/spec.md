# Spec 006 — Multibono: rollover coordinado de varios bonos sin mezclar saldo

## Contexto y objetivo
Cuando tienes **varios bonos** con rollover en casas distintas, conviene
liberarlos **a la vez** sin mezclar dinero real con dinero de bono. La estrategia
(operativa del usuario, no de la herramienta): en cada casa se **aparca** el
dinero real en una apuesta a futuro asegurada —así el saldo activo pasa a ser el
del bono, porque la casa gasta el real primero y retirar el real haría perder el
bono— y con **el bono de cada casa** se cubre un **resultado distinto** (1, X, 2)
de un partido **de ahora**, cerrando el rollover antes de que se salde el futuro.
Como las cuotas rara vez dejan las tres patas igualadas, las patas más flojas se
**rellenan con dinero real en otras casas** hasta igualar el retorno. Siguiendo el
objetivo del proyecto —**decir dónde apostar y cuánto**—, `multibonus` toma las
cuotas por casa (Formato A, el mismo JSON que usa `compare`), la lista de bonos
(casa, importe y cuota mínima) y, opcionalmente, la fecha del partido de
apalancamiento, y calcula, partido a partido, la mejor colocación de los bonos con
su relleno de dinero real, ordenada de **menor a mayor pérdida** y mostrando el
**dinero real a desplegar**. Es la generalización a **varios bonos a la vez** del
caso que la spec 004 (`bonus`) dejó fuera de alcance. No apuesta ni obtiene cuotas:
solo lee, calcula y muestra.

El **cálculo de la apuesta de apalancamiento a futuro** (dónde y cuánto) no lo hace
este comando: es una surebet normal que se resuelve con `surebet`; aquí solo se usa
su **fecha** para comprobar el plazo.

## Usuarios / actores
- **Apostador** (el propio usuario): tiene 2 o 3 bonos con rollover en casas
  distintas y quiere saber, para un partido de ahora, en qué resultado colocar
  cada bono y cómo rellenar con dinero real para liberarlos a la vez perdiendo lo
  mínimo, antes de que se salde su apuesta de apalancamiento.

## Historias de usuario
- H1: Como apostador quiero pasar 2 o 3 bonos (casa, importe, cuota mínima) y que
  el sistema coloque cada bono en un resultado distinto y me diga cuánto y dónde
  rellenar con dinero real para igualar el retorno.
- H2: Como apostador quiero ver las opciones ordenadas por **% de pérdida** de
  menor a mayor, para convertir los bonos en dinero real perdiendo lo mínimo.
- H3: Como apostador quiero ver el **dinero real a desplegar** de cada opción para
  preferir, entre pérdidas parecidas, la más pareja (menos capital).
- H4: Como apostador quiero ver el **retorno garantizado** y el **neto**, para
  saber con cuánto dinero real acabo.
- H5: Como apostador quiero que no me proponga partidos de bono que se saldan
  después de mi apuesta de apalancamiento, para cerrar el rollover dentro de la
  ventana.
- H6: Como apostador quiero poder montarlo con 2 bonos (cubriendo el tercer
  resultado solo con dinero real) o con 3, según los bonos que tenga.

## Requisitos funcionales (criterios de aceptación en EARS)

### Entrada y validación
- RF-1: CUANDO se ejecuta `multibonus` con el JSON de cuotas por casa (Formato A),
  la lista de bonos (cada uno: casa, importe y cuota mínima) y, opcionalmente, la
  fecha del partido de apalancamiento, EL SISTEMA calcula, para cada partido del
  archivo, la mejor opción de reparto de los bonos.
- RF-2: EL SISTEMA admite 2 o 3 bonos. SI se indican menos de 2 o más de 3,
  ENTONCES aborta con un mensaje de error y salida distinta de 0 (con 1 bono la
  herramienta es `bonus`, spec 004).
- RF-3: SI el importe de algún bono no es un número mayor que 0, o su cuota mínima
  no es un número mayor que 1, ENTONCES aborta con un mensaje de error y salida
  distinta de 0.
- RF-4: SI dos bonos indican la misma casa, ENTONCES aborta con un mensaje de error
  y salida distinta de 0 (cada bono vive en una casa distinta).
- RF-5: SI el archivo no existe, no es JSON válido, no tiene la estructura esperada
  o repite casa/partido (mismas reglas que compare), ENTONCES aborta con un mensaje
  de error y salida distinta de 0.
- RF-6: EL SISTEMA compara los nombres de casa ignorando mayúsculas/minúsculas y
  espacios exteriores (igual que compare).

### Colocación de los bonos
- RF-7: EL SISTEMA coloca cada bono ENTERO (su importe completo) en un resultado
  distinto del partido; ningún resultado recibe dos bonos.
- RF-8: EL SISTEMA solo ancla un bono en un resultado cuya cuota en la casa del
  bono sea mayor o igual que la cuota mínima de ese bono (constitución nº 11).
- RF-9: EL SISTEMA prueba las asignaciones válidas de bonos a resultados y elige,
  para cada partido, la de **menor pérdida**.
- RF-10: CUANDO hay 3 bonos, EL SISTEMA los ancla en los tres resultados (1, X y
  2), uno en cada uno.
- RF-11: CUANDO hay 2 bonos, EL SISTEMA los ancla en dos resultados y cubre el
  tercero íntegramente con dinero real.

### Retorno objetivo y relleno con dinero real
- RF-12: EL SISTEMA fija el retorno objetivo R como el mayor `importe × cuota`
  entre las patas ancladas con bono (el techo, que no puede reducirse).
- RF-13: PARA cada resultado cuyo retorno con bono sea menor que R, EL SISTEMA
  calcula el relleno con dinero real necesario para alcanzar R.
- RF-14: EL SISTEMA cubre el resultado sin bono (caso de 2 bonos) íntegramente con
  dinero real hasta alcanzar R.
- RF-15: EL SISTEMA coloca todo el dinero real (rellenos y cobertura) en casas
  DISTINTAS de las de los bonos (constitución nº 10), a la mejor cuota de ese
  resultado; ante empate, la primera por orden de entrada.
- RF-16: SI un resultado que requiere dinero real no tiene ninguna casa (distinta
  de las de los bonos) con cuota válida, ENTONCES EL SISTEMA no genera la opción de
  ese partido e informa del motivo.
- RF-17: SI en un partido alguna casa de bono no participa o no ofrece ninguna
  cuota mayor o igual que su cuota mínima, ENTONCES EL SISTEMA no genera opción de
  ese partido e informa del motivo.

### Métricas y orden
- RF-18: EL SISTEMA calcula la **pérdida** de cada opción = (suma de bonos + suma
  de dinero real) − retorno garantizado R, en euros.
- RF-19: EL SISTEMA expresa además la pérdida en **% sobre el total de bono
  apostado**.
- RF-20: EL SISTEMA calcula el **dinero real total a desplegar** (suma de rellenos
  y cobertura).
- RF-21: EL SISTEMA calcula el **retorno garantizado R** y el **neto** = R − dinero
  real desplegado.
- RF-22: EL SISTEMA ordena las opciones por **pérdida de menor a mayor**.
- RF-23: EL SISTEMA muestra, junto a cada opción, el dinero real a desplegar, para
  que, entre pérdidas parecidas, el usuario prefiera la opción más pareja (menos
  capital). Ni lo parejo del partido ni su payout predicen por sí solos la pérdida
  —una pata de cuota baja obliga a rellenar con mucho dinero real ineficiente
  aunque el payout sea bueno—, por eso EL SISTEMA ordena siempre por la pérdida
  calculada y deja el dinero real como criterio secundario del usuario.
- RF-24: SI la pérdida de una opción es negativa (el conjunto es un arbitraje con
  beneficio garantizado), ENTONCES EL SISTEMA la muestra igual, con pérdida
  negativa, ordenada por su valor.

### Plazo (ventana del apalancamiento)
- RF-25: EL SISTEMA lee la fecha de cada partido como campo opcional (compatible
  con compare, surebet, freebet y bonus).
- RF-26: DONDE el usuario indique la fecha del partido de apalancamiento, EL
  SISTEMA descarta los partidos de bono que se saldan en esa fecha o después (el
  rollover debe cerrarse antes de que se salde el apalancamiento).
- RF-27: SI se indica la fecha de apalancamiento y un partido de bono no trae
  fecha, ENTONCES EL SISTEMA lo incluye pero avisa de que no ha podido comprobar su
  plazo.
- RF-28: MIENTRAS el usuario no indique la fecha de apalancamiento, EL SISTEMA
  calcula sin filtro de plazo y recuerda que el rollover debe cerrarse antes de que
  se salde el apalancamiento.

### Salida y recordatorio
- RF-29: EL SISTEMA muestra, por cada opción: el partido; para cada resultado, la
  casa del bono con su importe y cuota (donde haya bono) y el dinero real con su
  casa, importe y cuota (donde haya relleno o cobertura); y el retorno garantizado
  R, el dinero real desplegado, la pérdida (€ y %) y el neto.
- RF-30: CUANDO el usuario lo solicite, EL SISTEMA emite las opciones en un formato
  JSON reutilizable, además de la tabla legible.
- RF-31: EL SISTEMA presenta importes, cuotas, porcentajes y pérdida con dos
  decimales.
- RF-32: EL SISTEMA recuerda que las cuotas pueden haber cambiado y que deben
  verificarse justo antes de apostar (constitución nº 9).

### Casos sin resultado
- RF-33: CUANDO el archivo es válido pero no contiene partidos, EL SISTEMA informa
  y termina con salida 0.
- RF-34: SI ningún partido produce una opción válida, ENTONCES EL SISTEMA informa
  de que no hay opciones y termina con salida 0.

## Requisitos no funcionales
- Los importes de relleno, R, la pérdida y el neto se calculan con precisión
  decimal, sin `float`; el redondeo a dos decimales ocurre solo al presentar
  (constitución nº 8).
- Los mensajes y la tabla se muestran en español (constitución nº 6).
- El sistema no accede a la red ni obtiene cuotas por su cuenta: su única entrada
  son el archivo, la lista de bonos y la fecha de apalancamiento opcional
  (constitución nº 7).
- El filtro necesita el detalle por casa (Formato A): coloca bonos y rellenos
  eligiendo casas concretas, no basta el resumen de mejores cuotas de `compare`.
- Las fechas (de partido y de apalancamiento) se interpretan como instantes
  comparables cronológicamente, sin gestión de zonas horarias (se asume la misma).

## Casos límite
- 3 bonos con cuotas casi 3/3/3 → sin dinero real y pérdida ~0 (el caso ideal).
- Partido muy parejo pero mal pagado (p. ej. 2.6/2.6/2.6) → sin dinero real pero
  pérdida alta (~13 %); queda ordenado por debajo de partidos más rentables aunque
  esos pidan dinero real (RF-22, RF-23).
- 2 bonos → el tercer resultado se cubre solo con dinero real (RF-11, RF-14).
- Bono cuya cuota en su casa está por debajo de su mínima en todos los resultados →
  no se puede anclar → partido sin opción, con motivo (RF-8, RF-17).
- Resultado a rellenar sin ninguna casa distinta con cuota válida → opción no
  generada, con motivo (RF-16).
- Empate en la mejor cuota de relleno → la primera por orden de entrada (RF-15).
- Pérdida negativa (el conjunto es un arbitraje) → se muestra como negativa,
  ordenada por su valor (RF-24).
- Fecha de apalancamiento indicada y partido posterior → descartado; partido sin
  fecha → incluido con aviso (RF-26, RF-27).
- Menos de 2 o más de 3 bonos, importe ≤ 0, cuota mínima ≤ 1 o casas de bono
  repetidas → error y salida ≠ 0 (RF-2, RF-3, RF-4).
- Archivo inexistente/corrupto/estructura inesperada o con casa/partido repetido →
  error y salida ≠ 0 (RF-5). Archivo sin partidos → salida 0 (RF-33); ningún
  partido con opciones → salida 0 (RF-34).

## Fuera de alcance
- El **cálculo de la apuesta de apalancamiento a futuro** (dónde y cuánto): es una
  surebet normal y se resuelve con `surebet`; aquí solo se usa su fecha para el
  plazo.
- El caso de **1 solo bono**: es `bonus` (spec 004).
- **Objetivos de retorno distintos del techo** (retorno variable por debajo o por
  encima del máximo): siempre se iguala al techo, con retorno garantizado idéntico
  salga lo que salga.
- Seguimiento del **total del rollover** liberado y tope de rollover por partido:
  lo lleva el usuario por su cuenta.
- Combinar **más de 3 bonos** o mercados que no sean 1X2 de tres resultados.
- Cobertura mediante casas de intercambio (lay en exchange).
- Comisiones de la casa, límites de stake por casa, conversión de divisas, gestión
  de zonas horarias y descarte de partidos ya disputados.
- Elegir automáticamente si "compensa": la herramienta muestra las cifras (pérdida
  y dinero real); la decisión es del usuario.
- La operativa de **ocultar el saldo real** (aparcar el real porque la casa gasta
  el real primero y retirar hace perder el bono): es la razón de la estrategia, no
  un cálculo de la herramienta.

## Criterios de finalización
- Todos los RF con test automático en verde (pytest), incluida una comprobación
  numérica a mano: (a) una opción de 3 bonos con relleno de dinero real que deja el
  mismo retorno R en los tres resultados, con su pérdida en € y %, su dinero real
  desplegado y su neto; (b) una opción de 2 bonos con el tercer resultado cubierto
  solo con dinero real.
- Demo manual sobre un JSON de ejemplo: (a) 3 bonos casi 3/3/3 → poco o ningún
  dinero real y pérdida baja; (b) un partido parejo pero mal pagado con pérdida alta
  ordenado por debajo de otro más rentable; (c) 2 bonos con el tercer resultado
  cubierto con dinero real; (d) un partido descartado por casa de bono ausente y
  otro por un resultado no rellenable; (e) una fecha de apalancamiento que deja
  fuera un partido posterior y avisa de uno sin fecha; y (f) la salida `--json`.
- Verificado el comportamiento con menos de 2 o más de 3 bonos, importe/cuota
  mínima no válidos y casas de bono repetidas (error y salida ≠ 0), archivo corrupto
  (error y salida ≠ 0), y archivo sin partidos o sin opciones (mensaje y salida 0).

## Dudas abiertas
- Ninguna pendiente: entrada (2–3 bonos con casa/importe/cuota mínima y fecha de
  apalancamiento), colocación de cada bono entero en un resultado distinto, retorno
  objetivo R = techo del mayor bono, relleno con dinero real en casas distintas,
  métrica de pérdida (€ y % sobre el total de bono) como orden principal con el
  dinero real como criterio secundario, plazo por fecha de apalancamiento y el
  recorte de alcance (el parking se hace con `surebet`, el caso de 1 bono es
  `bonus`) quedaron cerrados en la entrevista y recogidos en RF-1 a RF-34.
