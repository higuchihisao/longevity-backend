from __future__ import annotations

from decimal import Decimal
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.contrib.auth.models import AbstractUser, BaseUserManager


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True, db_index=True)

    class Meta:
        abstract = True


class Currency(models.TextChoices):
    PEN = "PEN", "PEN"
    USD = "USD", "USD"
    EUR = "EUR", "EUR"


class RiskProfile(models.TextChoices):
    CONSERVATIVE = "CONSERVATIVE", "Conservative"
    MODERATE = "MODERATE", "Moderate"
    AGGRESSIVE = "AGGRESSIVE", "Aggressive"


class AccountType(models.TextChoices):
    ETF_STOCKS = "ETF_STOCKS", "Acciones / ETF"
    RETIREMENT = "RETIREMENT", "Retirement / Tax-Advantaged"
    BONDS = "BONDS", "Bonds"
    FUNDS = "FUNDS", "Mutual Funds / Funds"
    CASH = "CASH", "Cash"


class ExpenseCategory(models.TextChoices):
    HOUSING = "HOUSING", "Housing"
    FOOD = "FOOD", "Food"
    TRANSPORT = "TRANSPORT", "Transport"
    HEALTH = "HEALTH", "Health"
    EDUCATION = "EDUCATION", "Education"
    LEISURE = "LEISURE", "Leisure"
    OTHER = "OTHER", "Other"


class SecurityAssetClass(models.TextChoices):
    EQUITY = "EQUITY", "Equities"
    BOND = "BOND", "Bonds"
    CASH_EQ = "CASH_EQ", "Cash & Equivalents"
    REIT = "REIT", "Real Estate (REITs)"
    COMMODITY = "COMMODITY", "Commodities"
    OTHER = "OTHER", "Other"


class TransactionType(models.TextChoices):
    BUY = "BUY", "Buy"
    SELL = "SELL", "Sell"
    DIVIDEND = "DIVIDEND", "Dividend"
    INTEREST = "INTEREST", "Interest"
    CONTRIBUTION = "CONTRIBUTION", "Contribution"
    WITHDRAWAL = "WITHDRAWAL", "Withdrawal"
    FEE = "FEE", "Fee"
    REBALANCE = "REBALANCE", "Rebalance"


