# -*- coding: utf-8 -*-
"""Servidor local de PAZ/Alejandra. Sirve el UI y expone el endpoint /chat.
Uso: python servidor_paz.py  (luego abre http://localhost:5000)
"""
import os, sys, uuid, pathlib
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"
os.environ["TOKENIZERS_PARALLELISM"] = "false"
# Persistir modelos de HuggingFace en el volumen de datos (Railway) si DATA_DIR esta definido
_DATA_DIR = os.environ.get("DATA_DIR")
if _DATA_DIR:
    os.environ["HF_HOME"] = str(pathlib.Path(_DATA_DIR) / "hf_cache")
    os.environ["TRANSFORMERS_CACHE"] = str(pathlib.Path(_DATA_DIR) / "hf_cache")
sys.path.insert(0, str(pathlib.Path(__file__).parent))

from flask import Flask, request, jsonify, send_from_directory
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from paz import PAZProduccion
import captura_pruebas as captura

app = Flask(__name__, static_folder=str(pathlib.Path(__file__).parent / "ui"), static_url_path="")
BASE_DIR = pathlib.Path(__file__).parent

limiter = Limiter(get_remote_address, app=app, default_limits=["200 per hour"])

# Instancia unica del agente (se carga al arrancar el servidor)
print("=== Iniciando servidor PAZ/Alejandra ===", flush=True)
agente = PAZProduccion(usar_cache=True, usar_memoria=True)
print("=== Agente listo. Esperando consultas ===", flush=True)

# Sesiones en memoria: session_id -> historial
sesiones = {}

@app.route("/")
def index():
    return send_from_directory(str(BASE_DIR / "ui"), "index.html")

@app.route("/chat", methods=["POST"])
@limiter.limit("15 per minute; 100 per hour")
def chat():
    data = request.get_json(force=True)
    query = (data.get("query") or "").strip()
    perfil = data.get("perfil") or "ambos"
    user_id = data.get("user_id") or "anonimo"
    es_premium = bool(data.get("premium"))
    session_id = data.get("session_id")
    if not query:
        return jsonify({"error": "Consulta vacia"}), 400
    if perfil == "ambos":
        perfil_api = None
    else:
        perfil_api = perfil
    # Crear o recuperar sesion
    if not session_id:
        session_id = f"ses_{user_id}_{uuid.uuid4().hex[:8]}"
        sesiones[session_id] = {"historial": [], "user_id": user_id, "perfil": perfil}
    if session_id not in sesiones:
        sesiones[session_id] = {"historial": [], "user_id": user_id, "perfil": perfil}
    hist = sesiones[session_id]["historial"]
    try:
        res = agente.consultar(query, perfil=perfil_api, top_k=5, historial=hist,
                              session_id=session_id, user_id=user_id, es_premium=es_premium)
    except Exception as e:
        return jsonify({"error": f"Error interno: {e}"}), 500
    # Actualizar historial
    hist.append({"usuario": query, "alejandra": res.get("respuesta", "")[:500]})
    # --- Captura para memoria de entrenamiento ---
    try:
        consulta_id = captura.registrar_consulta({
            "user_id": user_id, "session_id": session_id, "perfil": perfil,
            "premium": es_premium, "query": query,
            "respuesta": res.get("respuesta", ""),
            "semaforo": res.get("semaforo", "AMARILLO"),
            "modelo": res.get("modelo", ""), "tokens": res.get("tokens", 0),
            "tiempo": round(res.get("tiempo_generacion", 0), 2),
            "desde_cache": res.get("desde_cache", False),
            "fragmentos_recuperados": res.get("fragmentos_recuperados", 0),
            "citas": res.get("citas", []),
        })
    except Exception as e:
        consulta_id = None
        print(f"[aviso] captura fallo: {e}", flush=True)
    return jsonify({
        "respuesta": res.get("respuesta", ""),
        "citas": res.get("citas", []),
        "semaforo": res.get("semaforo", "AMARILLO"),
        "modelo": res.get("modelo", ""),
        "tokens": res.get("tokens", 0),
        "tiempo": round(res.get("tiempo_generacion", 0), 1),
        "desde_cache": res.get("desde_cache", False),
        "session_id": session_id,
        "cache_stats": agente.estadisticas,
        "consulta_id": consulta_id,
    })

@app.route("/feedback", methods=["POST"])
@limiter.limit("30 per minute")
def feedback():
    """Registra feedback del usuario (positivo/negativo) sobre una consulta."""
    data = request.get_json(force=True)
    consulta_id = data.get("consulta_id")
    fb = data.get("feedback")  # "positivo" | "negativo"
    nota = data.get("nota", "")
    if fb not in ("positivo", "negativo") or not consulta_id:
        return jsonify({"error": "datos invalidos"}), 400
    ok = captura.registrar_feedback(consulta_id, fb, nota)
    return jsonify({"ok": ok})

CAPTURA_TOKEN = os.environ.get("CAPTURA_TOKEN", "")

@app.route("/captura", methods=["GET"])
@limiter.limit("10 per minute")
def panel_captura():
    """Panel de captura (uso interno): resumen + consultas recientes.
    Contiene conversaciones reales de usuarios; requiere token de administrador."""
    token = request.args.get("token") or request.headers.get("X-Captura-Token")
    if not CAPTURA_TOKEN or token != CAPTURA_TOKEN:
        return jsonify({"error": "No autorizado"}), 403
    return jsonify({
        "resumen": captura.resumen(),
        "recientes": captura.listar_recientes(30),
    })

@app.route("/health")
def health():
    return jsonify({"status": "ok", "memoria": agente.memoria is not None})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False, threaded=True)
