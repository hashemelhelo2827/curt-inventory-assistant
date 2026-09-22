"""Vector RAG stub for PDF Q16 — TF-IDF over CORE_PART_INFO descriptions (no external vector DB)."""
try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    HAS_SKLEARN = True
except:
    HAS_SKLEARN = False
from agent.tools.databaseserver.helper import get_db_connection

_vectorizer = None
_docs = []
_meta = []

def _load():
    global _vectorizer, _docs, _meta
    if _docs:
        return
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT part_number, part_name, description, category FROM CORE_PART_INFO")
        rows = cur.fetchall()
        _docs = [f"{r['part_name']} ({r['part_number']}) {r['category']}: {r['description']}" for r in rows]
        _meta = [dict(r) for r in rows]
        if HAS_SKLEARN:
            _vectorizer = TfidfVectorizer().fit(_docs)
        else:
            _vectorizer = True

def rag_query(query: str, top_k: int = 3):
    """Simple RAG: cosine similarity over TF-IDF of part descriptions. Falls back to difflib if sklearn missing."""
    _load()
    if HAS_SKLEARN:
        q_vec = _vectorizer.transform([query])
        d_vec = _vectorizer.transform(_docs)
        sims = cosine_similarity(q_vec, d_vec)[0]
        idxs = sims.argsort()[::-1][:top_k]
        return [{"score": float(sims[i]), "doc": _docs[i], "meta": _meta[i]} for i in idxs if sims[i] > 0.1]
    else:
        import difflib
        closes = difflib.get_close_matches(query, _docs, n=top_k, cutoff=0.1)
        return [{"score": 0.5, "doc": c, "meta": _meta[_docs.index(c)]} for c in closes]
