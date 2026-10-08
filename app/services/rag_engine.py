import os
import re
import math
from typing import List, Dict, Any, Tuple
from collections import Counter
from app.core.config import settings

class DocumentChunk:
    def __init__(self, doc_id: str, title: str, section: str, content: str):
        self.doc_id = doc_id
        self.title = title
        self.section = section
        self.content = content
        self.words = self._tokenize(content)

    @staticmethod
    def _tokenize(text: str) -> List[str]:
        return re.findall(r"\b[a-zA-Z0-9_]{2,}\b", text.lower())

class RAGEngine:
    """Production hybrid retrieval engine using BM25 and term scoring."""
    
    def __init__(self, knowledge_dir: str = settings.KNOWLEDGE_DIR):
        self.knowledge_dir = knowledge_dir
        self.chunks: List[DocumentChunk] = []
        self.doc_freqs: Counter = Counter()
        self.avg_doc_len: float = 0.0
        self._load_and_index()

    def _load_and_index(self):
        if not os.path.exists(self.knowledge_dir):
            return

        total_words = 0
        for fname in os.listdir(self.knowledge_dir):
            if not fname.endswith(".md"):
                continue
            fpath = os.path.join(self.knowledge_dir, fname)
            with open(fpath, "r", encoding="utf-8") as f:
                raw_text = f.read()

            title = fname.replace(".md", "").replace("_", " ").title()
            # Split by markdown headers
            sections = re.split(r"\n(?=##?\s)", raw_text)
            for idx, sec in enumerate(sections):
                lines = sec.strip().split("\n")
                sec_header = lines[0].replace("#", "").strip() if lines else title
                content = sec.strip()
                if not content:
                    continue
                chunk = DocumentChunk(doc_id=fname, title=title, section=sec_header, content=content)
                self.chunks.append(chunk)
                total_words += len(chunk.words)
                
                # Unique terms in chunk for IDF
                unique_terms = set(chunk.words)
                for term in unique_terms:
                    self.doc_freqs[term] += 1

        if self.chunks:
            self.avg_doc_len = total_words / len(self.chunks)

    def search(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        query_terms = DocumentChunk._tokenize(query)
        if not query_terms or not self.chunks:
            return []

        scores: List[Tuple[float, DocumentChunk]] = []
        k1 = 1.5
        b = 0.75
        N = len(self.chunks)

        for chunk in self.chunks:
            chunk_len = len(chunk.words)
            term_counts = Counter(chunk.words)
            score = 0.0

            for q in query_terms:
                if q in term_counts:
                    freq = term_counts[q]
                    df = self.doc_freqs.get(q, 0)
                    idf = math.log(1 + (N - df + 0.5) / (df + 0.5))
                    tf = (freq * (k1 + 1)) / (freq + k1 * (1 - b + b * (chunk_len / (self.avg_doc_len or 1.0))))
                    score += idf * tf

            # Title / Section exact keyword boost
            for q in query_terms:
                if q in chunk.title.lower():
                    score += 2.0
                if q in chunk.section.lower():
                    score += 1.5

            if score > 0:
                scores.append((score, chunk))

        scores.sort(key=lambda x: x[0], reverse=True)
        top_results = scores[:top_k]

        if not top_results:
            return []

        max_score = top_results[0][0]
        results = []
        for score, chunk in top_results:
            # Normalize confidence score between 0.0 and 1.0
            norm_score = round(min(1.0, score / max(1.0, max_score * 0.9)), 3)
            results.append({
                "doc_id": chunk.doc_id,
                "title": chunk.title,
                "section": chunk.section,
                "content": chunk.content,
                "relevance_score": norm_score
            })
        return results

rag_engine = RAGEngine()
