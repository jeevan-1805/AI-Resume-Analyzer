# ATS Crack Resume Specification v1.0

## Purpose

The ATS Crack Score measures how likely a resume is to successfully pass through an Applicant Tracking System (ATS) before reaching a recruiter.

This score is independent of any specific job description. It evaluates the resume based on completeness, structure, formatting, readability, and ATS compatibility.

The ATS Crack Score is always calculated out of **100**.

---

# ATS Crack Score Architecture

The score is divided into four independent categories.

| Category             |  Weight |
| -------------------- | ------: |
| Resume Completeness  |      25 |
| Section Completeness |      40 |
| Layout & Formatting  |      25 |
| Grammar & Language   |      10 |
| **TOTAL**            | **100** |

Each category is calculated independently and contributes to the final ATS Crack Score.

---

# Resume Completeness (25)

This category checks whether the resume contains all essential sections expected by modern ATS software.

Required sections:

* Name
* Contact Information
* Professional Summary / Objective
* Technical Skills
* Experience
* Projects
* Education
* Certifications / Achievements

Missing sections reduce the score.

---

# Section Completeness (40)

Each detected section is evaluated for completeness.

## Contact

Expected:

* Phone Number
* Email Address
* Location
* LinkedIn Profile
* GitHub Profile

## Professional Summary

Expected:

* Current role
* Career objective
* Professional overview

## Skills

Expected:

* Minimum six skills
* Skills relevant to the professional summary

## Experience

Each experience should include:

* Role
* Company
* Duration
* Description

## Projects

Each project should include:

* Project title
* Technologies used
* Project description

## Education

Expected:

* Degree
* Institution
* Graduation Year

## Certifications

Expected:

* Certificate name
* Issuing platform
* Completion year

Groq AI performs semantic validation to determine whether skills, projects, and experiences are relevant to the professional summary.

---

# Layout & Formatting (25)

This category evaluates ATS compatibility.

The score begins with the full 25 points.

Penalties are applied for:

* Multi-column layouts
* Decorative icons or symbols
* Hidden or invisible text
* Profile photographs
* Other ATS parsing issues

The score cannot fall below zero.

---

# Grammar & Language (10)

Grammar is evaluated using LanguageTool.

The score begins with 10 points.

Penalties are applied for:

* Grammar mistakes
* Spelling mistakes
* Capitalization issues
* Punctuation issues
* Writing style issues

Grammar contributes to recruiter readability while maintaining ATS compatibility.

---

# ATS Breakdown

Every scoring category returns:

* Score
* Breakdown
* Detection Details

This information powers:

* ATS Dashboard
* Resume Comparison
* Resume Improvement Suggestions

---

# Future Extensions

The ATS Crack Score is intentionally independent from Job Description matching.

Future versions introduce:

* JD Match Score
* Recruiter Recommendation Engine
* Resume Comparison Dashboard
* ATS Breakdown Dashboard
* Resume Quality Analytics

---

# Version History

## Version 1.0

Initial ATS Crack Score architecture.

Includes:

* Resume Completeness
* Section Completeness
* Layout & Formatting
* Grammar & Language

This version establishes the engineering specification for all future ATS calculations.
