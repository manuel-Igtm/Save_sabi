"""
API Views for Save Sabi.

This module contains all the ViewSets and APIViews for the REST API:
- Authentication endpoints
- Wallet management
- Transaction recording and listing
- Summary analytics
- Goal tracking
- Budget rules and nudges
"""

import logging
from decimal import Decimal
from django.contrib.auth import authenticate, get_user_model
from django.db import transaction as db_transaction
from django.utils import timezone
from rest_framework import status, viewsets, generics
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.authtoken.models import Token
from django_filters.rest_framework import DjangoFilterBackend

from .models import (
    Wallet, Transaction, Goal, BudgetRule, Nudge,
    TransactionCategory, TransactionDirection, GoalStatus
)
from .serializers import (
    UserSerializer, UserRegistrationSerializer, ChangePasswordSerializer,
    LoginSerializer, TokenSerializer,
    WalletSerializer, WalletCreateSerializer, WalletUpdateSerializer,
    TransactionSerializer, TransactionCreateSerializer, TransactionResponseSerializer,
    SummarySerializer, SummaryFilterSerializer,
    GoalSerializer, GoalCreateSerializer, GoalUpdateSerializer, GoalContributionSerializer,
    BudgetRuleSerializer, BudgetRuleCreateSerializer, BudgetRuleUpdateSerializer,
    NudgeSerializer, NudgeAcknowledgeSerializer, NudgeAcknowledgeResponseSerializer
)
from .permissions import (
    IsOwner, IsWalletOwner, IsTransactionOwner, IsGoalOwner, IsNudgeOwner, IsRuleOwner
)
from .services import ledger, summaries, goals, nudges
from .repositories.wallet_repo import wallet_repository
from .repositories.transaction_repo import transaction_repository

User = get_user_model()
logger = logging.getLogger(__name__)


# ============================================================================
# Authentication Views
# ============================================================================

