import json
import os
import sys

from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer


# Add project root to Python path
sys.path.append(
    os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__)
        )
    )
)

from config.repository_loader import load_repositories


# Load environment variables
load_dotenv()


# Load embedding model once
print("Loading embedding model...")

model = SentenceTransformer("all-MiniLM-L6-v2")

print("Embedding model loaded successfully!")


def create_repository_embeddings(repository):

    repo = repository["repo"]

    input_filename = f"{repo}_issues.json"

    input_path = os.path.join(
        os.path.dirname(__file__),
        "documents",
        input_filename
    )

    # Check whether issue data exists
    if not os.path.exists(input_path):
        print(f"\nIssue file not found for repository: {repo}")
        print("Expected:", input_path)
        print("Skipping this repository.")
        return

    # Load GitHub issues
    with open(
        input_path,
        "r",
        encoding="utf-8"
    ) as file:
        issues = json.load(file)

    print(f"\nCreating embeddings for: {repo}")
    print("Number of issues loaded:", len(issues))

    # Create text for each issue
    documents = []

    for issue in issues:

        text = f"""
Title: {issue['title']}

Description: {issue['description']}

State: {issue['state']}

Labels: {', '.join(issue['labels'])}
"""

        documents.append(text.strip())

    # Generate embeddings
    print("Creating embeddings...")

    embeddings = model.encode(documents)

    print("Embeddings created successfully!")
    print("Number of embeddings:", len(embeddings))

    if len(embeddings) > 0:
        print("Embedding size:", len(embeddings[0]))

    # Prepare data to save
    embedding_data = []

    for issue, text, embedding in zip(
        issues,
        documents,
        embeddings
    ):

        embedding_data.append({
            "issue_number": issue["issue_number"],
            "title": issue["title"],
            "text": text,
            "embedding": embedding.tolist()
        })

    # Save embeddings
    output_filename = f"{repo}_issue_embeddings.json"

    output_path = os.path.join(
        os.path.dirname(__file__),
        "vector_db",
        output_filename
    )

    with open(
        output_path,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            embedding_data,
            file,
            indent=2
        )

    print("Embeddings saved successfully!")
    print("Saved to:", output_path)


def create_all_embeddings():

    repositories = load_repositories()

    print("\nRepositories found:", len(repositories))

    for repository in repositories:
        create_repository_embeddings(repository)


if __name__ == "__main__":
    create_all_embeddings()