# AI Resume Analyser

An ATS-focused resume analysis web application built with Django, Supabase, and AI-powered resume feedback. Users can upload a PDF resume, get ATS score insights, strength analysis, job-role recommendations, and executive summary optimization.

## Live Demo

Render deployment: https://ai-resume-analyser-y5cv.onrender.com/

> **Important:** The first load on Render can take **40–60 seconds** because the free web service may need time to wake up and load Python packages. Please wait a little before refreshing.

## Features

- Resume PDF upload
- ATS scoring
- Resume strength scoring
- AI-generated resume feedback
- Recommended job roles
- Executive summary optimization
- Resume detail page for each uploaded file
- Editable resume title
- Resume deletion
- Account deletion
- Supabase file storage
- Supabase PostgreSQL database
- Responsive UI for mobile, tablet, and desktop

## Tech Stack

- **Backend:** Django
- **Frontend:** HTML, CSS, JavaScript
- **Database:** Supabase PostgreSQL
- **Storage:** Supabase Storage
- **AI / NLP:** Groq API
- **Deployment:** Render
- **PDF Processing:** PyPDF2

## How to Run Locally

1. Clone the repository:
   ```bash
   git clone <your-github-repo-url>
   cd <your-project-folder>
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file in the project root and add your values:
   ```env
   SECRET_KEY=your_secret_key
   DEBUG=True
   DB_NAME=your_db_name
   DB_USER=your_db_user
   DB_PASSWORD=your_db_password
   DB_HOST=your_db_host
   DB_PORT=5432
   GROQ_API_KEY=your_groq_api_key
   SUPABASE_URL=your_supabase_url
   SUPABASE_KEY=your_supabase_key
   ```

5. Run migrations:
   ```bash
   python manage.py migrate
   ```

6. Start the development server:
   ```bash
   python manage.py runserver
   ```

7. Open the app in your browser:
   ```bash
   http://127.0.0.1:8000/
   ```

## Project Structure

- `config/` — Django project settings and URLs
- `users/` — app logic, views, models, services, templates
- `static/` — CSS and JavaScript files
- `templates/` — base templates and reusable components

## Future Improvements

- Google authentication for easier account creation
- Create Resume section with ATS-friendly resume templates
- Advanced ATS scoring with NLP
- Profile pages
- Cloud resume storage and download option

## Notes

- The app is optimized for PDF resume uploads.
- If the Render free instance is sleeping, the first request may take a while.

