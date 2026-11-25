import math
import re
from dataclasses import dataclass

from apps.resources.models import Resource

STOPWORDS = {
    # English
    'a', 'an', 'the', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
    'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'from', 'about',
    'and', 'or', 'but', 'if', 'then', 'so', 'as', 'it', 'this', 'that',
    'what', 'how', 'why', 'when', 'where', 'who', 'can', 'could', 'would',
    'should', 'do', 'does', 'did', 'me', 'my', 'you', 'your', 'we', 'i',
    'explain', 'help', 'please', 'tell',
    # Indonesian
    'yang', 'dan', 'di', 'ke', 'dari', 'ini', 'itu', 'untuk', 'pada',
    'dengan', 'adalah', 'apa', 'bagaimana', 'gimana', 'kenapa', 'mengapa',
    'tolong', 'jelaskan', 'jelasin', 'bisa', 'saya', 'aku', 'dong', 'ya',
    'pak', 'chill', 'kak', 'nya', 'atau', 'kalau', 'jika', 'dalam', 'ada',
}


@dataclass
class RetrievedChunk:
    resource: Resource
    snippet: str
    score: float


def _tokenize(text: str) -> list[str]:
    tokens = re.findall(r'[a-zA-Z0-9_+#]+', (text or '').lower())
    return [t for t in tokens if len(t) > 1 and t not in STOPWORDS]


def _chunk_text(text: str, chunk_size: int = 900, overlap: int = 150) -> list[str]:
    clean = (text or '').strip()
    if not clean:
        return []
    if len(clean) <= chunk_size:
        return [clean]
    chunks = []
    start = 0
    while start < len(clean):
        end = start + chunk_size
        chunks.append(clean[start:end].strip())
        if end >= len(clean):
            break
        start = end - overlap
    return chunks


def retrieve_relevant_resources(query: str, top_k: int = 4) -> list[RetrievedChunk]:
    """Find the most relevant faculty resource chunks using pure-Python weighted TF scoring."""
    query_tokens = _tokenize(query)
    resources = list(Resource.objects.filter(is_active=True).select_related('category'))
    if not resources:
        return []

    if not query_tokens:
        # Return brief summaries of the first few active resources
        return [
            RetrievedChunk(
                resource=r,
                snippet=(r.summary or r.extracted_text[:400]),
                score=0.1,
            )
            for r in resources[:top_k]
        ]

    query_set = set(query_tokens)
    candidates: list[RetrievedChunk] = []

    for resource in resources:
        title_tokens = set(_tokenize(resource.title))
        cat_tokens = set(_tokenize(resource.category.name if resource.category else ''))
        summary_tokens = set(_tokenize(resource.summary))

        title_hits = len(query_set & title_tokens)
        cat_hits = len(query_set & cat_tokens)
        summary_hits = len(query_set & summary_tokens)
        meta_boost = (title_hits * 4.0) + (cat_hits * 2.5) + (summary_hits * 2.0)

        chunks = _chunk_text(resource.extracted_text or resource.summary)
        if not chunks:
            if meta_boost > 0:
                candidates.append(RetrievedChunk(resource=resource, snippet=resource.summary, score=meta_boost))
            continue

        best_chunk_score = 0.0
        best_chunk_text = chunks[0]
        for chunk in chunks:
            chunk_tokens = _tokenize(chunk)
            if not chunk_tokens:
                continue
            tf_score = 0.0
            for qt in query_set:
                count = chunk_tokens.count(qt)
                if count > 0:
                    tf_score += 1.0 + math.log(count)
            # Small bonus for exact phrase match
            if len(query.strip()) >= 4 and query.strip().lower() in chunk.lower():
                tf_score += 3.0

            total = tf_score + meta_boost
            if total > best_chunk_score:
                best_chunk_score = total
                best_chunk_text = chunk

        if best_chunk_score > 0:
            candidates.append(
                RetrievedChunk(resource=resource, snippet=best_chunk_text, score=best_chunk_score)
            )

    candidates.sort(key=lambda item: item.score, reverse=True)
    return candidates[:top_k]
