"""
Model tests for Save Sabi.

Tests the data models and their methods.
"""

import pytest
from decimal import Decimal
from datetime import date, timedelta
from django.utils import timezone

from core.models import (
    User, Wallet, Transaction, Goal, BudgetRule, Nudge, SavingsStreak,
    TransactionCategory, TransactionDirection, GoalStatus,
    RuleType, RulePeriod, AlertType
)
from core.tests.factories import (
    UserFactory, WalletFactory, TransactionFactory, GoalFactory,
    BudgetRuleFactory, NudgeFactory
)


@pytest.mark.django_db
class TestUserModel:
    """Tests for the User model."""
    
    def test_create_user(self):
        """Test user creation."""
        user = UserFactory()
        assert user.id is not None
        assert user.email
        assert user.preferred_currency == 'KES'
    
    def test_user_str(self):
        """Test user string representation."""
        user = UserFactory(email='test@example.com')
        assert str(user) == 'test@example.com'


@pytest.mark.django_db
class TestWalletModel:
    """Tests for the Wallet model."""
    
    def test_create_wallet(self):
        """Test wallet creation."""
        wallet = WalletFactory()
        assert wallet.id is not None
        assert wallet.owner is not None
        assert wallet.currency == 'KES'
    
    def test_wallet_default_split(self):
        """Test default 20/80 split ratio."""
        wallet = WalletFactory(savings_ratio=20)
        assert wallet.savings_ratio == 20
        assert wallet.spend_ratio == 80
        assert wallet.get_split_ratio() == (20, 80)
    
    def test_wallet_custom_split(self):
        """Test custom split ratio."""
        wallet = WalletFactory(savings_ratio=30)
        assert wallet.savings_ratio == 30
        assert wallet.spend_ratio == 70
        assert wallet.get_split_ratio() == (30, 70)
    
    def test_wallet_total_balance(self):
        """Test total balance calculation."""
        wallet = WalletFactory(
            balance_savings=Decimal('1000.00'),
            balance_spend=Decimal('4000.00')
        )
        assert wallet.total_balance == Decimal('5000.00')
    
    def test_wallet_str(self):
        """Test wallet string representation."""
        user = UserFactory(username='testuser')
        wallet = WalletFactory(owner=user, name='Primary Wallet', currency='KES')
        assert "testuser" in str(wallet)
        assert "Primary Wallet" in str(wallet)


@pytest.mark.django_db
class TestTransactionModel:
    """Tests for the Transaction model."""
    
    def test_create_transaction(self):
        """Test transaction creation."""
        txn = TransactionFactory()
        assert txn.id is not None
        assert txn.wallet is not None
        assert txn.amount == Decimal('100.00')
    
    def test_transaction_metadata(self):
        """Test transaction metadata access."""
        txn = TransactionFactory(
            metadata={'notes': 'Test note', 'merchant': 'Test Shop'}
        )
        assert txn.notes == 'Test note'
        assert txn.merchant == 'Test Shop'
    
    def test_transaction_str(self):
        """Test transaction string representation."""
        txn = TransactionFactory(
            direction=TransactionDirection.IN,
            amount=Decimal('500.00'),
            currency='KES',
            category=TransactionCategory.SALARY
        )
        assert 'IN' in str(txn)
        assert '500' in str(txn)


@pytest.mark.django_db
class TestGoalModel:
    """Tests for the Goal model."""
    
    def test_create_goal(self):
        """Test goal creation."""
        goal = GoalFactory()
        assert goal.id is not None
        assert goal.status == GoalStatus.ACTIVE
    
    def test_goal_progress_percentage(self):
        """Test progress percentage calculation."""
        goal = GoalFactory(
            target_amount=Decimal('10000.00'),
            saved_amount=Decimal('2500.00')
        )
        assert goal.progress_percentage == Decimal('25.00')
    
    def test_goal_progress_percentage_zero_target(self):
        """Test progress with zero target."""
        goal = GoalFactory(target_amount=Decimal('0.00'))
        assert goal.progress_percentage == Decimal('0.00')
    
    def test_goal_progress_over_100(self):
        """Test progress capped at 100%."""
        goal = GoalFactory(
            target_amount=Decimal('1000.00'),
            saved_amount=Decimal('1500.00')
        )
        assert goal.progress_percentage == Decimal('100.00')
    
    def test_goal_remaining_amount(self):
        """Test remaining amount calculation."""
        goal = GoalFactory(
            target_amount=Decimal('10000.00'),
            saved_amount=Decimal('3000.00')
        )
        assert goal.remaining_amount == Decimal('7000.00')
    
    def test_goal_is_completed(self):
        """Test goal completion check."""
        incomplete = GoalFactory(
            target_amount=Decimal('10000.00'),
            saved_amount=Decimal('5000.00')
        )
        complete = GoalFactory(
            target_amount=Decimal('10000.00'),
            saved_amount=Decimal('10000.00')
        )
        
        assert not incomplete.is_completed
        assert complete.is_completed


@pytest.mark.django_db
class TestBudgetRuleModel:
    """Tests for the BudgetRule model."""
    
    def test_create_rule(self):
        """Test budget rule creation."""
        rule = BudgetRuleFactory()
        assert rule.id is not None
        assert rule.is_active
    
    def test_rule_str(self):
        """Test rule string representation."""
        rule = BudgetRuleFactory(
            rule_type=RuleType.CATEGORY_LIMIT,
            category=TransactionCategory.FOOD,
            threshold_amount=Decimal('5000.00')
        )
        assert 'category_limit' in str(rule)
        assert 'food' in str(rule)


@pytest.mark.django_db
class TestNudgeModel:
    """Tests for the Nudge model."""
    
    def test_create_nudge(self):
        """Test nudge creation."""
        nudge = NudgeFactory()
        assert nudge.id is not None
        assert not nudge.is_read
    
    def test_nudge_str(self):
        """Test nudge string representation."""
        nudge = NudgeFactory(
            alert_type=AlertType.WARNING,
            title='Test Alert'
        )
        assert 'warning' in str(nudge)
        assert 'Test Alert' in str(nudge)
