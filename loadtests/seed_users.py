"""Create synthetic citizen accounts for load tests (issues #20 and #22).

Run from the backend folder, against a TEST database only:

    python manage.py shell -c "exec(open('../loadtests/seed_users.py').read())"

Set LOADTEST_USERS (default 500). Never run this against production data.
"""

import os

from accounts.models import User

COUNT = int(os.getenv("LOADTEST_USERS", "500"))
PASSWORD = "LoadTest2026!Pass"

created = 0
for n in range(COUNT):
    email = f"loadtest{n}@example.com"
    if not User.objects.filter(email=email).exists():
        User.objects.create_user(email, f"+91700{n:07d}", f"Load Test {n}", PASSWORD)
        created += 1
print(f"Created {created} new load-test users ({COUNT} total expected).")
