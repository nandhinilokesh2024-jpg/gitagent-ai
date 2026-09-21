import os
import requests

from dotenv import load_dotenv
from google import genai
from google.genai import errors

from rag.retrieve_context import retrieve_similar_issues
from config.repository_loader import get_repository, load_repositories


# =========================
# Load environment variables
# =========================

load_dotenv()


# =========================
# Gemini
# =========================

gemini_key = os.getenv("GEMINI_API_KEY")

client = genai.Client(
    api_key=gemini_key
)


# =========================
# GitHub
# =========================

github_token = os.getenv("GITHUB_TOKEN")
github_owner = os.getenv("GITHUB_OWNER")
github_repo = os.getenv("GITHUB_REPO")


# =========================
# GitHub Repository Selection
# =========================

def set_repository(repository_name):

    repository = get_repository(repository_name)

    if repository is None:
        raise ValueError(
            f"Repository '{repository_name}' was not found."
        )

    global github_owner
    global github_repo
    global GITHUB_API_BASE

    github_owner = repository["owner"]
    github_repo = repository["repo"]

    GITHUB_API_BASE = (
        f"https://api.github.com/repos/"
        f"{github_owner}/{github_repo}"
    )


headers = {
    "Authorization": f"Bearer {github_token}",
    "Accept": "application/vnd.github+json"
}


GITHUB_API_BASE = (
    f"https://api.github.com/repos/"
    f"{github_owner}/{github_repo}"
)


# =========================
# Tool 0: Select repository
# =========================

def select_repository(repository_name):

    try:

        set_repository(repository_name)

        return {
            "success": True,
            "repository": repository_name,
            "owner": github_owner,
            "repo": github_repo,
            "message": "Repository selected successfully."
        }

    except ValueError as e:

        return {
            "success": False,
            "error": str(e)
        }


# =========================
# Tool: List repositories
# =========================

def list_repositories():

    repositories = load_repositories()

    return {
        "success": True,
        "repositories": [
            repository["name"]
            for repository in repositories
        ]
    }


# =========================
# Tool 1: Get GitHub issues
# =========================

def get_issues():

    url = f"{GITHUB_API_BASE}/issues"

    response = requests.get(
        url,
        headers=headers
    )

    if response.status_code == 200:

        return response.json()

    else:

        return {
            "success": False,
            "status_code": response.status_code,
            "error": response.text
        }


# =========================
# Tool 2: Check duplicate issue
# =========================

def issue_exists(title):

    issues = get_issues()

    if isinstance(issues, dict) and issues.get("success") is False:

        return issues

    for issue in issues:

        if issue.get("title", "").lower() == title.lower():

            return True

    return False


# =========================
# Tool 3: Create GitHub issue
# =========================

def create_issue(title, description):

    url = f"{GITHUB_API_BASE}/issues"

    data = {
        "title": title,
        "body": description
    }

    response = requests.post(
        url,
        headers=headers,
        json=data
    )

    if response.status_code == 201:

        return {
            "success": True,
            "issue_number": response.json()["number"],
            "url": response.json()["html_url"],
            "message": "GitHub issue created successfully."
        }

    else:

        return {
            "success": False,
            "status_code": response.status_code,
            "error": response.text
        }


# =========================
# Tool 4: Add comment
# =========================

def add_issue_comment(issue_number, comment):

    url = f"{GITHUB_API_BASE}/issues/{issue_number}/comments"

    data = {
        "body": comment
    }

    response = requests.post(
        url,
        headers=headers,
        json=data
    )

    if response.status_code == 201:

        return {
            "success": True,
            "issue_number": issue_number,
            "comment_url": response.json()["html_url"],
            "message": "Comment added to GitHub issue successfully."
        }

    else:

        return {
            "success": False,
            "status_code": response.status_code,
            "error": response.text
        }


# =========================
# Tool 5: Reopen issue
# =========================

