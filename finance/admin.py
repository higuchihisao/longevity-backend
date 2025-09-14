from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth import get_user_model
from .models import (
    Profile, IncomeSource, Expense, Account, ContributionPlan,
    Security, Holding, Transaction, Assumptions, ProjectionRun, ProjectionYear
)

User = get_user_model()


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['email', 'first_name', 'last_name', 'is_active', 'date_joined']
    list_filter = ['is_active', 'is_staff', 'date_joined']
    search_fields = ['email', 'first_name', 'last_name']
    ordering = ['email']
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name')}),
        ('Permissions', {'fields': ('is_active', 'is_staff')}),
        ('Important dates', {'fields': ('date_joined',)}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2'),
        }),
    )


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'birth_date', 'country', 'base_currency', 'risk_profile', 'target_retirement_age']
    list_filter = ['country', 'base_currency', 'risk_profile']
    search_fields = ['user__email', 'user__first_name', 'user__last_name']


@admin.register(IncomeSource)
class IncomeSourceAdmin(admin.ModelAdmin):
    list_display = ['name', 'user', 'amount_monthly', 'currency', 'start_date', 'end_date']
    list_filter = ['currency', 'start_date', 'end_date']
    search_fields = ['name', 'user__email']


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ['name', 'user', 'amount_monthly', 'category', 'is_fixed', 'currency']
    list_filter = ['category', 'is_fixed', 'currency']
    search_fields = ['name', 'user__email']


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ['name', 'user', 'type', 'broker', 'currency', 'opening_balance']
    list_filter = ['type', 'currency']
    search_fields = ['name', 'broker', 'user__email']


@admin.register(ContributionPlan)
class ContributionPlanAdmin(admin.ModelAdmin):
    list_display = ['account', 'amount_monthly', 'annual_increase_pct', 'end_date']
    list_filter = ['end_date']
    search_fields = ['account__name', 'account__user__email']


@admin.register(Security)
class SecurityAdmin(admin.ModelAdmin):
    list_display = ['ticker', 'name', 'user', 'asset_class', 'expected_return_annual_pct', 'currency']
    list_filter = ['asset_class', 'currency']
    search_fields = ['ticker', 'name', 'user__email']


@admin.register(Holding)
class HoldingAdmin(admin.ModelAdmin):
    list_display = ['account', 'security', 'units', 'avg_unit_cost']
    list_filter = ['account__type', 'security__asset_class']
    search_fields = ['account__name', 'security__ticker']


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ['date', 'account', 'security', 'type', 'amount', 'currency']
    list_filter = ['type', 'currency', 'date']
    search_fields = ['account__name', 'security__ticker', 'note']
    date_hierarchy = 'date'


@admin.register(Assumptions)
class AssumptionsAdmin(admin.ModelAdmin):
    list_display = ['user', 'inflation_annual_pct', 'equity_return_annual_pct', 'swr_pct']
    search_fields = ['user__email']


@admin.register(ProjectionRun)
class ProjectionRunAdmin(admin.ModelAdmin):
    list_display = ['user', 'as_of_date', 'horizon_years', 'status', 'estimated_exhaustion_age']
    list_filter = ['status', 'as_of_date']
    search_fields = ['user__email', 'notes']
    date_hierarchy = 'as_of_date'


@admin.register(ProjectionYear)
class ProjectionYearAdmin(admin.ModelAdmin):
    list_display = ['run', 'year_index', 'calendar_year', 'age', 'end_balance']
    list_filter = ['run__status', 'calendar_year']
    search_fields = ['run__user__email']

