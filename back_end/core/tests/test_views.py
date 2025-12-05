"""
API View tests for Save Sabi.

Tests the REST API endpoints.
"""

import pytest
from decimal import Decimal
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token
from django.urls import reverse

from core.models import (
    Wallet, Transaction, Goal, BudgetRule, Nudge,
    TransactionCategory, TransactionDirection, GoalStatus,
    RuleType, RulePeriod
)
from core.tests.factories import (
    UserFactory, WalletFactory, TransactionFactory, GoalFactory,
    BudgetRuleFactory, NudgeFactory
)


@pytest.fixture
def api_client():
    """Create an API client."""
    return APIClient()


@pytest.fixture
def authenticated_client(api_client):
    """Create an authenticated API client."""
    user = UserFactory()
    token, _ = Token.objects.get_or_create(user=user)
    api_client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
    return api_client, user


@pytest.mark.django_db
class TestAuthEndpoints:
    """Tests for authentication endpoints."""
    
    def test_register(self, api_client):
        """Test user registration."""
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'securepass123',
            'password_confirm': 'securepass123',
            'first_name': 'New',
            'last_name': 'User'
        }
        
        response = api_client.post('/api/v1/auth/register/', data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert 'token' in response.data
        assert 'user' in response.data
    
    def test_register_password_mismatch(self, api_client):
        """Test registration with mismatched passwords."""
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'securepass123',
            'password_confirm': 'differentpass',
        }
        
        response = api_client.post('/api/v1/auth/register/', data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_login(self, api_client):
        """Test user login."""
        user = UserFactory()
        
        data = {
            'username': user.username,
            'password': 'testpass123'
        }
        
        response = api_client.post('/api/v1/auth/login/', data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert 'token' in response.data
    
    def test_login_invalid_credentials(self, api_client):
        """Test login with invalid credentials."""
        data = {
            'username': 'nonexistent',
            'password': 'wrongpass'
        }
        
        response = api_client.post('/api/v1/auth/login/', data, format='json')
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_profile(self, authenticated_client):
        """Test getting user profile."""
        client, user = authenticated_client
        
        response = client.get('/api/v1/auth/profile/')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['username'] == user.username


@pytest.mark.django_db
class TestWalletEndpoints:
    """Tests for wallet endpoints."""
    
    def test_list_wallets(self, authenticated_client):
        """Test listing user's wallets."""
        client, user = authenticated_client
        # User already has a primary wallet from signal
        
        response = client.get('/api/v1/wallets/')
        
        assert response.status_code == status.HTTP_200_OK
        assert 'results' in response.data
    
    def test_create_wallet(self, authenticated_client):
        """Test creating a new wallet."""
        client, user = authenticated_client
        
        data = {
            'name': 'Vacation Fund',
            'currency': 'USD',
            'savings_ratio': 30
        }
        
        response = client.post('/api/v1/wallets/', data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['name'] == 'Vacation Fund'
        assert response.data['savings_ratio'] == 30
    
    def test_wallet_detail(self, authenticated_client):
        """Test getting wallet details."""
        client, user = authenticated_client
        wallet = Wallet.objects.get(owner=user, is_primary=True)
        
        response = client.get(f'/api/v1/wallets/{wallet.id}/')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == str(wallet.id)
    
    def test_update_wallet(self, authenticated_client):
        """Test updating wallet settings."""
        client, user = authenticated_client
        wallet = Wallet.objects.get(owner=user, is_primary=True)
        
        data = {
            'name': 'Updated Name',
            'savings_ratio': 25
        }
        
        response = client.patch(f'/api/v1/wallets/{wallet.id}/', data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == 'Updated Name'
        assert response.data['savings_ratio'] == 25
    
    def test_transfer_to_savings(self, authenticated_client):
        """Test manual transfer to savings."""
        client, user = authenticated_client
        wallet = Wallet.objects.get(owner=user, is_primary=True)
        wallet.balance_spend = Decimal('1000.00')
        wallet.save()
        
        data = {'amount': '100.00'}
        
        response = client.post(
            f'/api/v1/wallets/{wallet.id}/transfer_to_savings/',
            data,
            format='json'
        )
        
        assert response.status_code == status.HTTP_200_OK
        wallet.refresh_from_db()
        assert wallet.balance_savings == Decimal('100.00')


@pytest.mark.django_db
class TestTransactionEndpoints:
    """Tests for transaction endpoints."""
    
    def test_create_income_transaction(self, authenticated_client):
        """Test creating an income transaction with auto-split."""
        client, user = authenticated_client
        wallet = Wallet.objects.get(owner=user, is_primary=True)
        
        data = {
            'amount': '1000.00',
            'category': 'salary',
            'direction': 'in'
        }
        
        response = client.post('/api/v1/transactions/', data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert Decimal(response.data['saved_portion']) == Decimal('200.00')
        assert Decimal(response.data['spend_portion']) == Decimal('800.00')
    
    def test_create_expense_transaction(self, authenticated_client):
        """Test creating an expense transaction."""
        client, user = authenticated_client
        wallet = Wallet.objects.get(owner=user, is_primary=True)
        wallet.balance_spend = Decimal('1000.00')
        wallet.save()
        
        data = {
            'amount': '50.00',
            'category': 'food',
            'direction': 'out'
        }
        
        response = client.post('/api/v1/transactions/', data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
    
    def test_create_expense_with_round_up(self, authenticated_client):
        """Test expense with round-up savings."""
        client, user = authenticated_client
        wallet = Wallet.objects.get(owner=user, is_primary=True)
        wallet.balance_spend = Decimal('1000.00')
        wallet.save()
        
        data = {
            'amount': '45.30',
            'category': 'food',
            'direction': 'out',
            'round_up': True
        }
        
        response = client.post('/api/v1/transactions/', data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert Decimal(response.data['round_up_credit']) == Decimal('0.70')
    
    def test_list_transactions(self, authenticated_client):
        """Test listing transactions."""
        client, user = authenticated_client
        wallet = Wallet.objects.get(owner=user, is_primary=True)
        TransactionFactory(wallet=wallet)
        
        response = client.get('/api/v1/transactions/')
        
        assert response.status_code == status.HTTP_200_OK
        assert 'results' in response.data
    
    def test_list_transactions_with_filters(self, authenticated_client):
        """Test filtering transactions."""
        client, user = authenticated_client
        wallet = Wallet.objects.get(owner=user, is_primary=True)
        TransactionFactory(
            wallet=wallet,
            category=TransactionCategory.FOOD,
            direction=TransactionDirection.OUT
        )
        
        response = client.get('/api/v1/transactions/?category=food&direction=out')
        
        assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
class TestSummaryEndpoints:
    """Tests for summary endpoints."""
    
    def test_get_summary(self, authenticated_client):
        """Test getting wallet summary."""
        client, user = authenticated_client
        
        response = client.get('/api/v1/summaries/?range=30d')
        
        assert response.status_code == status.HTTP_200_OK
        assert 'period' in response.data
        assert 'savings_rate' in response.data
    
    def test_get_summary_custom_range(self, authenticated_client):
        """Test summary with custom date range."""
        client, user = authenticated_client
        
        response = client.get(
            '/api/v1/summaries/?range=custom&date_from=2025-01-01&date_to=2025-01-31'
        )
        
        assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
class TestGoalEndpoints:
    """Tests for goal endpoints."""
    
    def test_create_goal(self, authenticated_client):
        """Test creating a goal."""
        client, user = authenticated_client
        
        data = {
            'name': 'Emergency Fund',
            'target_amount': '10000.00',
            'target_date': '2025-12-31'
        }
        
        response = client.post('/api/v1/goals/', data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['name'] == 'Emergency Fund'
        assert Decimal(response.data['target_amount']) == Decimal('10000.00')
    
    def test_list_goals(self, authenticated_client):
        """Test listing goals."""
        client, user = authenticated_client
        wallet = Wallet.objects.get(owner=user, is_primary=True)
        GoalFactory(wallet=wallet)
        
        response = client.get('/api/v1/goals/')
        
        assert response.status_code == status.HTTP_200_OK
        assert 'results' in response.data
    
    def test_goal_contribute(self, authenticated_client):
        """Test contributing to a goal."""
        client, user = authenticated_client
        wallet = Wallet.objects.get(owner=user, is_primary=True)
        wallet.balance_savings = Decimal('5000.00')
        wallet.save()
        
        goal = GoalFactory(wallet=wallet)
        
        data = {'amount': '500.00'}
        
        response = client.post(
            f'/api/v1/goals/{goal.id}/contribute/',
            data,
            format='json'
        )
        
        assert response.status_code == status.HTTP_200_OK
        goal.refresh_from_db()
        assert goal.saved_amount == Decimal('500.00')


@pytest.mark.django_db
class TestBudgetRuleEndpoints:
    """Tests for budget rule endpoints."""
    
    def test_create_rule(self, authenticated_client):
        """Test creating a budget rule."""
        client, user = authenticated_client
        
        data = {
            'rule_type': 'category_limit',
            'category': 'food',
            'threshold_amount': '5000.00',
            'period': 'monthly'
        }
        
        response = client.post('/api/v1/rules/', data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['rule_type'] == 'category_limit'
    
    def test_list_rules(self, authenticated_client):
        """Test listing budget rules."""
        client, user = authenticated_client
        wallet = Wallet.objects.get(owner=user, is_primary=True)
        BudgetRuleFactory(wallet=wallet)
        
        response = client.get('/api/v1/rules/')
        
        assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
class TestNudgeEndpoints:
    """Tests for nudge endpoints."""
    
    def test_list_nudges(self, authenticated_client):
        """Test listing nudges."""
        client, user = authenticated_client
        wallet = Wallet.objects.get(owner=user, is_primary=True)
        NudgeFactory(wallet=wallet, rule=None)
        
        response = client.get('/api/v1/nudges/')
        
        assert response.status_code == status.HTTP_200_OK
    
    def test_acknowledge_nudges(self, authenticated_client):
        """Test acknowledging nudges."""
        client, user = authenticated_client
        wallet = Wallet.objects.get(owner=user, is_primary=True)
        nudge = NudgeFactory(wallet=wallet, rule=None)
        
        data = {'nudge_ids': [str(nudge.id)]}
        
        response = client.post('/api/v1/nudges/acknowledge/', data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['acknowledged_count'] == 1


@pytest.mark.django_db
class TestHealthEndpoint:
    """Tests for health check endpoint."""
    
    def test_health_check(self, api_client):
        """Test health check returns ok."""
        response = api_client.get('/healthz')
        
        assert response.status_code == status.HTTP_200_OK
        # Health check returns JsonResponse, use .json() to parse
        data = response.json()
        assert data['status'] == 'ok'
        assert 'database' in data
        assert 'timestamp' in data
