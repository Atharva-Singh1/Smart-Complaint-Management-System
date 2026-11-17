import pytest
from accounts.models import User
from django.urls import reverse

pytestmark = pytest.mark.django_db


def test_citizen_registration(client):
    response = client.post(
        reverse("register"),
        {
            "full_name": "Citizen One",
            "email": "citizen@example.com",
            "phone": "+919000000001",
            "password": "StrongPass2026!",
            "confirm_password": "StrongPass2026!",
        },
    )
    assert response.status_code == 302
    assert User.objects.get(email="citizen@example.com").role == User.Role.CITIZEN


def test_five_failed_logins_lock_the_account(client):
    user = User.objects.create_user(
        "citizen@example.com", "+919000000001", "Citizen One", "StrongPass2026!"
    )
    for _ in range(5):
        assert (
            client.post(
                reverse("login"), {"identifier": user.email, "password": "wrong"}
            ).status_code
            == 200
        )
    user.refresh_from_db()
    assert user.locked_until is not None


def test_staff_account_can_log_in(client):
    user = User.objects.create_user(
        "staff@example.com", "+919000000002", "Staff One", "StrongPass2026!", role=User.Role.STAFF
    )
    response = client.post(
        reverse("login"), {"identifier": user.email, "password": "StrongPass2026!"}
    )
    assert response.status_code == 302


def test_passwords_use_salted_argon2id_hashes():
    first = User.objects.create_user(
        "first@example.com", "+919000000003", "First Citizen", "StrongPass2026!"
    )
    second = User.objects.create_user(
        "second@example.com", "+919000000004", "Second Citizen", "StrongPass2026!"
    )

    assert first.password.startswith("argon2$")
    assert second.password.startswith("argon2$")
    assert first.password != "StrongPass2026!"
    assert first.password != second.password
    assert first.check_password("StrongPass2026!")
