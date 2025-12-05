"""
Nudges service for Save Sabi.

This module handles budget rule evaluation and nudge generation:
- Rule evaluation against transactions
- Nudge creation and delivery
- Alert management
"""

import logging
from decimal import Decimal
from datetime import date, timedelta
from typing import Optional, List, Dict, Any
from django.db import transaction as db_transaction
from django.db.models import Sum
from django.utils import timezone

from core.models import (
    Wallet, Transaction, BudgetRule, Nudge,
    RuleType, RulePeriod, AlertType, DeliveryMethod,
    TransactionDirection
)
from core.exceptions import RuleNotFoundError

logger = logging.getLogger(__name__)


def get_period_start_date(period: str) -> date:
    """
    Calculate the start date for a period.
    
    Args:
        period: Period type ('daily', 'weekly', 'monthly')
    
    Returns:
        Start date for the period
    """
    today = timezone.now().date()
    
    if period == RulePeriod.DAILY:
        return today
    elif period == RulePeriod.WEEKLY:
        # Start of week (Monday)
        return today - timedelta(days=today.weekday())
    elif period == RulePeriod.MONTHLY:
        # Start of month
        return today.replace(day=1)
    else:
        return today


def calculate_period_spending(
    wallet: Wallet,
    period: str,
    category: Optional[str] = None
) -> Decimal:
    """
    Calculate total spending for a period, optionally filtered by category.
    
    Args:
        wallet: The wallet to check
        period: Period type
        category: Optional category filter
    
    Returns:
        Total spending in the period
    """
    start_date = get_period_start_date(period)
    start_datetime = timezone.make_aware(
        timezone.datetime.combine(start_date, timezone.datetime.min.time())
    )
    
    queryset = Transaction.objects.filter(
        wallet=wallet,
        direction=TransactionDirection.OUT,
        created_at__gte=start_datetime
    )
    
    if category:
        queryset = queryset.filter(category=category)
    
    total = queryset.aggregate(total=Sum('amount'))['total']
    return total or Decimal('0.00')


def evaluate_rule(rule: BudgetRule) -> Optional[Dict[str, Any]]:
    """
    Evaluate a single budget rule.
    
    Args:
        rule: The rule to evaluate
    
    Returns:
        Dict with evaluation result if triggered, None otherwise
    """
    if not rule.is_active:
        return None
    
    wallet = rule.wallet
    
    # Calculate current spending for the period
    if rule.rule_type == RuleType.CATEGORY_LIMIT:
        current_spending = calculate_period_spending(
            wallet, rule.period, rule.category
        )
    elif rule.rule_type in [RuleType.DAILY_LIMIT, RuleType.WEEKLY_LIMIT, RuleType.MONTHLY_LIMIT]:
        current_spending = calculate_period_spending(wallet, rule.period)
    elif rule.rule_type == RuleType.LOW_BALANCE:
        # Check spend balance
        if wallet.balance_spend <= rule.threshold_amount:
            return {
                'triggered': True,
                'rule': rule,
                'current_value': wallet.balance_spend,
                'threshold': rule.threshold_amount,
                'alert_type': AlertType.WARNING,
                'percentage': (wallet.balance_spend / rule.threshold_amount * 100) if rule.threshold_amount > 0 else Decimal('0')
            }
        return None
    elif rule.rule_type == RuleType.SAVINGS_MILESTONE:
        # Check if savings reached milestone
        if wallet.balance_savings >= rule.threshold_amount:
            # Only trigger once
            if rule.last_triggered_at:
                return None
            return {
                'triggered': True,
                'rule': rule,
                'current_value': wallet.balance_savings,
                'threshold': rule.threshold_amount,
                'alert_type': AlertType.CONGRATULATIONS,
                'percentage': Decimal('100')
            }
        return None
    else:
        return None
    
    # Check if threshold exceeded
    if current_spending >= rule.threshold_amount:
        percentage = (current_spending / rule.threshold_amount * 100) if rule.threshold_amount > 0 else Decimal('100')
        return {
            'triggered': True,
            'rule': rule,
            'current_value': current_spending,
            'threshold': rule.threshold_amount,
            'alert_type': AlertType.WARNING,
            'percentage': percentage
        }
    
    # Check if approaching threshold (80%)
    warning_threshold = rule.threshold_amount * Decimal('0.8')
    if current_spending >= warning_threshold:
        percentage = (current_spending / rule.threshold_amount * 100)
        return {
            'triggered': True,
            'rule': rule,
            'current_value': current_spending,
            'threshold': rule.threshold_amount,
            'alert_type': AlertType.WARNING,
            'percentage': percentage,
            'approaching': True
        }
    
    return None


