"""
Goals service for Save Sabi.

This module handles savings goal management:
- Goal progress tracking
- Automatic allocation of savings to goals
- Goal completion handling
"""

import logging
from decimal import Decimal
from typing import Optional, List, Dict, Any
from django.db import transaction as db_transaction
from django.db.models import Sum
from django.utils import timezone

from core.models import (
    Wallet, Goal, Transaction, GoalStatus,
    TransactionDirection
)
from core.exceptions import (
    GoalNotFoundError, InvalidTransactionError, InsufficientBalanceError
)

logger = logging.getLogger(__name__)


def track_goal_progress(goal: Goal) -> Dict[str, Any]:
    """
    Calculate and return current goal progress.
    
    Note: saved_amount is tracked separately, not derived from transactions.
    This allows for flexible goal tracking.
    
    Args:
        goal: The goal to track
    
    Returns:
        Dict with progress information
    """
    return {
        'id': str(goal.id),
        'name': goal.name,
        'target_amount': goal.target_amount,
        'saved_amount': goal.saved_amount,
        'remaining_amount': goal.remaining_amount,
        'progress_pct': goal.progress_percentage,
        'is_completed': goal.is_completed,
        'target_date': goal.target_date,
        'status': goal.status,
        'days_remaining': _days_until_target(goal)
    }


def _days_until_target(goal: Goal) -> Optional[int]:
    """
    Calculate days until target date.
    
    Args:
        goal: The goal to check
    
    Returns:
        Number of days until target, or None if no target date
    """
    if not goal.target_date:
        return None
    
    today = timezone.now().date()
    delta = goal.target_date - today
    return max(0, delta.days)


@db_transaction.atomic
def contribute_to_goal(
    goal: Goal,
    amount: Decimal,
    from_savings: bool = True
) -> Dict[str, Any]:
    """
    Make a contribution to a goal.
    
    This can either:
    - Transfer from wallet savings balance to goal
    - Or just record a contribution (for external funds)
    
    Args:
        goal: The goal to contribute to
        amount: Amount to contribute
        from_savings: Whether to deduct from wallet savings
    
    Returns:
        Updated goal progress
    
    Raises:
        InvalidTransactionError: If amount is invalid
        InsufficientBalanceError: If savings balance is insufficient
    """
    if amount <= 0:
        raise InvalidTransactionError(
            message="Contribution amount must be positive"
        )
    
    if goal.status != GoalStatus.ACTIVE:
        raise InvalidTransactionError(
            message="Cannot contribute to a non-active goal",
            details={'status': goal.status}
        )
    
    wallet = Wallet.objects.select_for_update().get(id=goal.wallet_id)
    goal = Goal.objects.select_for_update().get(id=goal.id)
    
    if from_savings:
        if wallet.balance_savings < amount:
            raise InsufficientBalanceError(
                message="Insufficient savings balance",
                details={
                    'required': str(amount),
                    'available': str(wallet.balance_savings)
                }
            )
        
        # Deduct from savings
        wallet.balance_savings -= amount
        wallet.save()
    
    # Add to goal
    goal.saved_amount += amount
    
    # Check if goal is completed
    if goal.saved_amount >= goal.target_amount:
        goal.status = GoalStatus.COMPLETED
        logger.info(f"Goal {goal.id} completed!")
    
    goal.save()
    
    logger.info(f"Contributed {amount} to goal {goal.id}")
    
    return track_goal_progress(goal)


@db_transaction.atomic
def allocate_savings_to_goals(wallet: Wallet, amount: Optional[Decimal] = None) -> List[Dict[str, Any]]:
    """
    Allocate savings proportionally across active goals.
    
    Goals with allocation_percentage > 0 receive their share.
    Remaining amount goes to goals by priority.
    
    Args:
        wallet: The wallet to allocate from
        amount: Amount to allocate (default: all unallocated savings)
    
    Returns:
        List of allocation results
    """
    # Get active goals with allocation
    goals = Goal.objects.filter(
        wallet=wallet,
        status=GoalStatus.ACTIVE
    ).order_by('-priority', 'target_date')
    
    if not goals.exists():
        return []
    
    # Calculate total allocation percentage
    total_allocation_pct = sum(g.allocation_percentage for g in goals)
    
    if total_allocation_pct > 100:
        logger.warning(f"Total allocation percentage exceeds 100% for wallet {wallet.id}")
        # Normalize
        for goal in goals:
            goal._normalized_pct = (goal.allocation_percentage / total_allocation_pct) * 100
    else:
        for goal in goals:
            goal._normalized_pct = goal.allocation_percentage
    
    # If no amount specified, don't auto-allocate
    if amount is None:
        return []
    
    allocations = []
    remaining = amount
    
    # First pass: allocate based on percentage
    for goal in goals:
        if goal._normalized_pct > 0 and remaining > 0:
            allocation = (amount * Decimal(goal._normalized_pct) / 100).quantize(Decimal('0.01'))
            allocation = min(allocation, remaining, goal.remaining_amount)
            
            if allocation > 0:
                result = contribute_to_goal(goal, allocation, from_savings=False)
                allocations.append({
                    'goal_id': str(goal.id),
                    'goal_name': goal.name,
                    'allocated': allocation,
                    'progress': result
                })
                remaining -= allocation
    
    return allocations


