from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from finance.models import (
    Profile, IncomeSource, Expense, Account, ContributionPlan,
    Security, Holding, Transaction, Assumptions, ProjectionRun
)

User = get_user_model()


class Command(BaseCommand):
    help = 'Check database data and API functionality'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🔍 Checking Database Data...\n'))
        
        # Check Users
        self.stdout.write(self.style.WARNING('👥 USERS:'))
        users = User.objects.all()
        self.stdout.write(f'Total users: {users.count()}')
        for user in users:
            self.stdout.write(f'  - ID: {user.id}, Email: {user.email}, Name: {user.get_full_name()}, Active: {user.is_active}')
        self.stdout.write('')
        
        # Check Profiles
        self.stdout.write(self.style.WARNING('👤 PROFILES:'))
        profiles = Profile.objects.all()
        self.stdout.write(f'Total profiles: {profiles.count()}')
        for profile in profiles:
            age = profile.age_on()
            self.stdout.write(f'  - User: {profile.user.email}')
            self.stdout.write(f'    Age: {age} (Birth Date: {profile.birth_date})')
            self.stdout.write(f'    Country: {profile.country}')
            self.stdout.write(f'    Base Currency: {profile.base_currency}')
            self.stdout.write(f'    Tax Rate: {profile.marginal_tax_rate_pct}%')
            self.stdout.write(f'    Risk Profile: {profile.risk_profile}')
            self.stdout.write(f'    Target Retirement Age: {profile.target_retirement_age}')
            self.stdout.write('')
        self.stdout.write('')
        
        # Check Income Sources
        self.stdout.write(self.style.WARNING('💰 INCOME SOURCES:'))
        income_sources = IncomeSource.objects.all()
        self.stdout.write(f'Total income sources: {income_sources.count()}')
        for income in income_sources:
            self.stdout.write(f'  - User: {income.user.email}, Name: {income.name}, Amount: {income.amount_monthly} {income.currency}/mo')
        self.stdout.write('')
        
        # Check Expenses
        self.stdout.write(self.style.WARNING('💸 EXPENSES:'))
        expenses = Expense.objects.all()
        self.stdout.write(f'Total expenses: {expenses.count()}')
        for expense in expenses:
            self.stdout.write(f'  - User: {expense.user.email}, Name: {expense.name}, Amount: {expense.amount_monthly} {expense.currency}/mo, Category: {expense.category}')
        self.stdout.write('')
        
        # Check Accounts
        self.stdout.write(self.style.WARNING('🏦 ACCOUNTS:'))
        accounts = Account.objects.all()
        self.stdout.write(f'Total accounts: {accounts.count()}')
        for account in accounts:
            self.stdout.write(f'  - User: {account.user.email}, Name: {account.name}, Type: {account.type}, Balance: {account.opening_balance} {account.currency}')
        self.stdout.write('')
        
        # Check Securities
        self.stdout.write(self.style.WARNING('📈 SECURITIES:'))
        securities = Security.objects.all()
        self.stdout.write(f'Total securities: {securities.count()}')
        for security in securities:
            self.stdout.write(f'  - User: {security.user.email}, Ticker: {security.ticker}, Name: {security.name}, Asset Class: {security.asset_class}')
        self.stdout.write('')
        
        # Check Holdings
        self.stdout.write(self.style.WARNING('📊 HOLDINGS:'))
        holdings = Holding.objects.all()
        self.stdout.write(f'Total holdings: {holdings.count()}')
        for holding in holdings:
            value = holding.units * holding.avg_unit_cost
            self.stdout.write(f'  - Account: {holding.account.name}, Security: {holding.security.ticker}, Units: {holding.units}, Value: {value}')
        self.stdout.write('')
        
        # Check Transactions
        self.stdout.write(self.style.WARNING('💳 TRANSACTIONS:'))
        transactions = Transaction.objects.all()
        self.stdout.write(f'Total transactions: {transactions.count()}')
        for transaction in transactions:
            self.stdout.write(f'  - Date: {transaction.date}, Type: {transaction.type}, Amount: {transaction.amount} {transaction.currency}, Account: {transaction.account.name}')
        self.stdout.write('')
        
        # Check Assumptions
        self.stdout.write(self.style.WARNING('⚙️ ASSUMPTIONS:'))
        assumptions = Assumptions.objects.all()
        self.stdout.write(f'Total assumptions: {assumptions.count()}')
        for assumption in assumptions:
            self.stdout.write(f'  - User: {assumption.user.email}, Inflation: {assumption.inflation_annual_pct}%, Equity Return: {assumption.equity_return_annual_pct}%, SWR: {assumption.swr_pct}%')
        self.stdout.write('')
        
        # Check Projection Runs
        self.stdout.write(self.style.WARNING('🔮 PROJECTION RUNS:'))
        projection_runs = ProjectionRun.objects.all()
        self.stdout.write(f'Total projection runs: {projection_runs.count()}')
        for run in projection_runs:
            self.stdout.write(f'  - User: {run.user.email}, Date: {run.as_of_date}, Status: {run.status}, Horizon: {run.horizon_years} years')
        self.stdout.write('')
        
        # Summary
        self.stdout.write(self.style.SUCCESS('📊 SUMMARY:'))
        self.stdout.write(f'  - Users: {users.count()}')
        self.stdout.write(f'  - Profiles: {profiles.count()}')
        self.stdout.write(f'  - Income Sources: {income_sources.count()}')
        self.stdout.write(f'  - Expenses: {expenses.count()}')
        self.stdout.write(f'  - Accounts: {accounts.count()}')
        self.stdout.write(f'  - Securities: {securities.count()}')
        self.stdout.write(f'  - Holdings: {holdings.count()}')
        self.stdout.write(f'  - Transactions: {transactions.count()}')
        self.stdout.write(f'  - Assumptions: {assumptions.count()}')
        self.stdout.write(f'  - Projection Runs: {projection_runs.count()}')
        
        self.stdout.write(self.style.SUCCESS('\n✅ Database check completed!'))
