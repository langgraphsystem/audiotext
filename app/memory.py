"""
Memory system for bot - stores and retrieves analyzed content using Supabase + pgvector.
"""
import hashlib
from datetime import datetime
from typing import Optional, List, Dict, Any

from openai import AsyncOpenAI
from supabase import create_client, Client

from .config import settings
from .logger import get_logger

logger = get_logger(__name__)


class MemoryStore:
    """
    Memory store for bot using Supabase with pgvector for semantic search.
    """

    def __init__(self):
        self.supabase: Client = create_client(
            settings.supabase_url,
            settings.supabase_key
        )
        self.table = settings.supabase_table
        self.openai = AsyncOpenAI(api_key=settings.openai_api_key, timeout=30.0)
        self.embedding_model = settings.memory_embedding_model
        logger.info(f"Supabase memory store initialized. Table: {self.table}")

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

            response = await self.openai.embeddings.create(
                model=self.embedding_model,
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Error getting embedding: {e}")
            return []

    def _extract_summary(self, analysis: str) -> str:
        """Extract a short summary from analysis."""
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

        return analysis[:200].strip()

    async def add_memory(
        self,
        user_id: int,
        content: str,
        analysis: str,
        source_url: Optional[str] = None,
        content_type: str = "tiktok"
    ) -> bool:
        """
        Add new content to user's memory in Supabase.

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
            # Check for duplicates
            content_hash = self._content_hash(content)

            existing = self.supabase.table(self.table).select("id").eq(
                "user_id", user_id
            ).eq("content_hash", content_hash).execute()

            if existing.data:
                logger.info(f"Duplicate content skipped for user {user_id}")
                return False

            # Get embedding for the combined content + analysis
            combined_text = f"{content}\n\n{analysis}"
            embedding = await self._get_embedding(combined_text)

            if not embedding:
                logger.warning("Failed to get embedding, saving without vector")

            # Create memory entry
            entry = {
                "user_id": user_id,
                "content_hash": content_hash,
                "content_type": content_type,
                "source_url": source_url,
                "content": content[:5000],  # Limit content size
                "analysis": analysis[:10000],  # Limit analysis size
                "embedding": embedding if embedding else None,
                "summary": self._extract_summary(analysis),
                "created_at": datetime.utcnow().isoformat()
            }

            # Insert into Supabase
            result = self.supabase.table(self.table).insert(entry).execute()

            if result.data:
                logger.info(f"Added memory entry for user {user_id}")

                # Check and enforce max entries limit
                await self._enforce_max_entries(user_id)
                return True

            return False

        except Exception as e:
            logger.error(f"Error adding memory for user {user_id}: {e}")
            return False

    async def _enforce_max_entries(self, user_id: int):
        """Remove oldest entries if user exceeds max limit."""
        try:
            # Count user's entries
            count_result = self.supabase.table(self.table).select(
                "id", count="exact"
            ).eq("user_id", user_id).execute()

            total = count_result.count or 0
            max_entries = settings.memory_max_entries

            if total > max_entries:
                # Get oldest entries to delete
                excess = total - max_entries
                oldest = self.supabase.table(self.table).select("id").eq(
                    "user_id", user_id
                ).order("created_at", desc=False).limit(excess).execute()

                if oldest.data:
                    ids_to_delete = [entry["id"] for entry in oldest.data]
                    self.supabase.table(self.table).delete().in_(
                        "id", ids_to_delete
                    ).execute()
                    logger.info(f"Deleted {len(ids_to_delete)} old entries for user {user_id}")

        except Exception as e:
            logger.error(f"Error enforcing max entries: {e}")

    async def search_memory(
        self,
        user_id: int,
        query: str,
        top_k: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Search user's memory using semantic similarity via pgvector.

        Args:
            user_id: Telegram user ID
            query: Search query
            top_k: Number of results to return

        Returns:
            List of relevant memory entries
        """
        try:
            # Get query embedding
            query_embedding = await self._get_embedding(query)

            if not query_embedding:
                # Fallback to keyword search
                return await self._keyword_search(user_id, query, top_k)

            # Use Supabase RPC for vector similarity search
            result = self.supabase.rpc(
                "match_memories",
                {
                    "query_embedding": query_embedding,
                    "match_user_id": user_id,
                    "match_threshold": 0.5,
                    "match_count": top_k
                }
            ).execute()

            if not result.data:
                return []

            return [
                {
                    "id": r["id"],
                    "content": r["content"],
                    "analysis": r["analysis"],
                    "summary": r.get("summary", ""),
                    "source_url": r.get("source_url"),
                    "timestamp": r["created_at"],
                    "similarity": round(r.get("similarity", 0), 3)
                }
                for r in result.data
            ]

        except Exception as e:
            logger.error(f"Error searching memory for user {user_id}: {e}")
            # Fallback to keyword search on error
            return await self._keyword_search(user_id, query, top_k)

    async def _keyword_search(
        self,
        user_id: int,
        query: str,
        top_k: int
    ) -> List[Dict[str, Any]]:
        """Fallback keyword search when vector search fails."""
        try:
            # Simple text search using ilike
            result = self.supabase.table(self.table).select(
                "id, content, analysis, summary, source_url, created_at"
            ).eq("user_id", user_id).or_(
                f"content.ilike.%{query}%,analysis.ilike.%{query}%"
            ).limit(top_k).execute()

            if not result.data:
                return []

            return [
                {
                    "id": r["id"],
                    "content": r["content"],
                    "analysis": r["analysis"],
                    "summary": r.get("summary", ""),
                    "source_url": r.get("source_url"),
                    "timestamp": r["created_at"],
                    "similarity": 0.0
                }
                for r in result.data
            ]

        except Exception as e:
            logger.error(f"Error in keyword search: {e}")
            return []

    def get_all_memories(self, user_id: int) -> List[Dict[str, Any]]:
        """Get all memories for a user."""
        try:
            result = self.supabase.table(self.table).select(
                "id, created_at, content_type, summary, source_url"
            ).eq("user_id", user_id).order(
                "created_at", desc=True
            ).execute()

            return [
                {
                    "id": entry["id"],
                    "timestamp": entry["created_at"],
                    "content_type": entry.get("content_type", "unknown"),
                    "summary": entry.get("summary", "")[:100],
                    "source_url": entry.get("source_url")
                }
                for entry in result.data
            ] if result.data else []

        except Exception as e:
            logger.error(f"Error getting memories for user {user_id}: {e}")
            return []

    def get_memory_stats(self, user_id: int) -> Dict[str, Any]:
        """Get memory statistics for a user."""
        try:
            # Get count
            count_result = self.supabase.table(self.table).select(
                "id", count="exact"
            ).eq("user_id", user_id).execute()

            # Get first and last entry dates
            first = self.supabase.table(self.table).select(
                "created_at"
            ).eq("user_id", user_id).order(
                "created_at", desc=False
            ).limit(1).execute()

            last = self.supabase.table(self.table).select(
                "created_at"
            ).eq("user_id", user_id).order(
                "created_at", desc=True
            ).limit(1).execute()

            # Get content types
            types_result = self.supabase.table(self.table).select(
                "content_type"
            ).eq("user_id", user_id).execute()

            types = list(set(
                r.get("content_type", "unknown")
                for r in (types_result.data or [])
            ))

            return {
                "total_entries": count_result.count or 0,
                "created": first.data[0]["created_at"] if first.data else None,
                "updated": last.data[0]["created_at"] if last.data else None,
                "types": types
            }

        except Exception as e:
            logger.error(f"Error getting stats for user {user_id}: {e}")
            return {"total_entries": 0, "created": None, "updated": None, "types": []}

    def clear_memory(self, user_id: int) -> bool:
        """Clear all memories for a user."""
        try:
            self.supabase.table(self.table).delete().eq(
                "user_id", user_id
            ).execute()
            logger.info(f"Memory cleared for user {user_id}")
            return True
        except Exception as e:
            logger.error(f"Error clearing memory for user {user_id}: {e}")
            return False

    async def close(self):
        """Close the OpenAI client."""
        try:
            await self.openai.close()
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
