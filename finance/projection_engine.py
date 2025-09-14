"""
Financial projection engine for longevity calculations.
"""
from decimal import Decimal
from datetime import date, timedelta
from typing import Dict, List, Optional
import logging

from django.utils import timezone
from .models import (
    Profile, IncomeSource, Expense, Account, ContributionPlan,
    Security, Holding, Transaction, Assumptions, ProjectionRun, ProjectionYear
)

logger = logging.getLogger(__name__)


class ProjectionEngine:
    """
    Engine for calculating financial longevity projections.
    """
    
    def __init__(self, projection_run: ProjectionRun):
        self.projection_run = projection_run
        self.user = projection_run.user
        self.as_of_date = projection_run.as_of_date
        self.horizon_years = projection_run.horizon_years
        self.target_retirement_age = projection_run.target_retirement_age
        
        # Get user's profile and assumptions
        self.profile = Profile.objects.get(user=self.user)
        self.assumptions = Assumptions.objects.get(user=self.user)
        
        # Override SWR if provided
        self.swr_pct = projection_run.swr_override_pct or self.assumptions.swr_pct
        
    def run_deterministic_projection(self) -> Dict:
        """
        Run a deterministic financial projection.
        Returns a dictionary with key metrics and year-by-year data.
        """
        try:
            # Clear existing projection years
            ProjectionYear.objects.filter(run=self.projection_run).delete()
            
            # Calculate current portfolio value
            current_portfolio = self._calculate_current_portfolio()
            
            # Get income and expense projections
            income_projection = self._get_income_projection()
            expense_projection = self._get_expense_projection()
            
            # Run year-by-year projection
            projection_years = self._run_yearly_projection(
                current_portfolio, income_projection, expense_projection
            )
            
            # Calculate key metrics
            metrics = self._calculate_metrics(projection_years)
            
            # Save projection years to database
            for year_data in projection_years:
                ProjectionYear.objects.create(
                    run=self.projection_run,
                    **year_data
                )
            
            return metrics
            
        except Exception as e:
            logger.error(f"Projection calculation failed: {str(e)}")
            raise
    
    def _calculate_current_portfolio(self) -> Decimal:
        """Calculate current total portfolio value."""
        total_value = Decimal('0')
        
        for account in Account.objects.filter(user=self.user):
            for holding in account.holdings.all():
                # For now, use average cost as current price
                # In a real implementation, you'd fetch current market prices
                current_value = holding.units * holding.avg_unit_cost
                total_value += current_value
        
        return total_value
    
    def _get_income_projection(self) -> List[Dict]:
        """Get income projection for each year."""
        income_sources = IncomeSource.objects.filter(user=self.user)
        projection = []
        
        for year_offset in range(self.horizon_years):
            year = self.as_of_date.year + year_offset
            total_income = Decimal('0')
            
            for source in income_sources:
                # Check if source is active in this year
                if self._is_source_active(source, year):
                    monthly_amount = source.amount_monthly
                    # Apply growth rate
                    growth_factor = (1 + source.growth_rate_annual_pct / 100) ** year_offset
                    annual_amount = monthly_amount * 12 * Decimal(str(growth_factor))
                    total_income += annual_amount
            
            projection.append({
                'year': year,
                'total_income': total_income
            })
        
        return projection
    
    def _get_expense_projection(self) -> List[Dict]:
        """Get expense projection for each year."""
        expenses = Expense.objects.filter(user=self.user)
        projection = []
        
        for year_offset in range(self.horizon_years):
            year = self.as_of_date.year + year_offset
            total_expenses = Decimal('0')
            
            for expense in expenses:
                # Check if expense is active in this year
                if self._is_source_active(expense, year):
                    monthly_amount = expense.amount_monthly
                    # Apply inflation
                    inflation_factor = (1 + self.assumptions.inflation_annual_pct / 100) ** year_offset
                    annual_amount = monthly_amount * 12 * Decimal(str(inflation_factor))
                    total_expenses += annual_amount
            
            projection.append({
                'year': year,
                'total_expenses': total_expenses
            })
        
        return projection
    
    def _is_source_active(self, source, year: int) -> bool:
        """Check if an income source or expense is active in a given year."""
        if source.start_date and year < source.start_date.year:
            return False
        if source.end_date and year > source.end_date.year:
            return False
        return True
    
    def _run_yearly_projection(self, starting_balance: Decimal, 
                             income_projection: List[Dict], 
                             expense_projection: List[Dict]) -> List[Dict]:
        """Run year-by-year projection calculations."""
        projection_years = []
        current_balance = starting_balance
        
        for year_offset in range(self.horizon_years):
            year = self.as_of_date.year + year_offset
            age = self.profile.age_on(date(year, 1, 1))
            
            # Get income and expenses for this year
            year_income = income_projection[year_offset]['total_income']
            year_expenses = expense_projection[year_offset]['total_expenses']
            
            # Calculate contributions (from contribution plans)
            contributions = self._calculate_contributions(year_offset)
            
            # Calculate withdrawals (during retirement)
            withdrawals = self._calculate_withdrawals(year_offset, current_balance)
            
            # Calculate net cash flow
            net_cash_flow = year_income - year_expenses + contributions - withdrawals
            
            # Calculate portfolio return based on asset allocation
            # For now, use a simple weighted average
            portfolio_return = self._calculate_portfolio_return()
            
            # Apply returns to current balance
            start_balance = current_balance
            returns = current_balance * portfolio_return / 100
            end_balance = start_balance + returns + net_cash_flow
            
            # Store year data
            year_data = {
                'year_index': year_offset,
                'calendar_year': year,
                'age': age,
                'start_balance': start_balance,
                'contributions': contributions,
                'withdrawals': withdrawals,
                'nominal_return_rate_pct': portfolio_return,
                'inflation_rate_pct': self.assumptions.inflation_annual_pct,
                'end_balance': max(end_balance, Decimal('0'))  # Can't go negative
            }
            
            projection_years.append(year_data)
            current_balance = year_data['end_balance']
        
        return projection_years
    
    def _calculate_contributions(self, year_offset: int) -> Decimal:
        """Calculate total contributions for a given year."""
        total_contributions = Decimal('0')
        
        for account in Account.objects.filter(user=self.user):
            for plan in account.contribution_plans.all():
                if not plan.end_date or (self.as_of_date.year + year_offset) <= plan.end_date.year:
                    monthly_contribution = plan.amount_monthly
                    # Apply annual increase
                    growth_factor = (1 + plan.annual_increase_pct / 100) ** year_offset
                    annual_contribution = monthly_contribution * 12 * Decimal(str(growth_factor))
                    total_contributions += annual_contribution
        
        return total_contributions
    
    def _calculate_withdrawals(self, year_offset: int, current_balance: Decimal) -> Decimal:
        """Calculate withdrawals for a given year (during retirement)."""
        current_year = self.as_of_date.year + year_offset
        current_age = self.profile.age_on(date(current_year, 1, 1))
        
        # Only withdraw during retirement
        if self.target_retirement_age and current_age >= self.target_retirement_age:
            # Use SWR to calculate sustainable withdrawal
            annual_withdrawal = current_balance * self.swr_pct / 100
            return annual_withdrawal
        
        return Decimal('0')
    
    def _calculate_portfolio_return(self) -> Decimal:
        """Calculate expected portfolio return based on current holdings."""
        # This is a simplified calculation
        # In reality, you'd calculate based on actual asset allocation
        return self.assumptions.equity_return_annual_pct
    
    def _calculate_metrics(self, projection_years: List[Dict]) -> Dict:
        """Calculate key metrics from the projection."""
        if not projection_years:
            return {}
        
        # Find retirement year
        retirement_year = None
        if self.target_retirement_age:
            for year_data in projection_years:
                if year_data['age'] and year_data['age'] >= self.target_retirement_age:
                    retirement_year = year_data
                    break
        
        # Calculate exhaustion age
        exhaustion_age = None
        for year_data in projection_years:
            if year_data['end_balance'] <= Decimal('0'):
                exhaustion_age = year_data['age']
                break
        
        # Calculate sustainable monthly spend
        sustainable_monthly_spend = Decimal('0')
        if retirement_year:
            sustainable_monthly_spend = (
                retirement_year['end_balance'] * self.swr_pct / 100 / 12
            )
        
        return {
            'exhaustion_age': exhaustion_age,
            'retirement_portfolio': retirement_year['end_balance'] if retirement_year else Decimal('0'),
            'sustainable_spend': sustainable_monthly_spend,
            'total_years': len(projection_years),
            'final_balance': projection_years[-1]['end_balance']
        }