def generate_nudge_message(rule: BudgetRule, evaluation: Dict[str, Any]) -> tuple:
    """
    Generate a nudge title and message based on evaluation.
    
    Args:
        rule: The triggered rule
        evaluation: Evaluation result dict
    
    Returns:
        Tuple of (title, message)
    """
    # Use custom message if set
    if rule.custom_message:
        return ("Budget Alert", rule.custom_message)
    
    current = evaluation['current_value']
    threshold = evaluation['threshold']
    percentage = evaluation.get('percentage', Decimal('100'))
    
    if rule.rule_type == RuleType.CATEGORY_LIMIT:
        category = rule.category or 'expenses'
        if evaluation.get('approaching'):
            title = f"Approaching {category.title()} Limit"
            message = f"You've spent {current} on {category} this {rule.period}. That's {percentage:.0f}% of your {threshold} limit. Consider slowing down."
        else:
            title = f"{category.title()} Budget Exceeded"
            message = f"You've exceeded your {rule.period} {category} budget! Spent {current} of {threshold} limit."
    
    elif rule.rule_type in [RuleType.DAILY_LIMIT, RuleType.WEEKLY_LIMIT, RuleType.MONTHLY_LIMIT]:
        if evaluation.get('approaching'):
            title = f"Approaching {rule.period.title()} Limit"
            message = f"You've spent {current} this {rule.period}. That's {percentage:.0f}% of your {threshold} limit."
        else:
            title = f"{rule.period.title()} Budget Exceeded"
            message = f"You've exceeded your {rule.period} spending limit! Spent {current} of {threshold}."
    
    elif rule.rule_type == RuleType.LOW_BALANCE:
        title = "Low Balance Warning"
        message = f"Your spend balance is low at {current}. Consider reducing expenses or adding funds."
    
    elif rule.rule_type == RuleType.SAVINGS_MILESTONE:
        title = "Savings Milestone Reached! 🎉"
        message = f"Congratulations! You've saved {current}! Keep up the great work on your savings journey."
    
    else:
        title = "Budget Alert"
        message = f"Budget rule triggered: {current} against threshold {threshold}"
    
    return (title, message)


@db_transaction.atomic
def create_nudge(
    rule: BudgetRule,
    alert_type: str,
    title: str,
    message: str,
    sent_via: str = DeliveryMethod.IN_APP,
    metadata: Optional[dict] = None
) -> Nudge:
    """
    Create a nudge record.
    
    Args:
        rule: The rule that triggered the nudge
        alert_type: Type of alert
        title: Nudge title
        message: Nudge message
        sent_via: Delivery method
        metadata: Additional metadata
    
    Returns:
        Created Nudge object
    """
    nudge = Nudge.objects.create(
        wallet=rule.wallet,
        rule=rule,
        alert_type=alert_type,
        title=title,
        message=message,
        sent_via=sent_via,
        metadata=metadata or {}
    )
    
    # Update rule's last triggered timestamp
    rule.last_triggered_at = timezone.now()
    rule.save(update_fields=['last_triggered_at'])
    
    logger.info(f"Created nudge {nudge.id} for rule {rule.id}")
    
    return nudge


def should_send_nudge(rule: BudgetRule) -> bool:
    """
    Check if a nudge should be sent (rate limiting).
    
    Prevents spam by limiting how often nudges are sent.
    
    Args:
        rule: The rule to check
    
    Returns:
        True if nudge should be sent
    """
    if not rule.last_triggered_at:
        return True
    
    # Rate limits based on period
    rate_limits = {
        RulePeriod.DAILY: timedelta(hours=4),
        RulePeriod.WEEKLY: timedelta(hours=12),
        RulePeriod.MONTHLY: timedelta(days=1),
    }
    
    min_interval = rate_limits.get(rule.period, timedelta(hours=4))
    time_since_last = timezone.now() - rule.last_triggered_at
    
    return time_since_last >= min_interval


