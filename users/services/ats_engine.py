from PyPDF2 import PdfReader
import re
from .resume_parser import (
    extract_resume_structure,
    deduplicate_projects
)

# ===============================
# ATS CONSTANTS
# ===============================

REQUIRED_SECTIONS = [
    "education",
    "experience",
    "skills",
    "projects",
    "certifications",
    "achievements"
]

GENERIC_KEYWORDS = [
    "team", "project", "experience", "skills", "knowledge",
    "responsible", "managed", "developed", "designed",
    "analysis", "communication", "leadership"
]

SUMMARY_HEADINGS = [

    "summary",

    "professional summary",

    "executive summary",

    "career objective",

    "objective",

    "profile",

    "about",

    "resume objective",

    "resume objectives"
]

TECHNICAL_SKILLS = [

    # Programming

    "python",
    "java",
    "c",
    "c++",
    "c#",
    "javascript",
    "typescript",

    # Web

    "django",
    "flask",
    "fastapi",
    "html",
    "css",
    "bootstrap",
    "react",
    "nodejs",

    # Database

    "sql",
    "mysql",
    "postgresql",
    "sqlite",
    "mongodb",

    # Tools

    "git",
    "github",
    "docker",
    "linux",

    # Cloud

    "aws",
    "azure",
    "gcp",

    # Data

    "pandas",
    "numpy",
    "matplotlib",
    "power bi",
    "excel",

    # AI / ML

    "machine learning",
    "deep learning",
    "tensorflow",
    "pytorch",
    "scikit-learn",

]

PROJECT_KEYWORDS = [

    "project",

    "developed",

    "built",

    "created",

    "implemented",

    "designed",

    "web application",

    "application",

    "system",

    "api",

    "dashboard",

]

ACHIEVEMENT_KEYWORDS = [

    "improved",

    "increased",

    "reduced",

    "optimized",

    "achieved",

    "boosted",

    "enhanced",

    "saved",

    "grew",

    "delivered"

]
# ===============================
# PDF TEXT EXTRACTION
# ===============================

def extract_text_from_pdf(pdf_file):

    reader = PdfReader(pdf_file)

    text = ""

    for page in reader.pages:
        text += page.extract_text() or ""

    return text


# ===============================
# ATS SCORING FUNCTIONS
# ===============================

def ats_skills_score(
    consistency_data
):

    skills = (
        consistency_data.get(
            "skills",
            {}
        )
    )

    relevant_skills = sum(

        1

        for value in skills.values()

        if value is True

    )

    if relevant_skills >= 6:

        return 20

    elif relevant_skills >= 3:

        return 10

    elif relevant_skills >= 1:

        return 5

    return 0

def ats_project_score(
    consistency_data
):

    projects = (
        consistency_data.get(
            "projects",
            {}
        )
    )

    if not projects:

        return 0

    relevant_projects = sum(

        1

        for value in projects.values()

        if value is True

    )

    if relevant_projects >= 1:

        return 15

    return 5

def ats_experience_score(
    consistency_data
):

    experience = (
        consistency_data.get(
            "experience",
            {}
        )
    )

    if not experience:

        return 0

    relevant_experience = sum(

        1

        for value in experience.values()

        if value is True

    )

    if relevant_experience >= 1:

        return 20

    return 5

def resume_length_score(text):

    wc = len(text.split())

    if 300 <= wc <= 800:
        return 10

    elif 200 <= wc < 300 or 800 < wc <= 1000:
        return 7

    return 3


def section_completeness_score(text):

    found = sum(
        1 for s in REQUIRED_SECTIONS
        if s in text.lower()
    )

    return (found / len(REQUIRED_SECTIONS)) * 15


def keyword_density_score(text):

    matched = sum(
        1 for kw in GENERIC_KEYWORDS
        if kw in text.lower()
    )

    return (matched / len(GENERIC_KEYWORDS)) * 25


def formatting_score(text):

    bullets = len(re.findall(r"•|-|\*", text))

    headings = len(
        re.findall(r"\n[A-Z][A-Za-z ]{3,}\n", text)
    )

    score = 0

    if bullets >= 5:
        score += 7

    if headings >= 3:
        score += 8

    return min(score, 15)


def readability_score(text):

    sentences = re.split(r"[.!?]", text)

    words = text.split()

    avg = len(words) / max(len(sentences), 1)

    if avg <= 20:
        return 10

    elif avg <= 30:
        return 7

    return 4

def extract_summary(text):

    lines = text.splitlines()

    for i, line in enumerate(lines):

        cleaned = line.strip().lower()

        if cleaned in SUMMARY_HEADINGS:

            summary_lines = []

            for next_line in lines[i + 1:]:

                next_line = next_line.strip()

                if not next_line:

                    break

                summary_lines.append(
                    next_line
                )

            return " ".join(
                summary_lines
            )

    return ""

def summary_quality_score(text):

    summary = extract_summary(
        text
    )

    if not summary:

        return 0

    score = 5

    summary_words = set(

        re.findall(
            r"\b[a-zA-Z]+\b",
            summary.lower()
        )

    )

    resume_words = set(

        re.findall(
            r"\b[a-zA-Z]+\b",
            text.lower()
        )

    )

    overlap = len(

        summary_words.intersection(
            resume_words
        )

    )

    if overlap >= 15:

        score += 10

    elif overlap >= 8:

        score += 6

    elif overlap >= 4:

        score += 3

    return min(score, 15)

