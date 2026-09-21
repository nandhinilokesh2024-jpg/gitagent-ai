import requests
import os
from dotenv import load_dotenv

load_dotenv()

token = os.getenv("GITHUB_TOKEN")

headers = {
    "Authorization": f"Bearer {token}",
    "Accept": "application/vnd.github+json"
}


def get_issues():
    url = "https://api.github.com/repos/nandhinilokesh2024-jpg/gitagent-ai/issues"

    response = requests.get(url, headers=headers)

    return response.json()


issues = get_issues()

for issue in issues:
    print("Issue Number:", issue["number"])
    print("Title:", issue["title"])
    print("Status:", issue["state"])
    print("Description:", issue["body"])
    print("--------------------")

print(issues)
def create_issue(title, description):
    url = "https://api.github.com/repos/nandhinilokesh2024-jpg/gitagent-ai/issues"

    data = {
        "title": title,
        "body": description
    }

    response = requests.post(url, headers=headers, json=data)

    return response.json()
result = create_issue(
    "Login Bug",
    "The login button is not working."
)

print("Issue created!")
print("Issue Number:", result["number"])
print("Title:", result["title"])
print("Status:", result["state"])
print("URL:", result["html_url"])