"""
Service tests for Save Sabi.

Tests the business logic in the service layer.
"""

import pytest
from decimal import Decimal
from datetime import date, timedelta
from django.utils import timezone

from core.models import (
    Wallet, Transaction, Goal, BudgetRule, Nudge, SavingsStreak,
    TransactionCategory, TransactionDirection, GoalStatus,
    RuleType, RulePeriod
)
from core.services import ledger, summaries, goals, nudges
from core.exceptions import InsufficientBalanceError, InvalidTransactionError
from core.tests.factories import (
    UserFactory, WalletFactory, TransactionFactory, GoalFactory,
    BudgetRuleFactory, ExpenseTransactionFactory, IncomeTransactionFactory
)


@pytest.mark.django_db
class TestLedgerService:
    """Tests for the ledger service."""
    
    def test_split_transaction_default_ratio(self):
        """Test 20/80 split with default ratio."""
        wallet = WalletFactory(savings_ratio=20)
        
        saved, spend = ledger.split_transaction(wallet, Decimal('1000.00'))
        
        assert saved == Decimal('200.00')
        assert spend == Decimal('800.00')
    
    def test_split_transaction_custom_ratio(self):
        """Test split with custom ratio."""
        wallet = WalletFactory(savings_ratio=30)
        
        saved, spend = ledger.split_transaction(wallet, Decimal('1000.00'))
        
        assert saved == Decimal('300.00')
        assert spend == Decimal('700.00')
    
    def test_split_transaction_explicit_ratio(self):
        """Test split with explicit ratio override."""
        wallet = WalletFactory(savings_ratio=20)
        
        saved, spend = ledger.split_transaction(
            wallet, Decimal('1000.00'), split_ratio=(50, 50)
        )
        
        assert saved == Decimal('500.00')
        assert spend == Decimal('500.00')
    
    def test_apply_round_up(self):
        """Test round-up calculation."""
        round_up = ledger.apply_round_up(Decimal('85.30'))
        assert round_up == Decimal('0.70')
        
        round_up = ledger.apply_round_up(Decimal('85.00'))
        assert round_up == Decimal('0.00')
        
        round_up = ledger.apply_round_up(Decimal('99.99'))
        assert round_up == Decimal('0.01')
    
    def test_record_income_transaction(self):
        """Test recording income with automatic split."""
        wallet = WalletFactory(
            balance_savings=Decimal('1000.00'),
            balance_spend=Decimal('5000.00'),
            savings_ratio=20
        )
        
        txn = ledger.record_transaction(
            wallet=wallet,
            amount=Decimal('1000.00'),
            category=TransactionCategory.SALARY,
            direction=TransactionDirection.IN
        )
        
        wallet.refresh_from_db()
        
        assert txn.saved_portion == Decimal('200.00')
        assert txn.spend_portion == Decimal('800.00')
        assert wallet.balance_savings == Decimal('1200.00')
        assert wallet.balance_spend == Decimal('5800.00')
    
    def test_record_expense_transaction(self):
        """Test recording expense."""
        wallet = WalletFactory(
            balance_savings=Decimal('1000.00'),
            balance_spend=Decimal('5000.00')
        )
        
        txn = ledger.record_transaction(
            wallet=wallet,
            amount=Decimal('200.00'),
            category=TransactionCategory.FOOD,
            direction=TransactionDirection.OUT
        )
        
        wallet.refresh_from_db()
        
        assert txn.spend_portion == Decimal('200.00')
        assert wallet.balance_spend == Decimal('4800.00')
        assert wallet.balance_savings == Decimal('1000.00')  # Unchanged
    
    def test_record_expense_with_round_up(self):
        """Test expense with round-up savings."""
        wallet = WalletFactory(
            balance_savings=Decimal('1000.00'),
            balance_spend=Decimal('5000.00')
        )
        
        txn = ledger.record_transaction(
            wallet=wallet,
            amount=Decimal('85.30'),
            category=TransactionCategory.FOOD,
            direction=TransactionDirection.OUT,
            round_up=True
        )
        
        wallet.refresh_from_db()
        
        assert txn.round_up_amount == Decimal('0.70')
        # Spend deducted: 85.30 + 0.70 = 86.00
        assert wallet.balance_spend == Decimal('4914.00')
        # Savings increased by round-up
        assert wallet.balance_savings == Decimal('1000.70')
    
    def test_record_expense_insufficient_balance(self):
        """Test expense fails with insufficient balance."""
        wallet = WalletFactory(balance_spend=Decimal('50.00'))
        
        with pytest.raises(InsufficientBalanceError):
            ledger.record_transaction(
                wallet=wallet,
                amount=Decimal('100.00'),
                category=TransactionCategory.FOOD,
                direction=TransactionDirection.OUT
            )
    
    def test_record_transaction_invalid_amount(self):
        """Test transaction fails with invalid amount."""
        wallet = WalletFactory()
        
        with pytest.raises(InvalidTransactionError):
            ledger.record_transaction(
                wallet=wallet,
                amount=Decimal('-100.00'),
                category=TransactionCategory.FOOD,
                direction=TransactionDirection.OUT
            )
    
    def test_transfer_to_savings(self):
        """Test manual transfer to savings."""
        wallet = WalletFactory(
            balance_savings=Decimal('1000.00'),
            balance_spend=Decimal('5000.00')
        )
        
        txn = ledger.transfer_to_savings(wallet, Decimal('500.00'))
        
        wallet.refresh_from_db()
        
        assert txn is not None
        assert wallet.balance_savings == Decimal('1500.00')
        assert wallet.balance_spend == Decimal('4500.00')


