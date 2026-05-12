from PyPDF2 import PdfReader
import re


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

def resume_length_score(text):

    wc = len(text.split())

    if 300 <= wc <= 800:
        return 15

    elif 200 <= wc < 300 or 800 < wc <= 1000:
        return 10

    return 5


def section_completeness_score(text):

    found = sum(
        1 for s in REQUIRED_SECTIONS
        if s in text.lower()
    )

    return (found / len(REQUIRED_SECTIONS)) * 25


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
        return 20

    elif avg <= 30:
        return 14

    return 8


# ===============================
# RESUME STRENGTH FUNCTIONS
# ===============================

def skills_strength_score(text):

    skills = re.findall(r"\b[A-Za-z+#.]{2,}\b", text)

    unique_skills = set(skills)

    count = len(unique_skills)

    if count >= 20:
        return 3.0

    elif count >= 12:
        return 2.0

    elif count >= 6:
        return 1.0

    return 0.5


def experience_strength_score(text):

    years = re.findall(
        r"\b\d+\+?\s*(years|year|months|month)\b",
        text.lower()
    )

    keywords = [
        "experience",
        "worked",
        "employment",
        "internship"
    ]

    if years or any(k in text.lower() for k in keywords):

        if len(years) >= 2:
            return 3.0

        return 2.0

    return 1.0


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
            "frontend"
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

        + keyword_density_score(text)

        + formatting_score(text)

        + readability_score(text)
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