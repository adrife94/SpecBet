# Constitución — betting-cli

Principios innegociables. Toda spec, plan y tarea debe cumplirlos.

1. **Simplicidad primero**: Python 3.11+ y solo biblioteca estándar en la
   aplicación. Única dependencia de desarrollo permitida: pytest.
2. **La spec manda**: ningún comportamiento se implementa si no está en la
   spec activa. Si falta una decisión, se detiene el trabajo y se pregunta.
3. **Lógica separada de interfaz**: el núcleo (`core.py`) no imprime ni lee de
   consola. La CLI es una capa fina. Todo el core es testeable sin la CLI.
4. **Tests como puerta**: cada tarea termina con sus tests en verde. Prohibido
   avanzar con tests en rojo. Toda fórmula de cálculo lleva su test con un
   caso numérico verificado a mano.
5. **Datos locales y transparentes**: persistencia en un único archivo JSON
   legible. Nada de bases de datos ni de red.
6. **Idioma**: código e identificadores en inglés; mensajes al usuario y
   documentación en español.

7. **Calculadora, no apostador**: la herramienta solo calcula y compara. No
   ejecuta apuestas, no hace login, no scrapea cuotas en vivo ni interactúa con
   las webs de las casas. Las cuotas se introducen a mano o se cargan desde
   JSON/CSV.
8. **El dinero es `Decimal`**: todo importe, cuota y stake se opera con
   `Decimal`, nunca con `float`. El redondeo es explícito y solo en la capa de
   presentación; el core no redondea cálculos intermedios.
9. **Las cuotas caducan**: todo cálculo es una foto del momento en que se
    introdujeron las cuotas. La herramienta lo trata como dato perecedero,
    facilita refrescarlo y recuerda al usuario verificar la cuota justo antes
    de apostar.
10. **Cobertura en casas distintas**: en freebets y bonos, la pata del bono
    vive en la casa que lo otorga y la cobertura se reparte siempre en casas
    DISTINTAS. Ningún cálculo cubre una apuesta con la misma casa que da el
    bono o la freebet.
11. **Respetar los términos del bono**: los cálculos honran las restricciones
    de los términos (cuota mínima/máxima admitida, cap, plazo de uso, rollover
    Nx). Una apuesta fuera de rango no se propone como válida.
