import pytest
from django.db import OperationalError
from django.urls import reverse


pytestmark = pytest.mark.django_db


def test_health_endpoint_reports_ready(client):
    response = client.get(reverse("health"))

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert "checked_at" in response.json()


def test_health_endpoint_reports_service_unavailable_when_database_is_down(client, monkeypatch):
    def unavailable():
        raise OperationalError("database unavailable")

    monkeypatch.setattr("core.views.readiness_payload", unavailable)

    response = client.get(reverse("health"))

    assert response.status_code == 503
    assert response.json() == {"status": "unavailable"}
