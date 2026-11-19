"""Locust load test for SCMS.

Covers
  * Issue #20 / SCMS-NF-001 / TC-PERF-01: 90% of requests under 2 s at 200 users
  * Issue #22 / SCMS-NF-003 / TC-SCALE-01: 500 concurrent authenticated sessions

Setup (test environment only; use synthetic data):
    pip install locust
    cd backend && python manage.py migrate
    python manage.py shell -c "exec(open('../loadtests/seed_users.py').read())"
    python manage.py runserver            # or the real deployment under test

#20 (200 users, 5 min, headless, writes CSV + HTML evidence):
    locust -f loadtests/locustfile.py --host http://127.0.0.1:8000 \
      -u 200 -r 20 -t 5m --headless --csv results/perf --html results/perf.html

#22 (500 sessions held concurrently):
    locust -f loadtests/locustfile.py --host http://127.0.0.1:8000 \
      -u 500 -r 25 -t 10m --headless --csv results/scale --html results/scale.html

Read the "90%" column of results/*_stats.csv: it must be < 2000 ms. Results from a
laptop dev server are NOT acceptance evidence; run against the staging deployment.
"""

import itertools
import random
import re

from locust import HttpUser, between, task

PASSWORD = "LoadTest2026!Pass"
USER_IDS = itertools.count()  # each simulated user gets its own account
USER_POOL = int(__import__("os").getenv("LOADTEST_USERS", "500"))


def csrf_token(client):
    return client.cookies.get("csrftoken", "")


class Citizen(HttpUser):
    wait_time = between(1, 3)

    def on_start(self):
        n = next(USER_IDS) % USER_POOL
        self.client.get("/login/", name="GET /login/")
        with self.client.post(
            "/login/",
            data={
                "identifier": f"loadtest{n}@example.com",
                "password": PASSWORD,
                "csrfmiddlewaretoken": csrf_token(self.client),
            },
            name="POST /login/",
            allow_redirects=False,
            catch_response=True,
        ) as response:
            if response.status_code != 302:
                response.failure(f"login failed: {response.status_code}")
        self.tracking_ids = []

    @task(5)
    def dashboard(self):
        self.client.get("/dashboard/", name="GET /dashboard/")

    @task(3)
    def public_track(self):
        self.client.get("/track/?tracking_id=NOPE-0000", name="GET /track/")

    @task(2)
    def lodge_complaint(self):
        page = self.client.get("/complaints/new/", name="GET /complaints/new/")
        token = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', page.text)
        with self.client.post(
            "/complaints/new/",
            data={
                "category": "water",
                "title": f"Load test complaint {random.randint(1, 10**6)}",
                "description": "Synthetic complaint created by the load test.",
                "ward": f"Ward {random.randint(1, 30)}",
                "csrfmiddlewaretoken": token.group(1) if token else csrf_token(self.client),
            },
            name="POST /complaints/new/",
            allow_redirects=False,
            catch_response=True,
        ) as response:
            if response.status_code not in (200, 302):
                response.failure(f"lodge failed: {response.status_code}")

    @task(1)
    def health(self):
        self.client.get("/health/", name="GET /health/")
