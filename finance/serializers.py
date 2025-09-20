from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import (
    User, Profile, IncomeSource, Expense, Account, ContributionPlan,
    Security, Holding, Transaction, Assumptions, ProjectionRun, ProjectionYear,
    AccountType
)

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'is_active', 'date_joined']
        read_only_fields = ['id', 'date_joined']


class ProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    age = serializers.SerializerMethodField()

    class Meta:
        model = Profile
        fields = [
            'id', 'user', 'birth_date', 'country', 'base_currency',
            'marginal_tax_rate_pct', 'risk_profile', 'target_retirement_age',
            'age', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_age(self, obj):
        return obj.age_on()


class IncomeSourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = IncomeSource
        fields = [
            'id', 'name', 'amount_monthly', 'growth_rate_annual_pct',
            'currency', 'start_date', 'end_date', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate(self, data):
        if data.get('end_date') and data.get('start_date') and data['end_date'] < data['start_date']:
            raise serializers.ValidationError("End date must be >= start date.")
        return data


class ExpenseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Expense
        fields = [
            'id', 'name', 'amount_monthly', 'category', 'is_fixed',
            'currency', 'start_date', 'end_date', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate(self, data):
        if data.get('end_date') and data.get('start_date') and data['end_date'] < data['start_date']:
            raise serializers.ValidationError("End date must be >= start date.")
        return data


class AccountSerializer(serializers.ModelSerializer):
    computed_balance = serializers.SerializerMethodField()

    class Meta:
        model = Account
        fields = [
            'id', 'name', 'type', 'broker', 'currency',
            'opening_balance', 'current_balance',
            'expected_return_annual_pct', 'retirement_fund_type',
            'computed_balance', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_computed_balance(self, obj):
        if obj.type == AccountType.ETF_STOCKS:
            total = sum(h.units * h.avg_unit_cost for h in obj.holdings.all())
            return total
        return None

    def validate(self, attrs):
        # Required always
        for field in ['name', 'currency', 'broker']:
            if not attrs.get(field) and (self.instance is None or getattr(self.instance, field, None) in [None, '']):
                raise serializers.ValidationError({field: 'This field is required.'})

        account_type = attrs.get('type') or (self.instance.type if self.instance else None)

        # Type-specific rules
        if account_type in [AccountType.RETIREMENT, AccountType.BONDS, AccountType.FUNDS, AccountType.CASH]:
            if attrs.get('expected_return_annual_pct') is None and (
                self.instance is None or self.instance.expected_return_annual_pct is None
            ):
                raise serializers.ValidationError({'expected_return_annual_pct': 'This field is required for this account type.'})
            if account_type == AccountType.RETIREMENT:
                if not attrs.get('retirement_fund_type') and (
                    self.instance is None or not getattr(self.instance, 'retirement_fund_type', None)
                ):
                    raise serializers.ValidationError({'retirement_fund_type': 'This field is required for retirement accounts.'})

        if account_type == AccountType.ETF_STOCKS:
            # Ignore or reject current_balance in payload
            if 'current_balance' in attrs:
                attrs.pop('current_balance', None)

        return attrs

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if instance.type == AccountType.ETF_STOCKS:
            # Override current_balance with computed sum of holdings
            total = sum(h.units * h.avg_unit_cost for h in instance.holdings.all())
            data['current_balance'] = total
            data['computed_balance'] = True
        else:
            data['computed_balance'] = False
        return data


class ContributionPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContributionPlan
        fields = [
            'id', 'amount_monthly', 'annual_increase_pct',
            'end_date', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class SecuritySerializer(serializers.ModelSerializer):
    class Meta:
        model = Security
        fields = [
            'id', 'ticker', 'name', 'asset_class', 'expense_ratio_pct',
            'expected_return_annual_pct', 'volatility_annual_pct',
            'currency', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate_ticker(self, value):
        # Normalize ticker to uppercase without surrounding spaces
        if value is None:
            return value
        return value.strip().upper()

    def validate(self, attrs):
        # Gracefully enforce uniqueness of (user, ticker) to avoid 500 IntegrityError
        request = self.context.get('request')
        user = getattr(request, 'user', None) if request else None
        # Use incoming ticker if present; otherwise fall back to instance ticker (updates)
        ticker = attrs.get('ticker') or (self.instance.ticker if self.instance else None)

        if user is not None and ticker:
            qs = Security.objects.filter(user=user, ticker__iexact=ticker)
            if self.instance is not None:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise serializers.ValidationError({
                    'ticker': 'Security with this ticker already exists for the current user.'
                })

        return attrs


class HoldingSerializer(serializers.ModelSerializer):
    security = SecuritySerializer(read_only=True)
    security_id = serializers.IntegerField(write_only=True)
    account = AccountSerializer(read_only=True)
    account_id = serializers.IntegerField(write_only=True)
    current_value = serializers.SerializerMethodField()

    class Meta:
        model = Holding
        fields = [
            'id', 'account', 'account_id', 'security', 'security_id', 
            'units', 'avg_unit_cost', 'current_value', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_current_value(self, obj):
        # Calculate current value based on units and average unit cost
        return obj.units * obj.avg_unit_cost

    def validate_units(self, value):
        if value < 0:
            raise serializers.ValidationError("Units must be >= 0.")
        return value

    def validate_avg_unit_cost(self, value):
        if value < 0:
            raise serializers.ValidationError("Average unit cost must be >= 0.")
        return value

    def validate(self, attrs):
        # Prevent duplicate (account, security) pairs causing DB IntegrityError
        request = self.context.get('request')
        user = getattr(request, 'user', None) if request else None

        account_id = attrs.get('account_id') or (self.instance.account_id if self.instance else None)
        security_id = attrs.get('security_id') or (self.instance.security_id if self.instance else None)

        if user is not None and account_id and security_id:
            # Ensure the account belongs to the current user
            account_qs = Account.objects.filter(id=account_id, user=user)
            if not account_qs.exists():
                raise serializers.ValidationError({'account_id': 'Account not found for current user.'})
            account = account_qs.first()
            if account.type != AccountType.ETF_STOCKS:
                raise serializers.ValidationError({'detail': 'Holdings only allowed for ETF accounts.'})

            qs = Holding.objects.filter(account_id=account_id, security_id=security_id)
            if self.instance is not None:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise serializers.ValidationError('Holding for this account and security already exists.')

        return attrs


class TransactionSerializer(serializers.ModelSerializer):
    security = SecuritySerializer(read_only=True)
    security_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    account = AccountSerializer(read_only=True)
    account_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = Transaction
        fields = [
            'id', 'account', 'account_id', 'security', 'security_id',
            'date', 'type', 'units', 'price', 'amount', 'currency',
            'note', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate(self, data):
        transaction_type = data.get('type')
        if transaction_type in ['BUY', 'SELL'] and (not data.get('units') or not data.get('price')):
            raise serializers.ValidationError("Trades must include units and price.")
        if transaction_type in ['CONTRIBUTION', 'WITHDRAWAL'] and data.get('security_id'):
            raise serializers.ValidationError("Cash flows should not reference a security.")
        return data


class AssumptionsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Assumptions
        fields = [
            'id', 'inflation_annual_pct', 'equity_return_annual_pct',
            'bond_return_annual_pct', 'cash_return_annual_pct', 'swr_pct',
            'rebalance_frequency_months', 'montecarlo_trials',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class ProjectionYearSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectionYear
        fields = [
            'id', 'year_index', 'calendar_year', 'age', 'start_balance',
            'contributions', 'withdrawals', 'nominal_return_rate_pct',
            'inflation_rate_pct', 'end_balance', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class ProjectionRunSerializer(serializers.ModelSerializer):
    years = ProjectionYearSerializer(many=True, read_only=True)
    user = UserSerializer(read_only=True)

    class Meta:
        model = ProjectionRun
        fields = [
            'id', 'user', 'as_of_date', 'horizon_years', 'target_retirement_age',
            'swr_override_pct', 'status', 'success_probability_pct',
            'estimated_exhaustion_age', 'portfolio_at_retirement',
            'sustainable_monthly_spend', 'notes', 'years', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class ProjectionRunCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectionRun
        fields = [
            'as_of_date', 'horizon_years', 'target_retirement_age',
            'swr_override_pct', 'notes'
        ]


class LongevitySummarySerializer(serializers.Serializer):
    """Serializer for longevity summary endpoint"""
    current_age = serializers.IntegerField()
    target_retirement_age = serializers.IntegerField()
    years_to_retirement = serializers.IntegerField()
    current_portfolio_value = serializers.DecimalField(max_digits=18, decimal_places=2)
    estimated_retirement_portfolio = serializers.DecimalField(max_digits=18, decimal_places=2)
    sustainable_monthly_spend = serializers.DecimalField(max_digits=14, decimal_places=2)
    estimated_exhaustion_age = serializers.IntegerField(allow_null=True)
    success_probability = serializers.DecimalField(max_digits=5, decimal_places=2, allow_null=True)

