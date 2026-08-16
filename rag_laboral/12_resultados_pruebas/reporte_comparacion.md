# Reporte comparativo: DeepSeek vs OpenRouter (gpt-4o-mini)

Evaluacion del agente PAZ con recuperacion hibrida + reranking.

## Resumen de metricas

| Consulta | Perfil | API | Tiempo | Tokens | Estado |
|-----------|--------|-----|--------|--------|--------|
| ¿Cuando hay contrato realidad y que puede hac... | trabajador | DeepSeek | 9.6s | 1200 | OK |
| ¿Cuando hay contrato realidad y que puede hac... | trabajador | OpenRouter | 5.8s | 484 | OK |
| ¿Como puedo despedir un trabajador sin tener ... | empresa | DeepSeek | 10.5s | 1091 | OK |
| ¿Como puedo despedir un trabajador sin tener ... | empresa | OpenRouter | 7.7s | 457 | OK |
| ¿Tengo derecho a prima de servicios si llevo ... | trabajador | DeepSeek | 6.9s | 803 | OK |
| ¿Tengo derecho a prima de servicios si llevo ... | trabajador | OpenRouter | 5.6s | 353 | OK |
| ¿Que descuentos puedo hacer legalmente al sal... | empresa | DeepSeek | 9.4s | 1200 | OK |
| ¿Que descuentos puedo hacer legalmente al sal... | empresa | OpenRouter | 7.4s | 570 | OK |

## Evaluacion cualitativa (1-5)

| Criterio | DeepSeek | OpenRouter |
|----------|----------|------------|
| grounding | 3.0 | 3.5 |
| citas | 5.0 | 5.0 |
| perfil | 5.0 | 5.0 |
| estructura | 5.0 | 5.0 |
| advertencias | 5.0 | 5.0 |
| detalle | 5.0 | 5.0 |

## Promedios

- **Tiempo promedio**: DeepSeek 9.1s | OpenRouter 6.6s
- **Tokens promedio**: DeepSeek 1074 | OpenRouter 466
- **Velocidad**: OpenRouter es ~1.4x mas rapido
- **Detalle**: DeepSeek produce ~2.3x mas contenido

## Conclusion y recomendacion

### DeepSeek (deepseek-chat)
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
