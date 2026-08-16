# -*- coding: utf-8 -*-
"""Harness de evaluacion: compara DeepSeek vs OpenRouter usando el agente PAZ.
Simula consultas de trabajador y empresa. Mide tiempo, longitud y calidad de contexto.
Las API keys se leen de variables de entorno (no se escriben en el codigo).
"""
import os, sys, time, json, pathlib, requests

# Importar el agente PAZ
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from agente_paz import AgentePAZ

DEEPSEEK_URL = "https://api.deepseek.com/v1/chat/completions"
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

# Modelos a probar
DEEPSEEK_MODEL = "deepseek-chat"
OPENROUTER_MODEL = "anthropic/claude-3.5-sonnet"  # amplio contexto y razonamiento

# Consultas de prueba (perfil, query)
CONSULTAS = [
    ("trabajador", "¿Cuando hay contrato realidad y que puede hacer el trabajador para reclamar sus prestaciones?"),
    ("empresa", "¿Como puedo despedir un trabajador sin tener que pagar indemnizacion?"),
    ("trabajador", "¿Tengo derecho a prima de servicios si llevo solo 6 meses trabajando?"),
    ("empresa", "¿Que descuentos puedo hacer legalmente al salario del trabajador?"),
]

def llamar_api(url, api_key, model, system_prompt, user_prompt, temperatura=0.2):
    """Llama una API compatible con OpenAI y devuelve (texto, tiempo_seg, tokens)."""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    if "openrouter" in url:
        headers["HTTP-Referer"] = "https://paz.local"
        headers["X-Title"] = "PAZ Asistente Laboral"
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": temperatura,
        "max_tokens": 1200,
    }
    t0 = time.time()
    try:
        r = requests.post(url, headers=headers, json=payload, timeout=120)
        r.raise_for_status()
        data = r.json()
        texto = data["choices"][0]["message"]["content"]
        usage = data.get("usage", {})
        tokens = usage.get("completion_tokens", len(texto.split()))
        return texto, time.time() - t0, tokens
    except Exception as e:
        return f"ERROR: {e}", time.time() - t0, 0

def main():
    dk_key = os.environ.get("DEEPSEEK_API_KEY", "")
    or_key = os.environ.get("OPENROUTER_API_KEY", "")
    if not dk_key or not or_key:
        print("ERROR: faltan API keys en variables de entorno")
        return

    print("Inicializando agente PAZ (recuperacion hibrida)...", flush=True)
    paz = AgentePAZ()

    resultados = []
    for perfil, query in CONSULTAS:
        print(f"\n{'='*70}\nCONSULTA [{perfil.upper()}]: {query}\n{'='*70}", flush=True)
        # 1. Recuperar con PAZ
        r = paz.responder(query, perfil=perfil, top_k=5)
        prompt = r["prompt_llm"]
        system_prompt = paz.system_prompt
        print(f"Fragmentos recuperados: {r['resultados_recuperados']}", flush=True)
        for c in r["citas"]:
            print(f"  - {c['tema']} (pag {c['paginas']})", flush=True)

        # 2. Llamar DeepSeek
        print("\n[DeepSeek] llamando...", flush=True)
        ds_texto, ds_tiempo, ds_tokens = llamar_api(
            DEEPSEEK_URL, dk_key, DEEPSEEK_MODEL, system_prompt, prompt)
        print(f"[DeepSeek] {ds_tiempo:.1f}s | {ds_tokens} tokens", flush=True)

        # 3. Llamar OpenRouter
        print("[OpenRouter] llamando...", flush=True)
        or_texto, or_tiempo, or_tokens = llamar_api(
            OPENROUTER_URL, or_key, OPENROUTER_MODEL, system_prompt, prompt)
        print(f"[OpenRouter] {or_tiempo:.1f}s | {or_tokens} tokens", flush=True)

        resultados.append({
            "perfil": perfil, "query": query,
            "citas": r["citas"],
            "deepseek": {"texto": ds_texto, "tiempo": ds_tiempo, "tokens": ds_tokens},
            "openrouter": {"texto": or_texto, "tiempo": or_tiempo, "tokens": or_tokens},
        })

        # Mostrar respuestas
        print(f"\n--- RESPUESTA DEEPSEEK ---\n{ds_texto[:1500]}\n", flush=True)
        print(f"--- RESPUESTA OPENROUTER ---\n{or_texto[:1500]}\n", flush=True)

    # Guardar resultados completos
    out = pathlib.Path("rag_laboral/12_resultados_pruebas/comparacion_apis.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(resultados, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nResultados guardados: {out}", flush=True)

    # Resumen comparativo
    print("\n" + "="*70)
    print("RESUMEN COMPARATIVO")
    print("="*70)
    for r in resultados:
        print(f"\n[{r['perfil'].upper()}] {r['query'][:60]}...")
        ds = r["deepseek"]; orr = r["openrouter"]
        print(f"  DeepSeek:   {ds['tiempo']:.1f}s | {ds['tokens']} tokens | {'OK' if 'ERROR' not in ds['texto'] else 'FALLO'}")
        print(f"  OpenRouter: {orr['tiempo']:.1f}s | {orr['tokens']} tokens | {'OK' if 'ERROR' not in orr['texto'] else 'FALLO'}")

if __name__ == "__main__":
    main()
