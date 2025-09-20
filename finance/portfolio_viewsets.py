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

    def create(self, request, *args, **kwargs):
        """Idempotent create: reuse existing (user, ticker) instead of erroring."""
        data = request.data.copy()
        ticker = (data.get('ticker') or '').strip().upper()

        if ticker:
            existing = Security.objects.filter(user=request.user, ticker__iexact=ticker).first()
            if existing:
                serializer = self.get_serializer(existing)
                return Response(serializer.data, status=status.HTTP_200_OK)

            data['ticker'] = ticker

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

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

        # Idempotent: if holding exists for this (account, security), return it
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
