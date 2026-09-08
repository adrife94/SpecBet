import 'package:flutter/material.dart';

import '../theme.dart';
import '../widgets/form_bits.dart';

/// Pantalla de ayuda: explica qué es SpecBet y para qué sirve cada herramienta.
class GuiaScreen extends StatelessWidget {
  const GuiaScreen({super.key});

  static const _tools = [
    (
      icon: Icons.table_chart_outlined,
      title: 'Cuotas',
      body: 'La fuente única de datos. Importa el JSON de cuotas que copiaste del '
          'navegador; el resto de herramientas trabaja sobre estos partidos.',
    ),
    (
      icon: Icons.leaderboard_outlined,
      title: 'Comparador',
      body: 'Ordena los partidos por % de pago y resalta la mejor cuota de cada '
          'resultado (1/X/2). Los partidos con cuotas incompletas quedan al final.',
    ),
    (
      icon: Icons.balance_outlined,
      title: 'Surebet',
      body: 'Reparte tu inversión entre 1/X/2 con la mejor cuota de cada resultado, '
          'igualando el retorno. Si el % de pago supera el 100 %, hay beneficio seguro.',
    ),
    (
      icon: Icons.card_giftcard_outlined,
      title: 'Freebet',
      body: 'Convierte una apuesta gratis en dinero: la apuesta del bono '
          'más dos coberturas igualadas. Muestra el valor extraído y la conversión.',
    ),
    (
      icon: Icons.savings_outlined,
      title: 'Bono',
      body: 'Cumple el rollover de un bono al menor coste: apuesta anclada en la casa del '
          'bono y coberturas en el resto de resultados.',
    ),
    (
      icon: Icons.account_tree_outlined,
      title: 'Multibono',
      body: 'Reparte 2 o 3 bonos (cada uno en una casa distinta) entre los resultados de '
          'un partido; el relleno va con dinero real y se elige la asignación de menor pérdida.',
    ),
  ];

  static const _pasos = [
    'Abre en Chrome las páginas de las casas de apuestas con la liga o los partidos que quieras comparar. '
        'Déjalas en el mismo grupo de pestañas en el que actúa Claude (la extensión del navegador).',
    'En la pestaña Cuotas, pulsa «Importar JSON» y usa el botón «Copiar prompt».',
    'Pégale el prompt a Claude en el navegador: leerá las ventanas abiertas y generará el JSON '
        'en el formato exacto que necesita la app.',
    'Copia ese JSON, vuelve al diálogo de importar y pégalo en el paso 2. Pulsa «Importar».',
  ];

  @override
  Widget build(BuildContext context) {
    final p = Theme.of(context).extension<AppPalette>()!;

    return ListView(padding: const EdgeInsets.all(18), children: [
      screenTitle(context, 'Guía',
          'Qué es SpecBet y para qué sirve cada herramienta.'),
      const SizedBox(height: 14),
      formCard(
        context,
        note: 'Todo el cálculo es local: nada de lo que pegues o introduzcas sale de este dispositivo.',
        child: Text(
          'SpecBet es una calculadora de apuestas de valor sobre mercados 1X2. '
          'Tú aportas las cuotas (importándolas en la pestaña Cuotas) y la app calcula '
          'los repartos: apuestas seguras, aprovechamiento de freebets y bonos, y multibono.',
          style: TextStyle(fontSize: 13, color: p.ink2, height: 1.4),
        ),
      ),
      const SizedBox(height: 14),
      _pasosCard(context, p),
      const SizedBox(height: 14),
      for (final t in _tools)
        Padding(
          padding: const EdgeInsets.only(bottom: 10),
          child: _toolCard(context, p, t.icon, t.title, t.body),
        ),
      _toolCard(
        context,
        p,
        Icons.local_offer_outlined,
        'Filtro promo · ventaja de 2 goles',
        'Interruptor global (barra lateral, o desplegable superior en móvil) para las promociones de tipo '
            '«ventaja de 2 goles». Marca las casas que la ofrezcan y actívalo: en Surebet, Freebet, Bono y '
            'Multibono, las apuestas a ganar (1 y 2) se colocan en esas casas dentro de cada tarjeta, '
            'marcadas con 🎯. El reparto se recalcula (verás el coste frente a la mejor cuota) y, si salta '
            'la promo, cobrarías el windfall extra.',
      ),
      pieAviso(context),
    ]);
  }

  Widget _pasosCard(BuildContext c, AppPalette p) {
    return Container(
      decoration: BoxDecoration(
        color: p.panel,
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: p.line),
      ),
      padding: const EdgeInsets.all(14),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                width: 34,
                height: 34,
                alignment: Alignment.center,
                decoration: BoxDecoration(color: p.accentSoft, borderRadius: BorderRadius.circular(8)),
                child: Icon(Icons.auto_awesome_outlined, size: 19, color: p.accent),
              ),
              const SizedBox(width: 12),
              const Expanded(
                child: Text('Cómo obtener las cuotas con Claude',
                    style: TextStyle(fontSize: 14, fontWeight: FontWeight.w600)),
              ),
            ],
          ),
          const SizedBox(height: 12),
          for (var i = 0; i < _pasos.length; i++)
            Padding(
              padding: EdgeInsets.only(bottom: i == _pasos.length - 1 ? 0 : 10),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Container(
                    width: 22,
                    height: 22,
                    alignment: Alignment.center,
                    decoration: BoxDecoration(color: p.accentSoft, borderRadius: BorderRadius.circular(6)),
                    child: Text('${i + 1}',
                        style: TextStyle(color: p.accent, fontSize: 11.5, fontWeight: FontWeight.w700)),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Text(_pasos[i], style: TextStyle(fontSize: 12.5, color: p.ink2, height: 1.4)),
                  ),
                ],
              ),
            ),
        ],
      ),
    );
  }

  Widget _toolCard(BuildContext c, AppPalette p, IconData icon, String title, String body) {
    return Container(
      decoration: BoxDecoration(
        color: p.panel,
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: p.line),
      ),
      padding: const EdgeInsets.all(14),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            width: 34,
            height: 34,
            alignment: Alignment.center,
            decoration: BoxDecoration(color: p.accentSoft, borderRadius: BorderRadius.circular(8)),
            child: Icon(icon, size: 19, color: p.accent),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(title, style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w600)),
                const SizedBox(height: 3),
                Text(body, style: TextStyle(fontSize: 12.5, color: p.ink2, height: 1.4)),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
