from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from .models import Account
from .serializers import AccountSerializer
from django.contrib.auth import get_user_model

User = get_user_model()


@api_view(['POST'])
@permission_classes([AllowAny])
def test_create_account(request):
    """
    Test endpoint to create account without authentication
    """
    try:
        # Get the first user for testing
        user = User.objects.first()
        if not user:
            return Response(
                {'error': 'No users found'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create account
        account = Account.objects.create(
            user=user,
            name=request.data.get('name', 'Test Account'),
            type=request.data.get('type', 'BROKERAGE'),
            broker=request.data.get('broker', 'Test Broker'),
            currency=request.data.get('currency', 'USD'),
            opening_balance=request.data.get('opening_balance', 1000.00),
            current_balance=request.data.get('current_balance', 1000.00)
        )
        
        serializer = AccountSerializer(account)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        return Response(
            {'error': f'Error creating account: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
