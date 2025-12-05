"""
Core models for Save Sabi.

This module defines the data models for the savings platform:
- User: Extended Django user with profile fields
- Wallet: User's savings and spending wallets
- Transaction: Individual financial transactions with 20/80 split
- Goal: Savings goals with progress tracking
- BudgetRule: Rules for triggering nudges
- Nudge: Alert/notification records
"""

import uuid
from decimal import Decimal
from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models


class User(AbstractUser):
    """
    Extended User model for Save Sabi.
    Extends Django's AbstractUser with additional profile fields.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    preferred_currency = models.CharField(
        max_length=3,
        default='KES',
        choices=[(c, c) for c in settings.SAVE_SABI.get('SUPPORTED_CURRENCIES', ['KES', 'USD'])]
    )
    email_verified = models.BooleanField(default=False)
    phone_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def __str__(self):
        return self.email or self.username


class Wallet(models.Model):
    """
    Wallet model representing a user's savings and spending balances.
    
    Each user can have multiple wallets (for different currencies or purposes).
    The wallet tracks:
    - balance_savings: Amount saved (20% of income by default)
    - balance_spend: Amount available for spending (80% of income by default)
    - custom_split_ratio: Configurable savings/spend ratio
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='wallets'
    )
    name = models.CharField(max_length=100, default='Primary Wallet')
    currency = models.CharField(
        max_length=3,
        default='KES',
        choices=[(c, c) for c in settings.SAVE_SABI.get('SUPPORTED_CURRENCIES', ['KES', 'USD'])]
    )
    balance_savings = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    balance_spend = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    # Split ratio: (savings_percentage, spend_percentage) stored as savings percentage
    # E.g., 20 means 20% savings, 80% spend
    savings_ratio = models.PositiveIntegerField(
        default=20,
        validators=[MinValueValidator(1), MaxValueValidator(99)],
        help_text="Percentage of income to save (1-99)"
    )
    is_active = models.BooleanField(default=True)
    is_primary = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'wallets'
        verbose_name = 'Wallet'
        verbose_name_plural = 'Wallets'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['owner', 'is_active']),
            models.Index(fields=['owner', 'is_primary']),
        ]

    def __str__(self):
        return f"{self.owner.username}'s {self.name} ({self.currency})"

    @property
    def spend_ratio(self) -> int:
        """Calculate spend ratio from savings ratio."""
        return 100 - self.savings_ratio

    @property
    def total_balance(self) -> Decimal:
        """Total balance across savings and spend."""
        return self.balance_savings + self.balance_spend

    def get_split_ratio(self) -> tuple[int, int]:
        """Return (savings_percentage, spend_percentage) tuple."""
        return (self.savings_ratio, self.spend_ratio)


class TransactionCategory(models.TextChoices):
    """Enumeration of transaction categories."""
    FOOD = 'food', 'Food'
    TRANSPORT = 'transport', 'Transport'
    HEALTH = 'health', 'Health'
    EDUCATION = 'education', 'Education'
    ENTERTAINMENT = 'entertainment', 'Entertainment'
    UTILITIES = 'utilities', 'Utilities'
    SHOPPING = 'shopping', 'Shopping'
    SALARY = 'salary', 'Salary'
    GIFT = 'gift', 'Gift'
    OTHER = 'other', 'Other'


class TransactionDirection(models.TextChoices):
    """Direction of transaction: income or expense."""
    IN = 'in', 'Income'
    OUT = 'out', 'Expense'


class Transaction(models.Model):
    """
    Transaction model for tracking individual financial transactions.
    
    Each transaction automatically applies the 20/80 split based on the
    wallet's configured ratio. Round-up savings can also be applied.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    wallet = models.ForeignKey(
        Wallet,
        on_delete=models.CASCADE,
        related_name='transactions'
    )
    amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    currency = models.CharField(max_length=3)
    category = models.CharField(
        max_length=20,
        choices=TransactionCategory.choices,
        default=TransactionCategory.OTHER
    )
    direction = models.CharField(
        max_length=3,
        choices=TransactionDirection.choices
    )
    # Auto-calculated portions based on wallet's split ratio
    saved_portion = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00')
    )
    spend_portion = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00')
    )
    # Round-up savings feature
    round_up_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00')
    )
    # Flexible metadata field for additional info
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional transaction data: notes, merchant, receipt_url, etc."
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'transactions'
        verbose_name = 'Transaction'
        verbose_name_plural = 'Transactions'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['wallet', 'created_at']),
            models.Index(fields=['wallet', 'category']),
            models.Index(fields=['wallet', 'direction']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{self.direction.upper()} {self.amount} {self.currency} - {self.category}"

    @property
    def notes(self) -> str:
        """Get notes from metadata."""
        return self.metadata.get('notes', '')

    @property
    def merchant(self) -> str:
        """Get merchant from metadata."""
        return self.metadata.get('merchant', '')


class GoalStatus(models.TextChoices):
    """Status of a savings goal."""
    ACTIVE = 'active', 'Active'
    COMPLETED = 'completed', 'Completed'
    PAUSED = 'paused', 'Paused'
    CANCELLED = 'cancelled', 'Cancelled'


class Goal(models.Model):
    """
    Savings Goal model for tracking progress toward financial targets.
    
    Goals can be linked to a wallet and track progress automatically
    as transactions are recorded.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    wallet = models.ForeignKey(
        Wallet,
        on_delete=models.CASCADE,
        related_name='goals'
    )
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    target_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    target_date = models.DateField(null=True, blank=True)
    saved_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    status = models.CharField(
        max_length=20,
        choices=GoalStatus.choices,
        default=GoalStatus.ACTIVE
    )
    # Priority for allocation (higher = more priority)
    priority = models.PositiveIntegerField(default=1)
    # Optional: percentage of savings to allocate to this goal
    allocation_percentage = models.PositiveIntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Percentage of savings to allocate to this goal (0 = manual)"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'goals'
        verbose_name = 'Goal'
        verbose_name_plural = 'Goals'
        ordering = ['-priority', '-created_at']
        indexes = [
            models.Index(fields=['wallet', 'status']),
            models.Index(fields=['target_date']),
        ]

    def __str__(self):
        return f"{self.name} - {self.saved_amount}/{self.target_amount}"

    @property
    def progress_percentage(self) -> Decimal:
        """Calculate progress as a percentage."""
        if self.target_amount <= 0:
            return Decimal('0.00')
        progress = (self.saved_amount / self.target_amount) * 100
        return min(progress, Decimal('100.00'))

    @property
    def remaining_amount(self) -> Decimal:
        """Calculate remaining amount to reach goal."""
        return max(self.target_amount - self.saved_amount, Decimal('0.00'))

    @property
    def is_completed(self) -> bool:
        """Check if goal has been reached."""
        return self.saved_amount >= self.target_amount


