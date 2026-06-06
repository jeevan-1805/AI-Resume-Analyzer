import os
import uuid

from supabase import create_client
from dotenv import load_dotenv

load_dotenv()


def get_supabase_client():

    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")


    return create_client(
        SUPABASE_URL,
        SUPABASE_KEY
    )

def upload_resume_file(file, user_id):
    supabase = get_supabase_client()
    original_name = file.name
    file_extension = os.path.splitext(original_name)[1]
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    file_path = f"{user_id}/{unique_filename}"
    response = supabase.storage.from_("resume-pdfs").upload(
        file_path,
        file.read(),
        {
            "content-type": "application/pdf"
        }
    )
    return file_path

def delete_resume_file(file_path):
    supabase = get_supabase_client()
    response = supabase.storage.from_("resume-pdfs").remove([file_path])
    return response

def upload_profile_image(file, user_id):

    supabase = get_supabase_client()

    original_name = file.name

    file_extension = os.path.splitext(
        original_name
    )[1]

    unique_filename = (
        f"{uuid.uuid4()}"
        f"{file_extension}"
    )

    file_path = (
        f"{user_id}/"
        f"{unique_filename}"
    )

    supabase.storage.from_(
        "profile-images"
    ).upload(

        file_path,

        file.read(),

        {
            "content-type":
            file.content_type
        }

    )

    return file_path

def delete_profile_image(file_path):

    if not file_path:

        return

    supabase = get_supabase_client()

    try:

        supabase.storage.from_(
            "profile-images"
        ).remove(
            [file_path]
        )

    except Exception:

        pass