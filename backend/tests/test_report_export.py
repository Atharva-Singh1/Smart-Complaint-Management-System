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


def create_complaint(citizen, title):
    return Complaint.create_with_tracking_id(
        citizen=citizen,
        category=Complaint.Category.WATER,
        title=title,
        description="Water has not been available since morning.",
        ward="Ward 12",
    )


def test_staff_can_export_date_bounded_csv_report(client):
    staff = create_user(User.Role.STAFF, 1)
    citizen = create_user(User.Role.CITIZEN, 2)
    complaint = create_complaint(citizen, "Water pipeline issue")
    client.force_login(staff)

    response = client.get(
        reverse("complaint_report"),
        {"format": "csv", "start_date": complaint.created_at.date(), "end_date": complaint.created_at.date()},
    )

    assert response.status_code == 200
    assert response["Content-Type"].startswith("text/csv")
    assert complaint.tracking_id in response.content.decode()


def test_staff_can_export_pdf_report(client):
    staff = create_user(User.Role.STAFF, 3)
    citizen = create_user(User.Role.CITIZEN, 4)
    complaint = create_complaint(citizen, "Road damage issue")
    client.force_login(staff)

    response = client.get(
        reverse("complaint_report"),
        {"format": "pdf", "start_date": complaint.created_at.date(), "end_date": complaint.created_at.date()},
    )

    assert response.status_code == 200
    assert response["Content-Type"] == "application/pdf"
    assert response.content.startswith(b"%PDF")


def test_citizen_cannot_export_reports(client):
    citizen = create_user(User.Role.CITIZEN, 5)
    client.force_login(citizen)

    response = client.get(reverse("complaint_report"))

    assert response.status_code == 403
