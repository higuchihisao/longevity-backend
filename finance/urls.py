from django.urls import path, include
from rest_framework import routers
from rest_framework_simplejwt.views import TokenRefreshView
from . import viewsets
from . import auth_views
from . import portfolio_urls
from . import test_views
from . import agents

# Create router and register viewsets
router = routers.DefaultRouter()
router.register(r'profiles', viewsets.ProfileViewSet, basename='profile')
router.register(r'income', viewsets.IncomeSourceViewSet, basename='income')
router.register(r'expenses', viewsets.ExpenseViewSet, basename='expense')
router.register(r'accounts', viewsets.AccountViewSet, basename='account')
router.register(r'accounts/(?P<account_id>[^/.]+)/contributions', viewsets.ContributionPlanViewSet, basename='account-contributions')
router.register(r'securities', viewsets.SecurityViewSet, basename='security')
router.register(r'holdings', viewsets.HoldingViewSet, basename='holding')
router.register(r'transactions', viewsets.TransactionViewSet, basename='transaction')
router.register(r'assumptions', viewsets.AssumptionsViewSet, basename='assumptions')
router.register(r'projections/runs', viewsets.ProjectionRunViewSet, basename='projection-run')
router.register(r'projections/years', viewsets.ProjectionYearViewSet, basename='projection-year')

# Portfolio endpoints (also available at /api/accounts/, /api/securities/, /api/holdings/)
from . import portfolio_viewsets
router.register(r'portfolio-accounts', portfolio_viewsets.AccountViewSet, basename='portfolio-account')
router.register(r'portfolio-securities', portfolio_viewsets.SecurityViewSet, basename='portfolio-security')
router.register(r'portfolio-holdings', portfolio_viewsets.HoldingViewSet, basename='portfolio-holding')

urlpatterns = [
    path('api/', include(router.urls)),
    
    # Portfolio endpoints
    path('', include(portfolio_urls)),
    
    # Test endpoints
    path('api/test/accounts/', test_views.test_create_account, name='test-create-account'),
    
    # Authentication endpoints
    path('api/auth/login/', auth_views.LoginView.as_view(), name='token_obtain_pair'),
    path('api/auth/register/', auth_views.register, name='register'),
    path('api/auth/logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('api/auth/refresh/', auth_views.RefreshView.as_view(), name='token_refresh'),
    path('api/auth/user/', auth_views.user_profile, name='user_profile'),
    path('api/auth/user/update/', auth_views.update_profile, name='update_profile'),
    
    # Endpoints de utilidad para "acciones":
    # - Ejecutar proyección determinística
    path('api/projections/runs/<int:pk>/execute/', viewsets.ProjectionRunViewSet.as_view({'post': 'execute'}), name='execute-projection'),
    # - Duplicar escenario
    path('api/projections/runs/<int:pk>/clone/', viewsets.ProjectionRunViewSet.as_view({'post': 'clone'}), name='clone-projection'),
    # - Resumen de "¿hasta qué edad alcanzo?"
    path('api/summary/longevity/', viewsets.longevity_summary, name='longevity-summary'),

    # Agents endpoint (Assistants API)
    path('api/projection-agent', agents.agents_projection_view, name='projection-agent'),
]

