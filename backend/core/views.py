from accounts.forms import RegistrationForm
from accounts.services import authenticate_credentials
from django.contrib import messages
from django.contrib.auth import login, logout
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods


def home(request):
    return render(request, "core/home.html")


@require_http_methods(["GET", "POST"])
def register(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    form = RegistrationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user, backend="django.contrib.auth.backends.ModelBackend")
        messages.success(request, "Your citizen account has been created.")
        return redirect("dashboard")
    return render(request, "core/register.html", {"form": form})


@require_http_methods(["GET", "POST"])
def sign_in(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    if request.method == "POST":
        user = authenticate_credentials(
            request.POST.get("identifier", ""), request.POST.get("password", "")
        )
        if user:
            login(request, user, backend="django.contrib.auth.backends.ModelBackend")
            return redirect("dashboard")
        messages.error(request, "Unable to sign in with these credentials.")
    return render(request, "core/login.html")


@require_http_methods(["POST"])
def sign_out(request):
    logout(request)
    return redirect("home")


def dashboard(request):
    if not request.user.is_authenticated:
        return redirect("login")
    return render(request, "core/dashboard.html")
