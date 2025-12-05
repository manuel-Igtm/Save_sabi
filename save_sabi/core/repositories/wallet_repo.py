"""
Wallet repository for Save Sabi.

Provides data access for Wallet entities with support for
future Firestore migration.
"""

from typing import Optional, List, Dict, Any
from decimal import Decimal
from django.db import transaction as db_transaction

from core.models import Wallet, User
from core.exceptions import WalletNotFoundError
from .base import BaseRepository


class WalletRepository(BaseRepository[Wallet]):
    """
    Repository for Wallet data access.
    
    Currently implements PostgreSQL backend via Django ORM.
    Can be swapped for Firestore implementation.
    """
    
    def get_by_id(self, id: str) -> Optional[Wallet]:
        """Get a wallet by ID."""
        try:
            return Wallet.objects.get(id=id)
        except Wallet.DoesNotExist:
            return None
    
    def get_by_id_for_user(self, id: str, user: User) -> Optional[Wallet]:
        """Get a wallet by ID, ensuring ownership."""
        try:
            return Wallet.objects.get(id=id, owner=user)
        except Wallet.DoesNotExist:
            return None
    
    def get_all(self, filters: Optional[Dict[str, Any]] = None) -> List[Wallet]:
        """Get all wallets, optionally filtered."""
        queryset = Wallet.objects.all()
        
        if filters:
            if 'owner' in filters:
                queryset = queryset.filter(owner=filters['owner'])
            if 'is_active' in filters:
                queryset = queryset.filter(is_active=filters['is_active'])
            if 'currency' in filters:
                queryset = queryset.filter(currency=filters['currency'])
        
        return list(queryset)
    
    def get_for_user(self, user: User, active_only: bool = True) -> List[Wallet]:
        """Get all wallets for a user."""
        queryset = Wallet.objects.filter(owner=user)
        if active_only:
            queryset = queryset.filter(is_active=True)
        return list(queryset.order_by('-is_primary', '-created_at'))
    
    def get_primary_for_user(self, user: User) -> Optional[Wallet]:
        """Get the primary wallet for a user."""
        try:
            return Wallet.objects.get(owner=user, is_primary=True, is_active=True)
        except Wallet.DoesNotExist:
            return None
    
    def create(self, data: Dict[str, Any]) -> Wallet:
        """Create a new wallet."""
        return Wallet.objects.create(**data)
    
    @db_transaction.atomic
    def update(self, id: str, data: Dict[str, Any]) -> Optional[Wallet]:
        """Update an existing wallet."""
        try:
            wallet = Wallet.objects.select_for_update().get(id=id)
            
            for key, value in data.items():
                if hasattr(wallet, key):
                    setattr(wallet, key, value)
            
            wallet.save()
            return wallet
        except Wallet.DoesNotExist:
            return None
    
    def delete(self, id: str) -> bool:
        """Delete a wallet by ID (soft delete by deactivating)."""
        try:
            wallet = Wallet.objects.get(id=id)
            wallet.is_active = False
            wallet.save()
            return True
        except Wallet.DoesNotExist:
            return False
    
    def exists(self, id: str) -> bool:
        """Check if a wallet exists."""
        return Wallet.objects.filter(id=id).exists()
    
    @db_transaction.atomic
    def update_balances(
        self,
        wallet_id: str,
        savings_delta: Decimal = Decimal('0'),
        spend_delta: Decimal = Decimal('0')
    ) -> Wallet:
        """
        Atomically update wallet balances.
        
        Args:
            wallet_id: UUID of the wallet
            savings_delta: Amount to add to savings (can be negative)
            spend_delta: Amount to add to spend (can be negative)
        
        Returns:
            Updated wallet
        
        Raises:
            WalletNotFoundError: If wallet not found
        """
        try:
            wallet = Wallet.objects.select_for_update().get(id=wallet_id)
        except Wallet.DoesNotExist:
            raise WalletNotFoundError(
                message="Wallet not found",
                details={'wallet_id': str(wallet_id)}
            )
        
        wallet.balance_savings += savings_delta
        wallet.balance_spend += spend_delta
        wallet.save()
        
        return wallet
    
    @db_transaction.atomic
    def set_primary(self, wallet_id: str, user: User) -> Wallet:
        """
        Set a wallet as primary for a user.
        
        Unsets any existing primary wallet.
        """
        # Unset current primary
        Wallet.objects.filter(owner=user, is_primary=True).update(is_primary=False)
        
        # Set new primary
        try:
            wallet = Wallet.objects.get(id=wallet_id, owner=user)
            wallet.is_primary = True
            wallet.save()
            return wallet
        except Wallet.DoesNotExist:
            raise WalletNotFoundError(
                message="Wallet not found",
                details={'wallet_id': str(wallet_id)}
            )


# Singleton instance for use across the application
wallet_repository = WalletRepository()
