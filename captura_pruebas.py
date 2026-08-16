# -*- coding: utf-8 -*-
"""Captura de pruebas y memoria de entrenamiento.
Registra TODAS las consultas y respuestas del agente en un log estructurado
(JSONL) para usarlas como dataset de entrenamiento / mejora continua.

Estructura del registro:
  - consulta_id: identificador unico de la consulta
  - timestamp: fecha/hora ISO
  - user_id, session_id, perfil, premium: contexto del consultante
  - query: pregunta original del usuario
  - respuesta: respuesta de Alejandra
  - semaforo, modelo, tokens, tiempo, desde_cache: metricas internas
  - citas: fuentes recuperadas
  - perfil_detectado, fragmentos_recuperados: trazabilidad
  - feedback: null | "positivo" | "negativo" (marcado por el usuario en el UI)
  - nota_feedback: texto opcional del usuario
  - estado: "sin_revisar" | "revisado_aprobado" | "revisado_corregido" | "descartado"
  - respuesta_corregida: version corregida (para entrenamiento supervisado)

El log vive en rag_laboral/14_captura_pruebas/consultas_log.jsonl
"""
import json, uuid, pathlib, datetime

DIR_CAPTURA = pathlib.Path("rag_laboral/14_captura_pruebas")
DIR_CAPTURA.mkdir(parents=True, exist_ok=True)
LOG = DIR_CAPTURA / "consultas_log.jsonl"
INDICE = DIR_CAPTURA / "resumen_pruebas.json"


def _ahora():
    return datetime.datetime.now().isoformat(timespec="seconds")


def registrar_consulta(data):
    """Registra una consulta completa. data debe traer: user_id, session_id,
    perfil, premium, query, respuesta, semaforo, modelo, tokens, tiempo,
    desde_cache, citas, fragmentos_recuperados.
    Devuelve el consulta_id generado."""
    consulta_id = f"q_{uuid.uuid4().hex[:12]}"
    registro = {
        "consulta_id": consulta_id,
        "timestamp": _ahora(),
        "user_id": data.get("user_id", "anonimo"),
        "session_id": data.get("session_id", ""),
        "perfil": data.get("perfil", "ambos"),
        "premium": bool(data.get("premium", False)),
        "query": data.get("query", ""),
        "respuesta": data.get("respuesta", ""),
        "semaforo": data.get("semaforo", "AMARILLO"),
        "modelo": data.get("modelo", ""),
        "tokens": data.get("tokens", 0),
        "tiempo": data.get("tiempo", 0),
        "desde_cache": bool(data.get("desde_cache", False)),
        "fragmentos_recuperados": data.get("fragmentos_recuperados", 0),
        "citas": data.get("citas", []),
        "feedback": None,
        "nota_feedback": "",
        "estado": "sin_revisar",
        "respuesta_corregida": "",
    }
    with LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(registro, ensure_ascii=False) + "\n")
    _actualizar_resumen()
    return consulta_id


def registrar_feedback(consulta_id, feedback, nota=""):
    """Marca el feedback del usuario para una consulta ya registrada.
    feedback: "positivo" | "negativo"."""
    if not LOG.exists():
        return False
    encontrado = False
    lineas = LOG.read_text(encoding="utf-8").splitlines()
    nuevas = []
    for ln in lineas:
        if not ln.strip():
            continue
        r = json.loads(ln)
        if r["consulta_id"] == consulta_id:
            r["feedback"] = feedback
            r["nota_feedback"] = nota
            encontrado = True
        nuevas.append(json.dumps(r, ensure_ascii=False))
    if encontrado:
        LOG.write_text("\n".join(nuevas) + "\n", encoding="utf-8")
        _actualizar_resumen()
    return encontrado


