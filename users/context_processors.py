from .models import Resume
def sidebar_resumes(request):
    if request.user.is_authenticated:
        resumes = Resume.objects.filter(
            user = request.user
        ).order_by("-uploaded_at")
    else:
        resumes = []
    return {
        "resumes": resumes
    }
