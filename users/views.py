from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from authentication.serializers import UserSerializer, ChangePasswordSerializer
from .serializers import UserListSerializer, UserCreateSerializer, UserUpdateSerializer

User = get_user_model()


class UserListCreateView(generics.ListCreateAPIView):
    """List all non-superuser users and create new users"""
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Return only non-superuser users (is_superuser=False)
        return User.objects.filter(is_superuser=False).order_by('email')

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return UserCreateSerializer
        return UserListSerializer

    def create(self, request, *args, **kwargs):
        """Create a new user with the provided data"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Return the created user data using the list serializer
        response_serializer = UserListSerializer(user)
        return Response({
            'success': True,
            'message': 'User created successfully',
            'data': response_serializer.data
        }, status=status.HTTP_201_CREATED)


class UserDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update or delete a specific user"""
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Return only non-superuser users
        return User.objects.filter(is_superuser=False)

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return UserUpdateSerializer
        return UserListSerializer

    def update(self, request, *args, **kwargs):
        """Override update to return success message with updated user data"""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()

        # Use update serializer for validation and updating
        update_serializer = UserUpdateSerializer(instance, data=request.data, partial=partial)
        update_serializer.is_valid(raise_exception=True)
        updated_instance = update_serializer.save()

        # Return full user data using the list serializer
        response_serializer = UserListSerializer(updated_instance)
        return Response({
            'success': True,
            'message': 'User updated successfully',
            'data': response_serializer.data
        }, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        """Override destroy to return success message"""
        instance = self.get_object()
        user_email = instance.email
        user_id = str(instance.id)

        # Perform the deletion
        self.perform_destroy(instance)

        # Return success message
        return Response({
            "success": True,
            "message": f"User '{user_email}' has been successfully deleted.",
            "deleted_user_id": user_id
        }, status=status.HTTP_200_OK)


class UserProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    
    def get_object(self):
        return self.request.user


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def change_password(request):
    serializer = ChangePasswordSerializer(data=request.data)
    if serializer.is_valid():
        user = request.user
        
        # Check old password
        if not user.check_password(serializer.validated_data['old_password']):
            return Response({'error': 'Invalid old password'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Set new password
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        
        return Response({'message': 'Password changed successfully'}, status=status.HTTP_200_OK)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_avatar(request):
    """Update user avatar with base64 encoded image"""
    user = request.user
    avatar = request.data.get('avatar')

    if not avatar:
        return Response({'error': 'Avatar data is required'}, status=status.HTTP_400_BAD_REQUEST)

    # Update avatar
    user.avatar = avatar
    user.save()

    # Return updated user data
    serializer = UserSerializer(user)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_account(request):
    user = request.user
    user.is_active = False
    user.save()
    return Response({'message': 'Account deactivated successfully'}, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_operators(request):
    """Get list of users with role='supplier' for tour operator dropdown"""
    operators = User.objects.filter(role='supplier', is_active=True).order_by('full_name')

    # Return simplified data for dropdown
    operators_data = [
        {
            'id': str(operator.id),
            'full_name': operator.full_name,
            'email': operator.email
        }
        for operator in operators
    ]

    return Response(operators_data, status=status.HTTP_200_OK)
