from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from decimal import Decimal
from datetime import date
from .models import (
    Profile, IncomeSource, Expense, Account, ContributionPlan,
    Security, Holding, Transaction, Assumptions, ProjectionRun
)

User = get_user_model()


class ModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            first_name='Test',
            last_name='User'
        )

    def test_profile_creation(self):
        """Test profile creation and age calculation"""
        profile = Profile.objects.create(
            user=self.user,
            birth_date=date(1990, 1, 1),
            country='Peru',
            base_currency='PEN',
            risk_profile='MODERATE'
        )
        
        self.assertEqual(profile.user, self.user)
        self.assertEqual(profile.country, 'Peru')
        self.assertEqual(profile.base_currency, 'PEN')
        
        # Test age calculation
        age = profile.age_on(date(2024, 1, 1))
        self.assertEqual(age, 34)

    def test_income_source_validation(self):
        """Test income source validation"""
        # Valid income source
        income = IncomeSource.objects.create(
            user=self.user,
            name='Salary',
            amount_monthly=Decimal('5000.00'),
            currency='PEN'
        )
        self.assertEqual(income.amount_monthly, Decimal('5000.00'))
        
        # Test validation for negative amount
        with self.assertRaises(ValidationError):
            income = IncomeSource(
                user=self.user,
                name='Invalid Income',
                amount_monthly=Decimal('-100.00')
            )
            income.full_clean()

    def test_expense_validation(self):
        """Test expense validation"""
        expense = Expense.objects.create(
            user=self.user,
            name='Rent',
            amount_monthly=Decimal('2000.00'),
            category='HOUSING',
            is_fixed=True
        )
        self.assertEqual(expense.category, 'HOUSING')
        self.assertTrue(expense.is_fixed)

    def test_account_creation(self):
        """Test account creation"""
        account = Account.objects.create(
            user=self.user,
            name='Savings Account',
            type='CASH',
            broker='BCP',
            currency='PEN',
            opening_balance=Decimal('10000.00')
        )
        
        self.assertEqual(account.user, self.user)
        self.assertEqual(account.type, 'CASH')
        self.assertEqual(account.opening_balance, Decimal('10000.00'))

    def test_security_creation(self):
        """Test security creation"""
        security = Security.objects.create(
            user=self.user,
            ticker='VTI',
            name='Vanguard Total Stock Market ETF',
            asset_class='EQUITY',
            expected_return_annual_pct=Decimal('7.50')
        )
        
        self.assertEqual(security.ticker, 'VTI')
        self.assertEqual(security.asset_class, 'EQUITY')

    def test_holding_creation(self):
        """Test holding creation"""
        account = Account.objects.create(
            user=self.user,
            name='Investment Account',
            type='BROKERAGE',
            currency='USD'
        )
        
        security = Security.objects.create(
            user=self.user,
            ticker='VTI',
            name='Vanguard Total Stock Market ETF',
            asset_class='EQUITY'
        )
        
        holding = Holding.objects.create(
            account=account,
            security=security,
            units=Decimal('100.000000'),
            avg_unit_cost=Decimal('250.0000')
        )
        
        self.assertEqual(holding.account, account)
        self.assertEqual(holding.security, security)
        self.assertEqual(holding.units, Decimal('100.000000'))

    def test_transaction_validation(self):
        """Test transaction validation"""
        account = Account.objects.create(
            user=self.user,
            name='Investment Account',
            type='BROKERAGE',
            currency='USD'
        )
        
        security = Security.objects.create(
            user=self.user,
            ticker='VTI',
            name='Vanguard Total Stock Market ETF',
            asset_class='EQUITY'
        )
        
        # Valid buy transaction
        transaction = Transaction.objects.create(
            account=account,
            security=security,
            date=date(2024, 1, 15),
            type='BUY',
            units=Decimal('10.000000'),
            price=Decimal('250.0000'),
            amount=Decimal('-2500.00'),
            currency='USD'
        )
        
        self.assertEqual(transaction.type, 'BUY')
        self.assertEqual(transaction.units, Decimal('10.000000'))
        
        # Test validation for buy without units/price
        with self.assertRaises(ValidationError):
            invalid_transaction = Transaction(
                account=account,
                security=security,
                date=date(2024, 1, 15),
                type='BUY',
                amount=Decimal('-2500.00'),
                currency='USD'
            )
            invalid_transaction.full_clean()

    def test_assumptions_creation(self):
        """Test assumptions creation"""
        assumptions = Assumptions.objects.create(
            user=self.user,
            inflation_annual_pct=Decimal('2.50'),
            equity_return_annual_pct=Decimal('7.00'),
            bond_return_annual_pct=Decimal('3.00'),
            swr_pct=Decimal('4.00')
        )
        
        self.assertEqual(assumptions.user, self.user)
        self.assertEqual(assumptions.inflation_annual_pct, Decimal('2.50'))
        self.assertEqual(assumptions.swr_pct, Decimal('4.00'))

    def test_projection_run_creation(self):
        """Test projection run creation"""
        projection_run = ProjectionRun.objects.create(
            user=self.user,
            as_of_date=date(2024, 1, 1),
            horizon_years=30,
            target_retirement_age=65
        )
        
        self.assertEqual(projection_run.user, self.user)
        self.assertEqual(projection_run.horizon_years, 30)
        self.assertEqual(projection_run.status, 'PENDING')


