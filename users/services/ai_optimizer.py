import os
from groq import Groq
from django.conf import settings

from dotenv import load_dotenv

load_dotenv()




client = Groq(
    api_key=settings.GROQ_API_KEY
)




# ===============================
# AI RESUME OPTIMIZATION
# ===============================
def generate_resume_feedback(resume_text):

    prompt = f"""
    Analyze this resume and give:

    1. ATS improvement suggestions
    2. Missing skills
    3. Resume strengths
    4. Resume weaknesses
    5. Better keyword suggestions

    Resume:
    {resume_text}
    """

    try:

        chat_completion = client.chat.completions.create(

            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],

            model="llama-3.1-8b-instant",
        )

        return chat_completion.choices[0].message.content

    except Exception as e:

        print("Groq Error:", e)

        return "AI feedback unavailable currently."
    

def optimize_executive_summary(resume_text, target_role=None, general=False):
    if general:
        prompt = f"""
        You are a professional ATS resume optimizer.

        Improve ONLY the executive summary section
        of this resume.

        Make it:
        - professional
        - concise
        - ATS friendly
        - grammatically strong

        Resume:
        {resume_text}

        Return ONLY the optimized executive summary.
        """

    else:

        prompt = f"""
        You are a professional ATS resume optimizer.

        Create a strong executive summary for the
        following target role:

        TARGET ROLE:
        {target_role}

        Use the resume content below.

        Resume:
        {resume_text}

        Return ONLY the optimized executive summary.
        """
    try:
        response = client.chat.completions.create(
            messages=[
                {"role": "user",
                "content": prompt
                }
            ],
            model="llama-3.1-8b-instant",

        )
        return response.choices[0].message.content
    except Exception as e:
        print("Groq Error:", e)

        return "AI optimization unavailable currently."
