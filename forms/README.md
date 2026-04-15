# Forms — Expert annotation, Round 2

Script de Google Apps Script que genera un formulario en tu Google Drive con
25 hipótesis balanceadas por zona objetivo para una segunda ronda de
anotación con expertos independientes.

## Diseño

Estudio STANDALONE con raters independientes de la Ronda 1. No se busca
replicación rater-a-rater; se prioriza diseño zone-balanced desde cero.
Paper B reporta Ronda 2 como estudio principal y Ronda 1 como piloto /
análisis de sensibilidad.

| Zona objetivo | # hipótesis | Propósito |
|---|---|---|
| Contradiction | 10 | Probar el schema NS en casos con evidencia legítima a favor y en contra (T alto + F alto) |
| Ignorance | 10 | Probar el schema NS en casos sin evidencia (T bajo, F bajo; I alto o 0) |
| Consensus | 5 | Anclas + attention checks (VIH→SIDA, evolución, cambio climático antropogénico…) |
| Ambiguity | 5 | Evidencia emergente o subespecificada (mindfulness, vitamina D, PM2.5) |
| **Total** | **30** | 90 ítems · 13–18 min por rater |

## Uso

1. Abrí <https://script.google.com/create>
2. Pegá el contenido de `create_google_form_round2.gs` y guardá
3. Ejecutá la función `createForm`. Google te pide autorización la primera vez
4. Al terminar revisá `Ver → Registros` (o `View → Logs`) para obtener:
   - **Form URL** (para compartir con los expertos)
   - **Edit URL** (para editar antes de publicar)
   - **Responses Sheet URL** (exportar como xlsx al cerrar la ronda)
5. Exportá la hoja de respuestas como `.xlsx` cuando tengas los datos
6. Regenerá el CSV anonimizado con:

   ```bash
   python experiments/parse_expert_xlsx.py path/to/responses.xlsx
   # overwrites exp_expert_long.csv
   ```
7. Re-ejecutá análisis: `exp_expert_annotation.py` + `exp_expert_filter.py`
   y luego `gen_expert_figure.py` para regenerar Fig 4

## Plan de reclutamiento sugerido

- Reclutar ~30 expertos nuevos vía redes académicas (email o LinkedIn).
  Enviar en 2 oleadas (15 + 15) separadas por 1 semana para controlar efectos
  temporales (noticias cambiando evidencia durante la recolección).
- Recordatorio único a la semana del primer envío (aumenta respuestas ~50%).
- Cerrar ronda a las 3 semanas del primer envío.

## Meta-análisis esperado tras Ronda 2

- Poder ≥ 0.80 para detectar diferencia NS vs Interval **dentro de cada zona**
  con n=30 expertos y ~8 hipótesis por zona (McNemar + stratified).
- Las Contradiction y Ignorance son zonas donde Interval no puede distinguir
  pero NS sí — ahí se demuestra la ventaja real del framework.
- Comparación entre rondas (17 exp/30 hyp vs 30 exp/30 hyp balanceado) sirve
  como sensitivity analysis, no como replicación.