def skills_coverage_score(text):

    text = text.lower()

    found = sum(

        1

        for skill in TECHNICAL_SKILLS

        if skill in text

    )

    coverage = (

        found
        / len(TECHNICAL_SKILLS)

    )

    return round(
        coverage * 20,
        1
    )

def project_quality_score(text):

    text = text.lower()

    project_hits = sum(

        text.count(keyword)

        for keyword in PROJECT_KEYWORDS

    )

    if project_hits >= 10:

        return 15

    elif project_hits >= 6:

        return 10

    elif project_hits >= 3:

        return 5

    return 0

def nlp_project_score(text):

    try:

        structure = (
            extract_resume_structure(
                text
            )
        )

        projects = structure.get(
            "projects",
            []
        )

        projects = (
            deduplicate_projects(
                projects
            )
        )

        project_count = len(
            projects
        )

        if project_count >= 5:

            return 15

        elif project_count >= 3:

            return 10

        elif project_count >= 1:

            return 5

        return 0

    except Exception:

        return project_quality_score(
            text
        )

def achievement_impact_score(text):

    text = text.lower()

    keyword_hits = sum(

        text.count(keyword)

        for keyword in ACHIEVEMENT_KEYWORDS

    )

    percentage_hits = len(

        re.findall(
            r"\d+\s*%",
            text
        )

    )

    number_hits = len(

        re.findall(
            r"\d+\+?",
            text
        )

    )

    total = (
        keyword_hits
        + percentage_hits
        + number_hits
    )

    if total >= 12:

        return 10

    elif total >= 8:

        return 7

    elif total >= 4:

        return 4

    elif total >= 2:

        return 2

    return 0
# ===============================
# RESUME STRENGTH FUNCTIONS
# ===============================

def skills_strength_score(text):

    text = text.lower()

    found_skills = set()

    for skill in TECHNICAL_SKILLS:

        if skill in text:

            found_skills.add(
                skill
            )

    count = len(
        found_skills
    )

    if count >= 15:

        return 3.0

    elif count >= 10:

        return 2.5

    elif count >= 6:

        return 2.0

    elif count >= 3:

        return 1.0

    return 0.5

def experience_strength_score(text):

    text = text.lower()

    experience_hits = len(

        re.findall(

            r"(experience|internship|worked|employment)",

            text

        )

    )

    project_hits = sum(

        text.count(keyword)

        for keyword in PROJECT_KEYWORDS

    )

    total = (
        experience_hits
        + project_hits
    )

    if total >= 12:

        return 3.0

    elif total >= 8:

        return 2.5

    elif total >= 5:

        return 2.0

    elif total >= 2:

        return 1.0

    return 0.5

def certification_strength_score(text):

    cert_keywords = [
        "certified",
        "certification",
        "certificate",
        "coursera",
        "udemy",
        "google",
        "aws",
        "microsoft"
    ]

    found = sum(
        1 for k in cert_keywords
        if k in text.lower()
    )

    if found >= 3:
        return 2.0

    elif found >= 1:
        return 1.0

    return 0.0


def achievement_strength_score(text):

    metrics = re.findall(
        r"\d+%|\d+\s*(users|projects|clients)",
        text.lower()
    )

    if len(metrics) >= 5:
        return 2.0

    elif len(metrics) >= 2:
        return 1.0

    return 0.5


# ===============================
# JOB ROLE RECOMMENDATION
# ===============================

def recommend_job_roles(text):

    text = text.lower()

    role_scores = {}

    ROLE_MAP = {

        "Software Developer": [
            "python",
            "java",
            "developer",
            "api",
            "backend",
            "frontend",
            "software"
        ],

        "Data Analyst": [
            "data",
            "analysis",
            "sql",
            "excel",
            "statistics",
            "dashboard"
        ],

        "Business Analyst": [
            "business",
            "requirements",
            "stakeholder",
            "process"
        ],

        "Project Coordinator": [
            "project",
            "coordination",
            "planning",
            "timeline"
        ],

        "UI/UX Designer": [
            "design",
            "ui",
            "ux",
            "figma",
            "wireframe"
        ],

        "Digital Marketer": [
            "marketing",
            "seo",
            "content",
            "campaign"
        ],

        "HR Executive": [
            "recruitment",
            "hr",
            "talent",
            "onboarding"
        ],

        "Finance Executive": [
            "finance",
            "accounting",
            "budget",
            "audit"
        ]
    }

    for role, keywords in ROLE_MAP.items():

        score = sum(
            1 for kw in keywords
            if kw in text
        )

        if score > 0:
            role_scores[role] = score

    sorted_roles = sorted(
        role_scores,
        key=role_scores.get,
        reverse=True
    )

    return sorted_roles[:4]


# ===============================
# MAIN ANALYSIS FUNCTION
# ===============================

def analyze_resume_text(text):

    ats_score = round(

        resume_length_score(text)

        + section_completeness_score(text)

        + skills_coverage_score(text)

        + formatting_score(text)

        + readability_score(text)

        + summary_quality_score(text)

        + nlp_project_score(text)

        + achievement_impact_score(text)

    )

    strength_score = round(

        skills_strength_score(text)

        + experience_strength_score(text)

        + certification_strength_score(text)

        + achievement_strength_score(text),

        1
    )

    job_roles = recommend_job_roles(text)

    return {

        "ats_score": ats_score,

        "strength_score": strength_score,

        "job_roles": job_roles,

        "extracted_text": text
    }