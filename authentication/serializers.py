from rest_framework import serializers
from django.contrib.auth import get_user_model, authenticate
from django.contrib.auth.password_validation import validate_password

User = get_user_model()


class SignUpSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])
    confirm_password = serializers.CharField(write_only=True, required=False)
    fullName = serializers.CharField(source='full_name', max_length=255)
    
    class Meta:
        model = User
        fields = ('email', 'fullName', 'password', 'confirm_password', 'phone')
        extra_kwargs = {
            'phone': {'required': False}
        }
    
    def validate(self, attrs):
        # Check if confirm_password is provided and validate it
        confirm_password = attrs.pop('confirm_password', None)
        if confirm_password and attrs.get('password') != confirm_password:
            raise serializers.ValidationError("Passwords don't match")
        return attrs
    
    def create(self, validated_data):
        # Extract password and create user
        password = validated_data.pop('password')
        user = User.objects.create_user(
            email=validated_data['email'],
            full_name=validated_data['full_name'],
            password=password,
            phone=validated_data.get('phone')
        )
        return user


class SignInSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    
    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')
        
        if email and password:
            user = authenticate(email=email, password=password)
            if not user:
                raise serializers.ValidationError('Invalid credentials')
            if not user.is_active:
                raise serializers.ValidationError('User account is disabled')
            attrs['user'] = user
            return attrs
        raise serializers.ValidationError('Must include email and password')


class UserSerializer(serializers.ModelSerializer):
    fullName = serializers.CharField(source='full_name')
    isVerified = serializers.BooleanField(source='is_verified', read_only=True)
    isSuperuser = serializers.BooleanField(source='is_superuser', read_only=True)
    dateJoined = serializers.DateTimeField(source='date_joined', read_only=True)

    class Meta:
        model = User
        fields = ('id', 'email', 'fullName', 'phone', 'isVerified', 'isSuperuser',
                  'role', 'dateJoined', 'avatar', 'language', 'timezone')
        read_only_fields = ('id', 'email', 'dateJoined', 'isVerified', 'isSuperuser', 'role')


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()


class PasswordResetSerializer(serializers.Serializer):
    token = serializers.CharField()
    password = serializers.CharField(write_only=True, validators=[validate_password])
    confirm_password = serializers.CharField(write_only=True)
    
    def validate(self, attrs):
        if attrs['password'] != attrs['confirm_password']:
            raise serializers.ValidationError("Passwords don't match")
        return attrs


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, validators=[validate_password])
    confirm_password = serializers.CharField(write_only=True)
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError("Passwords don't match")
        return attrs
