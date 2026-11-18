"""Small, unauthenticated readiness endpoint for external availability monitors."""

from django.db import connection
from django.utils import timezone


def readiness_payload():
    """Return the minimum safe payload needed by an uptime monitor.

    The query verifies that Django can obtain a connection and the database can
    execute work.  It deliberately contains no user, complaint, or deployment
    data, because this endpoint is publicly reachable.
    """
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1")
        cursor.fetchone()
    return {"status": "ok", "checked_at": timezone.now().isoformat()}
