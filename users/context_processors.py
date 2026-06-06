from .models import (
    Resume,
    Message,
    Notification
)
from django.db.models import Count
def sidebar_resumes(request):
    resumes = Resume.objects.none()
    search_query = request.GET.get("search", "").strip()
    if request.user.is_authenticated:
        resumes = Resume.objects.filter(
            user = request.user
        ).order_by("-uploaded_at")

        if search_query:

            resumes = resumes.filter(
                title__icontains=search_query
            )
    return {
        "resumes": resumes,
        "search_query": search_query
    }

def unread_messages_count(request):

    if not request.user.is_authenticated:

        return {
            "global_unread_count": 0
        }

    unread_count = Message.objects.filter(
        receiver=request.user,
        is_read=False
    ).count()

    notification_count = Notification.objects.filter(
        user=request.user,
        is_read=False
    ).count()

    recent_notifications = Notification.objects.filter(
        user=request.user
    ).order_by("-created_at")[:5]

    display_count = (
        "99+"
        if unread_count > 99
        else unread_count
    )

    notification_display = (
        "99+"
        if notification_count > 99
        else notification_count
    )

    return {
        "global_unread_count": unread_count,
        "global_unread_display": display_count,

        "notification_count": notification_count,
        "notification_display": notification_display,
        "recent_notifications": recent_notifications,
    }