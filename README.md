# PAZ · Alejandra — Asistente jurídico laboral (Colombia)

Asistente conversacional de derecho laboral colombiano basado en RAG, con
recuperación híbrida, fichas hermenéuticas/fenomenológicas, memoria
conversacional multi-nivel y capa de captura para mejora continua.

## Componentes principales

- **Agente PAZ / Alejandra** (`agente_paz.py`, `paz.py`): capa de recuperación +
  construcción de prompt + generación con DeepSeek-V4-Flash (cache + fallback).
- **Motor de recuperación híbrida** (`motor_recuperacion.py`): vector + BM25 +
  multiquery + RRF + reranking con cross-encoder, con boost a fuente primaria.
- **Fuentes de conocimiento**:
  - Guía Laboral 2026 (fuente secundaria explicativa) — chunks Parent-Child.
  - Ley 2466 de 2025 (norma oficial primaria) — integrada con la misma lógica.
- **Memoria conversacional** (`memoria_alejandra.py`): mem0 — sesión (básica) y
  usuario (Premium, persistente).
- **Servidor local** (`servidor_paz.py`): Flask, sirve el UI y expone `/chat`,
  `/feedback`, `/captura`, `/health`.
- **UI** (`ui/index.html`): chat con selector de perfil Trabajador/Empresa,
  toggle Memoria Premium, feedback 👍/👎 y panel de memoria de entrenamiento.
- **Captura de pruebas** (`captura_pruebas.py`): registra todas las consultas y
  respuestas como dataset para entrenamiento supervisado y mejora continua.

## Estructura

```
agente_paz.py            # System prompt + recuperación + construcción de prompt
paz.py                   # Agente en producción (DeepSeek + cache + memoria)
motor_recuperacion.py    # Recuperación híbrida
memoria_alejandra.py     # mem0 (sesión + usuario premium)
captura_pruebas.py       # Logging de consultas + feedback + export dataset
servidor_paz.py          # Backend Flask + UI
ui/index.html            # Interfaz de chat
rag_laboral/             # Arquitectura de conocimiento (fichas, índice, etc.)
  01_fuente_original/    # PDF Guía + Ley 2466 de 2025
  02_inventario_cobertura/
  05_fichas_hermeneuticas/
  06_fichas_fenomenologicas/
  11_paquete_indexacion/ # chunks_parent_child + embeddings
  14_captura_pruebas/    # memoria de entrenamiento (no versionada)
```

## Puesta en marcha

```bash
# 1. Entorno
python -m venv .venv && source .venv/bin/activate
pip install flask requests sentence-transformers pymupdf rank_bm25 mem0ai

# 2. Variables de entorno
export DEEPSEEK_API_KEY=sk-...

# 3. (Opcional) Regenerar índices
python integrar_ley_2466.py   # integra la Ley 2466 al índice

# 4. Levantar servidor
python servidor_paz.py
# Abre http://localhost:5000
```

## Memoria de entrenamiento

Cada consulta se registra en `rag_laboral/14_captura_pruebas/consultas_log.jsonl`
con su perfil, semáforo, fuentes, feedback del usuario y estado de revisión.
El equipo legal puede marcar respuestas como `revisado_aprobado` o
`revisado_corregido` y luego exportar el dataset con `captura_pruebas.exportar_dataset()`
para entrenamiento supervisado.

> Nota: el log de consultas contiene conversaciones reales y **no se versiona**
> (ver `.gitignore`). Se gestiona como dato operativo privado.
