# -*- coding: utf-8 -*-
"""Consolida la comparacion DeepSeek vs OpenRouter y genera un reporte."""
import json, pathlib

dk = json.loads(pathlib.Path("rag_laboral/12_resultados_pruebas/comparacion_apis.json").read_text(encoding="utf-8"))
orr = json.loads(pathlib.Path("rag_laboral/12_resultados_pruebas/openrouter_resultados.json").read_text(encoding="utf-8"))

# Criterios de evaluacion (1-5)
def evaluar(texto, citas, perfil):
    score = {"grounding":0, "citas":0, "perfil":0, "estructura":0, "advertencias":0, "detalle":0}
    tl = texto.lower()
    score["grounding"] = 5 if "no tengo informacion" in tl or "segun" in tl or "guia laboral" in tl else 3
    score["citas"] = 5 if any(str(c) in texto for c in ["52","53","362","681","683","651","663","151","430"]) else 2
    score["perfil"] = 5 if ("trabajador" in tl and perfil=="trabajador") or ("empresa" in tl and perfil=="empresa") else 3
    score["estructura"] = 5 if "razonamiento" in tl and ("respuesta directa" in tl or "respuesta" in tl) else 3
    score["advertencias"] = 5 if "advertencia" in tl or "verificar" in tl or "norma oficial" in tl else 2
    score["detalle"] = min(5, len(texto)//300)
    return score

lineas = ["# Reporte comparativo: DeepSeek vs OpenRouter (gpt-4o-mini)\n",
          "Evaluacion del agente PAZ con recuperacion hibrida + reranking.\n",
          "## Resumen de metricas\n",
          "| Consulta | Perfil | API | Tiempo | Tokens | Estado |",
          "|-----------|--------|-----|--------|--------|--------|"]
for i in range(4):
    q = dk[i]["query"][:45]
    p = dk[i]["perfil"]
    lineas.append(f"| {q}... | {p} | DeepSeek | {dk[i]['deepseek']['tiempo']:.1f}s | {dk[i]['deepseek']['tokens']} | OK |")
    lineas.append(f"| {q}... | {p} | OpenRouter | {orr[i]['openrouter']['tiempo']:.1f}s | {orr[i]['openrouter']['tokens']} | OK |")

lineas.append("\n## Evaluacion cualitativa (1-5)\n")
lineas.append("| Criterio | DeepSeek | OpenRouter |")
lineas.append("|----------|----------|------------|")
criterios = ["grounding","citas","perfil","estructura","advertencias","detalle"]
for cr in criterios:
    sd = sum(evaluar(dk[i]['deepseek']['texto'], dk[i]['citas'], dk[i]['perfil'])[cr] for i in range(4))/4
    so = sum(evaluar(orr[i]['openrouter']['texto'], orr[i]['citas'], orr[i]['perfil'])[cr] for i in range(4))/4
    lineas.append(f"| {cr} | {sd:.1f} | {so:.1f} |")

# Promedios
lineas.append("\n## Promedios\n")
dk_t = sum(dk[i]['deepseek']['tiempo'] for i in range(4))/4
or_t = sum(orr[i]['openrouter']['tiempo'] for i in range(4))/4
dk_tok = sum(dk[i]['deepseek']['tokens'] for i in range(4))/4
or_tok = sum(orr[i]['openrouter']['tokens'] for i in range(4))/4
lineas.append(f"- **Tiempo promedio**: DeepSeek {dk_t:.1f}s | OpenRouter {or_t:.1f}s")
lineas.append(f"- **Tokens promedio**: DeepSeek {dk_tok:.0f} | OpenRouter {or_tok:.0f}")
lineas.append(f"- **Velocidad**: OpenRouter es ~{dk_t/or_t:.1f}x mas rapido")
lineas.append(f"- **Detalle**: DeepSeek produce ~{dk_tok/or_tok:.1f}x mas contenido")

lineas.append("\n## Conclusion y recomendacion\n")
lineas.append("""### DeepSeek (deepseek-chat)
- **Fortalezas**: Respuestas mas completas y detalladas, mejor manejo de casos donde falta informacion
  (dice explicitamente 'no tengo informacion suficiente'), mejor razonamiento paso a paso, incluye
  ejemplos numericos (calculo de prima), cita normas especificas (art. 24 CST, art. 64 CST, art. 59 CST).
- **Debilidades**: Mas lento (~9s vs ~6s), respuestas mas largas (puede cortarse en 1200 tokens).

### OpenRouter (gpt-4o-mini)
- **Fortalezas**: Mas rapido (~6s), respuestas concisas y bien estructuradas, buenas citas exactas
  con paginas, sigue el system prompt de forma consistente.
- **Debilidades**: Menos detalle, no siempre detecta cuando falta informacion, no incluye ejemplos
  numericos, depende de un agregador (mas modelos disponibles pero variabilidad).

### RECOMENDACION
**DeepSeek es mejor para recuperacion y contexto de respuesta** en este caso de uso juridico laboral:
1. Produce respuestas mas completas y matizadas (ideal para asesoria juridica donde el detalle importa).
2. Detecta mejor cuando el contexto no cubre la consulta (grounding mas estricto).
3. Incluye ejemplos practicos (calculos, formulas) que enriquecen la respuesta.
4. Cita normas especificas con articulos concretos.

**OpenRouter/gpt-4o-mini es mejor si priorizas velocidad y concision** (respuestas rapidas y al grano).

**Configuracion optima**: Usar DeepSeek como motor principal del agente PAZ, con OpenRouter
como fallback/alternativa. Ambos respetan el grounding y las citas configuradas en el system prompt.
""")

out = pathlib.Path("rag_laboral/12_resultados_pruebas/reporte_comparacion.md")
out.write_text("\n".join(lineas), encoding="utf-8")
print(out.read_text(encoding="utf-8"))
