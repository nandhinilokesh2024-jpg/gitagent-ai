import os
import json
import requests
from dotenv import load_dotenv

import sys

sys.path.append(
    os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__)
        )
    )
)

from config.repository_loader import load_repositories

# Load variables from .env
load_dotenv()

# GitHub settings
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

# Authentication headers
headers = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json"
}


def collect_repository_issues(repository):
    owner = repository["owner"]
    repo = repository["repo"]

    url = f"https://api.github.com/repos/{owner}/{repo}/issues"

    print(f"\nCollecting issues from: {owner}/{repo}")

    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        print("Failed to fetch GitHub issues.")
        print("Status code:", response.status_code)
        print("Response:", response.text)
        return

    issues = response.json()

    # Prepare data for RAG
    knowledge = []

    for issue in issues:

        # Ignore pull requests
        if "pull_request" in issue:
            continue

        knowledge.append({
            "issue_number": issue["number"],
            "title": issue["title"],
            "description": issue["body"] or "",
            "state": issue["state"],
            "labels": [label["name"] for label in issue["labels"]],
            "url": issue["html_url"]
        })

    # Save repository-specific knowledge
    output_filename = f"{repo}_issues.json"

    output_path = os.path.join(
        os.path.dirname(__file__),
        "documents",
        output_filename
    )

    with open(output_path, "w", encoding="utf-8") as file:
        json.dump(
            knowledge,
            file,
            indent=4,
            ensure_ascii=False
        )

    print("Issues collected:", len(knowledge))
    print("Saved to:", output_path)


def collect_all_repositories():

    repositories = load_repositories()

    print("Repositories found:", len(repositories))

    for repository in repositories:
        collect_repository_issues(repository)


if __name__ == "__main__":
    collect_all_repositories()