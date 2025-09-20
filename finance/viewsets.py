from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user_model
from django.db.models import Q, Sum
from django.utils import timezone
from decimal import Decimal
import logging

from .models import (
    Profile, IncomeSource, Expense, Account, ContributionPlan,
    Security, Holding, Transaction, Assumptions, ProjectionRun, ProjectionYear,
    AccountType
)
from .serializers import (
    ProfileSerializer, IncomeSourceSerializer, ExpenseSerializer,
    AccountSerializer, ContributionPlanSerializer, SecuritySerializer,
    HoldingSerializer, TransactionSerializer, AssumptionsSerializer,
    ProjectionRunSerializer, ProjectionRunCreateSerializer, ProjectionYearSerializer,
    LongevitySummarySerializer
)
from .projection_engine import ProjectionEngine

User = get_user_model()
logger = logging.getLogger(__name__)


class ProfileViewSet(viewsets.ModelViewSet):
    serializer_class = ProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Profile.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class IncomeSourceViewSet(viewsets.ModelViewSet):
    serializer_class = IncomeSourceSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return IncomeSource.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class ExpenseViewSet(viewsets.ModelViewSet):
    serializer_class = ExpenseSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Expense.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class AccountViewSet(viewsets.ModelViewSet):
    serializer_class = AccountSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = Account.objects.filter(user=self.request.user).prefetch_related('holdings__security')
        # Filtering by type and type__in
        req = self.request
        type_filter = req.query_params.get('type')
        type_in = req.query_params.get('type__in')
        if type_filter:
            qs = qs.filter(type=type_filter)
        if type_in:
            qs = qs.filter(type__in=[t.strip() for t in type_in.split(',') if t.strip()])
        return qs

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class ContributionPlanViewSet(viewsets.ModelViewSet):
    serializer_class = ContributionPlanSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        account_id = self.kwargs.get('account_id')
        return ContributionPlan.objects.filter(
            account__user=self.request.user,
            account_id=account_id
        )

    def perform_create(self, serializer):
        account_id = self.kwargs.get('account_id')
        account = Account.objects.get(id=account_id, user=self.request.user)
        serializer.save(account=account)


class SecurityViewSet(viewsets.ModelViewSet):
    serializer_class = SecuritySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Security.objects.filter(user=self.request.user)

    def create(self, request, *args, **kwargs):
        """Idempotent create: if (user, ticker) exists, return it instead of 500."""
        data = request.data.copy()
        ticker = (data.get('ticker') or '').strip().upper()

        if ticker:
            existing = Security.objects.filter(user=request.user, ticker__iexact=ticker).first()
            if existing:
                serializer = self.get_serializer(existing)
                return Response(serializer.data, status=status.HTTP_200_OK)

            # ensure normalized ticker goes through validation
            data['ticker'] = ticker

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class HoldingViewSet(viewsets.ModelViewSet):
    serializer_class = HoldingSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Holding.objects.filter(account__user=self.request.user)

    def create(self, request, *args, **kwargs):
        data = request.data.copy()
        account_id = data.get('account_id')
        security_id = data.get('security_id')

        # Validate account ownership
        try:
            account = Account.objects.get(id=account_id, user=request.user)
        except Account.DoesNotExist:
            return Response({'account_id': 'Account not found for current user.'}, status=status.HTTP_404_NOT_FOUND)

        # If a holding already exists for (account, security), return it (idempotent)
        if account_id and security_id:
            existing = Holding.objects.filter(account_id=account_id, security_id=security_id).first()
            if existing:
                serializer = self.get_serializer(existing)
                return Response(serializer.data, status=status.HTTP_200_OK)

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save(account=account)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class TransactionViewSet(viewsets.ModelViewSet):
    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Transaction.objects.filter(account__user=self.request.user)

    def perform_create(self, serializer):
        # Validate that the account belongs to the user
        account_id = serializer.validated_data.get('account_id')
        account = Account.objects.get(id=account_id, user=self.request.user)
        serializer.save(account=account)


class AssumptionsViewSet(viewsets.ModelViewSet):
    serializer_class = AssumptionsSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Assumptions.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def get_object(self):
        obj, created = Assumptions.objects.get_or_create(user=self.request.user)
        return obj


