from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse, HttpResponseRedirect
from django.db.models import Q
from django.utils import timezone
from datetime import timedelta

from django.contrib import messages
from allauth.socialaccount.models import SocialAccount
from django.contrib.auth.forms import UserCreationForm, SetPasswordForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User
from .services.supabase_storage import get_supabase_client, upload_resume_file, delete_resume_file
from users.models import Resume
from .models import (
    Resume, 
    Profile, 
    PublicResumePost, 
    Message, 
    DeletedChat,
    Notification,
    ResumeComment,
)
from .services.ats_engine import (
    extract_text_from_pdf,
    analyze_resume_text
)
from .services.ai_optimizer import generate_resume_feedback

import json
from django.views.decorators.http import require_POST

def home(request):
    return render(request, "users/home.html")



def register(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('/')
    else:
        form = UserCreationForm()
    return render(request, 'registration/register.html', {'form': form})

@login_required
def upload_resume(request):

    if request.method != "POST":

        return JsonResponse({
            "success": False,
            "error": "Invalid request method"
        })

    uploaded_file = request.FILES.get("resume")

    if not uploaded_file:

        return JsonResponse({
            "success": False,
            "error": "No file uploaded"
        })

    if not uploaded_file.name.endswith(".pdf"):

        return JsonResponse({
            "success": False,
            "error": "Only PDF files are allowed"
        })

    file_path = upload_resume_file(
        uploaded_file,
        request.user.id
    )

    title = uploaded_file.name.replace(".pdf", "")

    resume = Resume.objects.create(
        user=request.user,
        title=title,
        file_path=file_path
    )

    return JsonResponse({
        "success": True,
        "resume_id": resume.id,
        "title": resume.title
    })

@login_required
@require_POST
def analyze_resume(request):

    uploaded_file = request.FILES.get("resume")

    if not uploaded_file:

        return JsonResponse({
            "error": "No PDF uploaded"
        }, status=400)

    if not uploaded_file.name.endswith(".pdf"):

        return JsonResponse({
            "error": "Only PDF files are allowed"
        }, status=400)

    # =========================
    # Upload to Supabase
    # =========================

    file_path = upload_resume_file(
        uploaded_file,
        request.user.id
    )

    # Move file pointer back to start
    uploaded_file.seek(0)

    # Extract text from PDF
    text = extract_text_from_pdf(uploaded_file)

    # Analyze resume
    analysis = analyze_resume_text(text)

    ai_feedback = generate_resume_feedback(text)

    # =========================
    # Save Resume in DB
    # =========================

    title = uploaded_file.name.replace(".pdf", "")

    resumes = Resume.objects.filter(user=request.user)
    titles = [r.title for r in resumes]

    title_parts = title.split(" || ")

    if title in titles:
        time = datetime.now().strftime("%d/%m/%Y-%H:%M:%S")
        try:
            datetime.strptime(title_parts[1], "%d/%m/%Y-%H:%M:%S")
            title = title.replace(title_parts[1], time)
        except (ValueError, IndexError):
            title = f"{title} || {time}"
        

    resume = Resume.objects.create(
        user=request.user,
        title=title,
        pdf_path=file_path,
        ats_score=analysis["ats_score"],
        strength_score=analysis["strength_score"],
        ai_feedback=ai_feedback,
        job_roles=json.dumps(analysis["job_roles"]),
        resume_text = text,
    )


    return JsonResponse({

        "success": True,

        "ats_score": analysis["ats_score"],

        "strength_score": analysis["strength_score"],

        "job_roles": analysis["job_roles"],

        "ai_feedback": ai_feedback,

        "resume_id": resume.id
    })

@login_required
def resume_detail(request, resume_id):
    resume = get_object_or_404(
        Resume,
        id=resume_id,
        user = request.user
    )

    job_roles = []

    if resume.job_roles:
        job_roles = json.loads(resume.job_roles)

    


    context = {
        "resume": resume,
        "job_roles": json.dumps(job_roles),
    }

    context["users"] = User.objects.exclude(
        id=request.user.id
    )
    return render(
        request,
        'users/resume_detail.html',
        context
    )
from datetime import datetime

@login_required
@require_POST
def update_resume_title(request, resume_id):

    resume = get_object_or_404(
        Resume,
        id=resume_id,
        user=request.user
    )

    new_title = request.POST.get("title", "").strip()

    if not new_title:
        messages.error(
            request,
            "Resume Title cannot be empty"
        )
        return JsonResponse({
            "error": "Title cannot be empty"
        }, status=400)

    resumes = Resume.objects.filter(user=request.user)
    titles = [r.title for r in resumes]

    if new_title in titles:
        time = datetime.now().strftime("%d/%m/%Y-%H:%M:%S")
        new_title = f"{new_title} || {time}"
        
    old_title = resume.title
    resume.title=new_title
    resume.save()
    messages.success(
        request,
        f"Resume Renamed: {old_title} -> {new_title}"
    )

    return JsonResponse({
        "success": True,
        "new_title": resume.title
    })

from .services.ai_optimizer import optimize_executive_summary
@login_required
@require_POST
def optimize_summary(request, resume_id):

    resume = get_object_or_404(
        Resume,
        id=resume_id,
        user=request.user
    )

    data = json.loads(request.body)

    target_role = data.get("target_role")
    general = data.get("general", False)

    optimized_summary = optimize_executive_summary(
        resume_text=resume.resume_text,
        target_role=target_role,
        general=general
    )

    return JsonResponse({
        "optimized_summary": optimized_summary
    })

@login_required
@require_POST
def delete_resume(request, resume_id):
    resume = get_object_or_404(
        Resume,
        id=resume_id,
        user=request.user
    )
    try:
        if resume.pdf_path:
            delete_resume_file(resume.pdf_path)
    except Exception as e:
        print("Supabase delete failed:", e)
    resume.delete()
    messages.success(
        request,
        f"Your Resume: {resume.title} Deleted."
    )

    return JsonResponse({
        "success": True
    })

@login_required
def delete_account(request):
    if not request.user.has_usable_password():

        messages.warning(
            request,
            (
                "Please set a password before "
                "deleting your account."
            )
        )

        return redirect(
            "users:set_password"
        )

    if request.method == "POST":

        

        password = request.POST.get("password")

        user = authenticate(
            username=request.user.username,
            password=password
        )

        if user is None:

            return render(
                request,
                "users/delete_account.html",
                {
                    "error": "Incorrect password"
                }
            )

        # =====================================
        # DELETE RESUME FILES FROM SUPABASE
        # =====================================

        resumes = Resume.objects.filter(
            user=request.user
        )

        for resume in resumes:

            if resume.pdf_path:

                try:

                    supabase.storage.from_(
                        "resume-pdfs"
                    ).remove([resume.pdf_path])

                except Exception as e:
                    print("Supabase delete error:", e)

        # =====================================
        # DELETE USER
        # =====================================

        request.user.delete()

        logout(request)

        messages.success(
            request,
            "Account Deleted successfully."
        )

        return redirect('/')

    return render(
        request,
        "users/delete_account.html"
    )

def download_resume(request, resume_id):
    resume = get_object_or_404(
        Resume,
        id=resume_id,
        user=request.user
    )

    supabase=get_supabase_client()

    file_path=resume.pdf_path
    response=supabase.storage.from_("resume-pdfs").create_signed_url(
        file_path,
        60
    )

    download_url = response["signedURL"]

    return HttpResponseRedirect(download_url)

@login_required
def profile_view(request):

    profile = request.user.profile

    if request.method == "POST":

        display_name = request.POST.get(
                "display_name"
            )

        if display_name:

            profile.display_name = display_name

        if request.FILES.get(
            "profile_image"
        ):

            profile.profile_image = request.FILES[
                "profile_image"
            ]

        profile.save()

        return redirect("/profile/")
    
    user_resumes = Resume.objects.filter(
        user=request.user
    )

    public_resume_ids = set(

        PublicResumePost.objects.filter(
            user=request.user
        ).values_list(
            "resume_id",
            flat=True
        )

    )

    for resume in user_resumes:

        resume.is_posted = (
            resume.id
            in public_resume_ids
        )

    public_posts = (
        PublicResumePost.objects
        .select_related(
            "user",
            "resume"
        )
        .order_by("-created_at")
    )

    total_unread = Message.objects.filter(
        receiver=request.user,
        is_read=False
    ).count()

    google_account = (
        SocialAccount.objects
        .filter(
            user=request.user,
            provider="google"
        )
        .first()
    )
    google_account_email = None

    if google_account:

        google_account_email = (
            google_account.extra_data.get(
                "email"
            )
        )
    

    resume_count = Resume.objects.filter(
        user=request.user
    ).count()

    public_post_count = PublicResumePost.objects.filter(
        user=request.user
    ).count()

    comment_count = ResumeComment.objects.filter(
         resume__user=request.user
    ).count()

    return render(
        request,
        "users/profile.html",
        {
            "profile": profile,
            "user_resumes": user_resumes,
            "public_posts": public_posts,
            "public_resume_ids": public_resume_ids,
            "total_unread": total_unread,
            "google_account": google_account,
            "google_account_email": google_account_email,
            "has_password": request.user.has_usable_password(),
            "resume_count": resume_count,
            "public_post_count": public_post_count,
            "comment_count": comment_count,
        }
    )

@login_required
def create_public_post(request, resume_id):

    resume = get_object_or_404(
            Resume,
            id=resume_id,
            user=request.user
        )

    already_posted = PublicResumePost.objects.filter(
            resume=resume
        ).exists()

    if not already_posted:

        PublicResumePost.objects.create(
            user=request.user,
            resume=resume
        )

        all_users = User.objects.exclude(
            id=request.user.id
        )

        for user in all_users:

            Notification.objects.create(
                user=user,
                sender=request.user,
                title="New Resume Posted",
                message=(
                    f"{request.user.username} "
                    f"posted a new resume: "
                    f"{resume.title}"
                ),
                url=f"/profile/#post-{resume.id}/"
            )

        messages.success(
            request,
            "Post Shared to Public room successfully."
        )

    return redirect("/profile/")

@login_required
def view_public_resume(
    request,
    resume_id
):

    resume = get_object_or_404(
        Resume,
        id=resume_id
    )

    supabase=get_supabase_client()

    file_path = resume.pdf_path

    response = (
        supabase.storage
        .from_("resume-pdfs")
        .create_signed_url(
            file_path,
            60
        )
    )

    signed_url = response["signedURL"]

    return redirect(signed_url)

@login_required
def other_users(request):

    search_query = request.GET.get(
            "search",
            ""
        )

    users_list = (
        User.objects
        .exclude(
            id=request.user.id
        )
    )

    if search_query:

        users_list = users_list.filter(
                    Q(
                        username__icontains=search_query
                    )

                    |

                    Q(
                        profile__display_name__icontains=search_query
                    )
            )

    users_list = users_list.select_related(
            "profile"
        )

    return render(
        request,
        "users/other_users.html",
        {
            "users_list": users_list,
            "search_query": search_query,
        }
    )

@login_required
def view_user_profile(
    request,
    user_id
):

    other_user = get_object_or_404(
            User,
            id=user_id
        )

    public_posts = PublicResumePost.objects.filter(
            user=other_user
        ).select_related(
            "resume"
        ).order_by(
            "-created_at"
        )

    return render(
        request,
        "users/view_user_profile.html",
        {
            "other_user": other_user,
            "public_posts": public_posts,
        }
    )

@login_required
def chat_view(request, user_id):
    shared_resume = None
    resume_id = request.GET.get(
        "resume"
    )

    if resume_id:

        shared_resume = Resume.objects.filter(
            id=resume_id
        ).first()
    
    seven_days_ago = (
        timezone.now()
        - timedelta(days=7)
    )

    Message.objects.filter(
        created_at__lt=seven_days_ago
    ).delete()

    Notification.objects.filter(
        created_at__lt=seven_days_ago
    ).delete()

    other_user = get_object_or_404(
            User,
            id=user_id
        )
    
    Message.objects.filter(
        sender=other_user,
        receiver=request.user,
        is_read=False
    ).update(
        is_read=True
    )

    chat_messages = (
        Message.objects.filter(

            Q(
                sender=request.user,
                receiver=other_user
            )

            |

            Q(
                sender=other_user,
                receiver=request.user
            )

        )
        .order_by("created_at")
    )

    if request.method == "POST":

        message_text = request.POST.get(
                "message"
            )

        if message_text:

            resume_id = request.POST.get(
                "resume_id"
            )

            resume = None

            if resume_id:

                resume = Resume.objects.filter(
                    id=resume_id
                ).first()

            new_message = Message.objects.create(
                sender=request.user,
                receiver=other_user,
                message=message_text,
                shared_resume=resume
            )

            if resume:

                Notification.objects.create(

                    user=other_user,

                    sender=request.user,

                    title="Resume Shared",

                    message=(
                        f"{request.user.username} "
                        f"shared a resume with you."
                    ),

                    url=f"/chat/{request.user.id}/"

                )

            else:

                Notification.objects.create(

                    user=other_user,

                    sender=request.user,

                    title="New Message",

                    message=message_text[:60],

                    url=f"/chat/{request.user.id}/"

                )

        return redirect(
            "users:chat",
            user_id = other_user.id
        )

    return render(
        request,
        "users/chat.html",
        {
            "other_user": other_user,
            "messages": chat_messages,
            "shared_resume": shared_resume
        }
    )

@login_required
def remove_public_post(
    request,
    resume_id
):

    PublicResumePost.objects.filter(
        user=request.user,
        resume_id=resume_id
    ).delete()

    messages.success(
        request,
        "Post removed from Public room successfully."
    )

    return redirect(
        "users:profile"
    )

@login_required
def chat_list(request):

    deleted_users = set(
        DeletedChat.objects.filter(
            user=request.user
        ).values_list(
            "other_user_id",
            flat=True
        )
    )

        

    

    messages = Message.objects.filter(

        Q(sender=request.user)

        |

        Q(receiver=request.user)

    ).order_by("-created_at")

    conversations = {}

    for message in messages:

        if message.sender == request.user:

            other_user = message.receiver

        else:

            other_user = message.sender


        if other_user.id in deleted_users:
            continue

        if other_user.id not in conversations:

            unread_count = Message.objects.filter(
                sender=other_user,
                receiver=request.user,
                is_read=False
            ).count()

            conversations[other_user.id] = {

                "user": other_user,

                "last_message": message,

                "unread_count": unread_count

            }



    chat_cards = list(
        conversations.values()
    )

    query = request.GET.get(
        "search"
    )

    if query:

        chat_cards = [
            chat
            for chat in chat_cards
            if (
                query.lower()
                in
                chat["user"].username.lower()
            )
            or
            (
                chat["user"].profile.display_name
                and
                query.lower()
                in
                chat["user"].profile.display_name.lower()
            )
        ]

    DeletedChat.objects.filter(
        user=request.user,
        other_user=other_user
    ).delete()

    return render(
        request,
        "users/chat_list.html",
        {
            "chat_cards": chat_cards
        }
    )

@login_required
def delete_chat(
    request,
    user_id
):
    other_user = get_object_or_404(
        User,
        id=user_id
    )

    DeletedChat.objects.get_or_create(
        user=request.user,
        other_user=other_user
    )

    other_deleted = DeletedChat.objects.filter(
        user=other_user,
        other_user=request.user
    ).exists()

    if other_deleted:

        Message.objects.filter(

            Q(
                sender=request.user,
                receiver=other_user
            )

            |

            Q(
                sender=other_user,
                receiver=request.user
            )

        ).delete()


    return redirect(
        "users:chat_list"
    )

@login_required
def share_resume(
    request,
    resume_id
):
    resume = get_object_or_404(
        Resume,
        id=resume_id,
        user=request.user
    )
    if request.method == "POST":

        selected_users = request.POST.getlist(
            "selected_users"
        )

    for user_id in selected_users:

        receiver = User.objects.get(
            id=user_id
        )

        Message.objects.create(

            sender=request.user,

            receiver=receiver,

            message="",

            shared_resume=resume

        )

        Notification.objects.create(

            user=receiver,

            sender=request.user,

            title="Resume Shared",

            message=(
                f"{request.user.username} "
                f"shared a resume with you."
            ),

            url=f"/chat/{request.user.id}/"

        )
    return redirect(
        "users:resume_detail",
        resume_id=resume.id
    )

@login_required
def open_shared_resume(
    request,
    resume_id
):

    resume = get_object_or_404(
        Resume,
        id=resume_id
    )

    if resume.user == request.user:

        return redirect(
            "users:resume_detail",
            resume_id=resume.id
        )

    return redirect(
        "users:view_public_resume",
        resume_id=resume.id
    )

@login_required
def disconnect_google_account(request):

    social_account = SocialAccount.objects.filter(
        user=request.user,
        provider="google"
    ).first()

    if not request.user.has_usable_password():

        messages.error(
            request,
            "Please set a password before disconnecting Google."
        )

        return redirect(
            "users:profile"
        )

    if social_account:

        social_account.delete()

        messages.success(
            request,
            "Google account disconnected successfully."
        )

    return redirect(
        "users:profile"
    )

@login_required
def set_password(request):

    if request.user.has_usable_password():

        messages.info(
            request,
            "You already have a password."
        )

        return redirect(
            "users:profile"
        )

    if request.method == "POST":

        form = SetPasswordForm(
            request.user,
            request.POST
        )

        if form.is_valid():

            form.save()

            messages.success(
                request,
                "Password set successfully."
            )

            return redirect(
                "users:profile"
            )

    else:

        form = SetPasswordForm(
            request.user
        )

    return render(
        request,
        "users/set_password.html",
        {
            "form": form
        }
    )

@login_required
def notifications_view(request):

    notifications = Notification.objects.filter(
        user=request.user
    ).order_by("-created_at")

    return render(
        request,
        "users/notifications.html",
        {
            "notifications": notifications
        }
    )

@login_required
def open_notification(
    request,
    notification_id
):

    notification = get_object_or_404(
        Notification,
        id=notification_id,
        user=request.user
    )

    if notification.title == "New Message":

        Notification.objects.filter(
            user=request.user,
            sender=notification.sender,
            title="New Message",
            is_read=False
        ).update(
            is_read=True
        )

    else:

        notification.is_read = True

        notification.save()

    return redirect(
        notification.url
    )

@login_required
def create_comment(
    request,
    resume_id
):

    if request.method != "POST":

        return redirect("/profile/")

    resume = get_object_or_404(
        Resume,
        id=resume_id
    )

    content = request.POST.get(
        "content",
        ""
    ).strip()

    if not content:

        messages.warning(
            request,
            "Comment cannot be empty."
        )

        return redirect("/profile/")

    ResumeComment.objects.create(
        resume=resume,
        user=request.user,
        content=content
    )

    if resume.user != request.user:

        Notification.objects.create(

            user=resume.user,

            sender=request.user,

            title="New Comment",

            message=content[:60],

            url=(
                f"/profile/"
                f"?comment={resume.id}"
                f"#post-{resume.id}"
            )

        )

    messages.success(
        request,
        "Comment posted."
    )

    return redirect("/profile/")

@login_required
def get_new_messages(
    request,
    user_id
):

    last_message_id = int(
        request.GET.get(
            "last_id",
            0
        )
    )

    other_user = get_object_or_404(
        User,
        id=user_id
    )

    Message.objects.filter(
        sender=other_user,
        receiver=request.user,
        is_read=False
    ).update(
        is_read=True
    )

    Notification.objects.filter(
        user=request.user,
        sender=other_user,
        title="New Message",
        is_read=False
    ).update(
        is_read=True
    )

    messages = Message.objects.filter(

        (
            Q(
                sender=request.user,
                receiver=other_user
            )
            |
            Q(
                sender=other_user,
                receiver=request.user
            )
        ),

        id__gt=last_message_id

    ).order_by("id")

    data = []

    for msg in messages:

        data.append({

            "id": msg.id,

            "message": msg.message,

            "sender_id": msg.sender.id,

            "created_at":
                msg.created_at.strftime(
                    "%d %b %Y %H:%M"
                ),
            "shared_resume": (

                {
                    "id": msg.shared_resume.id,
                    "title": msg.shared_resume.title,
                    "ats_score": msg.shared_resume.ats_score,
                    "strength_score":
                        msg.shared_resume.strength_score
                }

                if msg.shared_resume
                else None

            )


        })

    return JsonResponse(
        {
            "messages": data
        }
    )

@login_required
def get_notifications(request):

    notifications = (
        Notification.objects
        .filter(
            user=request.user,
            is_read=False
        )
        .order_by("-created_at")[:20]
    )

    data = []

    for notification in notifications:

        data.append({

            "id": notification.id,

            "title": notification.title,

            "message": notification.message,

            "url": f"/notification/{notification.id}/",

            "sender": (
                notification.sender.username
                if notification.sender
                else ""
            )

        })

    return JsonResponse({
        "notifications": data,
        "unread_count":
            notifications.count()
    })