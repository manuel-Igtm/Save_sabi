"""
Ledger service for Save Sabi.

This module handles the core transaction logic including:
- 20/80 split calculation
- Round-up savings
- Balance updates
- Transaction recording

The ledger service ensures atomic operations and data integrity.
"""

import logging
from decimal import Decimal, ROUND_UP, ROUND_DOWN
from typing import Optional, Tuple
from django.db import transaction as db_transaction
from django.utils import timezone

from core.models import (
    Wallet, Transaction, TransactionDirection, SavingsStreak
)
from core.exceptions import (
    InsufficientBalanceError, InvalidTransactionError, WalletNotFoundError
)

logger = logging.getLogger(__name__)


def split_transaction(
    wallet: Wallet,
    amount: Decimal,
    split_ratio: Optional[Tuple[int, int]] = None
) -> Tuple[Decimal, Decimal]:
    """
    Calculate the savings and spend portions based on split ratio.
    
    The Hara Hachi Bu principle: Save a portion of every income.
    Default is 20% savings, 80% spend.
    
    Args:
        wallet: The wallet to apply the split to
        amount: The amount to split
        split_ratio: Optional tuple of (savings_pct, spend_pct). 
                    If not provided, uses wallet's configured ratio.
    
    Returns:
        Tuple of (saved_amount, spend_amount)
    
    Example:
        >>> split_transaction(wallet, Decimal('1000'))
        (Decimal('200.00'), Decimal('800.00'))
    """
    if split_ratio is None:
        split_ratio = wallet.get_split_ratio()
    
    savings_pct, spend_pct = split_ratio
    
    # Calculate portions using precise decimal arithmetic
    # We round savings down and spend up to ensure we never overspend
    saved_amount = (amount * Decimal(savings_pct) / Decimal(100)).quantize(
        Decimal('0.01'), rounding=ROUND_DOWN
    )
    spend_amount = amount - saved_amount  # Remainder goes to spend
    
    logger.debug(
        f"Split {amount}: saved={saved_amount} ({savings_pct}%), "
        f"spend={spend_amount} ({spend_pct}%)"
    )
    
    return saved_amount, spend_amount


def apply_round_up(spend_amount: Decimal, round_to: int = 1) -> Decimal:
    """
    Calculate round-up savings to the nearest unit.
    
    Round-up savings helps users save small amounts unconsciously.
    
    Args:
        spend_amount: The spend portion of a transaction
        round_to: The unit to round up to (default: 1)
    
    Returns:
        The round-up amount (what gets added to savings)
    
    Example:
        >>> apply_round_up(Decimal('85.30'))
        Decimal('0.70')  # Rounds to 86, saves the 0.70 difference
    """
    if spend_amount <= 0:
        return Decimal('0.00')
    
    round_to_decimal = Decimal(str(round_to))
    
    # Calculate the rounded amount
    remainder = spend_amount % round_to_decimal
    
    if remainder == 0:
        # Already at a round number
        return Decimal('0.00')
    
    round_up_amount = round_to_decimal - remainder
    
    # Quantize to 2 decimal places
    round_up_amount = round_up_amount.quantize(Decimal('0.01'), rounding=ROUND_UP)
    
    logger.debug(f"Round-up: {spend_amount} -> {round_up_amount} extra savings")
    
    return round_up_amount


@db_transaction.atomic
def record_transaction(
    wallet: Wallet,
    amount: Decimal,
    category: str,
    direction: str,
    notes: Optional[str] = None,
    merchant: Optional[str] = None,
    round_up: bool = False,
    metadata: Optional[dict] = None
) -> Transaction:
    """
    Record a transaction with automatic 20/80 split and balance updates.
    
    This is the main entry point for recording financial transactions.
    It handles:
    1. Input validation
    2. Split calculation (for income)
    3. Round-up savings (for expenses, if enabled)
    4. Atomic balance updates
    5. Streak tracking
    
    Args:
        wallet: The wallet to record the transaction in
        amount: Transaction amount (positive decimal)
        category: Transaction category
        direction: 'in' for income, 'out' for expense
        notes: Optional transaction notes
        merchant: Optional merchant name
        round_up: Whether to apply round-up savings (expenses only)
        metadata: Additional metadata dict
    
    Returns:
        The created Transaction object
    
    Raises:
        InvalidTransactionError: If inputs are invalid
        InsufficientBalanceError: If wallet has insufficient balance for expense
    """
    # Validate inputs
    if amount <= 0:
        raise InvalidTransactionError(
            message="Transaction amount must be positive",
            details={'amount': str(amount)}
        )
    
    if direction not in [TransactionDirection.IN, TransactionDirection.OUT]:
        raise InvalidTransactionError(
            message="Invalid transaction direction",
            details={'direction': direction}
        )
    
    # Lock the wallet row for atomic update
    wallet = Wallet.objects.select_for_update().get(id=wallet.id)
    
    # Build metadata
    txn_metadata = metadata or {}
    if notes:
        txn_metadata['notes'] = notes
    if merchant:
        txn_metadata['merchant'] = merchant
    
    # Calculate portions based on direction
    if direction == TransactionDirection.IN:
        # Income: Apply 20/80 split
        saved_portion, spend_portion = split_transaction(wallet, amount)
        round_up_amount = Decimal('0.00')
        
        # Update balances (add to both)
        wallet.balance_savings += saved_portion
        wallet.balance_spend += spend_portion
        
        logger.info(
            f"Income recorded: {amount} -> savings={saved_portion}, spend={spend_portion}"
        )
        
    else:  # direction == TransactionDirection.OUT
        # Expense: Deduct from spend balance
        saved_portion = Decimal('0.00')
        spend_portion = amount
        
        # Apply round-up if enabled
        if round_up:
            round_up_amount = apply_round_up(amount)
        else:
            round_up_amount = Decimal('0.00')
        
        # Total deduction from spend balance
        total_deduction = spend_portion + round_up_amount
        
        # Check sufficient balance
        if wallet.balance_spend < total_deduction:
            raise InsufficientBalanceError(
                message="Insufficient spend balance for this transaction",
                details={
                    'required': str(total_deduction),
                    'available': str(wallet.balance_spend)
                }
            )
        
        # Update balances
        wallet.balance_spend -= total_deduction
        wallet.balance_savings += round_up_amount  # Round-up goes to savings
        
        logger.info(
            f"Expense recorded: {amount} deducted, round_up={round_up_amount} saved"
        )
    
    # Save wallet
    wallet.save()
    
    # Create transaction record
    transaction = Transaction.objects.create(
        wallet=wallet,
        amount=amount,
        currency=wallet.currency,
        category=category,
        direction=direction,
        saved_portion=saved_portion + round_up_amount,  # Total saved
        spend_portion=spend_portion if direction == TransactionDirection.OUT else spend_portion,
        round_up_amount=round_up_amount,
        metadata=txn_metadata
    )
    
    # Update savings streak for income transactions
    if direction == TransactionDirection.IN and saved_portion > 0:
        _update_savings_streak(wallet)
    
    logger.info(f"Transaction {transaction.id} created for wallet {wallet.id}")
    
    return transaction