@pytest.mark.django_db
class TestSummariesService:
    """Tests for the summaries service."""
    
    def test_aggregate_transactions(self):
        """Test transaction aggregation."""
        wallet = WalletFactory()
        
        # Create some transactions
        IncomeTransactionFactory(
            wallet=wallet,
            amount=Decimal('1000.00'),
            saved_portion=Decimal('200.00'),
            spend_portion=Decimal('800.00')
        )
        ExpenseTransactionFactory(
            wallet=wallet,
            amount=Decimal('500.00'),
            saved_portion=Decimal('0.00'),
            spend_portion=Decimal('500.00')
        )
        
        today = timezone.now().date()
        agg = summaries.aggregate_transactions(
            wallet,
            today - timedelta(days=30),
            today
        )
        
        assert agg['total_in'] == Decimal('1000.00')
        assert agg['total_out'] == Decimal('500.00')
        assert agg['transaction_count'] == 2
    
    def test_compute_savings_rate(self):
        """Test savings rate calculation."""
        rate = summaries.compute_savings_rate(
            Decimal('10000.00'),  # total in
            Decimal('2000.00')   # total saved
        )
        
        assert rate == Decimal('20.00')
    
    def test_compute_savings_rate_zero_income(self):
        """Test savings rate with zero income."""
        rate = summaries.compute_savings_rate(
            Decimal('0.00'),
            Decimal('100.00')
        )
        
        assert rate == Decimal('0.00')
    
    def test_get_category_breakdown(self):
        """Test category breakdown."""
        wallet = WalletFactory()
        
        ExpenseTransactionFactory(
            wallet=wallet,
            category=TransactionCategory.FOOD,
            amount=Decimal('300.00')
        )
        ExpenseTransactionFactory(
            wallet=wallet,
            category=TransactionCategory.TRANSPORT,
            amount=Decimal('200.00')
        )
        
        today = timezone.now().date()
        breakdown = summaries.get_category_breakdown(
            wallet,
            today - timedelta(days=30),
            today
        )
        
        assert len(breakdown) == 2
        food = next(c for c in breakdown if c['category'] == 'food')
        assert food['total'] == Decimal('300.00')
        assert food['percentage'] == Decimal('60.00')
    
    def test_compute_30day_summary(self):
        """Test complete 30-day summary."""
        wallet = WalletFactory()
        
        # Create a transaction
        IncomeTransactionFactory(
            wallet=wallet,
            amount=Decimal('5000.00'),
            saved_portion=Decimal('1000.00')
        )
        
        summary = summaries.compute_30day_summary(wallet)
        
        assert summary['period'] == '30d'
        assert summary['total_in'] == Decimal('5000.00')
        assert 'categories' in summary
        assert 'goal_progress' in summary