class RegisterView(generics.CreateAPIView):
    """
    Register a new user.
    
    POST /api/v1/auth/register/
    """
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # Create auth token
        token, _ = Token.objects.get_or_create(user=user)
        
        return Response({
            'token': token.key,
            'user': UserSerializer(user).data
        }, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    """
    Login and get auth token.
    
    POST /api/v1/auth/login/
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        username = serializer.validated_data.get('username')
        email = serializer.validated_data.get('email')
        password = serializer.validated_data['password']
        
        # Try to authenticate
        if email:
            try:
                user_obj = User.objects.get(email=email)
                username = user_obj.username
            except User.DoesNotExist:
                return Response({
                    'error': True,
                    'message': 'Invalid credentials'
                }, status=status.HTTP_401_UNAUTHORIZED)
        
        user = authenticate(username=username, password=password)
        
        if not user:
            return Response({
                'error': True,
                'message': 'Invalid credentials'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        token, _ = Token.objects.get_or_create(user=user)
        
        return Response({
            'token': token.key,
            'user': UserSerializer(user).data
        })


class LogoutView(APIView):
    """
    Logout and delete auth token.
    
    POST /api/v1/auth/logout/
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            request.user.auth_token.delete()
        except Exception:
            pass
        
        return Response({'message': 'Logged out successfully'})


class UserProfileView(generics.RetrieveUpdateAPIView):
    """
    Get or update user profile.
    
    GET /api/v1/auth/profile/
    PUT /api/v1/auth/profile/
    """
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


class ChangePasswordView(APIView):
    """
    Change user password.
    
    POST /api/v1/auth/change-password/
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        
        request.user.set_password(serializer.validated_data['new_password'])
        request.user.save()
        
        return Response({'message': 'Password changed successfully'})


# ============================================================================
# Wallet Views
# ============================================================================

class WalletViewSet(viewsets.ModelViewSet):
    """
    ViewSet for wallet management.
    
    GET /api/v1/wallets/ - List user's wallets
    POST /api/v1/wallets/ - Create new wallet
    GET /api/v1/wallets/{id}/ - Get wallet details
    PUT /api/v1/wallets/{id}/ - Update wallet
    DELETE /api/v1/wallets/{id}/ - Deactivate wallet
    POST /api/v1/wallets/{id}/set_primary/ - Set as primary
    POST /api/v1/wallets/{id}/transfer_to_savings/ - Transfer to savings
    """
    permission_classes = [IsAuthenticated, IsWalletOwner]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['currency', 'is_active']

    def get_queryset(self):
        return Wallet.objects.filter(
            owner=self.request.user
        ).select_related('streak').order_by('-is_primary', '-created_at')

    def get_serializer_class(self):
        if self.action == 'create':
            return WalletCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return WalletUpdateSerializer
        return WalletSerializer

    def perform_destroy(self, instance):
        # Soft delete
        instance.is_active = False
        instance.save()

    @action(detail=True, methods=['post'])
    def set_primary(self, request, pk=None):
        """Set this wallet as the primary wallet."""
        wallet = self.get_object()
        wallet = wallet_repository.set_primary(wallet.id, request.user)
        return Response(WalletSerializer(wallet).data)

    @action(detail=True, methods=['post'])
    def transfer_to_savings(self, request, pk=None):
        """Transfer amount from spend to savings."""
        wallet = self.get_object()
        
        amount = request.data.get('amount')
        if not amount:
            return Response({
                'error': True,
                'message': 'Amount is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            amount = Decimal(str(amount))
            transaction = ledger.transfer_to_savings(wallet, amount)
            
            wallet.refresh_from_db()
            return Response({
                'message': 'Transfer successful',
                'transaction_id': str(transaction.id),
                'wallet': WalletSerializer(wallet).data
            })
        except Exception as e:
            return Response({
                'error': True,
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


# ============================================================================
# Transaction Views
# ============================================================================

class TransactionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for transaction management.
    
    GET /api/v1/transactions/ - List transactions with filters
    POST /api/v1/transactions/ - Create new transaction
    GET /api/v1/transactions/{id}/ - Get transaction details
    """
    permission_classes = [IsAuthenticated, IsTransactionOwner]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['wallet', 'category', 'direction']
    http_method_names = ['get', 'post', 'head', 'options']  # No PUT/DELETE

    def get_queryset(self):
        queryset = Transaction.objects.filter(
            wallet__owner=self.request.user
        ).select_related('wallet')
        
        # Apply date filters
        date_from = self.request.query_params.get('date_from')
        date_to = self.request.query_params.get('date_to')
        wallet_id = self.request.query_params.get('wallet_id')
        
        if wallet_id:
            queryset = queryset.filter(wallet_id=wallet_id)
        if date_from:
            queryset = queryset.filter(created_at__date__gte=date_from)
        if date_to:
            queryset = queryset.filter(created_at__date__lte=date_to)
        
        return queryset.order_by('-created_at')

    def get_serializer_class(self):
        if self.action == 'create':
            return TransactionCreateSerializer
        return TransactionSerializer

    @db_transaction.atomic
    def create(self, request, *args, **kwargs):
        """
        Create a new transaction with automatic 20/80 split.
        """
        serializer = TransactionCreateSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        
        data = serializer.validated_data
        wallet = Wallet.objects.get(id=data['wallet_id'])
        
        # Build metadata
        metadata = {}
        if data.get('notes'):
            metadata['notes'] = data['notes']
        if data.get('merchant'):
            metadata['merchant'] = data['merchant']
        if data.get('receipt_url'):
            metadata['receipt_url'] = data['receipt_url']
        
        # Record transaction via ledger service
        transaction = ledger.record_transaction(
            wallet=wallet,
            amount=data['amount'],
            category=data['category'],
            direction=data['direction'],
            notes=data.get('notes'),
            merchant=data.get('merchant'),
            round_up=data.get('round_up', False),
            metadata=metadata
        )
        
        # Evaluate budget rules after transaction
        nudges.evaluate_rules(wallet)
        
        # Refresh wallet for response
        wallet.refresh_from_db()
        
        response_data = {
            'id': str(transaction.id),
            'amount': transaction.amount,
            'currency': transaction.currency,
            'category': transaction.category,
            'direction': transaction.direction,
            'saved_portion': transaction.saved_portion,
            'spend_portion': transaction.spend_portion,
            'round_up_credit': transaction.round_up_amount,
            'wallet_balance_savings': wallet.balance_savings,
            'wallet_balance_spend': wallet.balance_spend,
            'created_at': transaction.created_at
        }
        
        return Response(
            TransactionResponseSerializer(response_data).data,
            status=status.HTTP_201_CREATED
        )


# ============================================================================
# Summary Views
# ============================================================================

class SummaryView(APIView):
    """
    Get period summary for a wallet.
    
    GET /api/v1/summaries/?wallet_id=...&range=30d
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = SummaryFilterSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        
        data = serializer.validated_data
        
        try:
            summary = summaries.get_summary_for_user(
                user=request.user,
                range_type=data.get('range', '30d'),
                wallet_id=data.get('wallet_id'),
                date_from=data.get('date_from'),
                date_to=data.get('date_to')
            )
            
            return Response(SummarySerializer(summary).data)
        
        except Exception as e:
            logger.error(f"Error generating summary: {e}")
            return Response({
                'error': True,
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


# ============================================================================
# Goal Views
# ============================================================================

class GoalViewSet(viewsets.ModelViewSet):
    """
    ViewSet for goal management.
    
    GET /api/v1/goals/ - List goals
    POST /api/v1/goals/ - Create goal
    GET /api/v1/goals/{id}/ - Get goal details
    PUT /api/v1/goals/{id}/ - Update goal
    DELETE /api/v1/goals/{id}/ - Archive goal
    POST /api/v1/goals/{id}/contribute/ - Contribute to goal
    POST /api/v1/goals/{id}/withdraw/ - Withdraw from goal
    """
    permission_classes = [IsAuthenticated, IsGoalOwner]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['wallet', 'status']

    def get_queryset(self):
        queryset = Goal.objects.filter(
            wallet__owner=self.request.user
        ).select_related('wallet')
        
        # Filter by wallet_id from query params
        wallet_id = self.request.query_params.get('wallet_id')
        if wallet_id:
            queryset = queryset.filter(wallet_id=wallet_id)
        
        return queryset.order_by('-priority', '-created_at')

    def get_serializer_class(self):
        if self.action == 'create':
            return GoalCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return GoalUpdateSerializer
        return GoalSerializer

    def perform_destroy(self, instance):
        # Archive instead of delete
        instance.status = GoalStatus.CANCELLED
        instance.save()

    @action(detail=True, methods=['post'])
    def contribute(self, request, pk=None):
        """Make a contribution to the goal from savings."""
        goal = self.get_object()
        
        serializer = GoalContributionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            result = goals.contribute_to_goal(
                goal=goal,
                amount=serializer.validated_data['amount'],
                from_savings=True
            )
            return Response(result)
        except Exception as e:
            return Response({
                'error': True,
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def withdraw(self, request, pk=None):
        """Withdraw from goal back to wallet savings."""
        goal = self.get_object()
        
        serializer = GoalContributionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            result = goals.withdraw_from_goal(
                goal=goal,
                amount=serializer.validated_data['amount']
            )
            return Response(result)
        except Exception as e:
            return Response({
                'error': True,
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


# ============================================================================
# Budget Rule Views
# ============================================================================

class BudgetRuleViewSet(viewsets.ModelViewSet):
    """
    ViewSet for budget rule management.
    
    GET /api/v1/rules/ - List rules
    POST /api/v1/rules/ - Create rule
    GET /api/v1/rules/{id}/ - Get rule details
    PUT /api/v1/rules/{id}/ - Update rule
    DELETE /api/v1/rules/{id}/ - Delete rule
    """
    permission_classes = [IsAuthenticated, IsRuleOwner]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['wallet', 'rule_type', 'is_active']

    def get_queryset(self):
        queryset = BudgetRule.objects.filter(
            wallet__owner=self.request.user
        ).select_related('wallet')
        
        wallet_id = self.request.query_params.get('wallet_id')
        if wallet_id:
            queryset = queryset.filter(wallet_id=wallet_id)
        
        return queryset.order_by('-created_at')

    def get_serializer_class(self):
        if self.action == 'create':
            return BudgetRuleCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return BudgetRuleUpdateSerializer
        return BudgetRuleSerializer


# ============================================================================
# Nudge Views
# ============================================================================

class NudgeViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for nudge listing (read-only).
    
    GET /api/v1/nudges/ - List nudges
    GET /api/v1/nudges/{id}/ - Get nudge details
    """
    serializer_class = NudgeSerializer
    permission_classes = [IsAuthenticated, IsNudgeOwner]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['wallet', 'alert_type', 'is_read']

    def get_queryset(self):
        queryset = Nudge.objects.filter(
            wallet__owner=self.request.user
        ).select_related('wallet', 'rule')
        
        wallet_id = self.request.query_params.get('wallet_id')
        if wallet_id:
            queryset = queryset.filter(wallet_id=wallet_id)
        
        # Filter unread only
        unread_only = self.request.query_params.get('unread_only', 'false')
        if unread_only.lower() in ('true', '1', 'yes'):
            queryset = queryset.filter(is_read=False)
        
        return queryset.order_by('-created_at')


class NudgeAcknowledgeView(APIView):
    """
    Acknowledge (mark as read) one or more nudges.
    
    POST /api/v1/nudges/acknowledge/
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = NudgeAcknowledgeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        acknowledged_ids = nudges.acknowledge_nudges(
            nudge_ids=serializer.validated_data['nudge_ids'],
            user=request.user
        )
        
        return Response(NudgeAcknowledgeResponseSerializer({
            'acknowledged_count': len(acknowledged_ids),
            'acknowledged_ids': acknowledged_ids
        }).data)
