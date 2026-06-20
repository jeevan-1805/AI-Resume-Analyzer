
from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from PyPDF2 import PdfReader

from django.conf import settings
from groq import Groq

from .resume_parser import (
    extract_resume_structure,
    evaluate_resume_consistency,
    evaluate_resume_language
)

try:
    import fitz  # PyMuPDF
except ImportError:  # pragma: no cover
    fitz = None

# Optional dependencies for richer layout checks.
try:
    import cv2  # noqa: F401
except ImportError:  # pragma: no cover
    cv2 = None

try:
    import numpy as np  # noqa: F401
except ImportError:  # pragma: no cover
    np = None


# ===============================
# ATS CONSTANTS
# ===============================

SUMMARY_HEADINGS = [
    "summary",
    "professional summary",
    "executive summary",
    "career objective",
    "objective",
    "profile",
    "about",
    "resume objective",
    "resume objectives",
]

REQUIRED_MAJOR_SECTIONS = [
    "name",
    "contact",
    "summary",
    "education",
    "skills",
    "projects",
    "experience",
    "achievements",
]

ROLE_HINT_KEYWORDS = [
    "developer",
    "engineer",
    "analyst",
    "designer",
    "manager",
    "student",
    "intern",
    "consultant",
    "researcher",
    "administrator",
    "architect",
    "specialist",
    "coordinator",
    "lead",
    "leadership",
    "tester",
    "scientist",
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

CONTACT_FIELD_WEIGHTS = {
    "email": 2,
    "phone": 2,
    "location": 2,
    "linkedin": 2,
    "github": 2,
}

ATS_CRACK_WEIGHTS = {
    "resume_completeness": 20,
    "section_completeness": 40,
    "layout_formatting": 40,
}

# ===============================
# PDF TEXT EXTRACTION
# ===============================

def extract_text_from_pdf(pdf_file):
    reader = PdfReader(pdf_file)
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""
    return text


def extract_text_from_pdf_path_or_file(pdf_file):
    """
    Alias kept for readability when the caller already has the uploaded file.
    """
    return extract_text_from_pdf(pdf_file)


# ===============================
# INTERNAL HELPERS
# ===============================

def _normalize_string(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _lower(value: Any) -> str:
    return _normalize_string(value).lower()


def _safe_json_loads(content: str) -> Dict[str, Any]:
    content = _normalize_string(content)

    if not content:
        raise ValueError("Empty response from model")

    if content.startswith("```"):
        content = content.replace("```json", "").replace("```", "").strip()

    match = re.search(r"\{.*\}", content, flags=re.DOTALL)
    if match:
        content = match.group(0).strip()

    return json.loads(content)


def _groq_client() -> Groq:
    return Groq(api_key=settings.GROQ_API_KEY)


def _load_structured_resume(text: str) -> Dict[str, Any]:
    try:
        structured = extract_resume_structure(text)
        return structured if isinstance(structured, dict) else {}
    except Exception:
        return {}


def _load_consistency_data(structured_resume: Dict[str, Any]) -> Dict[str, Any]:
    try:
        consistency = evaluate_resume_consistency(structured_resume)
        return consistency if isinstance(consistency, dict) else {}
    except Exception:
        return {}


def _ensure_list(value: Any) -> List[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def _project_name(project: Any) -> str:
    if isinstance(project, dict):
        for key in ("name", "title", "project", "project_name"):
            if project.get(key):
                return _normalize_string(project.get(key))
        return ""
    return _normalize_string(project)


def _project_technologies(project: Any) -> List[str]:
    if not isinstance(project, dict):
        return []
    tech = project.get("technologies") or project.get("tech") or project.get("stack") or []
    if isinstance(tech, str):
        return [tech.strip()] if tech.strip() else []
    return [_normalize_string(t) for t in tech if _normalize_string(t)]


def _project_description(project: Any) -> str:
    if not isinstance(project, dict):
        return ""
    for key in ("description", "summary", "details"):
        if project.get(key):
            return _normalize_string(project.get(key))
    return ""


def _experience_role(exp: Any) -> str:
    if isinstance(exp, dict):
        for key in ("role", "title", "position", "designation"):
            if exp.get(key):
                return _normalize_string(exp.get(key))
        return ""
    return _normalize_string(exp)


def _experience_duration(exp: Any) -> str:
    if isinstance(exp, dict):
        duration = exp.get("duration") or exp.get("duration_text") or exp.get("period")
        if duration:
            return _normalize_string(duration)
        years = exp.get("duration_years")
        if years not in (None, ""):
            return _normalize_string(years)
    return ""


def _experience_description(exp: Any) -> str:
    if isinstance(exp, dict):
        for key in ("description", "summary", "details"):
            if exp.get(key):
                return _normalize_string(exp.get(key))
    return ""


def _education_text(item: Any) -> str:
    if isinstance(item, dict):
        parts = [item.get(k) for k in ("degree", "course", "name", "institution", "school", "college", "university", "details") if item.get(k)]
        if parts:
            return " ".join(_normalize_string(p) for p in parts if _normalize_string(p))
        return ""
    return _normalize_string(item)


def _unique_projects(projects: List[Any]) -> List[Any]:
    seen = set()
    unique = []
    for project in projects:
        name = _project_name(project).lower()
        if not name:
            continue
        if name not in seen:
            seen.add(name)
            unique.append(project)
    return unique


def _looks_like_name(line: str) -> bool:
    line = _normalize_string(line)
    if not line or len(line) > 60:
        return False
    if any(ch.isdigit() for ch in line):
        return False
    lowered = line.lower()
    if lowered in {h.lower() for h in SUMMARY_HEADINGS}:
        return False
    if any(keyword in lowered for keyword in ["summary", "education", "skills", "experience", "projects", "certification", "achievement", "contact"]):
        return False
    words = line.split()
    if not (2 <= len(words) <= 4):
        return False
    alphabetic_ratio = sum(ch.isalpha() for ch in line) / max(len(line), 1)
    return alphabetic_ratio > 0.75


def _first_nonempty_lines(text: str, limit: int = 8) -> List[str]:
    lines = []
    for line in text.splitlines():
        clean = line.strip()
        if clean:
            lines.append(clean)
        if len(lines) >= limit:
            break
    return lines


def _extract_candidate_name(text: str, contact_data: Optional[Dict[str, Any]] = None) -> str:
    contact_data = contact_data or {}
    contact_name = _normalize_string(contact_data.get("name"))
    if contact_name and not _looks_like_name(contact_name):
        contact_name = ""
    if contact_name:
        return contact_name

    for line in _first_nonempty_lines(text, limit=8):
        if _looks_like_name(line):
            return line
    return ""


def _has_any_contact_detail(contact_data: Dict[str, Any]) -> bool:
    return any(_normalize_string(contact_data.get(key)) for key in ["email", "phone", "location", "linkedin", "github", "city", "country"])


def _extract_contact_details_with_groq(text: str) -> Dict[str, str]:
    """
    Hybrid contact extraction:
    - regex first for email/phone/linkedin/github
    - Groq to infer location and fill any missing contact fields
    """
    details = {
        "name": "",
        "email": "",
        "phone": "",
        "city": "",
        "country": "",
        "location": "",
        "linkedin": "",
        "github": "",
    }

    # Regex baseline
    email_match = re.search(
        r"\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[A-Za-z]{2,}\b",
        text,
    )
    if email_match:
        details["email"] = email_match.group(0)

    phone_match = re.search(
        r"(\+?\d[\d\s().-]{7,}\d)",
        text,
    )
    if phone_match:
        details["phone"] = phone_match.group(0).strip()

    linkedin_match = re.search(
        r"(https?://(?:www\.)?linkedin\.com/[^\s)]+|linkedin\.com/[^\s)]+)",
        text,
        flags=re.IGNORECASE,
    )
    if linkedin_match:
        details["linkedin"] = linkedin_match.group(0).strip()

    github_match = re.search(
        r"(https?://(?:www\.)?github\.com/[^\s)]+|github\.com/[^\s)]+)",
        text,
        flags=re.IGNORECASE,
    )
    if github_match:
        details["github"] = github_match.group(0).strip()

    # Groq enhancement
    try:
        client = _groq_client()
        prompt = f"""
You are a resume contact information extractor.

Extract the following contact fields from the resume text and return ONLY valid JSON:

{{
    "name": "",
    "email": "",
    "phone": "",
    "city": "",
    "country": "",
    "location": "",
    "linkedin": "",
    "github": ""
}}

Rules:
- Return only JSON.
- If a field is missing, use an empty string.
- Do not guess wildly.
- For location, extract the most likely city and country if available.
- If linkedin or github is not a full URL, return the clean profile URL if you can infer it confidently.

Resume:
{text}
"""
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
        )
        content = _normalize_string(response.choices[0].message.content)
        if content:
            parsed = _safe_json_loads(content)
            for key in details:
                value = parsed.get(key)
                if _normalize_string(value):
                    details[key] = _normalize_string(value)
    except Exception:
        pass

    return details


def _detect_role_hint(summary: str) -> bool:
    summary = _lower(summary)
    return any(keyword in summary for keyword in ROLE_HINT_KEYWORDS)


def _education_level_flags(education_items: List[Any]) -> Dict[str, bool]:
    college_keywords = [
        "college",
        "university",
        "b.tech",
        "btech",
        "b.e",
        "be ",
        "bca",
        "mca",
        "b.sc",
        "bsc",
        "m.sc",
        "msc",
        "b.com",
        "bcom",
        "m.com",
        "mcom",
        "bachelor",
        "master",
        "degree",
    ]
    hsc_keywords = [
        "hsc",
        "higher secondary",
        "12th",
        "higher secondary school",
        "school",
        "intermediate",
        "plus two",
        "10th",
        "sslc",
    ]

    combined_text = " | ".join(_education_text(item) for item in education_items if _education_text(item)).lower()

    return {
        "college": any(keyword in combined_text for keyword in college_keywords),
        "hsc": any(keyword in combined_text for keyword in hsc_keywords),
    }


def _project_detail_flags(project: Any) -> Dict[str, bool]:
    name = _project_name(project)
    technologies = _project_technologies(project)
    description = _project_description(project)
    return {
        "name": bool(name),
        "technologies": bool(technologies),
        "description": bool(description),
    }


def _experience_detail_flags(exp: Any) -> Dict[str, bool]:
    role = _experience_role(exp)
    duration = _experience_duration(exp)
    description = _experience_description(exp)
    return {
        "role": bool(role),
        "duration": bool(duration),
        "description": bool(description),
    }


def _extract_job_roles_from_text(text: str) -> List[str]:
    """
    Simple role suggestion helper kept for backward compatibility.
    """
    text = _lower(text)
    role_scores: Dict[str, int] = {}

    ROLE_MAP = {
        "Software Developer": ["python", "java", "developer", "api", "backend", "frontend", "software"],
        "Data Analyst": ["data", "analysis", "sql", "excel", "statistics", "dashboard"],
        "Business Analyst": ["business", "requirements", "stakeholder", "process"],
        "Project Coordinator": ["project", "coordination", "planning", "timeline"],
        "UI/UX Designer": ["design", "ui", "ux", "figma", "wireframe"],
        "Digital Marketer": ["marketing", "seo", "content", "campaign"],
        "HR Executive": ["recruitment", "hr", "talent", "onboarding"],
        "Finance Executive": ["finance", "accounting", "budget", "audit"],
    }

    for role, keywords in ROLE_MAP.items():
        score = sum(1 for kw in keywords if kw in text)
        if score > 0:
            role_scores[role] = score

    sorted_roles = sorted(role_scores, key=role_scores.get, reverse=True)
    return sorted_roles[:4]


# ===============================
# ATS CRACK SCORE FUNCTIONS
# ===============================

def ats_resume_completeness_score(
    text: str,
    structured_resume: Optional[Dict[str, Any]] = None,
    contact_data: Optional[Dict[str, Any]] = None,
) -> Tuple[int, Dict[str, Any]]:
    structured_resume = structured_resume or _load_structured_resume(text)
    contact_data = contact_data or _extract_contact_details_with_groq(text)

    summary = _normalize_string(structured_resume.get("summary"))
    skills = _ensure_list(structured_resume.get("skills"))
    projects = _ensure_list(structured_resume.get("projects"))
    experience = _ensure_list(structured_resume.get("experience"))
    education = _ensure_list(structured_resume.get("education"))
    certifications = _ensure_list(structured_resume.get("certifications"))
    achievements = _ensure_list(structured_resume.get("achievements"))

    name_present = bool(_extract_candidate_name(text, contact_data))
    contact_present = _has_any_contact_detail(contact_data)
    summary_present = bool(summary)
    education_present = bool(education)
    skills_present = bool(skills)
    projects_present = bool(projects)
    experience_present = bool(experience)
    achievements_present = bool(certifications or achievements)

    breakdown = {
        "name": {"present": name_present, "score": 3 if name_present else 0, "max": 3},
        "contact": {"present": contact_present, "score": 3 if contact_present else 0, "max": 3},
        "summary": {"present": summary_present, "score": 3 if summary_present else 0, "max": 3},
        "education": {"present": education_present, "score": 3 if education_present else 0, "max": 3},
        "skills": {"present": skills_present, "score": 3 if skills_present else 0, "max": 3},
        "projects": {"present": projects_present, "score": 2 if projects_present else 0, "max": 2},
        "experience": {"present": experience_present, "score": 2 if experience_present else 0, "max": 2},
        "achievements": {"present": achievements_present, "score": 1 if achievements_present else 0, "max": 1},
    }

    total = sum(item["score"] for item in breakdown.values())
    return min(total, ATS_CRACK_WEIGHTS["resume_completeness"]), breakdown


def ats_section_completeness_score(
    text: str,
    structured_resume: Optional[Dict[str, Any]] = None,
    consistency_data: Optional[Dict[str, Any]] = None,
    contact_data: Optional[Dict[str, Any]] = None,
) -> Tuple[int, Dict[str, Any]]:
    structured_resume = structured_resume or _load_structured_resume(text)
    consistency_data = consistency_data or _load_consistency_data(structured_resume)
    contact_data = contact_data or _extract_contact_details_with_groq(text)

    summary = _normalize_string(structured_resume.get("summary"))
    skills = _ensure_list(structured_resume.get("skills"))
    projects = _ensure_list(structured_resume.get("projects"))
    experience = _ensure_list(structured_resume.get("experience"))
    education = _ensure_list(structured_resume.get("education"))

    # Contact details: email, phone, city/country, linkedin, github
    contact_points = 0
    contact_fields = {
        "email": bool(_normalize_string(contact_data.get("email"))),
        "phone": bool(_normalize_string(contact_data.get("phone"))),
        "location": bool(_normalize_string(contact_data.get("city")) or _normalize_string(contact_data.get("country")) or _normalize_string(contact_data.get("location"))),
        "linkedin": bool(_normalize_string(contact_data.get("linkedin"))),
        "github": bool(_normalize_string(contact_data.get("github"))),
    }
    for field, present in contact_fields.items():
        if present:
            contact_points += CONTACT_FIELD_WEIGHTS[field]

    # Summary clarity
    summary_points = 0
    if summary:
        word_count = len(summary.split())
        summary_points += 4  # summary exists
        if 5 <= word_count <= 40:
            summary_points += 3
        elif word_count > 0:
            summary_points += 1
        if _detect_role_hint(summary):
            summary_points += 3
        elif any(skill.lower() in summary.lower() for skill in skills[:3]):
            summary_points += 2

    summary_points = min(summary_points, 10)

    # Education depth: college + HSC
    education_flags = _education_level_flags(education)
    education_points = 0
    if education_flags["college"]:
        education_points += 3
    if education_flags["hsc"]:
        education_points += 3

    # Skills relevance to summary/objective
    relevant_skills = 0
    skills_flags = consistency_data.get("skills", {}) if isinstance(consistency_data, dict) else {}
    if isinstance(skills_flags, dict):
        relevant_skills = sum(1 for value in skills_flags.values() if value is True)

    if relevant_skills >= 6:
        skills_points = 8
    elif relevant_skills >= 3:
        skills_points = 6
    elif relevant_skills >= 1:
        skills_points = 3
    else:
        skills_points = 0

    # Project completeness
    project_points = 0
    unique_projects = _unique_projects(projects)
    if unique_projects:
        project_points = 1  # at least one project exists
        # bonus for project details
        if any(_project_detail_flags(p)["description"] for p in unique_projects):
            project_points += 1
        if any(_project_detail_flags(p)["technologies"] for p in unique_projects):
            project_points += 1

    # Experience completeness
    experience_points = 0
    if experience:
        experience_points = 1
        if any(_experience_detail_flags(e)["role"] for e in experience):
            experience_points += 1
        if any(_experience_detail_flags(e)["duration"] for e in experience):
            experience_points += 1

    breakdown = {
        "contact": {
            "score": min(contact_points, 10),
            "max": 10,
            "fields": contact_fields,
        },
        "summary": {
            "score": summary_points,
            "max": 10,
            "summary_exists": bool(summary),
            "role_hint": _detect_role_hint(summary) if summary else False,
            "word_count": len(summary.split()) if summary else 0,
        },
        "education": {
            "score": min(education_points, 6),
            "max": 6,
            "college_present": education_flags["college"],
            "hsc_present": education_flags["hsc"],
        },
        "skills": {
            "score": skills_points,
            "max": 8,
            "relevant_skills": relevant_skills,
            "total_skills": len(skills),
        },
        "projects": {
            "score": min(project_points, 3),
            "max": 3,
            "projects_count": len(unique_projects),
        },
        "experience": {
            "score": min(experience_points, 3),
            "max": 3,
            "experience_count": len(experience),
        },
    }

    total = sum(item["score"] for item in breakdown.values())
    return min(total, ATS_CRACK_WEIGHTS["section_completeness"]), breakdown


def _read_pdf_bytes(pdf_file) -> bytes:
    if pdf_file is None:
        return b""

    if isinstance(pdf_file, (bytes, bytearray)):
        return bytes(pdf_file)

    if isinstance(pdf_file, str) and os.path.exists(pdf_file):
        return Path(pdf_file).read_bytes()

    if hasattr(pdf_file, "read"):
        current_pos = None
        try:
            if hasattr(pdf_file, "tell"):
                current_pos = pdf_file.tell()
        except Exception:
            current_pos = None

        try:
            if hasattr(pdf_file, "seek"):
                pdf_file.seek(0)
            data = pdf_file.read()
            if isinstance(data, str):
                data = data.encode("utf-8")
            return data or b""
        finally:
            if current_pos is not None and hasattr(pdf_file, "seek"):
                try:
                    pdf_file.seek(current_pos)
                except Exception:
                    pass

    return b""


def detect_multicolumn_layout(pdf_file) -> Tuple[bool, Dict[str, Any]]:
    if fitz is None or pdf_file is None:
        return False, {"available": False, "reason": "PyMuPDF not installed or PDF missing"}

    pdf_bytes = _read_pdf_bytes(pdf_file)
    if not pdf_bytes:
        return False, {"available": True, "reason": "No PDF bytes"}

    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    except Exception as exc:
        return False, {"available": True, "reason": f"Cannot open PDF: {exc}"}

    for page_index in range(len(doc)):
        page = doc[page_index]
        words = page.get_text("words")
        if not words:
            continue

        width = float(page.rect.width)
        left = sum(1 for w in words if w[0] < width * 0.45)
        right = sum(1 for w in words if w[0] > width * 0.55)

        # A simple but effective heuristic.
        if left >= 15 and right >= 15:
            return True, {
                "available": True,
                "page": page_index + 1,
                "left_words": left,
                "right_words": right,
            }

    return False, {"available": True, "reason": "No strong multi-column signal"}


def detect_icons_and_symbols(text: str) -> Tuple[bool, Dict[str, Any]]:
    text = text or ""
    if not text:
        return False, {"symbol_count": 0, "density": 0.0}

    icon_chars = re.findall(
        r"[•●◦▪▫■□◆◇★☆✓✔✦✧✪✫☑☒✉☎➤➔➜➢➣➤➥➦➧➨▶▷◀◁❖❖]",
        text,
    )
    suspicious_unicode = re.findall(r"[^\w\s.,;:()@/%&+\-#|]", text, flags=re.UNICODE)
    symbol_count = len(icon_chars) + len(suspicious_unicode)
    density = symbol_count / max(len(text), 1)

    has_issue = symbol_count >= 15 or density >= 0.02
    return has_issue, {"symbol_count": symbol_count, "density": round(density, 4)}


def detect_hidden_text(pdf_file) -> Tuple[bool, Dict[str, Any]]:
    if fitz is None or pdf_file is None:
        return False, {"available": False, "reason": "PyMuPDF not installed or PDF missing"}

    pdf_bytes = _read_pdf_bytes(pdf_file)
    if not pdf_bytes:
        return False, {"available": True, "reason": "No PDF bytes"}

    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    except Exception as exc:
        return False, {"available": True, "reason": f"Cannot open PDF: {exc}"}

    suspicious_spans = []

    for page_index in range(len(doc)):
        page = doc[page_index]
        data = page.get_text("dict")
        blocks = data.get("blocks", [])

        for block in blocks:
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    text = _normalize_string(span.get("text"))
                    if not text:
                        continue

                    size = float(span.get("size", 0) or 0)
                    color = int(span.get("color", 0) or 0)
                    # color is RGB packed as integer; white usually 0xFFFFFF.
                    if size <= 4 or color in (0xFFFFFF, 16777215):
                        suspicious_spans.append(
                            {
                                "page": page_index + 1,
                                "text": text[:80],
                                "size": size,
                                "color": color,
                            }
                        )
                        if len(suspicious_spans) >= 5:
                            return True, {"available": True, "suspicious_spans": suspicious_spans}

    return False, {"available": True, "suspicious_spans": suspicious_spans}


def detect_photo_in_pdf(pdf_file) -> Tuple[bool, Dict[str, Any]]:
    if fitz is None or pdf_file is None:
        return False, {"available": False, "reason": "PyMuPDF not installed or PDF missing"}

    pdf_bytes = _read_pdf_bytes(pdf_file)
    if not pdf_bytes:
        return False, {"available": True, "reason": "No PDF bytes"}

    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    except Exception as exc:
        return False, {"available": True, "reason": f"Cannot open PDF: {exc}"}

    image_pages = []
    for page_index in range(len(doc)):
        page = doc[page_index]
        blocks = page.get_text("dict").get("blocks", [])
        for block in blocks:
            if block.get("type") == 1:
                rect = block.get("bbox", [0, 0, 0, 0])
                x0, y0, x1, y1 = rect
                area = max((x1 - x0) * (y1 - y0), 0)
                page_area = float(page.rect.width * page.rect.height) or 1.0
                if area / page_area >= 0.04:
                    image_pages.append(
                        {
                            "page": page_index + 1,
                            "area_ratio": round(area / page_area, 4),
                        }
                    )
                    return True, {"available": True, "image_pages": image_pages}

    return False, {"available": True, "image_pages": image_pages}


def ats_layout_formatting_score(
    text: str,
    pdf_file=None,
) -> Tuple[int, Dict[str, Any]]:
    score = ATS_CRACK_WEIGHTS["layout_formatting"]

    multicolumn, multi_info = detect_multicolumn_layout(pdf_file)
    icons, icons_info = detect_icons_and_symbols(text)
    hidden, hidden_info = detect_hidden_text(pdf_file)
    photo, photo_info = detect_photo_in_pdf(pdf_file)

    penalties = {
        "multi_column": 10 if multicolumn else 0,
        "icons_symbols": 10 if icons else 0,
        "hidden_text": 10 if hidden else 0,
        "photo": 10 if photo else 0,
    }

    score -= sum(penalties.values())
    score = max(score, 0)

    breakdown = {
        "base": ATS_CRACK_WEIGHTS["layout_formatting"],
        "penalties": penalties,
        "detections": {
            "multi_column": multi_info,
            "icons_symbols": icons_info,
            "hidden_text": hidden_info,
            "photo": photo_info,
        },
    }

    return score, breakdown

def ats_grammar_language_score(
    text: str,
) -> Tuple[int, Dict[str, Any]]:

    score = ATS_CRACK_WEIGHTS["grammar_language"]

    try:

        report = evaluate_resume_language(
            text
        )

    except Exception as e:

        return score, {

            "base": ATS_CRACK_WEIGHTS["grammar_language"],

            "penalties": {},

            "detections": {

                "error": str(e)

            }

        }

    penalties = {

        "grammar": 0,

        "spelling": 0,

        "punctuation": 0,

        "capitalization": 0,

        "style": 0,

        "other": 0,

    }

    detections = {

        "grammar": report.get(
            "grammar",
            []
        ),

        "spelling": report.get(
            "spelling",
            []
        ),

        "punctuation": report.get(
            "punctuation",
            []
        ),

        "capitalization": report.get(
            "capitalization",
            []
        ),

        "style": report.get(
            "style",
            []
        ),

        "other": report.get(
            "other",
            []
        ),

    }

    penalties["grammar"] = (
        len(
            detections["grammar"]
        ) * 2
    )

    penalties["spelling"] = (
        len(
            detections["spelling"]
        ) * 1
    )

    penalties["punctuation"] = (
        len(
            detections["punctuation"]
        ) * 0.5
    )

    penalties["capitalization"] = (
        len(
            detections["capitalization"]
        ) * 0.5
    )

    penalties["style"] = (
        len(
            detections["style"]
        ) * 0.5
    )

    penalties["other"] = (
        len(
            detections["other"]
        ) * 0.5
    )

    total_penalty = sum(
        penalties.values()
    )

    score -= total_penalty

    score = max(

        round(score, 1),

        0

    )

    total_errors = sum(

        len(v)

        for v in detections.values()

    )

    breakdown = {

        "base": ATS_CRACK_WEIGHTS["grammar_language"],

        "penalties": penalties,

        "detections": detections,

        "total_errors": total_errors,

        "total_penalty": round(
            total_penalty,
            1
        )

    }

    return score, breakdown


def calculate_ats_crack_score(
    text: str,
    pdf_file=None,
    structured_resume: Optional[Dict[str, Any]] = None,
    consistency_data: Optional[Dict[str, Any]] = None,
    contact_data: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    structured_resume = structured_resume or _load_structured_resume(text)
    consistency_data = consistency_data or _load_consistency_data(structured_resume)
    contact_data = contact_data or _extract_contact_details_with_groq(text)

    resume_score, resume_breakdown = ats_resume_completeness_score(
        text=text,
        structured_resume=structured_resume,
        contact_data=contact_data,
    )
    section_score, section_breakdown = ats_section_completeness_score(
        text=text,
        structured_resume=structured_resume,
        consistency_data=consistency_data,
        contact_data=contact_data,
    )
    layout_score, layout_breakdown = ats_layout_formatting_score(
        text=text,
        pdf_file=pdf_file,
    )

    total = int(round(resume_score + section_score + layout_score))
    total = max(0, min(total, 100))

    return {
        "score": total,
        "breakdown": {
            "resume_completeness": {
                "score": resume_score,
                "max": ATS_CRACK_WEIGHTS["resume_completeness"],
                "details": resume_breakdown,
            },
            "section_completeness": {
                "score": section_score,
                "max": ATS_CRACK_WEIGHTS["section_completeness"],
                "details": section_breakdown,
            },
            "layout_formatting": {
                "score": layout_score,
                "max": ATS_CRACK_WEIGHTS["layout_formatting"],
                "details": layout_breakdown,
            },
        },
    }


# ===============================
# JD MATCH SCORE (PLACEHOLDER FOR NEXT PHASE)
# ===============================

def calculate_jd_match_score(
    structured_resume: Dict[str, Any],
    job_description_text: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """
    Placeholder for the next phase.
    This will later compare the structured resume against a JD.
    """
    if not job_description_text:
        return None
    return None


# ===============================
# LEGACY / COMPATIBILITY HELPERS
# ===============================

def resume_length_score(text):
    """
    Legacy helper retained for compatibility.
    """
    wc = len(text.split())

    if 300 <= wc <= 800:
        return 10

    elif 200 <= wc < 300 or 800 < wc <= 1000:
        return 7

    return 3


def section_completeness_score(text):
    """
    Legacy helper retained for compatibility.
    """
    found = sum(
        1 for s in REQUIRED_MAJOR_SECTIONS
        if s in text.lower()
    )

    return (found / len(REQUIRED_MAJOR_SECTIONS)) * 15


def keyword_density_score(text):
    """
    Legacy helper retained for compatibility.
    """
    generic_keywords = [
        "team", "project", "experience", "skills", "knowledge",
        "responsible", "managed", "developed", "designed",
        "analysis", "communication", "leadership",
    ]
    matched = sum(
        1 for kw in generic_keywords
        if kw in text.lower()
    )

    return (matched / len(generic_keywords)) * 25


def formatting_score(text):
    """
    Legacy helper retained for compatibility.
    """
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
    """
    Legacy helper retained for compatibility.
    """
    sentences = re.split(r"[.!?]", text)

    words = text.split()

    avg = len(words) / max(len(sentences), 1)

    if avg <= 20:
        return 10

    elif avg <= 30:
        return 7

    return 4


def extract_summary(text):
    """
    Legacy helper retained for compatibility.
    """
    lines = text.splitlines()

    for i, line in enumerate(lines):
        cleaned = line.strip().lower()

        if cleaned in SUMMARY_HEADINGS:
            summary_lines = []

            for next_line in lines[i + 1:]:
                next_line = next_line.strip()

                if not next_line:
                    break

                summary_lines.append(next_line)

            return " ".join(summary_lines)

    return ""


def summary_quality_score(text):
    """
    Legacy helper retained for compatibility.
    """
    summary = extract_summary(text)

    if not summary:
        return 0

    score = 5

    summary_words = set(
        re.findall(
            r"\b[a-zA-Z]+\b",
            summary.lower(),
        )
    )

    resume_words = set(
        re.findall(
            r"\b[a-zA-Z]+\b",
            text.lower(),
        )
    )

    overlap = len(summary_words.intersection(resume_words))

    if overlap >= 15:
        score += 10
    elif overlap >= 8:
        score += 6
    elif overlap >= 4:
        score += 3

    return min(score, 15)


def skills_coverage_score(text):
    """
    Legacy helper retained for compatibility.
    """
    text = text.lower()

    found = sum(
        1
        for skill in TECHNICAL_SKILLS
        if skill in text
    )

    coverage = found / len(TECHNICAL_SKILLS)

    return round(coverage * 20, 1)


def project_quality_score(text):
    """
    Legacy helper retained for compatibility.
    """
    text = text.lower()

    project_keywords = [
        "project", "developed", "built", "created", "implemented",
        "designed", "web application", "application", "system", "api", "dashboard",
    ]

    project_hits = sum(
        text.count(keyword)
        for keyword in project_keywords
    )

    if project_hits >= 10:
        return 15
    elif project_hits >= 6:
        return 10
    elif project_hits >= 3:
        return 5

    return 0


def nlp_project_score(text):
    """
    Legacy helper retained for compatibility.
    Uses the newer structure extraction if possible.
    """
    try:
        structure = extract_resume_structure(text)
        projects = _ensure_list(structure.get("projects", []))
        projects = _unique_projects(projects)
        project_count = len(projects)

        if project_count >= 5:
            return 15
        elif project_count >= 3:
            return 10
        elif project_count >= 1:
            return 5

        return 0

    except Exception:
        return project_quality_score(text)


def achievement_impact_score(text):
    """
    Legacy helper retained for compatibility.
    """
    text = text.lower()

    achievement_keywords = [
        "improved", "increased", "reduced", "optimized", "achieved",
        "boosted", "enhanced", "saved", "grew", "delivered",
    ]

    keyword_hits = sum(
        text.count(keyword)
        for keyword in achievement_keywords
    )

    percentage_hits = len(
        re.findall(
            r"\d+\s*%",
            text,
        )
    )

    number_hits = len(
        re.findall(
            r"\d+\+?",
            text,
        )
    )

    total = keyword_hits + percentage_hits + number_hits

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
            found_skills.add(skill)

    count = len(found_skills)

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
            text,
        )
    )

    project_hits = sum(
        text.count(keyword)
        for keyword in [
            "project", "developed", "built", "created", "implemented",
            "designed", "web application", "application", "system", "api", "dashboard",
        ]
    )

    total = experience_hits + project_hits

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
        "microsoft",
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
        text.lower(),
    )

    if len(metrics) >= 5:
        return 2.0
    elif len(metrics) >= 2:
        return 1.0

    return 0.5


def calculate_strength_score(text: str) -> Tuple[float, Dict[str, Any]]:
    """
    Legacy strength score kept for backward compatibility.
    """
    skill = skills_strength_score(text)
    exp = experience_strength_score(text)
    cert = certification_strength_score(text)
    ach = achievement_strength_score(text)
    total = round(skill + exp + cert + ach, 1)

    breakdown = {
        "skills": skill,
        "experience": exp,
        "certifications": cert,
        "achievements": ach,
    }
    return total, breakdown


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
            "software",
        ],
        "Data Analyst": [
            "data",
            "analysis",
            "sql",
            "excel",
            "statistics",
            "dashboard",
        ],
        "Business Analyst": [
            "business",
            "requirements",
            "stakeholder",
            "process",
        ],
        "Project Coordinator": [
            "project",
            "coordination",
            "planning",
            "timeline",
        ],
        "UI/UX Designer": [
            "design",
            "ui",
            "ux",
            "figma",
            "wireframe",
        ],
        "Digital Marketer": [
            "marketing",
            "seo",
            "content",
            "campaign",
        ],
        "HR Executive": [
            "recruitment",
            "hr",
            "talent",
            "onboarding",
        ],
        "Finance Executive": [
            "finance",
            "accounting",
            "budget",
            "audit",
        ],
    }

    for role, keywords in ROLE_MAP.items():
        score = sum(1 for kw in keywords if kw in text)
        if score > 0:
            role_scores[role] = score

    sorted_roles = sorted(role_scores, key=role_scores.get, reverse=True)
    return sorted_roles[:4]


