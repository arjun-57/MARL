"""RAG Document Ingestion, Indexing, and Semantic Retriever."""

import logging
from pathlib import Path
from typing import List, Dict, Any
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)


class KnowledgeRetriever:
    """Ingests engineering documents and provides cosine-similarity retrieval."""

    def __init__(self, doc_dir: str = "rag/documents"):
        self.doc_dir = Path(doc_dir)
        self.chunks: List[Dict[str, str]] = []
        self.vectorizer = TfidfVectorizer(stop_words="english")
        self.tfidf_matrix = None
        self._load_and_index()

    def _load_and_index(self):
        """Loads all markdown docs and splits them into section chunks."""
        if not self.doc_dir.exists():
            return

        docs = list(self.doc_dir.glob("*.md"))
        for d in docs:
            text = d.read_text(encoding="utf-8")
            # Split by headers (## )
            sections = text.split("\n## ")
            doc_title = sections[0].strip("# \n")

            for s in sections[1:]:
                header = s.split("\n")[0].strip()
                content = "\n".join(s.split("\n")[1:]).strip()
                chunk_text = f"Document: {doc_title} | Section: {header}\n{content}"
                self.chunks.append({
                    "title": doc_title,
                    "section": header,
                    "content": chunk_text,
                    "source": d.name
                })

        if self.chunks:
            texts = [c["content"] for c in self.chunks]
            self.tfidf_matrix = self.vectorizer.fit_transform(texts)
            logger.info(f"RAG indexed {len(self.chunks)} knowledge chunks from {len(docs)} documents")

    def retrieve(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """Finds top-k most relevant knowledge chunks."""
        if not self.chunks or self.tfidf_matrix is None:
            return []

        query_vec = self.vectorizer.transform([query])
        similarities = cosine_similarity(query_vec, self.tfidf_matrix).flatten()
        top_indices = np.argsort(similarities)[::-1][:top_k]

        results = []
        for idx in top_indices:
            score = float(similarities[idx])
            chunk = dict(self.chunks[idx])
            chunk["score"] = score
            results.append(chunk)

        return results