def _update_savings_streak(wallet: Wallet) -> None:
    """
    Update the savings streak for a wallet.
    
    Called after a positive savings transaction.
    """
    today = timezone.now().date()
    
    streak, _ = SavingsStreak.objects.get_or_create(wallet=wallet)
    
    if streak.last_savings_date is None:
        # First savings ever
        streak.current_streak = 1
        streak.longest_streak = 1
        streak.last_savings_date = today
    elif streak.last_savings_date == today:
        # Already saved today, no change
        pass
    elif streak.last_savings_date == today - timezone.timedelta(days=1):
        # Consecutive day
        streak.current_streak += 1
        streak.longest_streak = max(streak.longest_streak, streak.current_streak)
        streak.last_savings_date = today
    else:
        # Streak broken, start new
        streak.current_streak = 1
        streak.last_savings_date = today
    
    streak.save()


def get_wallet_balance(wallet_id: str, user) -> dict:
    """
    Get the current balance of a wallet.
    
    Args:
        wallet_id: UUID of the wallet
        user: The authenticated user
    
    Returns:
        Dict with balance information
    
    Raises:
        WalletNotFoundError: If wallet not found or not owned by user
    """
    try:
        wallet = Wallet.objects.get(id=wallet_id, owner=user)
    except Wallet.DoesNotExist:
        raise WalletNotFoundError(
            message="Wallet not found",
            details={'wallet_id': str(wallet_id)}
        )
    
    return {
        'wallet_id': str(wallet.id),
        'wallet_name': wallet.name,
        'currency': wallet.currency,
        'balance_savings': wallet.balance_savings,
        'balance_spend': wallet.balance_spend,
        'total_balance': wallet.total_balance,
        'savings_ratio': wallet.savings_ratio,
        'spend_ratio': wallet.spend_ratio,
    }


@db_transaction.atomic
def transfer_to_savings(
    wallet: Wallet,
    amount: Decimal
) -> Transaction:
    """
    Transfer amount from spend balance to savings.
    
    Allows users to manually boost their savings.
    
    Args:
        wallet: The wallet to transfer within
        amount: Amount to transfer
    
    Returns:
        Transaction record for the transfer
    
    Raises:
        InsufficientBalanceError: If spend balance is insufficient
    """
    if amount <= 0:
        raise InvalidTransactionError(
            message="Transfer amount must be positive"
        )
    
    wallet = Wallet.objects.select_for_update().get(id=wallet.id)
    
    if wallet.balance_spend < amount:
        raise InsufficientBalanceError(
            message="Insufficient spend balance for transfer",
            details={
                'required': str(amount),
                'available': str(wallet.balance_spend)
            }
        )
    
    # Transfer
    wallet.balance_spend -= amount
    wallet.balance_savings += amount
    wallet.save()
    
    # Record as internal transfer
    transaction = Transaction.objects.create(
        wallet=wallet,
        amount=amount,
        currency=wallet.currency,
        category='other',
        direction=TransactionDirection.IN,
        saved_portion=amount,
        spend_portion=Decimal('0.00'),
        round_up_amount=Decimal('0.00'),
        metadata={'type': 'internal_transfer', 'notes': 'Manual transfer to savings'}
    )
    
    logger.info(f"Transferred {amount} to savings for wallet {wallet.id}")
    
    return transaction