def get_goals_for_wallet(wallet: Wallet, status: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Get all goals for a wallet.
    
    Args:
        wallet: The wallet to get goals for
        status: Optional status filter
    
    Returns:
        List of goal progress dicts
    """
    goals = Goal.objects.filter(wallet=wallet)
    
    if status:
        goals = goals.filter(status=status)
    
    goals = goals.order_by('-priority', '-created_at')
    
    return [track_goal_progress(goal) for goal in goals]


def get_goal_by_id(goal_id: str, user) -> Goal:
    """
    Get a goal by ID, verifying ownership.
    
    Args:
        goal_id: UUID of the goal
        user: The authenticated user
    
    Returns:
        Goal object
    
    Raises:
        GoalNotFoundError: If goal not found or not owned by user
    """
    try:
        goal = Goal.objects.select_related('wallet').get(id=goal_id)
        if goal.wallet.owner != user:
            raise GoalNotFoundError(
                message="Goal not found",
                details={'goal_id': str(goal_id)}
            )
        return goal
    except Goal.DoesNotExist:
        raise GoalNotFoundError(
            message="Goal not found",
            details={'goal_id': str(goal_id)}
        )


@db_transaction.atomic
def update_goal_status(goal: Goal, new_status: str) -> Goal:
    """
    Update a goal's status.
    
    Args:
        goal: The goal to update
        new_status: The new status
    
    Returns:
        Updated goal
    """
    if goal.status == GoalStatus.COMPLETED and new_status != GoalStatus.COMPLETED:
        raise InvalidTransactionError(
            message="Cannot change status of a completed goal"
        )
    
    goal.status = new_status
    goal.save()
    
    logger.info(f"Goal {goal.id} status updated to {new_status}")
    
    return goal


@db_transaction.atomic
def withdraw_from_goal(goal: Goal, amount: Decimal) -> Dict[str, Any]:
    """
    Withdraw funds from a goal back to wallet savings.
    
    Args:
        goal: The goal to withdraw from
        amount: Amount to withdraw
    
    Returns:
        Updated goal progress
    
    Raises:
        InvalidTransactionError: If amount exceeds saved amount
    """
    if amount <= 0:
        raise InvalidTransactionError(
            message="Withdrawal amount must be positive"
        )
    
    if amount > goal.saved_amount:
        raise InvalidTransactionError(
            message="Cannot withdraw more than saved amount",
            details={
                'requested': str(amount),
                'available': str(goal.saved_amount)
            }
        )
    
    wallet = Wallet.objects.select_for_update().get(id=goal.wallet_id)
    goal = Goal.objects.select_for_update().get(id=goal.id)
    
    # Deduct from goal
    goal.saved_amount -= amount
    
    # If it was completed, may need to reactivate
    if goal.status == GoalStatus.COMPLETED and goal.saved_amount < goal.target_amount:
        goal.status = GoalStatus.ACTIVE
    
    goal.save()
    
    # Add back to wallet savings
    wallet.balance_savings += amount
    wallet.save()
    
    logger.info(f"Withdrew {amount} from goal {goal.id}")
    
    return track_goal_progress(goal)


def calculate_required_daily_savings(goal: Goal) -> Optional[Decimal]:
    """
    Calculate daily savings needed to reach goal by target date.
    
    Args:
        goal: The goal to calculate for
    
    Returns:
        Daily amount needed, or None if no target date
    """
    if not goal.target_date:
        return None
    
    days_remaining = _days_until_target(goal)
    if days_remaining is None or days_remaining <= 0:
        return None
    
    remaining_amount = goal.remaining_amount
    if remaining_amount <= 0:
        return Decimal('0.00')
    
    daily_amount = (remaining_amount / days_remaining).quantize(Decimal('0.01'))
    return daily_amount