class UserManager(BaseUserManager):
    """Custom user manager for email-based authentication."""
    
    def create_user(self, email, password=None, **extra_fields):
        """Create and return a regular user with an email and password."""
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """Create and return a superuser with an email and password."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    """
    Custom user model for the finance application.
    """
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=30, blank=True)
    last_name = models.CharField(max_length=30, blank=True)
    username = models.CharField(max_length=150, unique=True, null=True, blank=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    def save(self, *args, **kwargs):
        if not self.username:
            self.username = self.email
        super().save(*args, **kwargs)

    def __str__(self):
        return self.email

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    def get_short_name(self):
        return self.first_name


class Profile(TimeStampedModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="finance_profile")
    birth_date = models.DateField(null=True, blank=True)
    country = models.CharField(max_length=64, default="Peru")
    base_currency = models.CharField(max_length=3, choices=Currency.choices, default=Currency.PEN)
    marginal_tax_rate_pct = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("0.00"))
    risk_profile = models.CharField(max_length=16, choices=RiskProfile.choices, default=RiskProfile.MODERATE)
    target_retirement_age = models.PositiveIntegerField(default=65)

    def age_on(self, ref_date=None) -> int | None:
        if not self.birth_date:
            return None
        ref = ref_date or timezone.now().date()
        years = ref.year - self.birth_date.year - ((ref.month, ref.day) < (self.birth_date.month, self.birth_date.day))
        return max(years, 0)

    def __str__(self):
        return f"Profile({self.user})"


class IncomeSource(TimeStampedModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="income_sources")
    name = models.CharField(max_length=120)
    amount_monthly = models.DecimalField(max_digits=14, decimal_places=2)
    growth_rate_annual_pct = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("0.00"))
    currency = models.CharField(max_length=3, choices=Currency.choices, default=Currency.PEN)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ["name"]

    def clean(self):
        if self.amount_monthly < 0:
            raise ValidationError("Monthly income must be >= 0.")
        if self.end_date and self.start_date and self.end_date < self.start_date:
            raise ValidationError("Income end_date must be >= start_date.")

    def __str__(self):
        return f"Income({self.name}, {self.amount_monthly} {self.currency}/mo)"


class Expense(TimeStampedModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="expenses")
    name = models.CharField(max_length=120)
    amount_monthly = models.DecimalField(max_digits=14, decimal_places=2)
    category = models.CharField(max_length=16, choices=ExpenseCategory.choices, default=ExpenseCategory.OTHER)
    is_fixed = models.BooleanField(default=True)
    currency = models.CharField(max_length=3, choices=Currency.choices, default=Currency.PEN)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ["-amount_monthly"]

    def clean(self):
        if self.amount_monthly < 0:
            raise ValidationError("Monthly expense must be >= 0.")
        if self.end_date and self.start_date and self.end_date < self.start_date:
            raise ValidationError("Expense end_date must be >= start_date.")

    def __str__(self):
        return f"Expense({self.name}, {self.amount_monthly} {self.currency}/mo)"


class Account(TimeStampedModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="accounts")
    name = models.CharField(max_length=120)
    type = models.CharField(max_length=16, choices=AccountType.choices, default=AccountType.ETF_STOCKS)
    broker = models.CharField(max_length=120)
    currency = models.CharField(max_length=3, choices=Currency.choices, default=Currency.PEN)
    opening_balance = models.DecimalField(max_digits=16, decimal_places=2, default=Decimal("0.00"))
    current_balance = models.DecimalField(max_digits=16, decimal_places=2, default=Decimal("0.00"))
    expected_return_annual_pct = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("0.00"), null=True, blank=True)
    retirement_fund_type = models.CharField(max_length=64, null=True, blank=True)

    class Meta:
        unique_together = [("user", "name")]
        ordering = ["name"]

    def __str__(self):
        return f"Account({self.name}, {self.type})"


class ContributionPlan(TimeStampedModel):
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name="contribution_plans")
    amount_monthly = models.DecimalField(max_digits=14, decimal_places=2)
    annual_increase_pct = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("0.00"))
    end_date = models.DateField(null=True, blank=True)

    def clean(self):
        if self.amount_monthly < 0:
            raise ValidationError("Monthly contribution must be >= 0.")

    def __str__(self):
        return f"ContributionPlan({self.account.name}: {self.amount_monthly}/mo)"


class Security(TimeStampedModel):
    """
    Representa un instrumento (ETF, acción, bono, fondo).
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="securities")
    ticker = models.CharField(max_length=32)
    name = models.CharField(max_length=160)
    asset_class = models.CharField(max_length=16, choices=SecurityAssetClass.choices, default=SecurityAssetClass.EQUITY)
    expense_ratio_pct = models.DecimalField(max_digits=6, decimal_places=3, default=Decimal("0.000"))  # e.g. 0.03%
    expected_return_annual_pct = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("5.00"))
    volatility_annual_pct = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("10.00"))
    currency = models.CharField(max_length=3, choices=Currency.choices, default=Currency.USD)

    class Meta:
        unique_together = [("user", "ticker")]

    def __str__(self):
        return f"{self.ticker} ({self.asset_class})"


class Holding(TimeStampedModel):
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name="holdings")
    security = models.ForeignKey(Security, on_delete=models.PROTECT, related_name="holdings")
    units = models.DecimalField(max_digits=18, decimal_places=6, default=Decimal("0"))
    avg_unit_cost = models.DecimalField(max_digits=14, decimal_places=4, default=Decimal("0.0000"))

    class Meta:
        unique_together = [("account", "security")]

    def __str__(self):
        return f"Holding({self.account.name}, {self.security.ticker})"


