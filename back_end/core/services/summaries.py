"""
Summaries service for Save Sabi.

This module handles transaction aggregation and analytics:
- Period summaries (7d, 30d, custom)
- Category breakdowns
- Savings rate calculations
- Streak tracking
"""

import logging
from decimal import Decimal
from datetime import date, timedelta
from typing import Optional, List, Dict, Any
from django.db.models import Sum, Count, Q
from django.db.models.functions import TruncDate
from django.utils import timezone

from core.models import (
    Wallet, Transaction, Goal, SavingsStreak,
    TransactionDirection, GoalStatus
)
from core.exceptions import WalletNotFoundError

logger = logging.getLogger(__name__)


def get_date_range(range_type: str, date_from: Optional[date] = None, date_to: Optional[date] = None) -> tuple:
    """
    Calculate date range based on range type.
    
    Args:
        range_type: One of '7d', '30d', '90d', '365d', 'custom'
        date_from: Start date for custom range
        date_to: End date for custom range
    
    Returns:
        Tuple of (start_date, end_date)
    """
    today = timezone.now().date()
    
    range_mapping = {
        '7d': 7,
        '30d': 30,
        '90d': 90,
        '365d': 365,
    }
    
    if range_type in range_mapping:
        days = range_mapping[range_type]
        return (today - timedelta(days=days), today)
    elif range_type == 'custom':
        if date_from and date_to:
            return (date_from, date_to)
        return (today - timedelta(days=30), today)
    else:
        return (today - timedelta(days=30), today)


def aggregate_transactions(
    wallet: Wallet,
    start_date: date,
    end_date: date
) -> Dict[str, Any]:
    """
    Aggregate transactions for a wallet within a date range.
    
    Args:
        wallet: The wallet to aggregate
        start_date: Start of period (inclusive)
        end_date: End of period (inclusive)
    
    Returns:
        Dict with aggregated totals
    """
    # Convert dates to datetime for comparison
    start_datetime = timezone.make_aware(
        timezone.datetime.combine(start_date, timezone.datetime.min.time())
    )
    end_datetime = timezone.make_aware(
        timezone.datetime.combine(end_date, timezone.datetime.max.time())
    )
    
    # Get transactions in range
    transactions = Transaction.objects.filter(
        wallet=wallet,
        created_at__gte=start_datetime,
        created_at__lte=end_datetime
    )
    
    # Aggregate by direction
    aggregates = transactions.aggregate(
        total_in=Sum('amount', filter=Q(direction=TransactionDirection.IN)) or Decimal('0.00'),
        total_out=Sum('amount', filter=Q(direction=TransactionDirection.OUT)) or Decimal('0.00'),
        total_saved=Sum('saved_portion') or Decimal('0.00'),
        total_round_up=Sum('round_up_amount') or Decimal('0.00'),
        transaction_count=Count('id')
    )
    
    # Calculate spend (out transactions minus round-up which went to savings)
    total_spent = (aggregates['total_out'] or Decimal('0.00'))
    
    return {
        'total_in': aggregates['total_in'] or Decimal('0.00'),
        'total_out': aggregates['total_out'] or Decimal('0.00'),
        'total_saved': aggregates['total_saved'] or Decimal('0.00'),
        'total_spent': total_spent,
        'total_round_up': aggregates['total_round_up'] or Decimal('0.00'),
        'transaction_count': aggregates['transaction_count'] or 0
    }


def compute_savings_rate(total_in: Decimal, total_saved: Decimal) -> Decimal:
    """
    Calculate the savings rate as a percentage.
    
    Args:
        total_in: Total income
        total_saved: Total saved amount
    
    Returns:
        Savings rate as percentage (0-100)
    """
    if total_in <= 0:
        return Decimal('0.00')
    
    rate = (total_saved / total_in) * 100
    return rate.quantize(Decimal('0.01'))


def get_category_breakdown(
    wallet: Wallet,
    start_date: date,
    end_date: date
) -> List[Dict[str, Any]]:
    """
    Get spending breakdown by category.
    
    Args:
        wallet: The wallet to analyze
        start_date: Start of period
        end_date: End of period
    
    Returns:
        List of category breakdowns with totals and percentages
    """
    start_datetime = timezone.make_aware(
        timezone.datetime.combine(start_date, timezone.datetime.min.time())
    )
    end_datetime = timezone.make_aware(
        timezone.datetime.combine(end_date, timezone.datetime.max.time())
    )
    
    # Get expense transactions grouped by category
    category_totals = Transaction.objects.filter(
        wallet=wallet,
        direction=TransactionDirection.OUT,
        created_at__gte=start_datetime,
        created_at__lte=end_datetime
    ).values('category').annotate(
        total=Sum('amount'),
        count=Count('id')
    ).order_by('-total')
    
    # Calculate percentages
    grand_total = sum(item['total'] for item in category_totals)
    
    breakdown = []
    for item in category_totals:
        percentage = (item['total'] / grand_total * 100) if grand_total > 0 else Decimal('0.00')
        breakdown.append({
            'category': item['category'],
            'total': item['total'],
            'percentage': percentage.quantize(Decimal('0.01')),
            'count': item['count']
        })
    
    return breakdown


