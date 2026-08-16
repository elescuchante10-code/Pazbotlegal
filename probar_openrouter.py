# -*- coding: utf-8 -*-
"""Reintenta OpenRouter con varios modelos hasta encontrar uno disponible."""
import os, time, json, requests

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
or_key = os.environ["OPENROUTER_API_KEY"]

# Modelos candidatos en OpenRouter (orden de preferencia)
MODELOS = [
    "openai/gpt-4o-mini",
    "anthropic/claude-3.5-sonnet",
    "google/gemini-flash-1.5",
    "meta-llama/llama-3.1-70b-instruct",
    "openai/gpt-3.5-turbo",
]

headers = {
    "Authorization": f"Bearer {or_key}",
    "Content-Type": "application/json",
    "HTTP-Referer": "https://paz.local",
    "X-Title": "PAZ Asistente Laboral",
}
payload_base = {
    "messages": [
        {"role": "system", "content": "Eres PAZ, asistente juridico laboral. Responde breve."},
        {"role": "user", "content": "Di 'OK' si recibes este mensaje."},
    ],
    "temperature": 0.2,
    "max_tokens": 50,
}

for modelo in MODELOS:
    payload = dict(payload_base)
    payload["model"] = modelo
    print(f"Probando modelo: {modelo} ...", flush=True)
    try:
        r = requests.post(OPENROUTER_URL, headers=headers, json=payload, timeout=60)
        if r.status_code == 200:
            data = r.json()
            texto = data["choices"][0]["message"]["content"]
            print(f"  OK -> {texto[:80]}")
            print(f"MODELO_DISPONIBLE={modelo}")
            break
        else:
            print(f"  {r.status_code}: {r.text[:150]}")
    except Exception as e:
        print(f"  EXCEPCION: {e}")