class RuleType(models.TextChoices):
    """Types of budget rules."""
    CATEGORY_LIMIT = 'category_limit', 'Category Limit'
    DAILY_LIMIT = 'daily_limit', 'Daily Limit'
    WEEKLY_LIMIT = 'weekly_limit', 'Weekly Limit'
    MONTHLY_LIMIT = 'monthly_limit', 'Monthly Limit'
    LOW_BALANCE = 'low_balance', 'Low Balance Alert'
    SAVINGS_MILESTONE = 'savings_milestone', 'Savings Milestone'


class RulePeriod(models.TextChoices):
    """Time periods for budget rules."""
    DAILY = 'daily', 'Daily'
    WEEKLY = 'weekly', 'Weekly'
    MONTHLY = 'monthly', 'Monthly'


class BudgetRule(models.Model):
    """
    Budget Rule model for defining spending limits and triggers.
    
    Rules can be based on categories, time periods, or balance thresholds.
    When triggered, they generate Nudge alerts.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    wallet = models.ForeignKey(
        Wallet,
        on_delete=models.CASCADE,
        related_name='budget_rules'
    )
    rule_type = models.CharField(
        max_length=20,
        choices=RuleType.choices
    )
    # Category for category-specific rules (nullable)
    category = models.CharField(
        max_length=20,
        choices=TransactionCategory.choices,
        null=True,
        blank=True
    )
    threshold_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    period = models.CharField(
        max_length=10,
        choices=RulePeriod.choices,
        default=RulePeriod.MONTHLY
    )
    # Custom message for the nudge (optional)
    custom_message = models.TextField(blank=True)
    last_triggered_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'budget_rules'
        verbose_name = 'Budget Rule'
        verbose_name_plural = 'Budget Rules'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['wallet', 'is_active']),
            models.Index(fields=['rule_type']),
        ]

    def __str__(self):
        category_str = f" ({self.category})" if self.category else ""
        return f"{self.rule_type}{category_str} - {self.threshold_amount}"


class AlertType(models.TextChoices):
    """Types of nudge alerts."""
    WARNING = 'warning', 'Warning'
    CONGRATULATIONS = 'congratulations', 'Congratulations'
    TIP = 'tip', 'Tip'
    REMINDER = 'reminder', 'Reminder'
    MILESTONE = 'milestone', 'Milestone'


class DeliveryMethod(models.TextChoices):
    """Delivery methods for nudges."""
    EMAIL = 'email', 'Email'
    PUSH = 'push', 'Push Notification'
    SMS = 'sms', 'SMS'
    IN_APP = 'in_app', 'In-App'


class Nudge(models.Model):
    """
    Nudge model for storing alerts and notifications.
    
    Nudges are generated by budget rules or system events and
    delivered via various channels (email, push, SMS).
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    wallet = models.ForeignKey(
        Wallet,
        on_delete=models.CASCADE,
        related_name='nudges'
    )
    rule = models.ForeignKey(
        BudgetRule,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='nudges'
    )
    alert_type = models.CharField(
        max_length=20,
        choices=AlertType.choices
    )
    title = models.CharField(max_length=200, default='')
    message = models.TextField()
    sent_via = models.CharField(
        max_length=10,
        choices=DeliveryMethod.choices,
        default=DeliveryMethod.IN_APP
    )
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    # Additional data for the nudge
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'nudges'
        verbose_name = 'Nudge'
        verbose_name_plural = 'Nudges'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['wallet', 'is_read']),
            models.Index(fields=['wallet', 'created_at']),
            models.Index(fields=['alert_type']),
        ]

    def __str__(self):
        return f"{self.alert_type}: {self.title or self.message[:50]}"


class SavingsStreak(models.Model):
    """
    Model to track consecutive days of positive savings.
    
    This is a denormalized table for efficient streak calculations.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    wallet = models.OneToOneField(
        Wallet,
        on_delete=models.CASCADE,
        related_name='streak'
    )
    current_streak = models.PositiveIntegerField(default=0)
    longest_streak = models.PositiveIntegerField(default=0)
    last_savings_date = models.DateField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'savings_streaks'
        verbose_name = 'Savings Streak'
        verbose_name_plural = 'Savings Streaks'

    def __str__(self):
        return f"{self.wallet.owner.username}'s streak: {self.current_streak} days"
