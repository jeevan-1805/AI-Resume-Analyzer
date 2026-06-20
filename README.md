# AI Resume Analyser

An ATS-focused modern resume analysis web application and professional networking platform built with Django, Supabase, and AI-powered resume feedback. Users can upload a PDF resume, get ATS score insights, strength analysis, job-role recommendations, executive summary optimization and share resumes with other users.

## Live Demo

Render deployment: https://ai-resume-analyser-y5cv.onrender.com/

> **Important:** The first load on Render can take **40–60 seconds** because the free web service may need time to wake up and load Python packages. Please wait a little before refreshing.

## The platform helps users:

- Analyze resumes using ATS-based scoring
- Receive AI-generated resume feedback
- Generate professional executive summaries
- Share resumes publicly
- Connect with other users
- Discuss resumes through private messaging
- Build a professional online presence

## Core Features

### Resume Analysis

- ATS Score Calculation
- Resume Strength Score
- ATS-Friendly Resume Evaluation
- Resume Parsing
- Resume Storage
- Resume Management

### AI-Powered Features

- AI Resume Feedback
- Missing Skills Detection
- Resume Strength Analysis
- Resume Weakness Analysis
- Keyword Suggestions
- Executive Summary Generator

### Public Resume Community

- Public Resume Feed
- Resume Sharing
- Resume Comments
- Resume Discussion
- Resume Discovery

### Professional Networking

- User Profiles
- Display Names
- Profile Pictures
- Resume Sharing
- Private Messaging

### Realtime Communication

- User Profiles
- Display Names
- Profile Pictures
- Resume Sharing
- Private Messaging

### Authentication


- Username / Password Authentication
- Google Authentication
- Account Linking
- Secure Password Management

### User Experience

- Responsive Mobile Design
- Notification System
- Public Feed Navigation
- Resume Commenting System
- Improved ATS Scoring Engine

## Tech Stack

- **Backend:** Python, Django
- **Frontend:** HTML, CSS, JavaScript
- **Database:** Supabase PostgreSQL
- **Storage:** Supabase Storage
- **AI / NLP:** Groq API
- **Deployment:** Render
- **Authentication:** Django Allauth

## Version History

### Version 1

Version 1 introduced the foundation of the project:

#### Features:

- Resume Upload
- Resume Storage
- Basic ATS Scoring
- AI Resume Feedback
- Executive Summary Generator
- User Authentication
- Google Authentication
- Resume Management Dashboard

Version 1 successfully proved the concept of AI-assisted resume analysis.

***

### Version 1: Remastered

Version 1: Remastered transforms the project into a professional resume community platform.

#### New Features

- Public Resume Feed
- Resume Comments
- Realtime Chat System
- Resume Sharing Through Chat
- Notification Center
- Live Notification Badge Updates
- Mobile Responsive UI
- Public Resume Discovery
- Resume Discussion System

### Planned Enhancements For Version 1: Remastered

- [x] Improved ATS Engine
- [x] Summary Detection Scoring
- [x] Technical Skill Detection
- [x] Project Detection
- [x] Achievement Detection
- [x] Improved Resume Strength Calculation
- [x] Improved Account Security
- [x] Improved Google Account Management
- [x] NLP based ATS calculation
- [x] Welcome Page for render deployement
- [ ] Portfolio Section
- [ ] AI Resume Comparison summary
- [ ] Strength score based leveling System
- [ ] ATS Breakdown Dashboard
- [ ] JD Match Score - Job description vs Resume match analysis


## Long-Term Future Vision (Version 2)

Version 2 expands the platform from resume analysis into a complete professional networking and hiring ecosystem.

### Recruiter Platform

- Recruiter Login
- Recruiter Profiles
- Job Vacancy Publishing
- Candidate Discovery

### Professional Networking

- Follow System
- Friends System
- Friend Requests
- Professional Connections

### Portfolio Expansion

- Project Showcase Cards
- GitHub Integration
- Project Media Uploads
- Visual Project Galleries


### Professional Identity

- LinkedIn Profile Integration
- Enhanced User Profiles
- Professional Portfolio Pages

### Create Resume 

- A section for creating ATS friendly resumes
- Will come with ATS-friendly resume templates


## Intelligent Hiring System

### TalentMatch AI

TalentMatch AI automatically connects recruiters and candidates.

#### For Recruiters

- Post Job Vacancies
- Upload Job Descriptions
- Automatically Discover Matching Resumes
- Receive Ranked Candidate Suggestions

#### For Candidates

- Receive Relevant Job Opportunities
- Match Based On Skills
- Match Based On Executive Summary
- Match Based On Public Resume Content

TalentMatch AI creates a two-way recommendation engine where recruiters discover qualified candidates and candidates discover relevant opportunities.

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

## Notes

- The app is optimized for PDF resume uploads.
- If the Render free instance is sleeping, the first request may take a while.

***
# Author

## Built by Jeevan Y

<p align="center">Focused on Python, Django, Artificial Intelligence, Machine Learning, and Full Stack Development.</p>

