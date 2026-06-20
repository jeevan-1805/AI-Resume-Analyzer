import json

from groq import Groq

from django.conf import settings

def extract_resume_structure(
    resume_text
):

    client = Groq(
        api_key=settings.GROQ_API_KEY
    )

    prompt = f"""
You are an expert resume parser.

Analyze the resume and return ONLY valid JSON.

Return this exact structure:

{{
    "summary": "",

    "skills": [],

    "projects": [
        {{
            "name": "",
            "technologies": [],
            "description": ""
        }}
    ],

    "experience": [
        {{
            "role": "",
            "company": "",
            "duration_years": 0,
            "description": ""
        }}
    ],

    "education": [],

    "certifications": [],

    "achievements": []
}}

Rules:

1. Return ONLY JSON.
2. Do NOT explain anything.
3. Infer duration_years when possible.
4. Extract technologies used in projects.
5. Keep descriptions concise.

Resume:

{resume_text}
"""

    response = client.chat.completions.create(

        model="llama-3.3-70b-versatile",

        messages=[

            {
                "role": "user",
                "content": prompt
            }

        ],

        temperature=0

    )

    content = (
        response
        .choices[0]
        .message.content
    )

    content = content.strip()

    if content.startswith("```json") or content.startswith("```"):

        content = (
            content
            .replace("```json", "")
            .replace("```", "")
            .strip()
        )

    return json.loads(
        content
    )

def evaluate_resume_consistency(
    structured_resume
):

    client = Groq(
        api_key=settings.GROQ_API_KEY
    )

    prompt = f"""
You are an expert ATS evaluator.

Your task:

Use the SUMMARY section as the primary career direction.

Determine whether each skill,
project,
and experience entry
is relevant to the summary.

Return ONLY valid JSON.

Format:

{{
    "skills": {{
        "Python": true,
        "Photoshop": false
    }},

    "projects": {{
        "AI Resume Analyzer": true,
        "Wedding Album Designer": false
    }},

    "experience": {{
        "Python Developer Intern": true,
        "Graphic Designer": false
    }}
}}

Rules:

1. Use semantic understanding.
2. Python and Django are related.
3. AI and LLM are related.
4. Machine Learning and Data Science are related.
5. Web Development and Django are related.
6. Do NOT explain.
7. Return ONLY JSON.

Resume Structure:

{json.dumps(structured_resume, indent=4)}
"""

    response = client.chat.completions.create(

        model="llama-3.3-70b-versatile",

        messages=[

            {
                "role": "user",
                "content": prompt
            }

        ],

        temperature=0

    )

    content = (
        response
        .choices[0]
        .message.content
        .strip()
    )


    if content.startswith("```"):

        content = (
            content
            .replace(
                "```json",
                ""
            )
            .replace(
                "```",
                ""
            )
            .strip()
        )

    print(content)

    return json.loads(
        content
    )

def deduplicate_projects(
    projects
):

    seen = set()

    unique_projects = []

    for project in projects:

        normalized = (
            project
            .strip()
            .lower()
        )

        if normalized not in seen:

            seen.add(
                normalized
            )

            unique_projects.append(
                project
            )

    return unique_projects

def evaluate_resume_language(
    resume_text,
):

    client = Groq(
        api_key=settings.GROQ_API_KEY
    )

    prompt = f"""
You are an ATS grammar and language evaluator.

Your task is ONLY to detect language issues.

Do NOT calculate scores.

Do NOT calculate penalties.

Return ONLY valid JSON.

Categories:

- grammar
- spelling
- punctuation
- capitalization
- style
- other

Each issue must contain:

message
context

Example:

{{
    "grammar":[
        {{
            "message":"Subject and verb do not agree.",
            "context":"He have worked..."
        }}
    ],

    "spelling":[
        {{
            "message":"Misspelled word.",
            "context":"Experiance"
        }}
    ],

    "punctuation":[],

    "capitalization":[],

    "style":[],

    "other":[]
}}

Resume:

{resume_text}
"""

    response = client.chat.completions.create(

        model="llama-3.3-70b-versatile",

        messages=[

            {
                "role": "user",
                "content": prompt
            }

        ],

        temperature=0

    )

    content = (
        response
        .choices[0]
        .message.content
        .strip()
    )

    if content.startswith("```"):

        content = content.strip("`")

        if content.startswith("json"):

            content = content[4:]

        content = content.strip()

    return json.loads(content)