def reopen_issue(issue_number):

    url = f"{GITHUB_API_BASE}/issues/{issue_number}"

    data = {
        "state": "open"
    }

    response = requests.patch(
        url,
        headers=headers,
        json=data
    )

    if response.status_code == 200:

        return {
            "success": True,
            "issue_number": issue_number,
            "message": "GitHub issue reopened successfully."
        }

    else:

        return {
            "success": False,
            "status_code": response.status_code,
            "error": response.text
        }


# =========================
# Tool 6: Add severity label
# =========================

def add_issue_label(issue_number, label):

    url = f"{GITHUB_API_BASE}/issues/{issue_number}/labels"

    data = {
        "labels": [label]
    }

    response = requests.post(
        url,
        headers=headers,
        json=data
    )

    if response.status_code == 200:

        return {
            "success": True,
            "issue_number": issue_number,
            "label": label,
            "message": "GitHub issue label added successfully."
        }

    else:

        return {
            "success": False,
            "status_code": response.status_code,
            "error": response.text
        }


# =========================
# Tool 7: Read application error log
# =========================

def read_error_log():

    with open(
        "error.log",
        "r",
        encoding="utf-8"
    ) as file:

        return file.read()


# =========================
# Analyze error severity
# =========================

def analyze_error_severity(error_log):

    if "CRITICAL" in error_log:

        return "CRITICAL"

    elif "ERROR" in error_log:

        return "HIGH"

    elif "WARNING" in error_log:

        return "MEDIUM"

    else:

        return "LOW"


# =========================
# Tool 8: Search similar issues using RAG
# =========================

def search_similar_issues(error_text):

    results = retrieve_similar_issues(
        error_text,
        repository=github_repo,
        top_k=3,
        similarity_threshold=0.60
    )

    return {
        "query": error_text,
        "repository": github_repo,
        "similar_issues": results,
        "related_issue_found": any(
            result["is_related"]
            for result in results
        )
    }


# =========================
# Give tools to Gemini
# =========================

