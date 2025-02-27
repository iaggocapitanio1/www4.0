from django.contrib.auth.backends import BaseBackend
from users.models import User


class EmailOrUsernameBackend(BaseBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            # Check if the user is trying to log in with their email address
            user = User.objects.get(email=username)
        except User.DoesNotExist:
            try:
                # If not, check if they are trying to log in with their username
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                # If the user does not exist, return None
                return None

        # Verify the password and return the user if the password is correct
        if user.check_password(password):
            return user

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
