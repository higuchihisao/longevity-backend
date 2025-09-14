from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from decimal import Decimal
from datetime import date, timedelta
from finance.models import (
    Profile, IncomeSource, Expense, Account, ContributionPlan,
    Security, Holding, Transaction, Assumptions
)

User = get_user_model()


class Command(BaseCommand):
    help = 'Seed the database with sample financial data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--email',
            type=str,
            default='demo@example.com',
            help='Email for the demo user'
        )

    def handle(self, *args, **options):
        email = options['email']
        
        # Create or get user
        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                'first_name': 'Demo',
                'last_name': 'User',
                'is_active': True
            }
        )
        
        # Set password for demo user
        if created:
            user.set_password('demo123')
            user.save()
            self.stdout.write(f'Created user: {email} with password: demo123')
        else:
            self.stdout.write(f'Using existing user: {email}')

        # Create profile
        profile, created = Profile.objects.get_or_create(
            user=user,
            defaults={
                'birth_date': date(1985, 6, 15),
                'country': 'Peru',
                'base_currency': 'PEN',
                'marginal_tax_rate_pct': Decimal('28.00'),
                'risk_profile': 'MODERATE',
                'target_retirement_age': 65
            }
        )
        
        if created:
            self.stdout.write('Created user profile')

        # Create assumptions
        assumptions, created = Assumptions.objects.get_or_create(
            user=user,
            defaults={
                'inflation_annual_pct': Decimal('2.50'),
                'equity_return_annual_pct': Decimal('7.00'),
                'bond_return_annual_pct': Decimal('3.00'),
                'cash_return_annual_pct': Decimal('1.50'),
                'swr_pct': Decimal('4.00'),
                'rebalance_frequency_months': 12
            }
        )
        
        if created:
            self.stdout.write('Created financial assumptions')

        # Create income sources
        income_sources = [
            {
                'name': 'Primary Job',
                'amount_monthly': Decimal('8000.00'),
                'growth_rate_annual_pct': Decimal('3.00'),
                'currency': 'PEN'
            },
            {
                'name': 'Freelance Work',
                'amount_monthly': Decimal('2000.00'),
                'growth_rate_annual_pct': Decimal('5.00'),
                'currency': 'PEN',
                'start_date': date(2024, 1, 1),
                'end_date': date(2026, 12, 31)
            }
        ]
        
        for income_data in income_sources:
            income, created = IncomeSource.objects.get_or_create(
                user=user,
                name=income_data['name'],
                defaults=income_data
            )
            if created:
                self.stdout.write(f'Created income source: {income.name}')

        # Create expenses
        expenses = [
            {
                'name': 'Rent',
                'amount_monthly': Decimal('2500.00'),
                'category': 'HOUSING',
                'is_fixed': True,
                'currency': 'PEN'
            },
            {
                'name': 'Groceries',
                'amount_monthly': Decimal('800.00'),
                'category': 'FOOD',
                'is_fixed': False,
                'currency': 'PEN'
            },
            {
                'name': 'Transportation',
                'amount_monthly': Decimal('300.00'),
                'category': 'TRANSPORT',
                'is_fixed': False,
                'currency': 'PEN'
            },
            {
                'name': 'Health Insurance',
                'amount_monthly': Decimal('400.00'),
                'category': 'HEALTH',
                'is_fixed': True,
                'currency': 'PEN'
            },
            {
                'name': 'Entertainment',
                'amount_monthly': Decimal('500.00'),
                'category': 'LEISURE',
                'is_fixed': False,
                'currency': 'PEN'
            }
        ]
        
        for expense_data in expenses:
            expense, created = Expense.objects.get_or_create(
                user=user,
                name=expense_data['name'],
                defaults=expense_data
            )
            if created:
                self.stdout.write(f'Created expense: {expense.name}')

        # Create accounts
        accounts = [
            {
                'name': 'Primary Savings',
                'type': 'CASH',
                'broker': 'BCP',
                'currency': 'PEN',
                'opening_balance': Decimal('50000.00')
            },
            {
                'name': 'Investment Account',
                'type': 'BROKERAGE',
                'broker': 'Interactive Brokers',
                'currency': 'USD',
                'opening_balance': Decimal('25000.00')
            },
            {
                'name': 'Retirement 401k',
                'type': 'RETIREMENT',
                'broker': 'Company Plan',
                'currency': 'USD',
                'opening_balance': Decimal('15000.00')
            }
        ]
        
        for account_data in accounts:
            account, created = Account.objects.get_or_create(
                user=user,
                name=account_data['name'],
                defaults=account_data
            )
            if created:
                self.stdout.write(f'Created account: {account.name}')

        # Create contribution plans
        contribution_plans = [
            {
                'account': Account.objects.get(user=user, name='Investment Account'),
                'amount_monthly': Decimal('2000.00'),
                'annual_increase_pct': Decimal('2.00')
            },
            {
                'account': Account.objects.get(user=user, name='Retirement 401k'),
                'amount_monthly': Decimal('1000.00'),
                'annual_increase_pct': Decimal('3.00')
            }
        ]
        
        for plan_data in contribution_plans:
            plan, created = ContributionPlan.objects.get_or_create(
                account=plan_data['account'],
                defaults=plan_data
            )
            if created:
                self.stdout.write(f'Created contribution plan for {plan.account.name}')

        # Create securities
        securities = [
            {
                'ticker': 'VTI',
                'name': 'Vanguard Total Stock Market ETF',
                'asset_class': 'EQUITY',
                'expense_ratio_pct': Decimal('0.030'),
                'expected_return_annual_pct': Decimal('7.50'),
                'volatility_annual_pct': Decimal('16.00'),
                'currency': 'USD'
            },
            {
                'ticker': 'BND',
                'name': 'Vanguard Total Bond Market ETF',
                'asset_class': 'BOND',
                'expense_ratio_pct': Decimal('0.030'),
                'expected_return_annual_pct': Decimal('3.50'),
                'volatility_annual_pct': Decimal('3.50'),
                'currency': 'USD'
            },
            {
                'ticker': 'VXUS',
                'name': 'Vanguard Total International Stock ETF',
                'asset_class': 'EQUITY',
                'expense_ratio_pct': Decimal('0.080'),
                'expected_return_annual_pct': Decimal('6.50'),
                'volatility_annual_pct': Decimal('18.00'),
                'currency': 'USD'
            }
        ]
        
        for security_data in securities:
            security, created = Security.objects.get_or_create(
                user=user,
                ticker=security_data['ticker'],
                defaults=security_data
            )
            if created:
                self.stdout.write(f'Created security: {security.ticker}')

        # Create holdings
        investment_account = Account.objects.get(user=user, name='Investment Account')
        retirement_account = Account.objects.get(user=user, name='Retirement 401k')
        
        holdings = [
            {
                'account': investment_account,
                'security': Security.objects.get(user=user, ticker='VTI'),
                'units': Decimal('100.000000'),
                'avg_unit_cost': Decimal('250.0000')
            },
            {
                'account': investment_account,
                'security': Security.objects.get(user=user, ticker='BND'),
                'units': Decimal('50.000000'),
                'avg_unit_cost': Decimal('80.0000')
            },
            {
                'account': retirement_account,
                'security': Security.objects.get(user=user, ticker='VXUS'),
                'units': Decimal('75.000000'),
                'avg_unit_cost': Decimal('60.0000')
            }
        ]
        
        for holding_data in holdings:
            holding, created = Holding.objects.get_or_create(
                account=holding_data['account'],
                security=holding_data['security'],
                defaults=holding_data
            )
            if created:
                self.stdout.write(f'Created holding: {holding.security.ticker} in {holding.account.name}')

        # Create some sample transactions
        transactions = [
            {
                'account': investment_account,
                'security': Security.objects.get(user=user, ticker='VTI'),
                'date': date(2024, 1, 15),
                'type': 'BUY',
                'units': Decimal('10.000000'),
                'price': Decimal('245.5000'),
                'amount': Decimal('-2455.00'),
                'currency': 'USD',
                'note': 'Monthly investment'
            },
            {
                'account': investment_account,
                'security': Security.objects.get(user=user, ticker='BND'),
                'date': date(2024, 2, 15),
                'type': 'BUY',
                'units': Decimal('5.000000'),
                'price': Decimal('82.0000'),
                'amount': Decimal('-410.00'),
                'currency': 'USD',
                'note': 'Bond allocation'
            },
            {
                'account': investment_account,
                'date': date(2024, 3, 1),
                'type': 'CONTRIBUTION',
                'amount': Decimal('2000.00'),
                'currency': 'USD',
                'note': 'Monthly contribution'
            }
        ]
        
        for transaction_data in transactions:
            transaction, created = Transaction.objects.get_or_create(
                account=transaction_data['account'],
                date=transaction_data['date'],
                type=transaction_data['type'],
                amount=transaction_data['amount'],
                defaults=transaction_data
            )
            if created:
                self.stdout.write(f'Created transaction: {transaction.type} on {transaction.date}')

        self.stdout.write(
            self.style.SUCCESS('Successfully seeded database with sample data!')
        )

