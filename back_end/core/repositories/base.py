"""
Base repository class for Save Sabi.

Provides a common interface for data access that can be implemented
for different backends (PostgreSQL, Firestore, etc.).
"""

from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any, TypeVar, Generic
from django.db.models import Model

T = TypeVar('T', bound=Model)


class BaseRepository(ABC, Generic[T]):
    """
    Abstract base class for repositories.
    
    Defines the common interface for data access operations.
    Implementations can target different databases.
    """
    
    @abstractmethod
    def get_by_id(self, id: str) -> Optional[T]:
        """Get a single entity by ID."""
        pass
    
    @abstractmethod
    def get_all(self, filters: Optional[Dict[str, Any]] = None) -> List[T]:
        """Get all entities, optionally filtered."""
        pass
    
    @abstractmethod
    def create(self, data: Dict[str, Any]) -> T:
        """Create a new entity."""
        pass
    
    @abstractmethod
    def update(self, id: str, data: Dict[str, Any]) -> Optional[T]:
        """Update an existing entity."""
        pass
    
    @abstractmethod
    def delete(self, id: str) -> bool:
        """Delete an entity by ID."""
        pass
    
    @abstractmethod
    def exists(self, id: str) -> bool:
        """Check if an entity exists."""
        pass
