from users.services.resume_parser import (
    extract_resume_structure
)

result = extract_resume_structure(
    """
    Python Developer

    Skills:
    Python
    Django

    Projects:
    AI Resume Analyzer

    Experience:
    Project Leader
    """
)

print(result)