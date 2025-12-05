"""
Factory Boy fixtures for Save Sabi tests.

Provides factories for creating test data for all models.
"""

import factory
from factory.django import DjangoModelFactory
from django.contrib.auth import get_user_model
from decimal import Decimal
from datetime import date, timedelta

from core.models import (
    Wallet, Transaction, Goal, BudgetRule, Nudge, SavingsStreak,
    TransactionCategory, TransactionDirection, GoalStatus,
    RuleType, RulePeriod, AlertType, DeliveryMethod
)

User = get_user_model()


class UserFactory(DjangoModelFactory):
    """Factory for creating test users."""
    
    class Meta:
        model = User
        skip_postgeneration_save = True
    
    username = factory.Sequence(lambda n: f'user{n}')
    email = factory.LazyAttribute(lambda obj: f'{obj.username}@example.com')
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    phone_number = factory.Faker('phone_number')
    preferred_currency = 'KES'
    is_active = True
    
    @factory.post_generation
    def password(self, create, extracted, **kwargs):
        password = extracted or 'testpass123'
        self.set_password(password)
        if create:
            self.save()


class WalletFactory(DjangoModelFactory):
    """Factory for creating test wallets."""
    
    class Meta:
        model = Wallet
    
    owner = factory.SubFactory(UserFactory)
    name = factory.Sequence(lambda n: f'Wallet {n}')
    currency = 'KES'
    balance_savings = Decimal('1000.00')
    balance_spend = Decimal('5000.00')
    savings_ratio = 20
    is_active = True
    is_primary = True


class TransactionFactory(DjangoModelFactory):
    """Factory for creating test transactions."""
    
    class Meta:
        model = Transaction
    
    wallet = factory.SubFactory(WalletFactory)
    amount = Decimal('100.00')
    currency = factory.LazyAttribute(lambda obj: obj.wallet.currency)
    category = TransactionCategory.OTHER
    direction = TransactionDirection.IN
    saved_portion = Decimal('20.00')
    spend_portion = Decimal('80.00')
    round_up_amount = Decimal('0.00')
    metadata = factory.LazyFunction(dict)


class IncomeTransactionFactory(TransactionFactory):
    """Factory for income transactions."""
    direction = TransactionDirection.IN


class ExpenseTransactionFactory(TransactionFactory):
    """Factory for expense transactions."""
    direction = TransactionDirection.OUT
    category = TransactionCategory.FOOD
    saved_portion = Decimal('0.00')
    spend_portion = Decimal('100.00')


class GoalFactory(DjangoModelFactory):
    """Factory for creating test goals."""
    
    class Meta:
        model = Goal
    
    wallet = factory.SubFactory(WalletFactory)
    name = factory.Sequence(lambda n: f'Goal {n}')
    description = factory.Faker('sentence')
    target_amount = Decimal('10000.00')
    target_date = factory.LazyFunction(lambda: date.today() + timedelta(days=365))
    saved_amount = Decimal('0.00')
    status = GoalStatus.ACTIVE
    priority = 1
    allocation_percentage = 0


class BudgetRuleFactory(DjangoModelFactory):
    """Factory for creating test budget rules."""
    
    class Meta:
        model = BudgetRule
    
    wallet = factory.SubFactory(WalletFactory)
    rule_type = RuleType.CATEGORY_LIMIT
    category = TransactionCategory.FOOD
    threshold_amount = Decimal('5000.00')
    period = RulePeriod.MONTHLY
    custom_message = ''
    is_active = True


class DailyLimitRuleFactory(BudgetRuleFactory):
    """Factory for daily limit rules."""
    rule_type = RuleType.DAILY_LIMIT
    category = None
    period = RulePeriod.DAILY
    threshold_amount = Decimal('1000.00')


class NudgeFactory(DjangoModelFactory):
    """Factory for creating test nudges."""
    
    class Meta:
        model = Nudge
    
    wallet = factory.SubFactory(WalletFactory)
    rule = factory.SubFactory(BudgetRuleFactory, wallet=factory.SelfAttribute('..wallet'))
    alert_type = AlertType.WARNING
    title = factory.Faker('sentence', nb_words=4)
    message = factory.Faker('paragraph')
    sent_via = DeliveryMethod.IN_APP
    is_read = False
    metadata = factory.LazyFunction(dict)


class SavingsStreakFactory(DjangoModelFactory):
    """Factory for creating test savings streaks."""
    
    class Meta:
        model = SavingsStreak
    
    wallet = factory.SubFactory(WalletFactory)
    current_streak = 0
    longest_streak = 0
    last_savings_date = None
