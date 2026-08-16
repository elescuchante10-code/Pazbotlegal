# -*- coding: utf-8 -*-
"""PAZ - Asistente juridico laboral configurado en produccion.
Motor principal: DeepSeek-V4-Flash (rapido/economico).
Fallback: DeepSeek-V4-Pro (para consultas complejas).
Incluye CACHE de consultas para ahorrar costos (hash del prompt -> respuesta guardada).

Uso:
  export DEEPSEEK_API_KEY=sk-...
  python paz.py "¿consulta?" trabajador
  python paz.py "¿consulta?" empresa
  python paz.py "¿consulta?" ambos
"""
import os, sys, time, json, hashlib, pathlib, re
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"
sys.path.insert(0, str(pathlib.Path(__file__).parent))

from agente_paz import AgentePAZ
import requests

# --- Configuracion de modelos ---
MODELO_PRINCIPAL = "deepseek-v4-flash"   # rapido, economico, para la mayoria de consultas
MODELO_FALLBACK = "deepseek-v4-pro"     # mas potente, para consultas complejas o si el principal falla
DEEPSEEK_URL = "https://api.deepseek.com/v1/chat/completions"
TEMPERATURA = 0.2

# --- Cache de consultas (ahorro de costos) ---
DIR_CACHE = pathlib.Path("rag_laboral/13_versiones_publicadas/cache_paz")
DIR_CACHE.mkdir(parents=True, exist_ok=True)

def hash_prompt(system_prompt, user_prompt, modelo):
    """Hash determinista del prompt para clave de cache."""
    clave = f"{modelo}|{system_prompt}|{user_prompt}"
    return hashlib.sha256(clave.encode("utf-8")).hexdigest()

def leer_cache(clave):
    fp = DIR_CACHE / f"{clave}.json"
    if fp.exists():
        return json.loads(fp.read_text(encoding="utf-8"))
    return None

def escribir_cache(clave, data):
    fp = DIR_CACHE / f"{clave}.json"
    fp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

def llamar_deepseek(api_key, modelo, system_prompt, user_prompt, temperatura=TEMPERATURA):
    """Llama DeepSeek API (compatible OpenAI). Devuelve (texto, tiempo, tokens, modelo_usado).
    DeepSeek-V4-Flash es un modelo de razonamiento: usa reasoning_content (interno,
    NO se muestra al usuario) y content (la respuesta final visible)."""
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {
        "model": modelo,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": temperatura,
        "max_tokens": 8192,  # espacio amplio para razonamiento + respuesta final
    }
    t0 = time.time()
    r = requests.post(DEEPSEEK_URL, headers=headers, json=payload, timeout=180)
    r.raise_for_status()
    data = r.json()
    msg = data["choices"][0]["message"]
    # content = respuesta final visible; reasoning_content = razonamiento interno (oculto)
    texto = msg.get("content") or ""
    # Si content viene vacio (modelo gasto tokens en razonamiento), usar reasoning como fallback
    if not texto.strip():
        texto = msg.get("reasoning_content") or ""
    # Defensa: limpiar razonamiento que se haya filtrado al content visible
    texto = limpiar_razonamiento(texto)
    tokens = data.get("usage", {}).get("completion_tokens", 0)
    return texto, time.time() - t0, tokens, modelo


# --- Patrones de razonamiento interno que el modelo NO debe exponer ---
_RE_RAZON = re.compile(
    r"^(la consulta|el usuario|del historial|debo |necesito |voy a |puedo |"
    r"estructura de la respuesta|analisis|vuelvo a |espera|conclusi[óo]n:|"
    r"redacto|mi respuesta|la respuesta debe|la instrucci|dado que|dado el|"
    r"la pregunta|el contexto|las fuentes|debo hacer|debo citar|debo incluir|"
    r"debo considerar|mi recomendaci[óo]n es redactar|primero|segundo|tercero|"
    r"paso |paso a paso|resumen|resumen del caso|hechos|regla|norma aplicable)",
    re.IGNORECASE,
)
_CIERRE = "Si quieres implementar la norma, pasate a premium y contacta a PAZ ORTEGA"


