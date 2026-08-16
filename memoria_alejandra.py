# -*- coding: utf-8 -*-
"""Capa de memoria de Alejandra basada en mem0.
Tres niveles que mapean a la distincion free vs Premium del system prompt:

- MEMORIA DE SESION (basica, gratis): recuerda dentro de una conversacion.
  Se pierde al cerrar la sesion. Clave: session_id.
- MEMORIA DE USUARIO (persistente, PREMIUM): recuerda el caso del cliente entre sesiones.
  Permanece en el tiempo. Clave: user_id.
- MEMORIA DE AGENTE (estado de Alejandra): lo que Alejandra sabe del caso y del cliente.

Cada cliente tiene su propio user_id (memoria aislada = multi-tenant).
"""
import os
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"
os.environ["TOKENIZERS_PARALLELISM"] = "false"
import json, pathlib

# Configuracion de mem0: DeepSeek como LLM, HuggingFace local como embedder (privacidad)
def _config_mem0():
    from mem0 import Memory
    config = {
        "llm": {
            "provider": "deepseek",
            "config": {
                "model": "deepseek-chat",
                "api_key": os.environ.get("DEEPSEEK_API_KEY", ""),
                "temperature": 0.2,
            },
        },
        "embedder": {
            "provider": "huggingface",
            "config": {
                "model": "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
            },
        },
        "vector_store": {
            "provider": "qdrant",
            "config": {
                "path": str(pathlib.Path("rag_laboral/13_versiones_publicadas/memoria_qdrant").resolve()),
                "embedding_model_dims": 384,
            },
        },
    }
    return Memory.from_config(config)


class MemoriaAlejandra:
    """Capa de memoria multi-nivel para Alejandra."""

    def __init__(self):
        print("Inicializando capa de memoria (mem0)...", flush=True)
        self.mem = _config_mem0()
        print("Capa de memoria lista.", flush=True)

    # --- MEMORIA DE SESION (basica, gratis) ---
    def recordar_sesion(self, texto, session_id, user_id=None):
        """Guarda un hecho en la memoria de sesion (se pierde al cerrar)."""
        mid = f"ses_{session_id}"
        meta = {"nivel": "sesion", "session_id": session_id}
        if user_id:
            meta["user_id_orig"] = user_id
        return self.mem.add(texto, user_id=mid, metadata=meta)

    def buscar_sesion(self, query, session_id, top_k=5):
        """Recupera hechos de la memoria de sesion actual."""
        mid = f"ses_{session_id}"
        return self.mem.search(query, filters={"user_id": mid}, top_k=top_k)

    # --- MEMORIA DE USUARIO (persistente, PREMIUM) ---
    def recordar_usuario(self, texto, user_id):
        """Guarda un hecho en la memoria persistente del cliente (Premium)."""
        mid = f"usr_{user_id}"
        return self.mem.add(texto, user_id=mid, metadata={"nivel": "usuario"})

    def buscar_usuario(self, query, user_id, top_k=5):
        """Recupera hechos persistentes del cliente (entre sesiones)."""
        mid = f"usr_{user_id}"
        return self.mem.search(query, filters={"user_id": mid}, top_k=top_k)

    def es_premium(self, user_id):
        """Verifica si el cliente tiene memoria persistente (Premium) activa."""
        mid = f"usr_{user_id}"
        try:
            res = self.mem.search("caso trabajo empresa despido salario", filters={"user_id": mid}, top_k=1)
            return len(res.get("results", [])) > 0
        except Exception:
            return False

    # --- MEMORIA DE AGENTE (estado de Alejandra) ---
    def recordar_agente(self, texto):
        """Guarda un hecho en la memoria de Alejandra (su estado global)."""
        return self.mem.add(texto, user_id="alejandro_agente", metadata={"nivel": "agente"})

    def buscar_agente(self, query, top_k=3):
        return self.mem.search(query, filters={"user_id": "alejandro_agente"}, top_k=top_k)

    # --- CONTEXTO COMBINADO para inyectar en el prompt ---
    def contexto_para_prompt(self, query, session_id, user_id=None, es_premium=False):
        """Construye el bloque de memoria para inyectar en el prompt de Alejandra.
        El backend lo envia al modelo pero NO lo muestra al usuario."""
        partes = []
        # Memoria de sesion (siempre disponible = basica)
        ses = self.buscar_sesion(query, session_id, top_k=4)
        if ses.get("results"):
            hechos = [f"- {r['memory']}" for r in ses["results"]]
            partes.append("MEMORIA DE LA CONVERSACION ACTUAL (memoria basica):\n" + "\n".join(hechos))
        # Memoria de usuario (solo Premium)
        if es_premium and user_id:
            usr = self.buscar_usuario(query, user_id, top_k=5)
            if usr.get("results"):
                hechos = [f"- {r['memory']}" for r in usr["results"]]
                partes.append("MEMORIA PERSISTENTE DEL CLIENTE (PAZ Agente Premium):\n" + "\n".join(hechos))
        return "\n\n".join(partes) if partes else ""