def get_goal_progress(wallet: Wallet) -> List[Dict[str, Any]]:
    """
    Get progress for all active goals.
    
    Args:
        wallet: The wallet to check goals for
    
    Returns:
        List of goal progress dicts
    """
    goals = Goal.objects.filter(
        wallet=wallet,
        status=GoalStatus.ACTIVE
    ).order_by('-priority', 'target_date')
    
    progress_list = []
    for goal in goals:
        progress_list.append({
            'id': str(goal.id),
            'name': goal.name,
            'target_amount': goal.target_amount,
            'saved_amount': goal.saved_amount,
            'progress_pct': goal.progress_percentage,
            'target_date': goal.target_date
        })
    
    return progress_list


def get_streak_days(wallet: Wallet) -> int:
    """
    Get the current savings streak for a wallet.
    
    Args:
        wallet: The wallet to check
    
    Returns:
        Current streak in days
    """
    try:
        streak = SavingsStreak.objects.get(wallet=wallet)
        return streak.current_streak
    except SavingsStreak.DoesNotExist:
        return 0


def streak_counter(wallet: Wallet) -> Dict[str, int]:
    """
    Get comprehensive streak information.
    
    Args:
        wallet: The wallet to check
    
    Returns:
        Dict with current_streak, longest_streak, last_savings_date
    """
    try:
        streak = SavingsStreak.objects.get(wallet=wallet)
        return {
            'current_streak': streak.current_streak,
            'longest_streak': streak.longest_streak,
            'last_savings_date': streak.last_savings_date
        }
    except SavingsStreak.DoesNotExist:
        return {
            'current_streak': 0,
            'longest_streak': 0,
            'last_savings_date': None
        }


def compute_summary(
    wallet: Wallet,
    range_type: str = '30d',
    date_from: Optional[date] = None,
    date_to: Optional[date] = None
) -> Dict[str, Any]:
    """
    Compute a comprehensive summary for a wallet.
    
    This is the main summary function that combines all metrics.
    
    Args:
        wallet: The wallet to summarize
        range_type: Period type ('7d', '30d', '90d', '365d', 'custom')
        date_from: Start date for custom range
        date_to: End date for custom range
    
    Returns:
        Comprehensive summary dict
    """
    # Get date range
    start_date, end_date = get_date_range(range_type, date_from, date_to)
    
    # Aggregate transactions
    aggregates = aggregate_transactions(wallet, start_date, end_date)
    
    # Calculate savings rate
    savings_rate = compute_savings_rate(
        aggregates['total_in'],
        aggregates['total_saved']
    )
    
    # Get category breakdown
    categories = get_category_breakdown(wallet, start_date, end_date)
    
    # Get goal progress
    goal_progress = get_goal_progress(wallet)
    
    # Get streak
    streak_days = get_streak_days(wallet)
    
    return {
        'period': range_type,
        'date_from': start_date,
        'date_to': end_date,
        'total_in': aggregates['total_in'],
        'total_out': aggregates['total_out'],
        'total_saved': aggregates['total_saved'],
        'total_spent': aggregates['total_spent'],
        'savings_rate': savings_rate,
        'categories': categories,
        'goal_progress': goal_progress,
        'streak_days': streak_days,
        'transaction_count': aggregates['transaction_count']
    }


def compute_30day_summary(wallet: Wallet) -> Dict[str, Any]:
    """
    Convenience function for 30-day summary.
    
    Args:
        wallet: The wallet to summarize
    
    Returns:
        30-day summary dict
    """
    return compute_summary(wallet, range_type='30d')


def get_daily_breakdown(
    wallet: Wallet,
    start_date: date,
    end_date: date
) -> List[Dict[str, Any]]:
    """
    Get daily transaction breakdown.
    
    Args:
        wallet: The wallet to analyze
        start_date: Start of period
        end_date: End of period
    
    Returns:
        List of daily totals
    """
    start_datetime = timezone.make_aware(
        timezone.datetime.combine(start_date, timezone.datetime.min.time())
    )
    end_datetime = timezone.make_aware(
        timezone.datetime.combine(end_date, timezone.datetime.max.time())
    )
    
    daily_totals = Transaction.objects.filter(
        wallet=wallet,
        created_at__gte=start_datetime,
        created_at__lte=end_datetime
    ).annotate(
        day=TruncDate('created_at')
    ).values('day').annotate(
        total_in=Sum('amount', filter=Q(direction=TransactionDirection.IN)) or Decimal('0.00'),
        total_out=Sum('amount', filter=Q(direction=TransactionDirection.OUT)) or Decimal('0.00'),
        total_saved=Sum('saved_portion') or Decimal('0.00'),
        count=Count('id')
    ).order_by('day')
    
    return list(daily_totals)


def get_summary_for_user(
    user,
    range_type: str = '30d',
    wallet_id: Optional[str] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None
) -> Dict[str, Any]:
    """
    Get summary for a user, optionally for a specific wallet.
    
    Args:
        user: The authenticated user
        range_type: Period type
        wallet_id: Optional specific wallet ID
        date_from: Start date for custom range
        date_to: End date for custom range
    
    Returns:
        Summary dict
    
    Raises:
        WalletNotFoundError: If wallet not found
    """
    if wallet_id:
        try:
            wallet = Wallet.objects.get(id=wallet_id, owner=user)
        except Wallet.DoesNotExist:
            raise WalletNotFoundError(
                message="Wallet not found",
                details={'wallet_id': str(wallet_id)}
            )
    else:
        # Use primary wallet
        try:
            wallet = Wallet.objects.get(owner=user, is_primary=True, is_active=True)
        except Wallet.DoesNotExist:
            raise WalletNotFoundError(
                message="No primary wallet found"
            )
    
    return compute_summary(wallet, range_type, date_from, date_to)
