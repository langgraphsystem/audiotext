"""
Memory system for bot - stores and retrieves analyzed content using embeddings.
"""
import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any

from openai import AsyncOpenAI

from .config import settings
from .logger import get_logger

logger = get_logger(__name__)


class MemoryStore:
    """
    Memory store for bot - saves analyzed content and enables semantic search.
    Uses OpenAI embeddings for similarity search.
    """

    def __init__(self):
        self.memory_dir = settings.workdir / "memory"
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        self.client = AsyncOpenAI(api_key=settings.openai_api_key, timeout=30.0)
        self.embedding_model = settings.memory_embedding_model
        logger.info(f"Memory store initialized. Directory: {self.memory_dir}")

    def _get_user_file(self, user_id: int) -> Path:
        """Get path to user's memory file."""
        return self.memory_dir / f"user_{user_id}.json"

    def _load_user_memory(self, user_id: int) -> Dict[str, Any]:
        """Load user's memory from file."""
        file_path = self._get_user_file(user_id)
        if file_path.exists():
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading memory for user {user_id}: {e}")
        return {"entries": [], "metadata": {"created": datetime.now().isoformat()}}

    def _save_user_memory(self, user_id: int, memory: Dict[str, Any]):
        """Save user's memory to file."""
        file_path = self._get_user_file(user_id)
        try:
            memory["metadata"]["updated"] = datetime.now().isoformat()
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(memory, f, ensure_ascii=False, indent=2)
            logger.info(f"Memory saved for user {user_id}")
        except Exception as e:
            logger.error(f"Error saving memory for user {user_id}: {e}")

    def _content_hash(self, content: str) -> str:
        """Generate hash for content to avoid duplicates."""
        return hashlib.md5(content.encode()).hexdigest()[:16]

    async def _get_embedding(self, text: str) -> List[float]:
        """Get embedding vector for text using OpenAI."""
        try:
            # Truncate text if too long (max ~8000 tokens for embedding model)
            max_chars = 30000
            if len(text) > max_chars:
                text = text[:max_chars]

            response = await self.client.embeddings.create(
                model=self.embedding_model,
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Error getting embedding: {e}")
            return []

    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        if not vec1 or not vec2 or len(vec1) != len(vec2):
            return 0.0

        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        magnitude1 = sum(a * a for a in vec1) ** 0.5
        magnitude2 = sum(b * b for b in vec2) ** 0.5

        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0

        return dot_product / (magnitude1 * magnitude2)

    async def add_memory(
        self,
        user_id: int,
        content: str,
        analysis: str,
        source_url: Optional[str] = None,
        content_type: str = "tiktok"
    ) -> bool:
        """
        Add new content to user's memory.

        Args:
            user_id: Telegram user ID
            content: Original transcribed content
            analysis: GPT analysis of the content
            source_url: Source URL (e.g., TikTok link)
            content_type: Type of content

        Returns:
            True if successfully added
        """
        try:
            memory = self._load_user_memory(user_id)

            # Check for duplicates
            content_hash = self._content_hash(content)
            for entry in memory["entries"]:
                if entry.get("hash") == content_hash:
                    logger.info(f"Duplicate content skipped for user {user_id}")
                    return False

            # Get embedding for the combined content + analysis
            combined_text = f"{content}\n\n{analysis}"
            embedding = await self._get_embedding(combined_text)

            if not embedding:
                logger.warning("Failed to get embedding, saving without vector")

            # Create memory entry
            entry = {
                "id": len(memory["entries"]) + 1,
                "hash": content_hash,
                "timestamp": datetime.now().isoformat(),
                "content_type": content_type,
                "source_url": source_url,
                "content": content[:5000],  # Limit content size
                "analysis": analysis[:10000],  # Limit analysis size
                "embedding": embedding,
                "summary": self._extract_summary(analysis)
            }

            memory["entries"].append(entry)

            # Limit total entries per user
            max_entries = settings.memory_max_entries
            if len(memory["entries"]) > max_entries:
                # Remove oldest entries (keep embeddings space manageable)
                memory["entries"] = memory["entries"][-max_entries:]

            self._save_user_memory(user_id, memory)
            logger.info(f"Added memory entry #{entry['id']} for user {user_id}")
            return True

        except Exception as e:
            logger.error(f"Error adding memory for user {user_id}: {e}")
            return False

    def _extract_summary(self, analysis: str) -> str:
        """Extract a short summary from analysis."""
        # Try to find РЕЗЮМЕ section
        lines = analysis.split("\n")
        summary_lines = []
        in_summary = False

        for line in lines:
            if "РЕЗЮМЕ" in line.upper() or "SUMMARY" in line.upper():
                in_summary = True
                continue
            if in_summary:
                if line.strip().startswith(("2.", "ЧЕКЛИСТ", "CHECKLIST")):
                    break
                if line.strip():
                    summary_lines.append(line.strip())
                    if len(summary_lines) >= 3:
                        break

        if summary_lines:
            return " ".join(summary_lines)[:500]

        # Fallback: first 200 chars
        return analysis[:200].strip()

    async def search_memory(
        self,
        user_id: int,
        query: str,
        top_k: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Search user's memory using semantic similarity.

        Args:
            user_id: Telegram user ID
            query: Search query
            top_k: Number of results to return

        Returns:
            List of relevant memory entries
        """
        try:
            memory = self._load_user_memory(user_id)
            entries = memory.get("entries", [])

            if not entries:
                return []

            # Get query embedding
            query_embedding = await self._get_embedding(query)
            if not query_embedding:
                # Fallback to keyword search
                return self._keyword_search(entries, query, top_k)

            # Calculate similarities
            results = []
            for entry in entries:
                entry_embedding = entry.get("embedding", [])
                if entry_embedding:
                    similarity = self._cosine_similarity(query_embedding, entry_embedding)
                    results.append({
                        "entry": entry,
                        "similarity": similarity
                    })

            # Sort by similarity and return top_k
            results.sort(key=lambda x: x["similarity"], reverse=True)

            return [
                {
                    "id": r["entry"]["id"],
                    "content": r["entry"]["content"],
                    "analysis": r["entry"]["analysis"],
                    "summary": r["entry"].get("summary", ""),
                    "source_url": r["entry"].get("source_url"),
                    "timestamp": r["entry"]["timestamp"],
                    "similarity": round(r["similarity"], 3)
                }
                for r in results[:top_k]
                if r["similarity"] > 0.5  # Minimum similarity threshold
            ]

        except Exception as e:
            logger.error(f"Error searching memory for user {user_id}: {e}")
            return []

    def _keyword_search(
        self,
        entries: List[Dict],
        query: str,
        top_k: int
    ) -> List[Dict[str, Any]]:
        """Fallback keyword search when embeddings fail."""
        query_lower = query.lower()
        query_words = set(query_lower.split())

        results = []
        for entry in entries:
            content = entry.get("content", "").lower()
            analysis = entry.get("analysis", "").lower()

            # Count matching words
            text = f"{content} {analysis}"
            matches = sum(1 for word in query_words if word in text)

            if matches > 0:
                results.append({
                    "entry": entry,
                    "matches": matches
                })

        results.sort(key=lambda x: x["matches"], reverse=True)

        return [
            {
                "id": r["entry"]["id"],
                "content": r["entry"]["content"],
                "analysis": r["entry"]["analysis"],
                "summary": r["entry"].get("summary", ""),
                "source_url": r["entry"].get("source_url"),
                "timestamp": r["entry"]["timestamp"],
                "similarity": 0.0
            }
            for r in results[:top_k]
        ]

    def get_all_memories(self, user_id: int) -> List[Dict[str, Any]]:
        """Get all memories for a user (without embeddings)."""
        memory = self._load_user_memory(user_id)
        entries = memory.get("entries", [])

        return [
            {
                "id": entry["id"],
                "timestamp": entry["timestamp"],
                "content_type": entry.get("content_type", "unknown"),
                "summary": entry.get("summary", entry["content"][:100]),
                "source_url": entry.get("source_url")
            }
            for entry in entries
        ]

    def get_memory_stats(self, user_id: int) -> Dict[str, Any]:
        """Get memory statistics for a user."""
        memory = self._load_user_memory(user_id)
        entries = memory.get("entries", [])

        return {
            "total_entries": len(entries),
            "created": memory.get("metadata", {}).get("created"),
            "updated": memory.get("metadata", {}).get("updated"),
            "types": list(set(e.get("content_type", "unknown") for e in entries))
        }

    def clear_memory(self, user_id: int) -> bool:
        """Clear all memories for a user."""
        try:
            file_path = self._get_user_file(user_id)
            if file_path.exists():
                file_path.unlink()
            logger.info(f"Memory cleared for user {user_id}")
            return True
        except Exception as e:
            logger.error(f"Error clearing memory for user {user_id}: {e}")
            return False

    async def close(self):
        """Close the OpenAI client."""
        try:
            await self.client.close()
        except Exception:
            pass


# Global memory store instance
memory_store: Optional[MemoryStore] = None


def get_memory_store() -> MemoryStore:
    """Get or create global memory store instance."""
    global memory_store
    if memory_store is None:
        memory_store = MemoryStore()
    return memory_store
