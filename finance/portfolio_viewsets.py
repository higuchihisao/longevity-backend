from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from .models import Account, Security, Holding
from .serializers import AccountSerializer, SecuritySerializer, HoldingSerializer


class AccountViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing user accounts
    """
    serializer_class = AccountSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'broker']
    ordering_fields = ['name', 'created_at', 'current_balance']
    ordering = ['-created_at']

    def get_queryset(self):
        """Return accounts for the authenticated user only"""
        return Account.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        """Set the user to the current user when creating an account"""
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['get'])
    def holdings(self, request, pk=None):
        """Get all holdings for a specific account"""
        account = self.get_object()
        holdings = Holding.objects.filter(account=account)
        serializer = HoldingSerializer(holdings, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def balance_history(self, request, pk=None):
        """Get balance history for an account (placeholder for future implementation)"""
        account = self.get_object()
        return Response({
            'account': account.name,
            'current_balance': account.current_balance,
            'opening_balance': account.opening_balance,
            'message': 'Balance history feature coming soon'
        })


class SecurityViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing securities
    """
    serializer_class = SecuritySerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['ticker', 'name']
    ordering_fields = ['ticker', 'name', 'asset_class', 'expected_return_annual_pct']
    ordering = ['ticker']

    def get_queryset(self):
        """Return securities for the authenticated user only"""
        return Security.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        """Set the user to the current user when creating a security"""
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['get'])
    def holdings(self, request, pk=None):
        """Get all holdings for a specific security"""
        security = self.get_object()
        holdings = Holding.objects.filter(security=security)
        serializer = HoldingSerializer(holdings, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def by_asset_class(self, request):
        """Get securities grouped by asset class"""
        securities = self.get_queryset()
        grouped = {}
        for security in securities:
            asset_class = security.asset_class
            if asset_class not in grouped:
                grouped[asset_class] = []
            grouped[asset_class].append(SecuritySerializer(security).data)
        return Response(grouped)


class HoldingViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing user holdings
    """
    serializer_class = HoldingSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['account', 'security', 'security__asset_class']
    search_fields = ['security__ticker', 'security__name', 'account__name']
    ordering_fields = ['created_at', 'units', 'avg_unit_cost', 'current_value']
    ordering = ['-created_at']

    def get_queryset(self):
        """Return holdings for the authenticated user only"""
        return Holding.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        """Set the user to the current user when creating a holding"""
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['get'])
    def portfolio_summary(self, request):
        """Get portfolio summary for the user"""
        holdings = self.get_queryset()
        
        total_value = sum(holding.current_value for holding in holdings)
        
        # Group by asset class
        by_asset_class = {}
        for holding in holdings:
            asset_class = holding.security.asset_class
            if asset_class not in by_asset_class:
                by_asset_class[asset_class] = {
                    'total_value': 0,
                    'holdings': []
                }
            by_asset_class[asset_class]['total_value'] += holding.current_value
            by_asset_class[asset_class]['holdings'].append(HoldingSerializer(holding).data)
        
        # Calculate percentages
        for asset_class in by_asset_class:
            if total_value > 0:
                by_asset_class[asset_class]['percentage'] = (
                    by_asset_class[asset_class]['total_value'] / total_value * 100
                )
            else:
                by_asset_class[asset_class]['percentage'] = 0
        
        return Response({
            'total_value': total_value,
            'by_asset_class': by_asset_class,
            'total_holdings': holdings.count()
        })

    @action(detail=False, methods=['get'])
    def by_account(self, request):
        """Get holdings grouped by account"""
        holdings = self.get_queryset()
        grouped = {}
        for holding in holdings:
            account_name = holding.account.name
            if account_name not in grouped:
                grouped[account_name] = []
            grouped[account_name].append(HoldingSerializer(holding).data)
        return Response(grouped)
