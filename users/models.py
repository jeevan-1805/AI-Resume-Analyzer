from django.db import models
from django.contrib.auth.models import User
from .services.supabase_storage import get_supabase_client

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

class Profile(models.Model):

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE
    )

    display_name = models.CharField(
        max_length=100,
        blank=True
    )

    profile_image = models.CharField(
        max_length=500,
        blank=True,
        null=True
    )

    @property
    def profile_image_url(self):

        if not self.profile_image:

            return None

        supabase = get_supabase_client()

        return (

            supabase.storage
            .from_("profile-images")
            .get_public_url(
                self.profile_image
            )

        )


    def __str__(self):

        return self.user.username
    
    
class PublicResumePost(models.Model):

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )

    resume = models.ForeignKey(
        "users.Resume",
        on_delete=models.CASCADE
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):

        return (
            f"{self.user.username} - "
            f"{self.resume.title}"
        )
    
class Message(models.Model):

    sender = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="sent_messages"
    )

    receiver = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="received_messages"
    )

    message = models.TextField()

    shared_resume = models.ForeignKey(
        "users.Resume",
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    is_read = models.BooleanField(
        default=False
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):

        if self.shared_resume:

            return (
                f"{self.sender} shared "
                f"{self.shared_resume.title}"
            )

        return (
            f"{self.sender} -> "
            f"{self.receiver}"
        )
    
class DeletedChat(models.Model):

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )

    other_user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="deleted_by"
    )

    deleted_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:

        unique_together = (
            "user",
            "other_user"
        )

class Notification(models.Model):

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="notifications"
    )

    title = models.CharField(
        max_length=255
    )

    message = models.TextField()

    url = models.CharField(
        max_length=500,
        blank=True
    )

    is_read = models.BooleanField(
        default=False
    )

    sender = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="triggered_notifications"
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True
    )

    class Meta:

        ordering = [
            "-created_at"
        ]

    def __str__(self):

        return (
            f"{self.user.username} - "
            f"{self.title}"
        )
    
class ResumeComment(models.Model):

    resume = models.ForeignKey(
        Resume,
        on_delete=models.CASCADE,
        related_name="comments"
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )

    content = models.TextField()

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:

        ordering = [
            "-created_at"
        ]

    def __str__(self):

        return (
            f"{self.user.username} "
            f"commented on "
            f"{self.resume.title}"
        )