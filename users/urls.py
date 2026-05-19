from django.urls import path
from . import views

app_name = "users"

urlpatterns = [
    path('generate-resume/', views.generate_resume, name='generate_resume'),
    path('register/', views.register, name='register'),
    path("upload/", views.upload_resume, name="upload_resume"),
    path(
        "analyze/",
        views.analyze_resume,
        name="analyze_resume"
    ),
    path(
        "resume/<int:resume_id>/",
        views.resume_detail,
        name="resume_detail"
    ),
    path(
        "resume/<int:resume_id>/update-title/",
        views.update_resume_title,
        name="update_resume_title"
    ),
    path(
        "resume/<int:resume_id>/optimize-summary/",
        views.optimize_summary,
        name="optimize_summary"
    ),

    path(
        "resume/<int:resume_id>/delete/",
        views.delete_resume,
        name="delete"
    ),
    path(
        "delete_account/",
        views.delete_account,
        name="delete_account"
    ),
    path(
        "download/<int:resume_id>/",
        views.download_resume,
        name="download_resume"
    ),
]