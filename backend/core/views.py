from accounts.forms import RegistrationForm
from accounts.models import User
from accounts.services import authenticate_credentials
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

from .forms import ComplaintForm
from .models import Complaint, Evidence


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
    if request.user.role != User.Role.CITIZEN:
        return render(request, "core/dashboard.html", {"complaints": []})
    return render(
        request,
        "core/dashboard.html",
        {"complaints": Complaint.objects.filter(citizen=request.user)},
    )


@login_required
@require_http_methods(["GET", "POST"])
def lodge_complaint(request):
    if request.user.role != User.Role.CITIZEN:
        messages.error(request, "Only citizen accounts can lodge complaints.")
        return redirect("dashboard")
    form = ComplaintForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        complaint = Complaint.create_with_tracking_id(
            citizen=request.user,
            category=form.cleaned_data["category"],
            title=form.cleaned_data["title"],
            description=form.cleaned_data["description"],
            ward=form.cleaned_data["ward"],
        )
        for file in form.cleaned_data["evidence_files"]:
            Evidence.objects.create(complaint=complaint, file=file)
        messages.success(
            request, f"Complaint submitted. Your tracking ID is {complaint.tracking_id}."
        )
        return redirect("dashboard")
    return render(request, "core/lodge.html", {"form": form})


@require_http_methods(["GET", "POST"])
def track(request):
    tracking_id = request.POST.get("tracking_id") or request.GET.get("tracking_id")
    complaint = None
    if tracking_id:
        complaint = Complaint.objects.filter(tracking_id__iexact=tracking_id.strip()).first()
        if complaint is None:
            messages.error(request, "No complaint was found for that tracking ID.")
    return render(
        request, "core/track.html", {"complaint": complaint, "tracking_id": tracking_id or ""}
    )


@login_required
def complaint_detail(request, tracking_id):
    complaint = get_object_or_404(
        Complaint.objects.select_related("citizen", "assigned_to").prefetch_related(
            "history", "evidence"
        ),
        tracking_id=tracking_id,
    )
    if request.user.role == User.Role.CITIZEN and complaint.citizen_id != request.user.id:
        raise Http404
    return render(request, "core/complaint_detail.html", {"complaint": complaint})
