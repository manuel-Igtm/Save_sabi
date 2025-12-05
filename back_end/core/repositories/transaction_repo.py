"""
Transaction repository for Save Sabi.

Provides data access for Transaction entities.
"""

from typing import Optional, List, Dict, Any
from datetime import date
from django.db.models import Q
from django.utils import timezone

from core.models import Transaction, Wallet, User, TransactionDirection
from .base import BaseRepository


class TransactionRepository(BaseRepository[Transaction]):
    """
    Repository for Transaction data access.
    """
    
    def get_by_id(self, id: str) -> Optional[Transaction]:
        """Get a transaction by ID."""
        try:
            return Transaction.objects.select_related('wallet').get(id=id)
        except Transaction.DoesNotExist:
            return None
    
    def get_by_id_for_user(self, id: str, user: User) -> Optional[Transaction]:
        """Get a transaction by ID, ensuring ownership."""
        try:
            return Transaction.objects.select_related('wallet').get(
                id=id,
                wallet__owner=user
            )
        except Transaction.DoesNotExist:
            return None
    
    def get_all(self, filters: Optional[Dict[str, Any]] = None) -> List[Transaction]:
        """Get all transactions, optionally filtered."""
        queryset = Transaction.objects.select_related('wallet')
        
        if filters:
            queryset = self._apply_filters(queryset, filters)
        
        return list(queryset.order_by('-created_at'))
    
    def _apply_filters(self, queryset, filters: Dict[str, Any]):
        """Apply filters to queryset."""
        if 'wallet' in filters:
            queryset = queryset.filter(wallet=filters['wallet'])
        if 'wallet_id' in filters:
            queryset = queryset.filter(wallet_id=filters['wallet_id'])
        if 'user' in filters:
            queryset = queryset.filter(wallet__owner=filters['user'])
        if 'category' in filters:
            queryset = queryset.filter(category=filters['category'])
        if 'direction' in filters:
            queryset = queryset.filter(direction=filters['direction'])
        if 'date_from' in filters:
            start_datetime = timezone.make_aware(
                timezone.datetime.combine(filters['date_from'], timezone.datetime.min.time())
            )
            queryset = queryset.filter(created_at__gte=start_datetime)
        if 'date_to' in filters:
            end_datetime = timezone.make_aware(
                timezone.datetime.combine(filters['date_to'], timezone.datetime.max.time())
            )
            queryset = queryset.filter(created_at__lte=end_datetime)
        
        return queryset
    
    def get_for_wallet(
        self,
        wallet: Wallet,
        category: Optional[str] = None,
        direction: Optional[str] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        limit: int = 100
    ) -> List[Transaction]:
        """Get transactions for a wallet with optional filters."""
        filters = {'wallet': wallet}
        
        if category:
            filters['category'] = category
        if direction:
            filters['direction'] = direction
        if date_from:
            filters['date_from'] = date_from
        if date_to:
            filters['date_to'] = date_to
        
        queryset = Transaction.objects.filter(wallet=wallet)
        queryset = self._apply_filters(queryset, filters)
        
        return list(queryset.order_by('-created_at')[:limit])
    
    def get_for_user(
        self,
        user: User,
        wallet_id: Optional[str] = None,
        category: Optional[str] = None,
        direction: Optional[str] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        limit: int = 100
    ) -> List[Transaction]:
        """Get transactions for a user with optional filters."""
        filters = {'user': user}
        
        if wallet_id:
            filters['wallet_id'] = wallet_id
        if category:
            filters['category'] = category
        if direction:
            filters['direction'] = direction
        if date_from:
            filters['date_from'] = date_from
        if date_to:
            filters['date_to'] = date_to
        
        queryset = Transaction.objects.filter(wallet__owner=user)
        queryset = self._apply_filters(queryset, filters)
        
        return list(queryset.order_by('-created_at')[:limit])
    
    def create(self, data: Dict[str, Any]) -> Transaction:
        """Create a new transaction."""
        return Transaction.objects.create(**data)
    
    def update(self, id: str, data: Dict[str, Any]) -> Optional[Transaction]:
        """
        Update a transaction.
        
        Note: Transactions are generally immutable after creation.
        Only metadata updates are typically allowed.
        """
        try:
            transaction = Transaction.objects.get(id=id)
            
            # Only allow updating metadata
            if 'metadata' in data:
                transaction.metadata = data['metadata']
                transaction.save()
            
            return transaction
        except Transaction.DoesNotExist:
            return None
    
    def delete(self, id: str) -> bool:
        """
        Delete a transaction.
        
        Note: In practice, transactions should not be deleted.
        Consider soft delete or archiving instead.
        """
        try:
            transaction = Transaction.objects.get(id=id)
            transaction.delete()
            return True
        except Transaction.DoesNotExist:
            return False
    
    def exists(self, id: str) -> bool:
        """Check if a transaction exists."""
        return Transaction.objects.filter(id=id).exists()
    
    def count_for_wallet(self, wallet: Wallet) -> int:
        """Count transactions for a wallet."""
        return Transaction.objects.filter(wallet=wallet).count()


# Singleton instance
transaction_repository = TransactionRepository()
