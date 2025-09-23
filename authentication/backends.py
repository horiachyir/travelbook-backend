from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model

User = get_user_model()


class EmailBackend(ModelBackend):
    """
    Email authentication backend for custom User model
    """

    def authenticate(self, request, username=None, password=None, email=None, **kwargs):
        # Support both 'username' and 'email' parameters
        email = email or username

        if email is None or password is None:
            return None

        try:
            # Normalize email to lowercase for consistent lookup
            email = email.lower()
            user = User.objects.get(email__iexact=email)

            # Check password
            if user.check_password(password):
                return user

        except User.DoesNotExist:
            # Run the default password hasher once to reduce the timing
            # difference between an existing and a nonexistent user
            User().set_password(password)
            return None

        return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None