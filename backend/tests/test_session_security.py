import time

import pytest
from accounts.models import User
from django.conf import settings
from django.contrib.sessions.models import Session
from django.urls import reverse

pytestmark = pytest.mark.django_db


def create_citizen():
    return User.objects.create_user(
        "citizen@example.com", "+919000000001", "Citizen One", "StrongPass2026!"
    )


def test_idle_session_is_rejected_on_the_next_request(client):
    user = create_citizen()
    client.force_login(user)
    session = client.session
    session["_scms_last_activity_epoch"] = time.time() - settings.SESSION_IDLE_TIMEOUT_SECONDS - 1
    session.save()

    response = client.get(reverse("dashboard"))

    assert response.status_code == 302
    assert response.url == reverse("login")


def test_active_session_activity_is_refreshed(client):
    user = create_citizen()
    client.force_login(user)

    response = client.get(reverse("dashboard"))

    assert response.status_code == 200
    assert client.session["_scms_last_activity_epoch"] <= time.time()


def test_role_change_revokes_existing_sessions(client):
    user = create_citizen()
    client.force_login(user)
    session_key = client.session.session_key
    assert Session.objects.filter(session_key=session_key).exists()

    user.role = User.Role.STAFF
    user.save()

    assert not Session.objects.filter(session_key=session_key).exists()
