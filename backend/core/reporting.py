"""Bounded complaint report generation for SCMS-F-019."""

import csv
from datetime import date
from io import BytesIO, StringIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

MAX_REPORT_ROWS = 10_000


class ReportFilterError(ValueError):
    pass


class ReportLimitError(ValueError):
    pass


def filtered_complaints(queryset, *, start_date_text, end_date_text, status):
    """Require bounded ISO dates and limit report materialisation to 10,000 rows."""
    try:
        start_date = date.fromisoformat(start_date_text)
        end_date = date.fromisoformat(end_date_text)
    except (TypeError, ValueError) as error:
        raise ReportFilterError("Start date and end date must use YYYY-MM-DD.") from error
    if start_date > end_date:
        raise ReportFilterError("Start date must not be after end date.")

    reports = queryset.filter(created_at__date__gte=start_date, created_at__date__lte=end_date)
    if status:
        reports = reports.filter(status=status)
    rows = list(reports.order_by("created_at").select_related("assigned_to")[: MAX_REPORT_ROWS + 1])
    if len(rows) > MAX_REPORT_ROWS:
        raise ReportLimitError("Refine the date range or status: reports are limited to 10,000 rows.")
    return rows


def report_rows(complaints):
    for complaint in complaints:
        yield [
            complaint.tracking_id,
            complaint.created_at.strftime("%Y-%m-%d %H:%M"),
            complaint.get_category_display(),
            complaint.ward,
            complaint.get_status_display(),
            complaint.assigned_to.full_name if complaint.assigned_to else "Unassigned",
        ]


def csv_content(complaints):
    output = StringIO(newline="")
    writer = csv.writer(output)
    writer.writerow(["Tracking ID", "Submitted", "Category", "Ward", "Status", "Assigned to"])
    writer.writerows(report_rows(complaints))
    return output.getvalue()


def pdf_content(complaints, *, start_date_text, end_date_text):
    output = BytesIO()
    document = SimpleDocTemplate(
        output,
        pagesize=landscape(A4),
        leftMargin=1.2 * cm,
        rightMargin=1.2 * cm,
        topMargin=1.2 * cm,
        bottomMargin=1.2 * cm,
    )
    styles = getSampleStyleSheet()
    data = [["Tracking ID", "Submitted", "Category", "Ward", "Status", "Assigned to"]]
    data.extend(report_rows(complaints))
    table = Table(data, repeatRows=1, colWidths=[4.2 * cm, 3.2 * cm, 3.6 * cm, 3.0 * cm, 3.0 * cm, 4.2 * cm])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1d4f91")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#b7c7dc")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#eef4fb")]),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    document.build([
        Paragraph("SCMS Complaint Report", styles["Title"]),
        Spacer(1, 0.25 * cm),
        Paragraph(f"Reporting period: {start_date_text} to {end_date_text}", styles["Normal"]),
        Spacer(1, 0.35 * cm),
        table,
    ])
    return output.getvalue()
