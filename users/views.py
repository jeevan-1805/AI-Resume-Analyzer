from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse, HttpResponseRedirect

from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout, authenticate

from .services.supabase_storage import get_supabase_client, upload_resume_file, delete_resume_file
from .models import Resume
from .services.ats_engine import (
    extract_text_from_pdf,
    analyze_resume_text
)
from .services.ai_optimizer import generate_resume_feedback

import json
from django.views.decorators.http import require_POST

def home(request):
    return render(request, "users/home.html")

def generate_resume(request):
    return HttpResponse("Generate Resume Page")

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
        return JsonResponse({
            "error": "Title cannot be empty"
        }, status=400)

    resumes = Resume.objects.filter(user=request.user)
    titles = [r.title for r in resumes]

    if new_title in titles:
        time = datetime.now().strftime("%d/%m/%Y-%H:%M:%S")
        new_title = f"{new_title} || {time}"
        
    resume.title=new_title
    resume.save()

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

    return JsonResponse({
        "success": True
    })

@login_required
def delete_account(request):

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