class ProjectionRunViewSet(viewsets.ModelViewSet):
    serializer_class = ProjectionRunSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return ProjectionRun.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        if self.action == 'create':
            return ProjectionRunCreateSerializer
        return ProjectionRunSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['post'])
    def execute(self, request, pk=None):
        """Execute a projection run"""
        projection_run = self.get_object()
        
        try:
            engine = ProjectionEngine(projection_run)
            result = engine.run_deterministic_projection()
            
            projection_run.status = 'COMPLETED'
            projection_run.estimated_exhaustion_age = result.get('exhaustion_age')
            projection_run.portfolio_at_retirement = result.get('retirement_portfolio')
            projection_run.sustainable_monthly_spend = result.get('sustainable_spend')
            projection_run.save()
            
            return Response({
                'status': 'success',
                'message': 'Projection completed successfully',
                'data': result
            })
            
        except Exception as e:
            logger.error(f"Projection execution failed: {str(e)}")
            projection_run.status = 'FAILED'
            projection_run.save()
            
            return Response({
                'status': 'error',
                'message': f'Projection failed: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['post'])
    def clone(self, request, pk=None):
        """Clone a projection run"""
        original_run = self.get_object()
        
        # Create a new projection run with the same parameters
        new_run = ProjectionRun.objects.create(
            user=request.user,
            as_of_date=original_run.as_of_date,
            horizon_years=original_run.horizon_years,
            target_retirement_age=original_run.target_retirement_age,
            swr_override_pct=original_run.swr_override_pct,
            notes=f"Cloned from {original_run.id}"
        )
        
        serializer = self.get_serializer(new_run)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ProjectionYearViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ProjectionYearSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return ProjectionYear.objects.filter(run__user=self.request.user)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def longevity_summary(request):
    """Get a summary of financial longevity for the current user"""
    try:
        # Get user's profile
        profile = Profile.objects.get(user=request.user)
        
        # Get current portfolio value
        current_portfolio = 0
        for account in Account.objects.filter(user=request.user):
            for holding in account.holdings.all():
                current_portfolio += holding.units * holding.avg_unit_cost
        
        # Get assumptions
        assumptions, _ = Assumptions.objects.get_or_create(user=request.user)
        
        # Calculate basic metrics
        current_age = profile.age_on() or 0
        target_retirement_age = profile.target_retirement_age
        years_to_retirement = max(0, target_retirement_age - current_age)
        
        # Simple projection for summary (this would be more complex in reality)
        annual_contribution = sum(
            plan.amount_monthly * 12 
            for account in Account.objects.filter(user=request.user)
            for plan in account.contribution_plans.all()
        )
        
        # Estimate retirement portfolio (simplified)
        estimated_retirement_portfolio = current_portfolio
        for year in range(years_to_retirement):
            estimated_retirement_portfolio = (
                estimated_retirement_portfolio * (1 + assumptions.equity_return_annual_pct / 100) +
                annual_contribution
            )
        
        # Calculate sustainable monthly spend
        sustainable_monthly_spend = (
            estimated_retirement_portfolio * assumptions.swr_pct / 100 / 12
        )
        
        # Estimate exhaustion age (simplified)
        monthly_expenses = sum(
            expense.amount_monthly 
            for expense in Expense.objects.filter(user=request.user)
        )
        
        if monthly_expenses > 0:
            years_of_spending = estimated_retirement_portfolio / (monthly_expenses * 12)
            estimated_exhaustion_age = target_retirement_age + years_of_spending
        else:
            estimated_exhaustion_age = None
        
        summary_data = {
            'current_age': current_age,
            'target_retirement_age': target_retirement_age,
            'years_to_retirement': years_to_retirement,
            'current_portfolio_value': current_portfolio,
            'estimated_retirement_portfolio': estimated_retirement_portfolio,
            'sustainable_monthly_spend': sustainable_monthly_spend,
            'estimated_exhaustion_age': estimated_exhaustion_age,
            'success_probability': None  # Placeholder for Monte Carlo
        }
        
        serializer = LongevitySummarySerializer(summary_data)
        return Response(serializer.data)
        
    except Profile.DoesNotExist:
        return Response(
            {'error': 'User profile not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        logger.error(f"Longevity summary failed: {str(e)}")
        return Response(
            {'error': f'Failed to calculate summary: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
