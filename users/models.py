from django.db import models
from django.contrib.auth.models import User

class Resume(models.Model):
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        related_name="resumes"
    )
    title = models.CharField(max_length=255)
    pdf_path = models.TextField()
    uploaded_at = models.DateTimeField(auto_now_add=True)
    ats_score = models.IntegerField(default=0)
    strength_score = models.FloatField(default=0)
    job_roles = models.JSONField(default=list)
    ai_feedback = models.TextField(default="No Feedback")
    resume_text = models.TextField(default="No Text...")

    def __str__(self):
        return self.title

# Create your models here.