@pytest.mark.django_db
class TestGoalsService:
    """Tests for the goals service."""
    
    def test_track_goal_progress(self):
        """Test goal progress tracking."""
        goal = GoalFactory(
            target_amount=Decimal('10000.00'),
            saved_amount=Decimal('2500.00')
        )
        
        progress = goals.track_goal_progress(goal)
        
        assert progress['progress_pct'] == Decimal('25.00')
        assert progress['remaining_amount'] == Decimal('7500.00')
        assert not progress['is_completed']
    
    def test_contribute_to_goal(self):
        """Test contributing to a goal."""
        wallet = WalletFactory(balance_savings=Decimal('5000.00'))
        goal = GoalFactory(
            wallet=wallet,
            target_amount=Decimal('10000.00'),
            saved_amount=Decimal('1000.00')
        )
        
        result = goals.contribute_to_goal(goal, Decimal('500.00'))
        
        wallet.refresh_from_db()
        goal.refresh_from_db()
        
        assert goal.saved_amount == Decimal('1500.00')
        assert wallet.balance_savings == Decimal('4500.00')
        assert result['progress_pct'] == Decimal('15.00')
    
    def test_contribute_to_goal_completion(self):
        """Test goal completion on contribution."""
        wallet = WalletFactory(balance_savings=Decimal('5000.00'))
        goal = GoalFactory(
            wallet=wallet,
            target_amount=Decimal('1000.00'),
            saved_amount=Decimal('900.00')
        )
        
        result = goals.contribute_to_goal(goal, Decimal('100.00'))
        
        goal.refresh_from_db()
        
        assert goal.status == GoalStatus.COMPLETED
        assert result['is_completed']
    
    def test_contribute_insufficient_savings(self):
        """Test contribution fails with insufficient savings."""
        wallet = WalletFactory(balance_savings=Decimal('50.00'))
        goal = GoalFactory(wallet=wallet)
        
        with pytest.raises(InsufficientBalanceError):
            goals.contribute_to_goal(goal, Decimal('100.00'))
    
    def test_withdraw_from_goal(self):
        """Test withdrawing from a goal."""
        wallet = WalletFactory(balance_savings=Decimal('1000.00'))
        goal = GoalFactory(
            wallet=wallet,
            target_amount=Decimal('10000.00'),
            saved_amount=Decimal('5000.00')
        )
        
        result = goals.withdraw_from_goal(goal, Decimal('1000.00'))
        
        wallet.refresh_from_db()
        goal.refresh_from_db()
        
        assert goal.saved_amount == Decimal('4000.00')
        assert wallet.balance_savings == Decimal('2000.00')


@pytest.mark.django_db
class TestNudgesService:
    """Tests for the nudges service."""
    
    def test_calculate_period_spending(self):
        """Test period spending calculation."""
        wallet = WalletFactory()
        
        ExpenseTransactionFactory(
            wallet=wallet,
            category=TransactionCategory.FOOD,
            amount=Decimal('500.00')
        )
        ExpenseTransactionFactory(
            wallet=wallet,
            category=TransactionCategory.FOOD,
            amount=Decimal('300.00')
        )
        
        total = nudges.calculate_period_spending(
            wallet,
            RulePeriod.MONTHLY,
            TransactionCategory.FOOD
        )
        
        assert total == Decimal('800.00')
    
    def test_evaluate_rule_not_triggered(self):
        """Test rule evaluation when not triggered."""
        wallet = WalletFactory()
        rule = BudgetRuleFactory(
            wallet=wallet,
            rule_type=RuleType.CATEGORY_LIMIT,
            category=TransactionCategory.FOOD,
            threshold_amount=Decimal('5000.00')
        )
        
        # Small expense
        ExpenseTransactionFactory(
            wallet=wallet,
            category=TransactionCategory.FOOD,
            amount=Decimal('100.00')
        )
        
        result = nudges.evaluate_rule(rule)
        
        assert result is None
    
    def test_evaluate_rule_triggered(self):
        """Test rule evaluation when triggered."""
        wallet = WalletFactory()
        rule = BudgetRuleFactory(
            wallet=wallet,
            rule_type=RuleType.CATEGORY_LIMIT,
            category=TransactionCategory.FOOD,
            threshold_amount=Decimal('500.00')
        )
        
        # Expense exceeding threshold
        ExpenseTransactionFactory(
            wallet=wallet,
            category=TransactionCategory.FOOD,
            amount=Decimal('600.00')
        )
        
        result = nudges.evaluate_rule(rule)
        
        assert result is not None
        assert result['triggered']
    
    def test_evaluate_rules_creates_nudges(self):
        """Test evaluating all rules creates nudges."""
        wallet = WalletFactory()
        BudgetRuleFactory(
            wallet=wallet,
            rule_type=RuleType.CATEGORY_LIMIT,
            category=TransactionCategory.FOOD,
            threshold_amount=Decimal('500.00')
        )
        
        ExpenseTransactionFactory(
            wallet=wallet,
            category=TransactionCategory.FOOD,
            amount=Decimal('600.00')
        )
        
        created_nudges = nudges.evaluate_rules(wallet)
        
        assert len(created_nudges) >= 1
        assert Nudge.objects.filter(wallet=wallet).exists()
    
    def test_acknowledge_nudges(self):
        """Test acknowledging nudges."""
        user = UserFactory()
        wallet = WalletFactory(owner=user)
        nudge = Nudge.objects.create(
            wallet=wallet,
            rule=None,
            alert_type='warning',
            title='Test',
            message='Test message'
        )
        
        acknowledged = nudges.acknowledge_nudges([str(nudge.id)], user)
        
        nudge.refresh_from_db()
        
        assert str(nudge.id) in acknowledged
        assert nudge.is_read
        assert nudge.read_at is not None
