import requests
import os
from dotenv import load_dotenv

load_dotenv()

token = os.getenv("GITHUB_TOKEN")

headers = {
    "Authorization": f"Bearer {token}",
    "Accept": "application/vnd.github+json"
}

url = "https://api.github.com/repos/nandhinilokesh2024-jpg/gitagent-ai"

response = requests.get(url, headers=headers)

print(response.status_code)
print(response.json())