def limpiar_razonamiento(texto):
    """Si el modelo filtra su razonamiento al content, recorta hasta la respuesta
    real. Heuristica: la respuesta final SIEMPRE termina con la linea de cierre
    obligatoria. Si esa linea existe, la respuesta util esta antes; si ademas hay
    razonamiento previo, lo descartamos tomando desde la primera linea que no sea
    meta-razonamiento. Si no existe la linea de cierre, el modelo solo razono:
    devolvemos el mensaje de no-informacion."""
    if not texto or not texto.strip():
        return texto
    t = texto.strip()
    # Caso 1: el modelo solo razono (no llego a la respuesta final)
    if _CIERRE.lower() not in t.lower():
        # Buscar si hay al menos una seccion de fuentes -> respuesta parcial
        if "**fuentes consultadas:**" in t.lower() or "fuentes consultadas:" in t.lower():
            # Hay respuesta parcial: tomar desde el inicio hasta el cierre si aparece,
            # sino hasta el final (la respuesta esta, solo falta el cierre)
            return _recortar_inicio(t)
        # No hay respuesta real: devolver guardrail de no-informacion
        return ("No tengo informacion suficiente sobre eso en las fuentes consultadas. "
                "Para revisarlo con detalle, podemos escalar el caso a PAZ Agente Premium.\n\n"
                '"Si quieres implementar la norma, pasate a premium y contacta a PAZ ORTEGA."')
    # Caso 2: hay linea de cierre -> la respuesta esta completa; quitar razonamiento previo
    return _recortar_inicio(t)


def _recortar_inicio(t):
    """Elimina lineas iniciales que sean meta-razonamiento hasta la primera linea
    que parezca orientacion real al usuario."""
    lineas = t.split("\n")
    idx = 0
    # Saltar lineas de razonamiento al inicio (hasta 40 lineas de salvaguarda)
    while idx < len(lineas) and idx < 40:
        ln = lineas[idx].strip()
        if not ln:
            idx += 1
            continue
        # Si la linea es claramente meta-razonamiento, saltar
        if _RE_RAZON.match(ln):
            idx += 1
            continue
        # Si la linea comienza con un marcador de cita dentro de razonamiento tipo "[1] habla de..."
        # pero no es la seccion de fuentes, igual saltamos solo si estamos en bloque de razonamiento
        break
    recortado = "\n".join(lineas[idx:]).strip()
    # Si tras recortar quedo muy poco o sin la seccion de fuentes, devolver original
    if len(recortado) < 40:
        return t
    return recortado


