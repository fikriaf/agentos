"""Vector memory using ChromaDB."""

import hashlib
from pathlib import Path
from typing import Optional

from agentos.models.memory import Memory
from agentos.utils.logger import get_logger

logger = get_logger("agentos.memory.vector")


class VectorMemory:
    """ChromaDB-backed semantic memory.

    Provides semantic search over conversation history,
    learned patterns, and context.
    """

    def __init__(
        self,
        persist_directory: Optional[Path] = None,
        collection_name: str = "agentos_memory",
    ):
        """Initialize vector memory.

        Args:
            persist_directory: Directory to persist ChromaDB
            collection_name: Name of collection
        """
        self.persist_directory = persist_directory or Path.home() / ".agentos" / "memory"
        self.collection_name = collection_name
        self.client = None
        self.collection = None

        self._initialize()

    def _initialize(self) -> None:
        """Initialize ChromaDB."""
        try:
            import chromadb
            from chromadb.config import Settings

            self.client = chromadb.PersistentClient(
                path=str(self.persist_directory),
                settings=Settings(anonymized_telemetry=False),
            )
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"description": "AgentOS memory store"},
            )
            logger.info(f"VectorMemory initialized: {self.persist_directory}")
        except ImportError:
            logger.warning("ChromaDB not installed. Vector search disabled.")
            self.client = None
            self.collection = None

    async def add(
        self,
        content: str,
        metadata: Optional[dict] = None,
        embedding: Optional[list[float]] = None,
    ) -> str:
        """Add memory.

        Args:
            content: Memory content
            metadata: Optional metadata
            embedding: Optional pre-computed embedding

        Returns:
            Memory ID
        """
        if not self.collection:
            logger.warning("ChromaDB not available")
            return ""

        memory_id = self._generate_id(content)
        metadata = metadata or {}

        # Generate embedding if not provided
        if not embedding:
            embedding = await self._embed(content)

        self.collection.add(
            ids=[memory_id],
            documents=[content],
            embeddings=[embedding],
            metadatas=[metadata],
        )

        logger.debug(f"Memory added: {memory_id}")
        return memory_id

    async def search(
        self,
        query: str,
        k: int = 5,
        filter_metadata: Optional[dict] = None,
    ) -> list[Memory]:
        """Search memories by semantic similarity.

        Args:
            query: Search query
            k: Number of results
            filter_metadata: Optional metadata filter

        Returns:
            List of matching memories
        """
        if not self.collection:
            logger.warning("ChromaDB not available")
            return []

        embedding = await self._embed(query)

        results = self.collection.query(
            query_embeddings=[embedding],
            n_results=k,
            where=filter_metadata,
        )

        memories = []
        if results and results["ids"]:
            for i, memory_id in enumerate(results["ids"][0]):
                memories.append(
                    Memory(
                        id=memory_id,
                        content=results["documents"][0][i],
                        metadata=results["metadatas"][0][i] if results["metadatas"] else {},
                    )
                )

        return memories

    async def get(self, memory_id: str) -> Optional[Memory]:
        """Get memory by ID.

        Args:
            memory_id: Memory ID

        Returns:
            Memory or None
        """
        if not self.collection:
            return None

        results = self.collection.get(ids=[memory_id])
        if not results or not results["ids"]:
            return None

        return Memory(
            id=memory_id,
            content=results["documents"][0],
            metadata=results["metadatas"][0] if results["metadatas"] else {},
        )

    async def delete(self, memory_id: str) -> bool:
        """Delete memory.

        Args:
            memory_id: Memory ID

        Returns:
            True if deleted
        """
        if not self.collection:
            return False

        try:
            self.collection.delete(ids=[memory_id])
            return True
        except Exception as e:
            logger.error(f"Delete failed: {e}")
            return False

    async def _embed(self, text: str) -> list[float]:
        """Generate embedding for text.

        Args:
            text: Text to embed

        Returns:
            Embedding vector
        """
        # Simple hash-based fallback if no embedding model
        # In production, use OpenAI/Cohere embeddings
        try:
            import numpy as np

            # Simple TF-IDF-like embedding (placeholder)
            # Real implementation would use: openai.embeddings.create()
            hash_val = hashlib.md5(text.encode()).digest()
            arr = list(hash_val)
            # Normalize
            norm = sum(x * x for x in arr) ** 0.5
            return [x / norm * 100 for x in arr]
        except Exception:
            # Fallback: random but deterministic
            import numpy as np

            np.random.seed(hash(text) % (2**32))
            return list(np.random.randn(128))

    @staticmethod
    def _generate_id(content: str) -> str:
        """Generate deterministic ID for content.

        Args:
            content: Content to hash

        Returns:
            ID string
        """
        return hashlib.md5(content.encode()).hexdigest()[:16]

    def count(self) -> int:
        """Get memory count.

        Returns:
            Number of memories
        """
        if not self.collection:
            return 0
        return self.collection.count()
