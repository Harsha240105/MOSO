from moso_core.memory.manager import MemoryManager
from moso_core.memory.models import (
    EpisodicMemory,
    PreferenceMemory,
    ProceduralMemory,
    SemanticMemory,
)

try:
    from moso_core.memory.vector_store import VectorStore
    VECTOR_STORE_AVAILABLE = True
except ImportError:
    VectorStore = None  # noqa: F811
    VECTOR_STORE_AVAILABLE = False

MEMORY_AVAILABLE = True

__all__ = [
    "MEMORY_AVAILABLE",
    "VECTOR_STORE_AVAILABLE",
    "MemoryManager",
    "EpisodicMemory",
    "SemanticMemory",
    "ProceduralMemory",
    "PreferenceMemory",
    "VectorStore",
]