@db_transaction.atomic
def evaluate_rules(wallet: Wallet) -> List[Nudge]:
    """
    Evaluate all active rules for a wallet and generate nudges.
    
    Args:
        wallet: The wallet to evaluate rules for
    
    Returns:
        List of created Nudge objects
    """
    rules = BudgetRule.objects.filter(wallet=wallet, is_active=True)
    nudges = []
    
    for rule in rules:
        try:
            evaluation = evaluate_rule(rule)
            
            if evaluation and evaluation.get('triggered'):
                # Check rate limiting
                if not should_send_nudge(rule):
                    logger.debug(f"Skipping nudge for rule {rule.id} due to rate limiting")
                    continue
                
                # Generate message
                title, message = generate_nudge_message(rule, evaluation)
                
                # Create nudge
                nudge = create_nudge(
                    rule=rule,
                    alert_type=evaluation['alert_type'],
                    title=title,
                    message=message,
                    metadata={
                        'current_value': str(evaluation['current_value']),
                        'threshold': str(evaluation['threshold']),
                        'percentage': str(evaluation.get('percentage', 100))
                    }
                )
                nudges.append(nudge)
        
        except Exception as e:
            logger.error(f"Error evaluating rule {rule.id}: {e}")
            continue
    
    return nudges


def evaluate_all_wallets() -> List[Nudge]:
    """
    Evaluate rules for all active wallets.
    
    Called periodically by Celery beat.
    
    Returns:
        List of all created nudges
    """
    wallets = Wallet.objects.filter(is_active=True)
    all_nudges = []
    
    for wallet in wallets:
        nudges = evaluate_rules(wallet)
        all_nudges.extend(nudges)
    
    logger.info(f"Evaluated rules for {wallets.count()} wallets, created {len(all_nudges)} nudges")
    
    return all_nudges


def get_nudges_for_wallet(
    wallet: Wallet,
    unread_only: bool = False,
    limit: int = 50
) -> List[Nudge]:
    """
    Get nudges for a wallet.
    
    Args:
        wallet: The wallet to get nudges for
        unread_only: Only return unread nudges
        limit: Maximum number to return
    
    Returns:
        List of Nudge objects
    """
    queryset = Nudge.objects.filter(wallet=wallet)
    
    if unread_only:
        queryset = queryset.filter(is_read=False)
    
    return list(queryset.order_by('-created_at')[:limit])


@db_transaction.atomic
def acknowledge_nudges(nudge_ids: List[str], user) -> List[str]:
    """
    Mark nudges as read.
    
    Args:
        nudge_ids: List of nudge UUIDs
        user: The authenticated user
    
    Returns:
        List of successfully acknowledged nudge IDs
    """
    acknowledged = []
    now = timezone.now()
    
    for nudge_id in nudge_ids:
        try:
            nudge = Nudge.objects.select_for_update().get(
                id=nudge_id,
                wallet__owner=user
            )
            
            if not nudge.is_read:
                nudge.is_read = True
                nudge.read_at = now
                nudge.save(update_fields=['is_read', 'read_at'])
            
            acknowledged.append(str(nudge.id))
        
        except Nudge.DoesNotExist:
            logger.warning(f"Nudge {nudge_id} not found or not owned by user")
            continue
    
    logger.info(f"Acknowledged {len(acknowledged)} nudges for user {user.id}")
    
    return acknowledged


def create_tip_nudge(wallet: Wallet, message: str, title: str = "Savings Tip") -> Nudge:
    """
    Create a tip nudge (not tied to a rule).
    
    Args:
        wallet: The wallet to create nudge for
        message: Tip message
        title: Tip title
    
    Returns:
        Created Nudge object
    """
    nudge = Nudge.objects.create(
        wallet=wallet,
        rule=None,
        alert_type=AlertType.TIP,
        title=title,
        message=message,
        sent_via=DeliveryMethod.IN_APP
    )
    
    logger.info(f"Created tip nudge {nudge.id}")
    
    return nudge


def cleanup_old_nudges(days: int = 90) -> int:
    """
    Delete old read nudges.
    
    Args:
        days: Delete nudges older than this many days
    
    Returns:
        Number of deleted nudges
    """
    cutoff = timezone.now() - timedelta(days=days)
    
    deleted_count, _ = Nudge.objects.filter(
        is_read=True,
        created_at__lt=cutoff
    ).delete()
    
    logger.info(f"Cleaned up {deleted_count} old nudges")
    
    return deleted_count
