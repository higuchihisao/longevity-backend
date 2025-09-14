from django.urls import path, include
from rest_framework import routers
from . import portfolio_viewsets

# Create router for portfolio endpoints
portfolio_router = routers.DefaultRouter()
portfolio_router.register(r'accounts', portfolio_viewsets.AccountViewSet, basename='portfolio-account')
portfolio_router.register(r'securities', portfolio_viewsets.SecurityViewSet, basename='portfolio-security')
portfolio_router.register(r'holdings', portfolio_viewsets.HoldingViewSet, basename='portfolio-holding')

urlpatterns = [
    path('api/portfolio/', include(portfolio_router.urls)),
]
