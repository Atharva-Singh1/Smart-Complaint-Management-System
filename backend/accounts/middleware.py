"""Session-security middleware for the local Django session strategy."""

import time

from django.conf import settings
from django.contrib.auth import logout


class IdleSessionTimeoutMiddleware:
    """Invalidate an authenticated session after the configured idle period."""

    activity_key = "_scms_last_activity_epoch"

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            now = time.time()
            last_activity = request.session.get(self.activity_key)
            try:
                expired = (
                    last_activity is not None
                    and now - float(last_activity) >= settings.SESSION_IDLE_TIMEOUT_SECONDS
                )
            except (TypeError, ValueError):
                expired = True

            if expired:
                logout(request)
            else:
                request.session[self.activity_key] = now

        return self.get_response(request)
