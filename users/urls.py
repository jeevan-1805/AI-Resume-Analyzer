from django.urls import path
from . import views

app_name = "users"

urlpatterns = [
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

    path(
        "profile/",
        views.profile_view,
        name="profile"
    ),

    path(
        "post-resume/<int:resume_id>/",
        views.create_public_post,
        name="post_resume"
    ),

    path(
        "public-resume/<int:resume_id>/",
        views.view_public_resume,
        name="view_public_resume"
    ),

    path(
        "other-users/",
        views.other_users,
        name="other_users"
    ),

    path(
        "user-profile/<int:user_id>/",
        views.view_user_profile,
        name="view_user_profile"
    ),

    path(
        "chat/<int:user_id>/",
        views.chat_view,
        name="chat"
    ),

    path(
        "remove-public-post/<int:resume_id>/",
        views.remove_public_post,
        name="remove_public_post"
    ),

    path(
        "chats/",
        views.chat_list,
        name="chat_list"
    ),

    path(
        "delete-chat/<int:user_id>/",
        views.delete_chat,
        name="delete_chat"
    ),

    path(
        "share-resume/<int:resume_id>/",
        views.share_resume,
        name="share_resume"
    ),

    path(
        "shared-resume/<int:resume_id>/",
        views.open_shared_resume,
        name="open_shared_resume"
    ),

    path(
        "disconnect-google/",
        views.disconnect_google_account,
        name="disconnect_google_account"
    ),

    path(
        "set-password/",
        views.set_password,
        name="set_password"
    ),

    path(
        "notifications/",
        views.notifications_view,
        name="notifications"
    ),

    path(
        "notification/<int:notification_id>/",
        views.open_notification,
        name="open_notification"
    ),

    path(
        "comment/<int:resume_id>/",
        views.create_comment,
        name="create_comment"
    ),

    path(
        "comment/<int:resume_id>/",
        views.create_comment,
        name="create_comment"
    ),

    path(
        "chat/<int:user_id>/new-messages/",
        views.get_new_messages,
        name="get_new_messages"
    ),

    path(
        "notifications/api/",
        views.get_notifications,
        name="get_notifications"
    ),
]