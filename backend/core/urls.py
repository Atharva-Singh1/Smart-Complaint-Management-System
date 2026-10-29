from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("register/", views.register, name="register"),
    path("login/", views.sign_in, name="login"),
    path("logout/", views.sign_out, name="logout"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("complaints/new/", views.lodge_complaint, name="lodge_complaint"),
    path("track/", views.track, name="track"),
    path("complaints/<str:tracking_id>/", views.complaint_detail, name="complaint_detail"),
]
