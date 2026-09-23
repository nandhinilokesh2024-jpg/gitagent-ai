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
    from config.repository_loader import load_repositories

    return {
        "success": True,
        "repositories": [
            repository["name"]
            for repository in load_repositories()
        ]
    }


@app.get("/issues")
def issues():
    import requests

    github_token = os.getenv("GITHUB_TOKEN")
    github_owner = os.getenv("GITHUB_OWNER")
    github_repo = os.getenv("GITHUB_REPO")

    url = (
        f"https://api.github.com/repos/"
        f"{github_owner}/{github_repo}/issues"
    )

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
    import requests

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
    # GitHub Configuration
    # --------------------------------

    github_token = os.getenv("GITHUB_TOKEN")
    github_owner = os.getenv("GITHUB_OWNER")
    github_repo = os.getenv("GITHUB_REPO")

    headers = {
        "Authorization": f"Bearer {github_token}",
        "Accept": "application/vnd.github+json"
    }

    github_url = (
        f"https://api.github.com/repos/"
        f"{github_owner}/{github_repo}/issues"
    )

    # --------------------------------
    # Lightweight GitHub Issue Search
    # --------------------------------
    #
    # This replaces the heavy SentenceTransformer/RAG
    # loading inside the Render request.
    #
    # The GitAgent AI project still contains the full
    # RAG implementation separately.
    # --------------------------------

    try:
        response = requests.get(
            github_url,
            headers=headers,
            params={
                "state": "open",
                "per_page": 30
            },
            timeout=15
        )

        if response.status_code != 200:
            return {
                "success": False,
                "error": "Unable to retrieve GitHub issues.",
                "status_code": response.status_code
            }

        latest_issues = response.json()

    except Exception as exc:
        return {
            "success": False,
            "error": f"GitHub connection failed: {str(exc)}"
        }

    # --------------------------------
    # Find Similar / Related Issues
    # --------------------------------

    error_words = {
        word.lower()
        for word in error_text.split()
        if len(word) >= 4
    }

    similar_issues = []

    for issue in latest_issues:

        issue_title = issue.get("title", "")

        issue_body = issue.get("body") or ""

        combined_text = (
            f"{issue_title} {issue_body}"
        ).lower()

        matched_words = [
            word
            for word in error_words
            if word in combined_text
        ]

        if matched_words:

            similarity = round(
                len(matched_words) / max(len(error_words), 1),
                2
            )

            similar_issues.append({
                "issue_number": issue.get("number"),
                "title": issue_title,
                "url": issue.get("html_url"),
                "similarity_score": similarity,
                "is_related": similarity >= 0.50
            })

    similar_issues.sort(
        key=lambda item: item["similarity_score"],
        reverse=True
    )

    similar_issues = similar_issues[:3]

    # --------------------------------
    # Existing Related Issue
    # --------------------------------

    related_issues = [
        issue
        for issue in similar_issues
        if issue["is_related"]
    ]

    if related_issues:

        return {
            "success": True,
            "error": error_text,
            "severity": severity,
            "action": "existing_issue_found",
            "repository": repository_name,
            "similar_issues": similar_issues
        }

    # --------------------------------
    # Exact Duplicate Check
    # --------------------------------

    target_title = (
        f"Application Error: {error_text[:80]}"
    ).strip().lower()

    duplicate_issue = None

    for issue in latest_issues:

        issue_title = (
            issue.get("title", "")
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
            "repository": repository_name,
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

    title = (
        f"Application Error: {error_text[:80]}"
    )

    description = f"""## Severity

{severity}

## Problem Summary

{error_text}

## Detection

GitAgent AI analyzed this application error and did not find a sufficiently similar existing GitHub issue.

## Recommended Action

Investigate the application logs and identify the root cause of this error.
"""

    create_response = requests.post(
        github_url,
        headers=headers,
        json={
            "title": title,
            "body": description
        },
        timeout=15
    )

    if create_response.status_code in (200, 201):

        created_issue = create_response.json()

        return {
            "success": True,
            "error": error_text,
            "severity": severity,
            "action": "new_issue_created",
            "repository": repository_name,
            "similar_issues": similar_issues,
            "created_issue": {
                "issue_number": created_issue.get("number"),
                "title": created_issue.get("title"),
                "url": created_issue.get("html_url")
            }
        }

    return {
        "success": False,
        "error": "Unable to create GitHub issue.",
        "status_code": create_response.status_code,
        "github_response": create_response.text
    }