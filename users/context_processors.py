from .models import Resume
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
