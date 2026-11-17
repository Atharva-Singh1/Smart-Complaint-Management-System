import pytest
from accounts.models import User
from core.models import Complaint
from django.urls import reverse

pytestmark = pytest.mark.django_db


def create_user(role, number):
    return User.objects.create_user(
        f"{role}{number}@example.com",
        f"+9190000000{number:02d}",
        f"{role.title()} {number}",
        "StrongPass2026!",
        role=role,
    )


def test_anonymous_user_is_redirected_to_login_for_triage(client):
    response = client.get(reverse("triage"))

    assert response.status_code == 302
    assert response.url.startswith(reverse("login"))


def test_citizen_is_denied_access_to_staff_triage(client):
    citizen = create_user(User.Role.CITIZEN, 1)
    client.force_login(citizen)

    response = client.get(reverse("triage"))

    assert response.status_code == 403


@pytest.mark.parametrize("role", [User.Role.STAFF, User.Role.ADMIN])
def test_staff_and_admin_can_access_triage(client, role):
    user = create_user(role, 2 if role == User.Role.STAFF else 3)
    client.force_login(user)

    response = client.get(reverse("triage"))

    assert response.status_code == 200


def test_citizen_is_denied_access_to_complaint_management(client):
    citizen = create_user(User.Role.CITIZEN, 4)
    complaint = Complaint.create_with_tracking_id(
        citizen=citizen,
        category=Complaint.Category.WATER,
        title="Water supply issue",
        description="Water has not been available since morning.",
        ward="Ward 12",
    )
    client.force_login(citizen)

    response = client.get(reverse("manage_complaint", args=[complaint.tracking_id]))

    assert response.status_code == 403


@pytest.mark.parametrize("role", [User.Role.STAFF, User.Role.ADMIN])
def test_staff_and_admin_can_manage_a_complaint(client, role):
    citizen = create_user(User.Role.CITIZEN, 5)
    manager = create_user(role, 6 if role == User.Role.STAFF else 7)
    complaint = Complaint.create_with_tracking_id(
        citizen=citizen,
        category=Complaint.Category.WATER,
        title="Water supply issue",
        description="Water has not been available since morning.",
        ward="Ward 12",
    )
    client.force_login(manager)

    response = client.get(reverse("manage_complaint", args=[complaint.tracking_id]))

    assert response.status_code == 200


@pytest.mark.parametrize("role", [User.Role.STAFF, User.Role.ADMIN])
def test_only_citizens_can_lodge_complaints(client, role):
    user = create_user(role, 8 if role == User.Role.STAFF else 9)
    client.force_login(user)

    response = client.get(reverse("lodge_complaint"))

    assert response.status_code == 403