# ===============================
# MAIN ANALYSIS FUNCTIONS
# ===============================

def analyze_resume_text(
    text: str,
    pdf_file=None,
    job_description_text: Optional[str] = None,
):
    """
    Main analyzer.

    Returns:
    - ats_score: ATS Crack Score (0-100)
    - strength_score: legacy strength score
    - optional breakdowns for dashboarding
    """
    structured_resume = _load_structured_resume(text)
    consistency_data = _load_consistency_data(structured_resume)
    contact_data = _extract_contact_details_with_groq(text)

    ats_result = calculate_ats_crack_score(
        text=text,
        pdf_file=pdf_file,
        structured_resume=structured_resume,
        consistency_data=consistency_data,
        contact_data=contact_data,
    )

    strength_score, strength_breakdown = calculate_strength_score(text)

    # Placeholder for future JD matching.
    jd_match_score = calculate_jd_match_score(
        structured_resume=structured_resume,
        job_description_text=job_description_text,
    )

    return {
        # Backward-compatible key used by your current app
        "ats_score": ats_result["score"],

        # New explicit crack score naming
        "ats_crack_score": ats_result["score"],
        "ats_crack_breakdown": ats_result["breakdown"],

        "strength_score": strength_score,
        "strength_breakdown": strength_breakdown,

        "job_roles": recommend_job_roles(text),
        "jd_match_score": jd_match_score,

        "structured_resume": structured_resume,
        "consistency_data": consistency_data,
        "contact_details": contact_data,
        "extracted_text": text,
    }


def analyze_resume_pdf(
    pdf_file,
    job_description_text: Optional[str] = None,
):
    text = extract_text_from_pdf(pdf_file)
    return analyze_resume_text(
        text=text,
        pdf_file=pdf_file,
        job_description_text=job_description_text,
    )
