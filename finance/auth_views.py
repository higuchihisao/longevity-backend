from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from django.contrib.auth import authenticate
from django.contrib.auth import get_user_model
from .serializers import UserSerializer, ProfileSerializer
from .models import Profile

User = get_user_model()


class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Custom login view that returns user data along with tokens
    """
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        
        if response.status_code == 200:
            # Get user data
            email = request.data.get('email')
            try:
                user = User.objects.get(email=email)
                user_data = UserSerializer(user).data
                response.data['user'] = user_data
            except User.DoesNotExist:
                pass
        
        return response


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


@api_view(['POST'])
@permission_classes([AllowAny])
def logout(request):
    """
    Logout user by blacklisting the refresh token
    """
    try:
        refresh_token = request.data.get('refresh')
        if refresh_token:
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({'message': 'Successfully logged out'}, status=status.HTTP_200_OK)
        else:
            return Response(
                {'error': 'Refresh token is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
    except Exception as e:
        return Response(
            {'error': f'Logout failed: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


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
