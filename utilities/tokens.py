import six
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from users.models import User


class AccountActivationTokenGenerator(PasswordResetTokenGenerator):

    def _make_hash_value(self, user, timestamp):
        is_active = six.text_type(user.is_active)
        pk = six.text_type(user.pk)
        role = six.text_type(user.role)
        if isinstance(user.role, User.Roles):
            role = six.text_type(user.role.value)
        ts = six.text_type(timestamp)
        return is_active + pk + role + ts


accountActivationTokenGenerator = AccountActivationTokenGenerator()
