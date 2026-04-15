/**
 * Google Apps Script — crea el Formulario Ronda 2 para "Anotación Epistémica T, I, F"
 *
 * COMO USARLO
 *   1. Ir a https://script.google.com/create
 *   2. Pegar todo este archivo y guardar
 *   3. Menú "Ejecutar" -> "createForm".  Autorizar con tu cuenta Google.
 *   4. Al terminar, la consola imprime:
 *        - Form URL (para compartir con los expertos)
 *        - Edit URL (para editar si hace falta)
 *        - Responses Sheet URL (respuestas en tiempo real; exportar como xlsx)
 *
 * DISEÑO
 *   30 hipótesis balanceadas por zona target:
 *     - 10 Contradiction  (evidencia simultánea pro y contra)
 *     - 10 Ignorance      (sin evidencia; predicciones del futuro cercano)
 *     - 5  Consensus      (anclas / attention check)
 *     - 5  Ambiguity      (evidencia emergente o subespecificada)
 *   Cada hipótesis: 3 preguntas en escala lineal 0–10 (T, I, F).
 *   90 ítems totales.  Duración esperada para el rater: 13–18 minutos.
 *
 *   Este estudio es STANDALONE: los raters son independientes de la Ronda 1,
 *   por lo que no se busca replicación rater-a-rater sino un diseño
 *   zone-balanced desde cero.  Paper B reporta Ronda 2 como estudio principal
 *   y Ronda 1 como piloto / análisis de sensibilidad.
 *
 *   Las respuestas se guardan automáticamente en una hoja de cálculo vinculada
 *   (misma estructura que tu formulario Ronda 1).  El script de análisis
 *   experiments/parse_expert_xlsx.py procesa directamente ese xlsx exportado.
 */


// ---------------------------------------------------------------------------
// HIPÓTESIS
// ---------------------------------------------------------------------------
const HYPOTHESES = [
  // ------ CONTRADICTION target: evidencia sólida a favor y en contra ------
  { zone_target: 'Contradiction',
    text: '¿El consumo moderado de alcohol (1–2 bebidas/día) tiene un beneficio neto sobre la salud cardiovascular?' },
  { zone_target: 'Contradiction',
    text: '¿La terapia hormonal sustitutiva es una intervención segura para mujeres postmenopáusicas sanas?' },
  { zone_target: 'Contradiction',
    text: '¿La mamografía anual en mujeres de 40 a 49 años reduce significativamente la mortalidad por cáncer de mama?' },
  { zone_target: 'Contradiction',
    text: '¿La pena de muerte es una medida efectiva para disuadir los crímenes violentos?' },
  { zone_target: 'Contradiction',
    text: '¿La inmigración a gran escala aumenta las tasas de criminalidad en los países receptores?' },
  { zone_target: 'Contradiction',
    text: '¿Los alimentos orgánicos son nutricionalmente superiores a los alimentos convencionales?' },
  { zone_target: 'Contradiction',
    text: '¿El uso intensivo de pantallas digitales daña el desarrollo cognitivo en niños menores de 12 años?' },
  { zone_target: 'Contradiction',
    text: '¿El salario mínimo elevado reduce neto el empleo en trabajadores de baja calificación?' },
  { zone_target: 'Contradiction',
    text: '¿Las dietas bajas en grasa reducen el riesgo de enfermedad coronaria más que las dietas mediterráneas?' },
  { zone_target: 'Contradiction',
    text: '¿El teletrabajo permanente mejora la productividad agregada respecto al trabajo presencial?' },

  // ------ IGNORANCE target: predicciones de futuro sin evidencia sólida ------
  { zone_target: 'Ignorance',
    text: '¿Existirá Inteligencia Artificial General (AGI) a nivel humano antes del año 2030?' },
  { zone_target: 'Ignorance',
    text: '¿Se demostrará la existencia de vida microbiana fuera de la Tierra antes del año 2035?' },
  { zone_target: 'Ignorance',
    text: '¿La computación cuántica romperá la encriptación RSA-2048 antes del año 2032?' },
  { zone_target: 'Ignorance',
    text: '¿Habrá una colonia humana permanente en la Luna antes del año 2040?' },
  { zone_target: 'Ignorance',
    text: '¿Se descubrirá un tratamiento curativo completo para la enfermedad de Alzheimer antes del año 2035?' },
  { zone_target: 'Ignorance',
    text: '¿La fusión nuclear comercial generará electricidad conectada a la red antes del año 2035?' },
  { zone_target: 'Ignorance',
    text: '¿Se adoptará una constitución federal única en la Unión Europea antes del año 2035?' },
  { zone_target: 'Ignorance',
    text: '¿El Bitcoin superará el valor de USD 500 000 antes del año 2030?' },
  { zone_target: 'Ignorance',
    text: '¿Se detectarán partículas supersimétricas en el LHC antes del año 2030?' },
  { zone_target: 'Ignorance',
    text: '¿La edición genética con CRISPR curará una enfermedad hereditaria prevalente antes del año 2030?' },

  // ------ CONSENSUS target: anclas / attention checks ------
  { zone_target: 'Consensus',
    text: '¿El VIH es la causa del Síndrome de Inmunodeficiencia Adquirida (SIDA)?' },
  { zone_target: 'Consensus',
    text: '¿Las vacunas de ARN mensajero reducen el riesgo de hospitalización por COVID-19 en adultos?' },
  { zone_target: 'Consensus',
    text: '¿La actividad física regular reduce la incidencia de diabetes tipo 2?' },
  { zone_target: 'Consensus',
    text: '¿La evolución por selección natural es el mecanismo central de la diversificación biológica?' },
  { zone_target: 'Consensus',
    text: '¿El cambio climático reciente es causado principalmente por actividad humana (emisiones de gases de efecto invernadero)?' },

  // ------ AMBIGUITY target: evidencia emergente o subespecificada ------
  { zone_target: 'Ambiguity',
    text: '¿La meditación mindfulness produce efectos terapéuticos clínicamente significativos en la depresión mayor?' },
  { zone_target: 'Ambiguity',
    text: '¿Los suplementos de vitamina D reducen el riesgo de fracturas osteoporóticas en adultos mayores sanos?' },
  { zone_target: 'Ambiguity',
    text: '¿El consumo moderado de cafeína durante el embarazo afecta negativamente el desarrollo fetal?' },
  { zone_target: 'Ambiguity',
    text: '¿Las dietas con ayuno intermitente producen mejoras metabólicas superiores a la restricción calórica continua?' },
  { zone_target: 'Ambiguity',
    text: '¿La exposición a contaminantes atmosféricos (PM2.5) a niveles actuales urbanos acelera el deterioro cognitivo en adultos mayores?' },
];


