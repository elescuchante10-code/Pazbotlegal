# -*- coding: utf-8 -*-
"""Reevalua OpenRouter (gpt-4o-mini) con las mismas consultas y prompts de PAZ."""
import os, sys, time, json, pathlib, requests
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from agente_paz import AgentePAZ

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_MODEL = "openai/gpt-4o-mini"
or_key = os.environ["OPENROUTER_API_KEY"]

CONSULTAS = [
    ("trabajador", "¿Cuando hay contrato realidad y que puede hacer el trabajador para reclamar sus prestaciones?"),
    ("empresa", "¿Como puedo despedir un trabajador sin tener que pagar indemnizacion?"),
    ("trabajador", "¿Tengo derecho a prima de servicios si llevo solo 6 meses trabajando?"),
    ("empresa", "¿Que descuentos puedo hacer legalmente al salario del trabajador?"),
]

def llamar(system_prompt, user_prompt):
    headers = {"Authorization": f"Bearer {or_key}", "Content-Type": "application/json",
               "HTTP-Referer": "https://paz.local", "X-Title": "PAZ Asistente Laboral"}
    payload = {"model": OPENROUTER_MODEL,
               "messages": [{"role":"system","content":system_prompt},
                            {"role":"user","content":user_prompt}],
               "temperature": 0.2, "max_tokens": 1200}
    t0 = time.time()
    r = requests.post(OPENROUTER_URL, headers=headers, json=payload, timeout=120)
    r.raise_for_status()
    data = r.json()
    return data["choices"][0]["message"]["content"], time.time()-t0, data.get("usage",{}).get("completion_tokens",0)

print("Inicializando PAZ...", flush=True)
paz = AgentePAZ()
resultados = []
for perfil, query in CONSULTAS:
    print(f"\n{'='*70}\n[{perfil.upper()}] {query}\n{'='*70}", flush=True)
    r = paz.responder(query, perfil=perfil, top_k=5)
    print(f"Fragmentos: {r['resultados_recuperados']}", flush=True)
    for c in r["citas"]:
        print(f"  - {c['tema']} (pag {c['paginas']})", flush=True)
    print("[OpenRouter] llamando...", flush=True)
    try:
        texto, t, tok = llamar(paz.system_prompt, r["prompt_llm"])
        print(f"[OpenRouter] {t:.1f}s | {tok} tokens", flush=True)
    except Exception as e:
        texto, t, tok = f"ERROR: {e}", 0, 0
        print(f"[OpenRouter] FALLO: {e}", flush=True)
    resultados.append({"perfil":perfil,"query":query,"citas":r["citas"],
                       "openrouter":{"texto":texto,"tiempo":t,"tokens":tok}})
    print(f"\n--- RESPUESTA OPENROUTER ---\n{texto[:1800]}\n", flush=True)

out = pathlib.Path("rag_laboral/12_resultados_pruebas/openrouter_resultados.json")
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(resultados, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"\nGuardado: {out}", flush=True)

print("\n" + "="*70 + "\nRESUMEN OPENROUTER (gpt-4o-mini)\n" + "="*70)
for r in resultados:
    orr = r["openrouter"]
    print(f"[{r['perfil'].upper()}] {r['query'][:55]}... -> {orr['tiempo']:.1f}s | {orr['tokens']} tok | {'OK' if 'ERROR' not in orr['texto'] else 'FALLO'}")