class Transaction(TimeStampedModel):
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name="transactions")
    security = models.ForeignKey(Security, on_delete=models.SET_NULL, null=True, blank=True, related_name="transactions")
    date = models.DateField()
    type = models.CharField(max_length=16, choices=TransactionType.choices)
    units = models.DecimalField(max_digits=18, decimal_places=6, null=True, blank=True)
    price = models.DecimalField(max_digits=14, decimal_places=6, null=True, blank=True)
    amount = models.DecimalField(max_digits=16, decimal_places=2)  # signo según tipo
    currency = models.CharField(max_length=3, choices=Currency.choices, default=Currency.USD)
    note = models.CharField(max_length=240, blank=True, default="")

    class Meta:
        ordering = ["-date", "-created_at"]

    def clean(self):
        if self.type in {TransactionType.BUY, TransactionType.SELL} and (self.units is None or self.price is None):
            raise ValidationError("Trades must include units and price.")
        if self.type in {TransactionType.CONTRIBUTION, TransactionType.WITHDRAWAL} and self.security is not None:
            raise ValidationError("Cash flows should not reference a security.")

    def __str__(self):
        return f"{self.date} {self.type} {self.amount} {self.currency}"


class Assumptions(TimeStampedModel):
    """
    Supuestos globales por usuario para las proyecciones determinísticas.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="assumptions")
    inflation_annual_pct = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("2.00"))
    equity_return_annual_pct = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("7.00"))
    bond_return_annual_pct = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("3.00"))
    cash_return_annual_pct = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("1.50"))
    swr_pct = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("4.00"))  # Safe Withdrawal Rate
    rebalance_frequency_months = models.PositiveIntegerField(default=12)
    montecarlo_trials = models.PositiveIntegerField(default=0)  # 0 = desactivado (placeholder)

    def __str__(self):
        return f"Assumptions({self.user})"


class ProjectionRunStatus(models.TextChoices):
    PENDING = "PENDING", "Pending"
    COMPLETED = "COMPLETED", "Completed"
    FAILED = "FAILED", "Failed"


class ProjectionRun(TimeStampedModel):
    """
    Un "job" de proyección guardado, para poder comparar escenarios.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="projection_runs")
    as_of_date = models.DateField(default=timezone.now)
    horizon_years = models.PositiveIntegerField(default=60)
    target_retirement_age = models.PositiveIntegerField(null=True, blank=True)
    swr_override_pct = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)

    status = models.CharField(max_length=12, choices=ProjectionRunStatus.choices, default=ProjectionRunStatus.PENDING)
    success_probability_pct = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)  # Montecarlo futuro
    estimated_exhaustion_age = models.PositiveIntegerField(null=True, blank=True)
    portfolio_at_retirement = models.DecimalField(max_digits=18, decimal_places=2, null=True, blank=True)
    sustainable_monthly_spend = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)

    notes = models.TextField(blank=True, default="")

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"ProjectionRun({self.user}, {self.as_of_date}, status={self.status})"


class ProjectionYear(TimeStampedModel):
    """
    Detalle de proyección año a año (determinística), útil para gráficas.
    """
    run = models.ForeignKey(ProjectionRun, on_delete=models.CASCADE, related_name="years")
    year_index = models.PositiveIntegerField(help_text="0 = año base")
    calendar_year = models.PositiveIntegerField()
    age = models.PositiveIntegerField(null=True, blank=True)
    start_balance = models.DecimalField(max_digits=18, decimal_places=2, default=Decimal("0.00"))
    contributions = models.DecimalField(max_digits=18, decimal_places=2, default=Decimal("0.00"))
    withdrawals = models.DecimalField(max_digits=18, decimal_places=2, default=Decimal("0.00"))
    nominal_return_rate_pct = models.DecimalField(max_digits=6, decimal_places=3, default=Decimal("0.000"))
    inflation_rate_pct = models.DecimalField(max_digits=6, decimal_places=3, default=Decimal("0.000"))
    end_balance = models.DecimalField(max_digits=18, decimal_places=2, default=Decimal("0.00"))

    class Meta:
        unique_together = [("run", "year_index")]
        ordering = ["year_index"]

    def __str__(self):
        return f"ProjectionYear(run={self.run_id}, idx={self.year_index}, end={self.end_balance})"

