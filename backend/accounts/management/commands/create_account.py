from getpass import getpass

from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError

from accounts.models import User


class Command(BaseCommand):
    help = "Provision an account interactively; never put passwords in command arguments."

    def add_arguments(self, parser):
        parser.add_argument("--email", required=True)
        parser.add_argument("--phone", required=True)
        parser.add_argument("--name", required=True)
        parser.add_argument("--role", choices=User.Role.values, default="citizen")

    def handle(self, *args, **options):
        password = getpass("Password: ")
        if password != getpass("Confirm password: "):
            raise CommandError("Passwords do not match")
        try:
            validate_password(password)
            User.objects.create_user(
                options["email"],
                options["phone"],
                options["name"],
                password,
                role=options["role"],
            )
        except ValidationError as exc:
            raise CommandError("Invalid or duplicate account details") from exc
        self.stdout.write("Account created")
