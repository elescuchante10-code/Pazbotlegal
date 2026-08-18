# -*- coding: utf-8 -*-
"""F4: Motor de recuperacion hibrida (Vector + BM25) + Multiquery + RRF + Reranking (cross-encoder).
Modulo reutilizable: from motor_recuperacion import RecuperadorHibrido
"""
import os
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"
import json, pathlib, re, math
import numpy as np
from collections import defaultdict

CHUNKS_EMB = pathlib.Path("rag_laboral/11_paquete_indexacion/chunks_parent_child_embeddings.jsonl")
PARENTS = pathlib.Path("rag_laboral/11_paquete_indexacion/chunks_parent_child.jsonl")

# --- Carga ---
def cargar_childs():
    childs = []
    with CHUNKS_EMB.open(encoding="utf-8") as f:
        for line in f:
            c = json.loads(line)
            childs.append(c)
    return childs

def cargar_parents():
    parents = {}
    with PARENTS.open(encoding="utf-8") as f:
        for line in f:
            c = json.loads(line)
            if c.get("tipo") == "parent":
                parents[c["chunk_id"]] = c
    return parents

# --- BM25 ---
class BM25:
    def __init__(self, corpus):
        self.corpus = [self._tok(d) for d in corpus]
        self.N = len(self.corpus)
        self.df = defaultdict(int)
        for doc in self.corpus:
            for t in set(doc):
                self.df[t] += 1
        self.avgdl = sum(len(d) for d in self.corpus) / max(self.N, 1)
        self.k1 = 1.5; self.b = 0.75
    def _tok(self, t):
        return re.findall(r"\w+", t.lower())
    def score(self, query):
        q = self._tok(query)
        scores = np.zeros(self.N)
        for i, doc in enumerate(self.corpus):
            if not doc: continue
            tf = defaultdict(int)
            for t in doc: tf[t] += 1
            s = 0.0
            for t in q:
                if t not in self.df: continue
                idf = math.log((self.N - self.df[t] + 0.5) / (self.df[t] + 0.5) + 1)
                f = tf.get(t, 0)
                s += idf * (f * (self.k1 + 1)) / (f + self.k1 * (1 - self.b + self.b * len(doc) / self.avgdl))
            scores[i] = s
        return scores

# --- Multiquery: genera variaciones de la pregunta ---
def generar_multiquery(query, perfil=None):
    variantes = [query]
    q = query.strip().rstrip("?")
    variantes.append(f"¿Cuales son los derechos y obligaciones sobre {q}?")
    variantes.append(f"¿Que dice la guia laboral sobre {q}?")
    if perfil == "trabajador":
        variantes.append(f"¿Que puede reclamar el trabajador sobre {q}?")
    elif perfil == "empresa":
        variantes.append(f"¿Que obligaciones tiene la empresa sobre {q}?")
    else:
        variantes.append(f"¿Que elementos y requisitos aplican a {q}?")
    return list(dict.fromkeys(variantes))[:5]

# --- RRF (Reciprocal Rank Fusion) ---
def rrf(rankings, k=60):
    """rankings: lista de listas de chunk_ids ordenados por relevancia."""
    scores = defaultdict(float)
    for ranking in rankings:
        for r, cid in enumerate(ranking):
            scores[cid] += 1.0 / (k + r + 1)
    return sorted(scores.items(), key=lambda x: -x[1])