tools = [

    # =========================
    # Tool 0: Select repository
    # =========================

    {
        "type": "function",
        "name": "select_repository",
        "description": (
            "Select the GitHub repository that GitAgent AI should "
            "work with. Use this before reading, searching, creating, "
            "or managing issues."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "repository_name": {
                    "type": "string",
                    "description": (
                        "The configured repository name to select."
                    )
                }
            },
            "required": [
                "repository_name"
            ]
        }
    },

    # =========================
    # Tool: List repositories
    # =========================

    {
        "type": "function",
        "name": "list_repositories",
        "description": (
            "List all GitHub repositories configured for GitAgent AI. "
            "Use this to discover available repositories before "
            "selecting one."
        ),
        "parameters": {
            "type": "object",
            "properties": {}
        }
    },

    # =========================
    # Tool 1: Get issues
    # =========================

    {
        "type": "function",
        "name": "get_issues",
        "description": (
            "Use this tool when the user wants to view, "
            "list, check, or find existing GitHub issues."
        ),
        "parameters": {
            "type": "object",
            "properties": {}
        }
    },

    # =========================
    # Tool 2: Create issue
    # =========================

    {
        "type": "function",
        "name": "create_issue",
        "description": (
            "Use this tool when creating a NEW GitHub issue. "
            "The description must include Severity, Problem Summary, "
            "Impact, Possible Root Cause, Error Log, and "
            "Recommended Action."
        ),
        "parameters": {
            "type": "object",
            "properties": {

                "title": {
                    "type": "string",
                    "description": "The title of the GitHub issue."
                },

                "description": {
                    "type": "string",
                    "description": (
                        "A detailed structured description of the problem."
                    )
                }
            },
            "required": [
                "title",
                "description"
            ]
        }
    },

    # =========================
    # Tool 3: Add issue comment
    # =========================

    {
        "type": "function",
        "name": "add_issue_comment",
        "description": (
            "Use this tool when the current application error "
            "is clearly related to an existing GitHub issue. "
            "Add a comment containing the new occurrence details, "
            "severity, error information, and recommended action. "
            "Do not create a duplicate issue."
        ),
        "parameters": {
            "type": "object",
            "properties": {

                "issue_number": {
                    "type": "integer",
                    "description": (
                        "The GitHub issue number that represents "
                        "the existing related problem."
                    )
                },

                "comment": {
                    "type": "string",
                    "description": (
                        "The comment to add to the existing issue."
                    )
                }
            },
            "required": [
                "issue_number",
                "comment"
            ]
        }
    },

    # =========================
    # Tool 4: Reopen issue
    # =========================

    {
        "type": "function",
        "name": "reopen_issue",
        "description": (
            "Reopen an existing GitHub issue when the current "
            "application error is related to a previously closed issue."
        ),
        "parameters": {
            "type": "object",
            "properties": {

                "issue_number": {
                    "type": "integer",
                    "description": (
                        "The GitHub issue number to reopen."
                    )
                }
            },
            "required": [
                "issue_number"
            ]
        }
    },

    # =========================
    # Tool 5: Add issue label
    # =========================

    {
        "type": "function",
        "name": "add_issue_label",
        "description": (
            "Add a severity label to a GitHub issue. "
            "Use exactly one of: severity:critical, "
            "severity:high, severity:medium, severity:low."
        ),
        "parameters": {
            "type": "object",
            "properties": {

                "issue_number": {
                    "type": "integer",
                    "description": (
                        "The GitHub issue number that should "
                        "receive the label."
                    )
                },

                "label": {
                    "type": "string",
                    "description": (
                        "The severity label, for example severity:high."
                    )
                }
            },
            "required": [
                "issue_number",
                "label"
            ]
        }
    },

    # =========================
    # Tool 6: Read error log
    # =========================

    {
        "type": "function",
        "name": "read_error_log",
        "description": (
            "Read the application error log "
            "and return the recorded errors."
        ),
        "parameters": {
            "type": "object",
            "properties": {}
        }
    },

    # =========================
    # Tool 7: Check duplicate
    # =========================

    {
        "type": "function",
        "name": "issue_exists",
        "description": (
            "Check whether a GitHub issue with the same title "
            "already exists."
        ),
        "parameters": {
            "type": "object",
            "properties": {

                "title": {
                    "type": "string",
                    "description": (
                        "The title of the issue to check."
                    )
                }
            },
            "required": [
                "title"
            ]
        }
    },

    # =========================
    # Tool 8: RAG search
    # =========================

    {
        "type": "function",
        "name": "search_similar_issues",
        "description": (
            "Use RAG semantic search to compare an application "
            "error with previous GitHub issues. Each result "
            "contains a similarity score and is_related value."
        ),
        "parameters": {
            "type": "object",
            "properties": {

                "error_text": {
                    "type": "string",
                    "description": (
                        "The application error or error log "
                        "to compare with previous issues."
                    )
                }
            },
            "required": [
                "error_text"
            ]
        }
    }
]


# =========================
# Main Gemini Agent
# =========================