class PAZProduccion:
    """Agente PAZ en produccion con DeepSeek-V4-Flash + cache + memoria multi-nivel."""

    def __init__(self, usar_cache=True, usar_memoria=True):
        print("Inicializando PAZ (DeepSeek-V4-Flash)...", flush=True)
        self.agente = AgentePAZ()
        self.usar_cache = usar_cache
        self.modelo_principal = MODELO_PRINCIPAL
        self.modelo_fallback = MODELO_FALLBACK
        self.system_prompt = self.agente.system_prompt  # System prompt de Alejandra
        self.temperatura = TEMPERATURA
        self.api_key = os.environ.get("DEEPSEEK_API_KEY", "")
        if not self.api_key:
            raise RuntimeError("Falta DEEPSEEK_API_KEY en variables de entorno")
        self.estadisticas = {"cache_hit": 0, "cache_miss": 0, "fallback": 0}
        # Capa de memoria multi-nivel (mem0)
        self.memoria = None
        if usar_memoria:
            try:
                from memoria_alejandra import MemoriaAlejandra
                self.memoria = MemoriaAlejandra()
            except Exception as e:
                print(f"[aviso] Memoria no disponible: {e}", flush=True)

    def consultar(self, query, perfil=None, top_k=5, historial=None,
                   session_id=None, user_id=None, es_premium=False):
        """Consulta completa: recuperar + memoria + generar con DeepSeek + cache.
        El backend envia el prompt al modelo pero NO lo muestra al usuario."""
        # 0. Recuperar memoria (sesion + usuario premium)
        memoria_ctx = ""
        if self.memoria and session_id:
            memoria_ctx = self.memoria.contexto_para_prompt(query, session_id, user_id, es_premium)
        # 1. Recuperar contexto juridico con motor hibrido
        r = self.agente.responder(query, perfil=perfil, top_k=top_k, historial=historial)
        prompt = r["prompt_llm"]
        # 1b. Inyectar memoria en el prompt (no se muestra al usuario)
        if memoria_ctx:
            prompt = prompt.replace(
                "CONTEXTO RECUPERADO",
                f"MEMORIA RECUPERADA DEL CLIENTE (usala naturalmente, no la menciones como 'memoria'):\n{memoria_ctx}\n\n---\n\nCONTEXTO RECUPERADO")
        # 2. Clave de cache
        clave = hash_prompt(self.system_prompt, prompt, self.modelo_principal)

        # 3. Verificar cache
        if self.usar_cache:
            cached = leer_cache(clave)
            if cached:
                self.estadisticas["cache_hit"] += 1
                cached["desde_cache"] = True
                return cached

        # 4. Llamar DeepSeek-V4-Flash (principal)
        self.estadisticas["cache_miss"] += 1
        try:
            texto, t, tokens, modelo = llamar_deepseek(
                self.api_key, self.modelo_principal, self.system_prompt, prompt, self.temperatura)
        except Exception as e:
            # 5. Fallback a V4-Pro si el principal falla
            self.estadisticas["fallback"] += 1
            texto, t, tokens, modelo = llamar_deepseek(
                self.api_key, self.modelo_fallback, self.system_prompt, prompt, self.temperatura)

        # 6. Construir resultado
        resultado = {
            "query": query,
            "perfil": perfil or "ambos",
            "modelo": modelo,
            "temperatura": self.temperatura,
            "respuesta": texto,
            "tiempo_generacion": t,
            "tokens": tokens,
            "desde_cache": False,
            "fragmentos_recuperados": r["resultados_recuperados"],
            "citas": r["citas"],
            "semaforo": r.get("semaforo", "AMARILLO"),
            "prompt_enviado": prompt,  # NO se muestra al usuario
        }

        # 7. Guardar en cache
        if self.usar_cache:
            escribir_cache(clave, resultado)

        # 8. Guardar en memoria (sesion + usuario premium)
        if self.memoria and session_id:
            try:
                # Memoria de sesion (basica): la consulta y respuesta
                self.memoria.recordar_sesion(
                    f"El usuario pregunto: {query}. Alejandra respondio sobre: {r['citas'][0].get('tema') if r['citas'] else 'el tema'}",
                    session_id, user_id)
                # Memoria de usuario (persistente, solo Premium)
                if es_premium and user_id:
                    self.memoria.recordar_usuario(
                        f"Caso del cliente: {query}. Tema: {r['citas'][0].get('tema') if r['citas'] else 'varios'}. "
                        f"Perfil: {perfil or 'ambos'}. Respuesta: {texto[:300]}",
                        user_id)
            except Exception as e:
                print(f"[aviso] No se pudo guardar memoria: {e}", flush=True)

        return resultado

    def mostrar_system_prompt(self):
        """Devuelve el system prompt de PAZ."""
        return self.system_prompt


