from functools import wraps

from accounts.forms import RegistrationForm
from accounts.models import User
from accounts.services import authenticate_credentials
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.core.exceptions import PermissionDenied
from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

from .forms import AssignmentForm, ComplaintForm, StatusForm
from django.db import DatabaseError
from .health import readiness_payload
from .models import AssignmentEmail, Complaint, Evidence, RejectionEmail, ResolutionProof
from .reporting import ReportFilterError, ReportLimitError, csv_content, filtered_complaints, pdf_content


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
        return redirect("triage")
    return render(
        request,
        "core/dashboard.html",
        {"complaints": Complaint.objects.filter(citizen=request.user)},
    )


@login_required
@require_http_methods(["GET", "POST"])
def lodge_complaint(request):
    if request.user.role != User.Role.CITIZEN:
        raise PermissionDenied("Only citizen accounts can lodge complaints.")
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
    if request.method == "POST":
        evidence_errors = form.errors.as_data().get("evidence_files", [])
        if any(error.code == "unsupported_media_type" for error in evidence_errors):
            return render(request, "core/lodge.html", {"form": form}, status=415)
    return render(request, "core/lodge.html", {"form": form})


@require_http_methods(["GET", "POST"])
def track(request):
    tracking_id = request.POST.get("tracking_id") or request.GET.get("tracking_id")
    complaint = None
    if tracking_id:
        tracking_id = tracking_id.strip()[:64]
        complaint = Complaint.objects.filter(tracking_id__iexact=tracking_id).first()
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


def staff_or_admin(user):
    return user.is_authenticated and user.role in {User.Role.STAFF, User.Role.ADMIN}


def staff_or_admin_required(view):
    """Return HTTP 403 when an authenticated user lacks a privileged role."""

    @wraps(view)
    def wrapped(request, *args, **kwargs):
        if not staff_or_admin(request.user):
            raise PermissionDenied("Staff or Administrator access is required.")
        return view(request, *args, **kwargs)

    return wrapped


@login_required
@staff_or_admin_required
def triage(request):
    complaints = Complaint.objects.select_related("citizen", "assigned_to")
    status = request.GET.get("status")
    ward = request.GET.get("ward")
    if status:
        complaints = complaints.filter(status=status)
    if ward:
        complaints = complaints.filter(ward__icontains=ward)
    return render(
        request,
        "core/triage.html",
        {"complaints": complaints, "statuses": Complaint.Status.choices},
    )


@login_required
@staff_or_admin_required
@require_http_methods(["GET", "POST"])
def manage_complaint(request, tracking_id):
    complaint = get_object_or_404(
        Complaint.objects.select_related("citizen", "assigned_to"), tracking_id=tracking_id
    )
    assignment_form = AssignmentForm(request.POST or None, prefix="assign")
    status_form = StatusForm(request.POST or None, request.FILES or None, prefix="status")
    if request.method == "POST":
        if "assign-submit" in request.POST and assignment_form.is_valid():
            with transaction.atomic():
                complaint.assigned_to = assignment_form.cleaned_data["assigned_to"]
                complaint.internal_note = assignment_form.cleaned_data["internal_note"]
                complaint.save(update_fields=["assigned_to", "internal_note", "updated_at"])
                complaint.change_status(
                    actor=request.user,
                    new_status=Complaint.Status.ASSIGNED,
                    note="Assigned to department staff",
                )
                AssignmentEmail.objects.create(complaint=complaint, assignee=complaint.assigned_to)
            messages.success(request, "Complaint assigned successfully.")
            return redirect("manage_complaint", tracking_id=tracking_id)
        if "status-submit" in request.POST and status_form.is_valid():
            new_status = status_form.cleaned_data["status"]
            note = status_form.cleaned_data["note"]
            proof_image = status_form.cleaned_data["proof_image"]
            rejection_code = status_form.cleaned_data["rejection_code"]
            if new_status == Complaint.Status.RESOLVED and len(note.strip()) < 20:
                status_form.add_error(
                    "note", "A resolution note of at least 20 characters is required."
                )
            elif (
                new_status == Complaint.Status.RESOLVED
                and proof_image is None
                and not complaint.resolution_proofs.exists()
            ):
                status_form.add_error("proof_image", "At least one proof image is required.")
            elif new_status == Complaint.Status.REJECTED and not note.strip():
                status_form.add_error("note", "A rejection reason is required.")
            elif new_status == Complaint.Status.REJECTED and not rejection_code:
                status_form.add_error("rejection_code", "A justification code is required.")
            else:
                with transaction.atomic():
                    if new_status == Complaint.Status.RESOLVED:
                        complaint.resolution_note = note
                        if proof_image is not None:
                            ResolutionProof.objects.create(
                                complaint=complaint, image=proof_image, uploaded_by=request.user
                            )
                    if new_status == Complaint.Status.REJECTED:
                        complaint.rejection_reason = note
                        complaint.rejection_code = rejection_code
                    complaint.save(
                        update_fields=["resolution_note", "rejection_reason", "rejection_code", "updated_at"]
                    )
                    complaint.change_status(actor=request.user, new_status=new_status, note=note)
                    if new_status == Complaint.Status.REJECTED:
                        RejectionEmail.objects.create(complaint=complaint, citizen=complaint.citizen)
                messages.success(request, "Complaint status updated.")
                return redirect("manage_complaint", tracking_id=tracking_id)
    return render(
        request,
        "core/manage_complaint.html",
        {"complaint": complaint, "assignment_form": assignment_form, "status_form": status_form},
    )
from functools import wraps

@login_required
@staff_or_admin_required
@require_http_methods(["GET"])
def complaint_report(request):
    context = {
        "statuses": Complaint.Status.choices,
        "start_date": request.GET.get("start_date", ""),
        "end_date": request.GET.get("end_date", ""),
        "selected_status": request.GET.get("status", ""),
    }
    report_format = request.GET.get("format")
    if not report_format:
        return render(request, "core/reports.html", context)
    if report_format not in {"csv", "pdf"}:
        return render(request, "core/reports.html", {**context, "error": "Select CSV or PDF."}, status=400)
    try:
        complaints = filtered_complaints(
            Complaint.objects.all(),
            start_date_text=context["start_date"],
            end_date_text=context["end_date"],
            status=context["selected_status"],
        )
    except (ReportFilterError, ReportLimitError) as error:
        return render(request, "core/reports.html", {**context, "error": str(error)}, status=400)
    filename = f"scms-complaints-{context['start_date']}-to-{context['end_date']}"
    if report_format == "csv":
        response = HttpResponse(csv_content(complaints), content_type="text/csv; charset=utf-8")
        response["Content-Disposition"] = f'attachment; filename="{filename}.csv"'
        return response
    response = HttpResponse(
        pdf_content(complaints, start_date_text=context["start_date"], end_date_text=context["end_date"]),
        content_type="application/pdf",
    )
    response["Content-Disposition"] = f'attachment; filename="{filename}.pdf"'
    return response


@require_http_methods(["GET"])
def health(request):
    """Public readiness endpoint used only by uptime monitoring."""
    try:
        return JsonResponse(readiness_payload())
    except DatabaseError:
        return JsonResponse({"status": "unavailable"}, status=503)
