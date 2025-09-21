from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.models import User
from django.db.models import Q

from .models import ParentProfile

class UsernameEmailPhoneBackend(ModelBackend):
    """Authenticate with username OR email OR parent's phone number."""
    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None or password is None:
            return None
        user = None
        # Try by username or email first
        try:
            user = User.objects.get(Q(username__iexact=username) | Q(email__iexact=username))
        except User.DoesNotExist:
            # Try by phone via ParentProfile
            try:
                parent = ParentProfile.objects.select_related('user').get(phone_number=username)
                user = parent.user
            except ParentProfile.DoesNotExist:
                return None
        if user and user.check_password(password):
            return user
        return None
