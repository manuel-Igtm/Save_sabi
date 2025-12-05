"""
DRF Serializers for Save Sabi API.

This module provides serializers for:
- User registration and profile
- Wallet management
- Transaction creation and listing
- Goal tracking
- Budget rules and nudges
"""

from decimal import Decimal
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.utils import timezone
from rest_framework import serializers

from .models import (
    Wallet, Transaction, Goal, BudgetRule, Nudge, SavingsStreak,
    TransactionCategory, TransactionDirection, GoalStatus,
    RuleType, RulePeriod, AlertType, DeliveryMethod
)

User = get_user_model()


# ============================================================================
# User Serializers
# ============================================================================

class UserSerializer(serializers.ModelSerializer):
    """Serializer for user profile information."""
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'phone_number', 'preferred_currency', 'email_verified',
            'phone_verified', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'email_verified', 'phone_verified', 'created_at', 'updated_at']


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for user registration."""
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'password', 'password_confirm',
            'first_name', 'last_name', 'phone_number', 'preferred_currency'
        ]
        read_only_fields = ['id']

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({
                'password_confirm': "Passwords do not match."
            })
        return attrs

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class ChangePasswordSerializer(serializers.Serializer):
    """Serializer for password change."""
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, validators=[validate_password])

    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Old password is incorrect.")
        return value


# ============================================================================
# Wallet Serializers
# ============================================================================

class SavingsStreakSerializer(serializers.ModelSerializer):
    """Serializer for savings streak data."""
    
    class Meta:
        model = SavingsStreak
        fields = ['current_streak', 'longest_streak', 'last_savings_date', 'updated_at']
        read_only_fields = fields


class WalletSerializer(serializers.ModelSerializer):
    """Serializer for wallet information."""
    owner_username = serializers.CharField(source='owner.username', read_only=True)
    spend_ratio = serializers.IntegerField(read_only=True)
    total_balance = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)
    streak = SavingsStreakSerializer(read_only=True)

    class Meta:
        model = Wallet
        fields = [
            'id', 'owner', 'owner_username', 'name', 'currency',
            'balance_savings', 'balance_spend', 'total_balance',
            'savings_ratio', 'spend_ratio', 'is_active', 'is_primary',
            'streak', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'owner', 'balance_savings', 'balance_spend',
            'created_at', 'updated_at'
        ]

    def validate_savings_ratio(self, value):
        if not 1 <= value <= 99:
            raise serializers.ValidationError(
                "Savings ratio must be between 1 and 99."
            )
        return value


class WalletCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a new wallet."""
    
    class Meta:
        model = Wallet
        fields = ['id', 'name', 'currency', 'savings_ratio', 'is_primary']
        read_only_fields = ['id']

    def validate_savings_ratio(self, value):
        if not 1 <= value <= 99:
            raise serializers.ValidationError(
                "Savings ratio must be between 1 and 99."
            )
        return value

    def create(self, validated_data):
        validated_data['owner'] = self.context['request'].user
        return super().create(validated_data)


class WalletUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating wallet settings."""
    
    class Meta:
        model = Wallet
        fields = ['name', 'savings_ratio', 'is_active', 'is_primary']

    def validate_savings_ratio(self, value):
        if not 1 <= value <= 99:
            raise serializers.ValidationError(
                "Savings ratio must be between 1 and 99."
            )
        return value


# ============================================================================
# Transaction Serializers
# ============================================================================

class TransactionSerializer(serializers.ModelSerializer):
    """Serializer for transaction details."""
    wallet_name = serializers.CharField(source='wallet.name', read_only=True)
    notes = serializers.CharField(read_only=True)
    merchant = serializers.CharField(read_only=True)

    class Meta:
        model = Transaction
        fields = [
            'id', 'wallet', 'wallet_name', 'amount', 'currency', 'category',
            'direction', 'saved_portion', 'spend_portion', 'round_up_amount',
            'metadata', 'notes', 'merchant', 'created_at'
        ]
        read_only_fields = [
            'id', 'saved_portion', 'spend_portion', 'round_up_amount', 'created_at'
        ]


class TransactionCreateSerializer(serializers.Serializer):
    """
    Serializer for creating a new transaction.
    
    Handles the 20/80 split calculation and round-up feature.
    """
    wallet_id = serializers.UUIDField(required=False, allow_null=True)
    amount = serializers.DecimalField(
        max_digits=15, decimal_places=2,
        min_value=Decimal('0.01')
    )
    currency = serializers.CharField(max_length=3, required=False)
    category = serializers.ChoiceField(
        choices=TransactionCategory.choices,
        default=TransactionCategory.OTHER
    )
    direction = serializers.ChoiceField(
        choices=TransactionDirection.choices,
        default=TransactionDirection.OUT
    )
    round_up = serializers.BooleanField(default=False)
    notes = serializers.CharField(required=False, allow_blank=True)
    merchant = serializers.CharField(required=False, allow_blank=True)
    receipt_url = serializers.URLField(required=False, allow_blank=True)

    def validate_wallet_id(self, value):
        if value:
            user = self.context['request'].user
            try:
                wallet = Wallet.objects.get(id=value, owner=user, is_active=True)
            except Wallet.DoesNotExist:
                raise serializers.ValidationError(
                    "Wallet not found or you don't have access to it."
                )
        return value

    def validate(self, attrs):
        user = self.context['request'].user
        wallet_id = attrs.get('wallet_id')
        
        # If no wallet specified, use primary wallet
        if not wallet_id:
            try:
                wallet = Wallet.objects.get(owner=user, is_primary=True, is_active=True)
                attrs['wallet_id'] = wallet.id
            except Wallet.DoesNotExist:
                raise serializers.ValidationError({
                    'wallet_id': "No primary wallet found. Please specify a wallet."
                })
        
        return attrs


class TransactionResponseSerializer(serializers.Serializer):
    """Serializer for transaction creation response."""
    id = serializers.UUIDField()
    amount = serializers.DecimalField(max_digits=15, decimal_places=2)
    currency = serializers.CharField()
    category = serializers.CharField()
    direction = serializers.CharField()
    saved_portion = serializers.DecimalField(max_digits=15, decimal_places=2)
    spend_portion = serializers.DecimalField(max_digits=15, decimal_places=2)
    round_up_credit = serializers.DecimalField(max_digits=15, decimal_places=2)
    wallet_balance_savings = serializers.DecimalField(max_digits=15, decimal_places=2)
    wallet_balance_spend = serializers.DecimalField(max_digits=15, decimal_places=2)
    created_at = serializers.DateTimeField()


class TransactionFilterSerializer(serializers.Serializer):
    """Serializer for transaction list filters."""
    wallet_id = serializers.UUIDField(required=False)
    date_from = serializers.DateField(required=False)
    date_to = serializers.DateField(required=False)
    category = serializers.ChoiceField(choices=TransactionCategory.choices, required=False)
    direction = serializers.ChoiceField(choices=TransactionDirection.choices, required=False)


# ============================================================================
# Summary Serializers
# ============================================================================

class CategoryBreakdownSerializer(serializers.Serializer):
    """Serializer for category spending breakdown."""
    category = serializers.CharField()
    total = serializers.DecimalField(max_digits=15, decimal_places=2)
    percentage = serializers.DecimalField(max_digits=5, decimal_places=2)
    count = serializers.IntegerField()


class GoalProgressSerializer(serializers.Serializer):
    """Serializer for goal progress in summary."""
    id = serializers.UUIDField()
    name = serializers.CharField()
    target_amount = serializers.DecimalField(max_digits=15, decimal_places=2)
    saved_amount = serializers.DecimalField(max_digits=15, decimal_places=2)
    progress_pct = serializers.DecimalField(max_digits=5, decimal_places=2)
    target_date = serializers.DateField(allow_null=True)


class SummarySerializer(serializers.Serializer):
    """Serializer for period summary response."""
    period = serializers.CharField()
    date_from = serializers.DateField()
    date_to = serializers.DateField()
    total_in = serializers.DecimalField(max_digits=15, decimal_places=2)
    total_out = serializers.DecimalField(max_digits=15, decimal_places=2)
    total_saved = serializers.DecimalField(max_digits=15, decimal_places=2)
    total_spent = serializers.DecimalField(max_digits=15, decimal_places=2)
    savings_rate = serializers.DecimalField(max_digits=5, decimal_places=2)
    categories = CategoryBreakdownSerializer(many=True)
    goal_progress = GoalProgressSerializer(many=True)
    streak_days = serializers.IntegerField()
    transaction_count = serializers.IntegerField()


class SummaryFilterSerializer(serializers.Serializer):
    """Serializer for summary request filters."""
    wallet_id = serializers.UUIDField(required=False)
    range = serializers.ChoiceField(
        choices=['7d', '30d', '90d', '365d', 'custom'],
        default='30d'
    )
    date_from = serializers.DateField(required=False)
    date_to = serializers.DateField(required=False)

    def validate(self, attrs):
        if attrs.get('range') == 'custom':
            if not attrs.get('date_from') or not attrs.get('date_to'):
                raise serializers.ValidationError({
                    'range': "Custom range requires date_from and date_to."
                })
            if attrs['date_from'] > attrs['date_to']:
                raise serializers.ValidationError({
                    'date_from': "Start date must be before end date."
                })
        return attrs


# ============================================================================
# Goal Serializers
# ============================================================================

class GoalSerializer(serializers.ModelSerializer):
    """Serializer for goal details."""
    wallet_name = serializers.CharField(source='wallet.name', read_only=True)
    progress_pct = serializers.DecimalField(
        source='progress_percentage',
        max_digits=5, decimal_places=2, read_only=True
    )
    remaining_amount = serializers.DecimalField(
        max_digits=15, decimal_places=2, read_only=True
    )
    is_completed = serializers.BooleanField(read_only=True)

    class Meta:
        model = Goal
        fields = [
            'id', 'wallet', 'wallet_name', 'name', 'description',
            'target_amount', 'target_date', 'saved_amount', 'status',
            'priority', 'allocation_percentage', 'progress_pct',
            'remaining_amount', 'is_completed', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'saved_amount', 'created_at', 'updated_at'
        ]


class GoalCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a new goal."""
    wallet_id = serializers.UUIDField(required=False, allow_null=True)

    class Meta:
        model = Goal
        fields = [
            'id', 'wallet_id', 'name', 'description', 'target_amount',
            'target_date', 'priority', 'allocation_percentage'
        ]
        read_only_fields = ['id']

    def validate_wallet_id(self, value):
        if value:
            user = self.context['request'].user
            try:
                Wallet.objects.get(id=value, owner=user, is_active=True)
            except Wallet.DoesNotExist:
                raise serializers.ValidationError(
                    "Wallet not found or you don't have access to it."
                )
        return value

    def validate_target_date(self, value):
        if value and value < timezone.now().date():
            raise serializers.ValidationError(
                "Target date cannot be in the past."
            )
        return value

    def validate(self, attrs):
        user = self.context['request'].user
        wallet_id = attrs.get('wallet_id')
        
        if not wallet_id:
            try:
                wallet = Wallet.objects.get(owner=user, is_primary=True, is_active=True)
                attrs['wallet_id'] = wallet.id
            except Wallet.DoesNotExist:
                raise serializers.ValidationError({
                    'wallet_id': "No primary wallet found. Please specify a wallet."
                })
        
        return attrs

    def create(self, validated_data):
        wallet_id = validated_data.pop('wallet_id')
        validated_data['wallet_id'] = wallet_id
        return super().create(validated_data)


class GoalUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating a goal."""
    
    class Meta:
        model = Goal
        fields = [
            'name', 'description', 'target_amount', 'target_date',
            'status', 'priority', 'allocation_percentage'
        ]

    def validate_target_date(self, value):
        if value and value < timezone.now().date():
            raise serializers.ValidationError(
                "Target date cannot be in the past."
            )
        return value

    def validate_status(self, value):
        instance = self.instance
        if instance and instance.status == GoalStatus.COMPLETED:
            if value != GoalStatus.COMPLETED:
                raise serializers.ValidationError(
                    "Cannot change status of a completed goal."
                )
        return value


class GoalContributionSerializer(serializers.Serializer):
    """Serializer for manual goal contribution."""
    amount = serializers.DecimalField(
        max_digits=15, decimal_places=2,
        min_value=Decimal('0.01')
    )


# ============================================================================
# Budget Rule Serializers
# ============================================================================

class BudgetRuleSerializer(serializers.ModelSerializer):
    """Serializer for budget rule details."""
    wallet_name = serializers.CharField(source='wallet.name', read_only=True)

    class Meta:
        model = BudgetRule
        fields = [
            'id', 'wallet', 'wallet_name', 'rule_type', 'category',
            'threshold_amount', 'period', 'custom_message',
            'last_triggered_at', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'last_triggered_at', 'created_at', 'updated_at']


class BudgetRuleCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a budget rule."""
    wallet_id = serializers.UUIDField(required=False, allow_null=True)

    class Meta:
        model = BudgetRule
        fields = [
            'id', 'wallet_id', 'rule_type', 'category', 'threshold_amount',
            'period', 'custom_message', 'is_active'
        ]
        read_only_fields = ['id']

    def validate_wallet_id(self, value):
        if value:
            user = self.context['request'].user
            try:
                Wallet.objects.get(id=value, owner=user, is_active=True)
            except Wallet.DoesNotExist:
                raise serializers.ValidationError(
                    "Wallet not found or you don't have access to it."
                )
        return value

    def validate(self, attrs):
        user = self.context['request'].user
        wallet_id = attrs.get('wallet_id')
        rule_type = attrs.get('rule_type')
        category = attrs.get('category')
        
        # Get wallet
        if not wallet_id:
            try:
                wallet = Wallet.objects.get(owner=user, is_primary=True, is_active=True)
                attrs['wallet_id'] = wallet.id
            except Wallet.DoesNotExist:
                raise serializers.ValidationError({
                    'wallet_id': "No primary wallet found. Please specify a wallet."
                })
        
        # Validate category is required for category_limit
        if rule_type == RuleType.CATEGORY_LIMIT and not category:
            raise serializers.ValidationError({
                'category': "Category is required for category limit rules."
            })
        
        return attrs

    def create(self, validated_data):
        wallet_id = validated_data.pop('wallet_id')
        validated_data['wallet_id'] = wallet_id
        return super().create(validated_data)


class BudgetRuleUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating a budget rule."""
    
    class Meta:
        model = BudgetRule
        fields = [
            'threshold_amount', 'period', 'custom_message', 'is_active'
        ]


# ============================================================================
# Nudge Serializers
# ============================================================================

class NudgeSerializer(serializers.ModelSerializer):
    """Serializer for nudge details."""
    wallet_name = serializers.CharField(source='wallet.name', read_only=True)
    rule_type = serializers.CharField(source='rule.rule_type', read_only=True, allow_null=True)

    class Meta:
        model = Nudge
        fields = [
            'id', 'wallet', 'wallet_name', 'rule', 'rule_type',
            'alert_type', 'title', 'message', 'sent_via',
            'is_read', 'read_at', 'metadata', 'created_at'
        ]
        read_only_fields = fields


class NudgeAcknowledgeSerializer(serializers.Serializer):
    """Serializer for acknowledging nudges."""
    nudge_ids = serializers.ListField(
        child=serializers.UUIDField(),
        min_length=1,
        max_length=100
    )


class NudgeAcknowledgeResponseSerializer(serializers.Serializer):
    """Response serializer for nudge acknowledgment."""
    acknowledged_count = serializers.IntegerField()
    acknowledged_ids = serializers.ListField(child=serializers.UUIDField())


# ============================================================================
# Auth Serializers
# ============================================================================

class LoginSerializer(serializers.Serializer):
    """Serializer for user login."""
    username = serializers.CharField(required=False)
    email = serializers.EmailField(required=False)
    password = serializers.CharField()

    def validate(self, attrs):
        username = attrs.get('username')
        email = attrs.get('email')
        
        if not username and not email:
            raise serializers.ValidationError(
                "Either username or email is required."
            )
        
        return attrs


class TokenSerializer(serializers.Serializer):
    """Serializer for auth token response."""
    token = serializers.CharField()
    user = UserSerializer()
