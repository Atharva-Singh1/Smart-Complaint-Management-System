from datetime import timedelta

from django.contrib.auth.hashers import check_password, make_password
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from .models import LockoutEmail, User

# A real-cost dummy check prevents the missing-account fast path.
DUMMY_HASH = make_password("not-a-user-credential")


def authenticate_credentials(identifier, password):
    with transaction.atomic():
        user = (
            User.objects.select_for_update()
            .filter(Q(email__iexact=identifier.strip()) | Q(phone=identifier.strip()))
            .first()
        )
        now = timezone.now()
        if user is None:
            check_password(password, DUMMY_HASH)
            return None
        if not user.is_active or (user.locked_until and user.locked_until > now):
            check_password(password, DUMMY_HASH)
            return None
        if user.locked_until:
            user.failed_attempts = 0
            user.locked_until = None
        if not user.check_password(password):
            user.failed_attempts += 1
            if user.failed_attempts >= 5:
                user.locked_until = now + timedelta(minutes=30)
                LockoutEmail.objects.create(user=user, locked_until=user.locked_until)
            user.save(update_fields=["failed_attempts", "locked_until"])
            return None
        user.failed_attempts = 0
        user.locked_until = None
        user.save(update_fields=["failed_attempts", "locked_until"])
        return user