def marcar_estado(consulta_id, estado, respuesta_corregida=""):
    """Cambia el estado de revision de una consulta (uso del equipo legal)."""
    if not LOG.exists():
        return False
    encontrado = False
    lineas = LOG.read_text(encoding="utf-8").splitlines()
    nuevas = []
    for ln in lineas:
        if not ln.strip():
            continue
        r = json.loads(ln)
        if r["consulta_id"] == consulta_id:
            r["estado"] = estado
            if respuesta_corregida:
                r["respuesta_corregida"] = respuesta_corregida
            encontrado = True
        nuevas.append(json.dumps(r, ensure_ascii=False))
    if encontrado:
        LOG.write_text("\n".join(nuevas) + "\n", encoding="utf-8")
        _actualizar_resumen()
    return encontrado


def _actualizar_resumen():
    """Mantiene un resumen agregado para rapida consulta."""
    if not LOG.exists():
        return
    total = 0
    por_perfil = {"trabajador": 0, "empresa": 0, "ambos": 0}
    por_semaforo = {"VERDE": 0, "AMARILLO": 0, "ROJO": 0}
    feedback_pos = 0
    feedback_neg = 0
    sin_revisar = 0
    cache_hit = 0
    with LOG.open(encoding="utf-8") as f:
        for ln in f:
            if not ln.strip():
                continue
            r = json.loads(ln)
            total += 1
            por_perfil[r.get("perfil", "ambos")] = por_perfil.get(r.get("perfil", "ambos"), 0) + 1
            sem = r.get("semaforo", "AMARILLO")
            por_semaforo[sem] = por_semaforo.get(sem, 0) + 1
            if r.get("feedback") == "positivo":
                feedback_pos += 1
            elif r.get("feedback") == "negativo":
                feedback_neg += 1
            if r.get("estado") == "sin_revisar":
                sin_revisar += 1
            if r.get("desde_cache"):
                cache_hit += 1
    resumen = {
        "actualizado": _ahora(),
        "total_consultas": total,
        "por_perfil": por_perfil,
        "por_semaforo": por_semaforo,
        "feedback_positivo": feedback_pos,
        "feedback_negativo": feedback_neg,
        "sin_revisar": sin_revisar,
        "cache_hit": cache_hit,
    }
    INDICE.write_text(json.dumps(resumen, ensure_ascii=False, indent=2), encoding="utf-8")


def exportar_dataset(aprobadas_solo=True):
    """Exporta consultas listas para entrenamiento supervisado.
    Si aprobadas_solo=True, solo incluye las marcadas como revisado_aprobado
    o con feedback positivo. Devuelve una lista de pares (prompt, respuesta)."""
    if not LOG.exists():
        return []
    dataset = []
    with LOG.open(encoding="utf-8") as f:
        for ln in f:
            if not ln.strip():
                continue
            r = json.loads(ln)
            estado = r.get("estado", "sin_revisar")
            fb = r.get("feedback")
            usar = False
            if aprobadas_solo:
                if estado == "revisado_aprobado" or fb == "positivo":
                    usar = True
            else:
                usar = True
            if not usar:
                continue
            respuesta_final = r.get("respuesta_corregida") or r.get("respuesta", "")
            if not respuesta_final.strip():
                continue
            dataset.append({
                "consulta_id": r["consulta_id"],
                "perfil": r.get("perfil", "ambos"),
                "prompt": r.get("query", ""),
                "respuesta": respuesta_final,
                "citas": r.get("citas", []),
                "semaforo": r.get("semaforo", "AMARILLO"),
            })
    return dataset


def listar_recientes(n=20):
    """Devuelve las N consultas mas recientes (para el panel de captura)."""
    if not LOG.exists():
        return []
    lineas = LOG.read_text(encoding="utf-8").splitlines()
    recientes = []
    for ln in reversed(lineas[-n:]):
        if not ln.strip():
            continue
        r = json.loads(ln)
        recientes.append({
            "consulta_id": r["consulta_id"],
            "timestamp": r.get("timestamp", ""),
            "perfil": r.get("perfil", "ambos"),
            "query": r.get("query", "")[:120],
            "semaforo": r.get("semaforo", ""),
            "feedback": r.get("feedback"),
            "estado": r.get("estado", "sin_revisar"),
        })
    return recientes


def resumen():
    """Devuelve el resumen agregado actual."""
    if INDICE.exists():
        return json.loads(INDICE.read_text(encoding="utf-8"))
    return {"total_consultas": 0}