# --- CLI ---
def main():
    if len(sys.argv) < 2:
        print('Uso: python paz.py "¿consulta?" [trabajador|empresa|ambos] [user_id] [--premium]')
        print('     python paz.py --prompt   (muestra el system prompt)')
        print('     python paz.py --chat [trabajador|empresa] [user_id] [--premium]  (modo conversacional)')
        return
    if sys.argv[1] == "--prompt":
        paz = PAZProduccion(usar_cache=False, usar_memoria=False)
        print("\n" + "=" * 70)
        print("SYSTEM PROMPT DE ALEJANDRA (no se muestra al usuario en produccion)")
        print("=" * 70 + "\n")
        print(paz.mostrar_system_prompt())
        print("\n" + "=" * 70)
        print("Ubicacion: agente_paz.py (variable SYSTEM_PROMPT_ALEJANDRA)")
        print("=" * 70)
        return

    if sys.argv[1] == "--chat":
        # Modo conversacional interactivo con memoria
        perfil = sys.argv[2] if len(sys.argv) > 2 else "ambos"
        user_id = sys.argv[3] if len(sys.argv) > 3 else "cliente_demo"
        es_premium = "--premium" in sys.argv
        if perfil == "ambos":
            perfil = None
        session_id = f"ses_{user_id}_{int(time.time())}"
        paz = PAZProduccion(usar_cache=True, usar_memoria=True)
        historial = []
        print(f"\n{'='*70}\nALEJANDRA (modo conversacional) | cliente: {user_id} | premium: {es_premium}")
        print(f"Escribe 'salir' para terminar.\n{'='*70}\n")
        while True:
            try:
                query = input("Tu: ").strip()
            except (EOFError, KeyboardInterrupt):
                break
            if query.lower() in ("salir", "exit", "quit"):
                break
            if not query:
                continue
            res = paz.consultar(query, perfil=perfil, top_k=5, historial=historial,
                               session_id=session_id, user_id=user_id, es_premium=es_premium)
            historial.append({"usuario": query, "alejandra": res["respuesta"][:400]})
            print(f"\nAlejandra: {res['respuesta']}\n")
            if res.get("citas"):
                print("Fuentes: " + ", ".join(f"{c['marcador']}{c.get('documento','')} {c.get('locator','')}" for c in res["citas"][:3]))
            print(f"[interno] semaforo: {res.get('semaforo','?')} | cache: {paz.estadisticas}\n")
        print("\nHasta pronto. Si necesitas seguir trabajando el caso, podemos retomarlo cuando quieras.")
        return

    # Consulta unica
    query = sys.argv[1]
    perfil = sys.argv[2] if len(sys.argv) > 2 else "ambos"
    user_id = sys.argv[3] if len(sys.argv) > 3 else None
    es_premium = "--premium" in sys.argv
    if perfil == "ambos":
        perfil = None

    paz = PAZProduccion(usar_cache=True, usar_memoria=True)
    session_id = f"ses_{user_id or 'anon'}_{int(time.time())}" if user_id else None
    res = paz.consultar(query, perfil=perfil, top_k=5,
                       session_id=session_id, user_id=user_id, es_premium=es_premium)

    # El backend envia el prompt al modelo pero NO lo muestra al usuario.
    # Solo se muestra la respuesta de Alejandra (la profesional visible).
    print("\n" + "=" * 70)
    print(f"ALEJANDRA  [modelo: {res['modelo']} | cache: {'SI' if res['desde_cache'] else 'NO'} | semaforo: {res.get('semaforo','?')}]")
    print("=" * 70 + "\n")
    print(res["respuesta"])
    print("\n" + "-" * 70)
    print("Fuentes consultadas:")
    for c in res["citas"]:
        loc = c.get("locator", "")
        print(f"  {c['marcador']} {c.get('documento','')} - {loc} [{c.get('topic_id','')}]")
    print("-" * 70)
    print(f"[interno] cache: {paz.estadisticas} | tokens: {res['tokens']} | tiempo: {res['tiempo_generacion']:.1f}s")

if __name__ == "__main__":
    main()