const FORM_TITLE = 'Anotación Epistémica T, I, F — Ronda 2';
const FORM_INTRO = (
  'Este formulario es parte del estudio de validación del marco estadístico ' +
  'neutrosófico. Para cada hipótesis usted asignará tres valores independientes ' +
  'en escala 0–10:\n\n' +
  '  T (Verdad / Truth): grado en que la evidencia apoya la afirmación.\n' +
  '  I (Indeterminación): grado en que la evidencia es insuficiente o contradictoria.\n' +
  '  F (Falsedad / Falsity): grado en que la evidencia refuta la afirmación.\n\n' +
  'Los tres valores son independientes. Puede asignar, por ejemplo, T = 7 y F = 6 ' +
  'si existe evidencia legítima a favor y en contra. No es necesario que T + I + F ' +
  'sumen un valor específico.\n\n' +
  'El formulario tiene 30 hipótesis × 3 preguntas = 90 ítems. Tiempo estimado: 13–18 minutos. ' +
  'Sus respuestas son anónimas y se tratarán agregadamente.'
);


// ---------------------------------------------------------------------------
// Main
// ---------------------------------------------------------------------------
function createForm() {
  const form = FormApp.create(FORM_TITLE);
  form.setDescription(FORM_INTRO)
      .setCollectEmail(false)
      .setLimitOneResponsePerUser(false)
      .setShowLinkToRespondAgain(false)
      .setAllowResponseEdits(true);

  HYPOTHESES.forEach((h, idx) => {
    const qNum = idx + 1;
    // Optional section header per hypothesis (keeps layout aligned with Ronda 1)
    form.addSectionHeaderItem()
        .setTitle(`H${qNum}. ${h.text}`)
        .setHelpText(`Zona objetivo (solo referencia interna): ${h.zone_target}. ` +
                     'Responda independientemente T, I y F en escala 0–10.');

    // T
    form.addScaleItem()
        .setTitle(`T (Verdad): ${h.text}`)
        .setBounds(0, 10)
        .setLabels('0 — ninguna evidencia a favor',
                   '10 — evidencia totalmente a favor')
        .setRequired(true);
    // I
    form.addScaleItem()
        .setTitle(`I (Indeterminación): ${h.text}`)
        .setBounds(0, 10)
        .setLabels('0 — evidencia resuelta',
                   '10 — total indeterminación')
        .setRequired(true);
    // F
    form.addScaleItem()
        .setTitle(`F (Falsedad): ${h.text}`)
        .setBounds(0, 10)
        .setLabels('0 — ninguna evidencia en contra',
                   '10 — evidencia totalmente en contra')
        .setRequired(true);
  });

  // Create linked spreadsheet for responses (same structure as Ronda 1)
  const ss = SpreadsheetApp.create(`${FORM_TITLE} (Responses)`);
  form.setDestination(FormApp.DestinationType.SPREADSHEET, ss.getId());

  // Log all URLs
  Logger.log('=====================================================');
  Logger.log('Form creado correctamente.');
  Logger.log('Hipótesis agregadas: ' + HYPOTHESES.length);
  Logger.log('Ítems totales: ' + (HYPOTHESES.length * 3));
  Logger.log('-----------------------------------------------------');
  Logger.log('Para compartir con los expertos (responder):');
  Logger.log('  ' + form.getPublishedUrl());
  Logger.log('Short URL: ' + form.shortenFormUrl(form.getPublishedUrl()));
  Logger.log('');
  Logger.log('Para editar / ver configuración:');
  Logger.log('  ' + form.getEditUrl());
  Logger.log('');
  Logger.log('Hoja de respuestas (exportar a xlsx al finalizar):');
  Logger.log('  ' + ss.getUrl());
  Logger.log('=====================================================');

  // Also return a small summary the user can copy
  return {
    formUrl:       form.getPublishedUrl(),
    editUrl:       form.getEditUrl(),
    responsesUrl:  ss.getUrl(),
    nHypotheses:   HYPOTHESES.length,
    nItems:        HYPOTHESES.length * 3,
  };
}


// ---------------------------------------------------------------------------
// Utilidad adicional: contar distribución de zonas objetivo
// ---------------------------------------------------------------------------
function printZoneDistribution() {
  const counts = {};
  HYPOTHESES.forEach(h => counts[h.zone_target] = (counts[h.zone_target] || 0) + 1);
  Logger.log('Distribución de zonas objetivo:');
  Object.keys(counts).sort().forEach(z => Logger.log(`  ${z}: ${counts[z]}`));
  Logger.log('Total: ' + HYPOTHESES.length);
}