def run_agent():

    user_input = """
Check the application error log.

First, use list_repositories to discover the configured
repositories.

Then select the appropriate repository using
select_repository before using any GitHub or RAG tools.

If there is an important error:

1. Read the error log.
2. Analyze its severity.
3. Use RAG to search for similar existing GitHub issues.
4. Compare the current error with the retrieved issues.
5. Use the RAG result field "is_related" as an important
   signal when deciding whether an existing issue represents
   the same problem.
6. If "related_issue_found" is false, treat the retrieved
   issues as not clearly related.
7. If "related_issue_found" is true, identify the related
   issue with the strongest relevant similarity score.

If the problem is clearly related to an existing issue:

8. Do NOT create a duplicate issue.
9. Use add_issue_comment to add the new occurrence details
   to the existing related issue.
10. Use add_issue_label to add the appropriate severity label.
11. If the related issue is CLOSED, use reopen_issue.
12. The comment should include:
    - Severity
    - New occurrence summary
    - Relevant error log
    - Possible root cause or investigation information
    - Recommended action

If the problem is not clearly related to an existing issue:

13. Check for an exact duplicate title using issue_exists.
14. If no duplicate exists, create a NEW GitHub issue with:
    - Severity
    - Problem Summary
    - Impact
    - Possible Root Cause
    - Error Log
    - Recommended Action
15. After creating the new issue, add the appropriate severity
    label to the newly created issue.

Do not create a duplicate issue when an existing issue clearly
represents the same problem.

For severity labels, use exactly one of:
severity:critical
severity:high
severity:medium
severity:low
"""

    # =========================
    # Send request to Gemini
    # =========================

    try:

        interaction = client.interactions.create(
            model="gemini-3.6-flash",
            input=user_input,
            tools=tools
        )

    except errors.APIError as e:

        print("\nGemini API error occurred.")
        print("Error:", e)

        return

    # =========================
    # Handle Gemini tool calls
    # =========================

    current_interaction = interaction

    while True:

        tool_called = False

        for step in current_interaction.steps:

            if step.type != "function_call":

                continue

            tool_called = True

            # =========================
            # Execute selected tool
            # =========================

            if step.name == "select_repository":

                repository_name = step.arguments["repository_name"]

                result = select_repository(
                    repository_name
                )

            elif step.name == "list_repositories":

                result = list_repositories()

            elif step.name == "get_issues":

                result = get_issues()

            elif step.name == "create_issue":

                title = step.arguments["title"]

                description = step.arguments["description"]

                result = create_issue(
                    title,
                    description
                )

            elif step.name == "add_issue_comment":

                issue_number = step.arguments["issue_number"]

                comment = step.arguments["comment"]

                result = add_issue_comment(
                    issue_number,
                    comment
                )

            elif step.name == "reopen_issue":

                issue_number = step.arguments["issue_number"]

                result = reopen_issue(
                    issue_number
                )

            elif step.name == "add_issue_label":

                issue_number = step.arguments["issue_number"]

                label = step.arguments["label"]

                result = add_issue_label(
                    issue_number,
                    label
                )

            elif step.name == "read_error_log":

                result = read_error_log()

            elif step.name == "issue_exists":

                title = step.arguments["title"]

                result = issue_exists(title)

            elif step.name == "search_similar_issues":

                error_text = step.arguments["error_text"]

                result = search_similar_issues(
                    error_text
                )

            else:

                print(
                    "Unknown Gemini tool:",
                    step.name
                )

                continue

            # =========================
            # Show selected tool
            # =========================

            print("\n========================================")
            print("Gemini selected:", step.name)
            print("========================================")

            print("\nTool result:")

            print(result)

            # =========================
            # Send tool result to Gemini
            # =========================

            try:

                current_interaction = client.interactions.create(
                    model="gemini-3.6-flash",
                    previous_interaction_id=current_interaction.id,
                    input=[
                        {
                            "type": "function_result",
                            "name": step.name,
                            "call_id": step.id,
                            "result": {
                                "result": result
                            }
                        }
                    ],
                    tools=tools
                )

            except errors.APIError as e:

                print("\nGemini API error occurred.")

                print(
                    "The selected tool was completed, "
                    "but Gemini could not continue."
                )

                print("Error:", e)

                return

            # Process one Gemini function call at a time.

            break

        # =========================
        # No more tools requested
        # =========================

        if not tool_called:

            print("\n========================================")
            print("Gemini's final answer")
            print("========================================")

            print(
                current_interaction.output_text
            )

            break


# =========================
# Local severity check
# =========================

def show_local_severity():

    try:

        error_log = read_error_log()

        severity = analyze_error_severity(
            error_log
        )

        print("\n========================================")
        print("Local Error Severity")
        print("========================================")

        print(
            "Error Severity:",
            severity
        )

    except FileNotFoundError:

        print("\nerror.log was not found.")


# =========================
# IMPORTANT
# Only run Gemini when this
# file is executed directly.
# =========================

if __name__ == "__main__":

    run_agent()

    show_local_severity()