import os
import sys

from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config.repository_loader import load_repositories


app = FastAPI(title="GitAgent AI API")


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
    "http://localhost:5173",
    "https://gitagent-ai.vercel.app"
],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {
        "message": "GitAgent AI API is running"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }


@app.get("/repositories")
def repositories():
    return {
        "success": True,
        "repositories": [
            repository["name"]
            for repository in load_repositories()
        ]
    }


@app.get("/issues")
def issues():
    import os
    import requests

    github_token = os.getenv("GITHUB_TOKEN")
    github_owner = os.getenv("GITHUB_OWNER")
    github_repo = os.getenv("GITHUB_REPO")

    url = f"https://api.github.com/repos/{github_owner}/{github_repo}/issues"

    headers = {
        "Authorization": f"Bearer {github_token}",
        "Accept": "application/vnd.github+json"
    }

    response = requests.get(
        url,
        headers=headers,
        timeout=15
    )

    if response.status_code == 200:
        return response.json()

    return {
        "success": False,
        "status_code": response.status_code,
        "error": response.text
    }


@app.post("/analyze")
def analyze_error(data: dict):

    from rag.retrieve_context import retrieve_similar_issues
    from gemini_agent import create_issue, get_issues

    error_text = data.get("error", "").strip()

    repository_name = data.get(
             "repository",
            "gitagent-ai"
          ).strip()
    if not error_text:
        return {
            "success": False,
            "error": "Please enter an error message."
        }

    # --------------------------------
    # Severity Detection
    # --------------------------------

    error_upper = error_text.upper()

    if (
        "CRITICAL" in error_upper
        or "DATA LOSS" in error_upper
        or "DATA CORRUPTION" in error_upper
        or "SECURITY BREACH" in error_upper
    ):
        severity = "CRITICAL"

    elif (
        "ERROR" in error_upper
        or "FAILED" in error_upper
        or "FAILURE" in error_upper
        or "EXCEPTION" in error_upper
        or "CRASH" in error_upper
        or "CORRUPTION" in error_upper
        or "TIMEOUT" in error_upper
        or "SERVICE DOWN" in error_upper
    ):
        severity = "HIGH"

    elif (
        "WARNING" in error_upper
        or "DEGRADED" in error_upper
        or "SLOW" in error_upper
    ):
        severity = "MEDIUM"

    else:
        severity = "LOW"

    # --------------------------------
    # RAG Search
    # --------------------------------

    similar_issues = retrieve_similar_issues(
        error_text,
        repository=repository_name,
        top_k=3,
        similarity_threshold=0.60
    )

    related_issues = [
        issue
        for issue in similar_issues
        if issue["is_related"]
    ]

    # --------------------------------
    # Existing Related Issue Found
    # --------------------------------

    if related_issues:
        return {
            "success": True,
            "error": error_text,
            "severity": severity,
            "action": "existing_issue_found",
            "similar_issues": similar_issues
        }

    # --------------------------------
    # Duplicate Check
    # --------------------------------

    latest_issues = get_issues()

    duplicate_issue = None

    target_title = (
        f"Application Error: {error_text[:80]}"
    ).strip().lower()

    for issue in latest_issues:

        issue_title = (
            issue["title"]
            .strip()
            .lower()
        )

        if issue_title == target_title:
            duplicate_issue = issue
            break

    # --------------------------------
    # Duplicate Found
    # --------------------------------

    if duplicate_issue:
        return {
            "success": True,
            "error": error_text,
            "severity": severity,
            "action": "existing_issue_found",
            "similar_issues": similar_issues,
            "duplicate_issue": {
                "issue_number": duplicate_issue["number"],
                "title": duplicate_issue["title"],
                "url": duplicate_issue["html_url"]
            }
        }

    # --------------------------------
    # Create New GitHub Issue
    # --------------------------------

    title = f"Application Error: {error_text[:80]}"

    description = f"""## Severity

{severity}

## Problem Summary

{error_text}

## Detection

GitAgent AI analyzed this application error and did not find a sufficiently similar existing GitHub issue.

## Recommended Action

Investigate the application logs and identify the root cause of this error.
"""

    created_issue = create_issue(
        title,
        description
    )

    return {
        "success": True,
        "error": error_text,
        "severity": severity,
        "action": "new_issue_created",
        "similar_issues": similar_issues,
        "created_issue": created_issue
    }