class APITests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            first_name='Test',
            last_name='User'
        )
        self.client.force_authenticate(user=self.user)

    def test_profile_api(self):
        """Test profile API endpoints"""
        # Create profile
        response = self.client.post('/api/profiles/', {
            'birth_date': '1990-01-01',
            'country': 'Peru',
            'base_currency': 'PEN',
            'risk_profile': 'MODERATE',
            'target_retirement_age': 65
        })
        self.assertEqual(response.status_code, 201)
        
        # Get profile
        response = self.client.get('/api/profiles/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 1)

    def test_income_source_api(self):
        """Test income source API endpoints"""
        # Create income source
        response = self.client.post('/api/income/', {
            'name': 'Salary',
            'amount_monthly': '5000.00',
            'currency': 'PEN',
            'growth_rate_annual_pct': '3.00'
        })
        self.assertEqual(response.status_code, 201)
        
        # Get income sources
        response = self.client.get('/api/income/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 1)

    def test_expense_api(self):
        """Test expense API endpoints"""
        # Create expense
        response = self.client.post('/api/expenses/', {
            'name': 'Rent',
            'amount_monthly': '2000.00',
            'category': 'HOUSING',
            'is_fixed': True,
            'currency': 'PEN'
        })
        self.assertEqual(response.status_code, 201)
        
        # Get expenses
        response = self.client.get('/api/expenses/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 1)

    def test_account_api(self):
        """Test account API endpoints"""
        # Create account
        response = self.client.post('/api/accounts/', {
            'name': 'Savings Account',
            'type': 'CASH',
            'broker': 'BCP',
            'currency': 'PEN',
            'opening_balance': '10000.00'
        })
        self.assertEqual(response.status_code, 201)
        
        # Get accounts
        response = self.client.get('/api/accounts/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 1)

    def test_security_api(self):
        """Test security API endpoints"""
        # Create security
        response = self.client.post('/api/securities/', {
            'ticker': 'VTI',
            'name': 'Vanguard Total Stock Market ETF',
            'asset_class': 'EQUITY',
            'expected_return_annual_pct': '7.50',
            'currency': 'USD'
        })
        self.assertEqual(response.status_code, 201)
        
        # Get securities
        response = self.client.get('/api/securities/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 1)

    def test_assumptions_api(self):
        """Test assumptions API endpoints"""
        # Create assumptions
        response = self.client.post('/api/assumptions/', {
            'inflation_annual_pct': '2.50',
            'equity_return_annual_pct': '7.00',
            'bond_return_annual_pct': '3.00',
            'swr_pct': '4.00'
        })
        self.assertEqual(response.status_code, 201)
        
        # Get assumptions
        response = self.client.get('/api/assumptions/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 1)

    def test_projection_run_api(self):
        """Test projection run API endpoints"""
        # Create projection run
        response = self.client.post('/api/projections/runs/', {
            'as_of_date': '2024-01-01',
            'horizon_years': 30,
            'target_retirement_age': 65
        })
        self.assertEqual(response.status_code, 201)
        
        # Get projection runs
        response = self.client.get('/api/projections/runs/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 1)