class RecuperadorHibrido:
    def __init__(self):
        print("Cargando indice...", flush=True)
        self.childs = cargar_childs()
        self.parents = cargar_parents()
        self.textos = [c["texto_enriquecido"] for c in self.childs]
        self.embs = np.array([c["embedding"] for c in self.childs], dtype=np.float32)
        self.embs /= np.linalg.norm(self.embs, axis=1, keepdims=True) + 1e-9
        self.bm25 = BM25(self.textos)
        self.cid_index = {c["chunk_id"]: i for i, c in enumerate(self.childs)}
        print(f"Indice: {len(self.childs)} childs, {len(self.parents)} parents", flush=True)
        self._reranker = None

    def _rerank_model(self):
        if self._reranker is None:
            from sentence_transformers import CrossEncoder
            print("Cargando cross-encoder para reranking (CPU)...", flush=True)
            self._reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2", device="cpu")
        return self._reranker

    def buscar_vectorial(self, query_emb, top_k=50, perfil=None):
        q = query_emb / (np.linalg.norm(query_emb) + 1e-9)
        sims = self.embs @ q
        idx = np.argsort(-sims)[:top_k*3]
        results = []
        for i in idx:
            c = self.childs[i]
            if perfil and c.get("perfil") not in (perfil, "ambos"):
                continue
            results.append((c["chunk_id"], float(sims[i])))
            if len(results) >= top_k: break
        return results

    def buscar_bm25(self, query, top_k=50, perfil=None):
        scores = self.bm25.score(query)
        idx = np.argsort(-scores)[:top_k*3]
        results = []
        for i in idx:
            c = self.childs[i]
            if perfil and c.get("perfil") not in (perfil, "ambos"):
                continue
            results.append((c["chunk_id"], float(scores[i])))
            if len(results) >= top_k: break
        return results

    def recuperar(self, query, query_emb, top_k=10, perfil=None, rerank=True):
        # 1. Multiquery
        variantes = generar_multiquery(query, perfil)
        rankings = []
        for v in variantes:
            # Vectorial
            res_v = self.buscar_vectorial(query_emb, top_k=50, perfil=perfil)
            rankings.append([cid for cid, _ in res_v])
            # BM25
            res_b = self.buscar_bm25(v, top_k=50, perfil=perfil)
            rankings.append([cid for cid, _ in res_b])
        # 2. RRF para fusionar todos los rankings
        fused = rrf(rankings)
        top_cids = [cid for cid, _ in fused[:50]]
        # 3. Reranking con cross-encoder
        if rerank and top_cids:
            model = self._rerank_model()
            pares = [(query, self.childs[self.cid_index[cid]]["texto"]) for cid in top_cids]
            scores = model.predict(pares)
            # Boost a fuente primaria (Ley 2466): la norma oficial debe competir
            # de igual a igual con la guia explicativa, que suele dominar el reranker.
            # Solo se aplica a chunks cuyo ranking ORIGINAL (antes del boost) ya
            # estaba entre los mas relevantes del cross-encoder: un umbral por
            # porcentaje del rango de scores resulto insuficiente (la distribucion
            # de scores puede estar comprimida y dejar pasar articulos poco
            # relacionados, ej.: teletrabajo en una pregunta sobre vacaciones).
            # El ranking por posicion es mas robusto a esa compresion.
            if scores.size:
                smin, smax = float(scores.min()), float(scores.max())
                rango = (smax - smin) or 1.0
                orden_original = np.argsort(-scores)
                rank_original = {int(idx): pos for pos, idx in enumerate(orden_original)}
                TOP_RANK_PARA_BOOST = 8
                for j, cid in enumerate(top_cids):
                    doc = self.childs[self.cid_index[cid]].get("documento", "")
                    if "Ley" in doc and rank_original[j] < TOP_RANK_PARA_BOOST:
                        scores[j] += 0.35 * rango  # boost ~35% del rango
            orden = np.argsort(-scores)
            top_cids = [top_cids[i] for i in orden[:top_k]]
        else:
            top_cids = top_cids[:top_k]
        # 4. Expandir a parents (Parent-Child: entregar el parent al LLM)
        resultados = []
        vistos_parent = set()
        for cid in top_cids:
            child = self.childs[self.cid_index[cid]]
            pid = child.get("parent_id")
            parent = self.parents.get(pid)
            if parent and pid not in vistos_parent:
                vistos_parent.add(pid)
                resultados.append({
                    "child_id": cid, "parent_id": pid,
                    "tema": child["tema"], "bloque": child["bloque"],
                    "paginas": child.get("paginas", []),
                    "articulo": child.get("articulo"),
                    "documento": child.get("documento", "Guia Laboral 2026"),
                    "perfil": child["perfil"],
                    "texto_child": child["texto"],
                    "texto_parent": parent["texto"],
                    "contexto_prefijo": parent["contexto_prefijo"],
                    "topic_id": child["topic_id"],
                })
        return resultados

# --- Demo ---
if __name__ == "__main__":
    import sys
    os.environ["CUDA_VISIBLE_DEVICES"] = "-1"
    from sentence_transformers import SentenceTransformer
    print("Cargando modelo de query...", flush=True)
    qmodel = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2", device="cpu")
    rec = RecuperadorHibrido()
    query = sys.argv[1] if len(sys.argv) > 1 else "¿Cuando hay contrato realidad?"
    perfil = sys.argv[2] if len(sys.argv) > 2 else None
    print(f"\nConsulta: {query} (perfil: {perfil})\n")
    qemb = qmodel.encode([query], device="cpu", convert_to_numpy=True)[0]
    res = rec.recuperar(query, qemb, top_k=5, perfil=perfil, rerank=True)
    print(f"Resultados: {len(res)}\n")
    for i, r in enumerate(res, 1):
        print(f"--- {i}. {r['tema']} (pag {r['paginas']}) [perfil: {r['perfil']}] ---")
        print(r["texto_parent"][:300] + "...")
        print()
