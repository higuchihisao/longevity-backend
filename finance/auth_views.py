from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from django.contrib.auth import authenticate
from django.contrib.auth import get_user_model
from django.conf import settings
from .serializers import UserSerializer, ProfileSerializer
from .models import Profile

User = get_user_model()


COOKIE_ACCESS = 'access_token'
COOKIE_REFRESH = 'refresh_token'

def _cookie_kwargs():
    return dict(
        httponly=True,
        samesite='Lax',
        secure=not settings.DEBUG,  # secure in prod
        path='/'
    )


class LoginView(TokenObtainPairView):
    """Login that returns tokens in JSON and sets httpOnly cookies."""
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        base_response = super().post(request, *args, **kwargs)
        data = getattr(base_response, 'data', {}) or {}
        access = data.get('access')
        refresh = data.get('refresh')

        # Attach user info for convenience
        user_data = None
        email = request.data.get('email')
        try:
            user = User.objects.get(email=email)
            user_data = UserSerializer(user).data
        except Exception:
            user_data = None

        resp = Response({'access': access, 'refresh': refresh, 'user': user_data}, status=base_response.status_code)
        if access:
            resp.set_cookie(COOKIE_ACCESS, access, **_cookie_kwargs())
        if refresh:
            resp.set_cookie(COOKIE_REFRESH, refresh, **_cookie_kwargs())
        return resp


@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    """
    Register a new user
    """
    try:
        # Validate required fields
        email = request.data.get('email')
        password = request.data.get('password')
        first_name = request.data.get('first_name', '')
        last_name = request.data.get('last_name', '')
        
        # Check if email and password are provided
        if not email:
            return Response(
                {'error': 'Email is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not password:
            return Response(
                {'error': 'Password is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate email format
        if '@' not in email or '.' not in email:
            return Response(
                {'error': 'Please enter a valid email address'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if password is long enough
        if len(password) < 6:
            return Response(
                {'error': 'Password must be at least 6 characters long'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if user already exists
        if User.objects.filter(email=email).exists():
            return Response(
                {'error': 'User with this email already exists'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create user
        user = User.objects.create_user(
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name
        )
        
        # Generate tokens
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': UserSerializer(user).data
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        return Response(
            {'error': f'Registration failed: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


class RefreshView(TokenRefreshView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        # Allow refresh via cookie when body not provided
        if not request.data.get('refresh'):
            cookie_refresh = request.COOKIES.get(COOKIE_REFRESH)
            if cookie_refresh:
                request.data['refresh'] = cookie_refresh

        base_response = super().post(request, *args, **kwargs)
        access = getattr(base_response, 'data', {}).get('access')
        resp = Response({'access': access}, status=base_response.status_code)
        if access:
            resp.set_cookie(COOKIE_ACCESS, access, **_cookie_kwargs())
        return resp


class LogoutView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        token_str = request.data.get('refresh') or request.COOKIES.get(COOKIE_REFRESH)
        if token_str:
            try:
                token = RefreshToken(token_str)
                token.blacklist()
            except Exception:
                pass
        resp = Response(status=status.HTTP_204_NO_CONTENT)
        resp.delete_cookie(COOKIE_ACCESS, path='/')
        resp.delete_cookie(COOKIE_REFRESH, path='/')
        return resp


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_profile(request):
    """
    Get current user profile and financial profile
    """
    user = request.user
    
    # Get or create profile
    profile, created = Profile.objects.get_or_create(user=user)
    
    return Response({
        'user': UserSerializer(user).data,
        'profile': ProfileSerializer(profile).data
    })


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_profile(request):
    """
    Update current user profile and financial profile
    """
    user = request.user
    
    try:
        # Update user fields
        if 'first_name' in request.data:
            user.first_name = request.data['first_name']
        if 'last_name' in request.data:
            user.last_name = request.data['last_name']
        if 'email' in request.data:
            # Check if email is already taken by another user
            if User.objects.filter(email=request.data['email']).exclude(id=user.id).exists():
                return Response(
                    {'error': 'Email already taken'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            user.email = request.data['email']
        
        user.save()
        
        # Get or create profile
        profile, created = Profile.objects.get_or_create(user=user)
        
        # Update profile fields
        if 'birth_date' in request.data:
            from datetime import datetime
            if request.data['birth_date']:
                # Convert string to date object
                birth_date_str = request.data['birth_date']
                if isinstance(birth_date_str, str):
                    profile.birth_date = datetime.strptime(birth_date_str, '%Y-%m-%d').date()
                else:
                    profile.birth_date = birth_date_str
        if 'country' in request.data:
            profile.country = request.data['country']
        if 'base_currency' in request.data:
            profile.base_currency = request.data['base_currency']
        if 'marginal_tax_rate_pct' in request.data:
            profile.marginal_tax_rate_pct = request.data['marginal_tax_rate_pct']
        if 'risk_profile' in request.data:
            profile.risk_profile = request.data['risk_profile']
        if 'target_retirement_age' in request.data:
            profile.target_retirement_age = request.data['target_retirement_age']
        
        profile.save()
        
        return Response({
            'user': UserSerializer(user).data,
            'profile': ProfileSerializer(profile).data
        })
        
    except Exception as e:
        return Response(
            {'error': f'Profile update failed: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
