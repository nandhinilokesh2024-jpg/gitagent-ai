import json
import os

from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity


# Load variables from .env
load_dotenv()

# Get repository name
REPO = os.getenv("GITHUB_REPO")

# Repository-specific embedding file
embedding_filename = f"{REPO}_issue_embeddings.json"

embedding_path = os.path.join(
    os.path.dirname(__file__),
    "vector_db",
    embedding_filename
)


# Load saved embeddings
with open(
    embedding_path,
    "r",
    encoding="utf-8"
) as file:

    data = json.load(file)

print("Loaded embeddings:", len(data))


# Load the same embedding model
print("Loading embedding model...")

model = SentenceTransformer(
    "all-MiniLM-L6-v2"
)

print("Embedding model loaded successfully!")


# New error we want to search for
query = "Users are unable to log in to the application."

print("\nNew error:")
print(query)


# Convert the new error into an embedding
query_embedding = model.encode(
    [query]
)


# Get stored embeddings
stored_embeddings = [
    item["embedding"]
    for item in data
]


# Calculate similarity
similarities = cosine_similarity(
    query_embedding,
    stored_embeddings
)[0]


# Combine issues with their similarity scores
results = []

for item, score in zip(
    data,
    similarities
):

    results.append({
        "issue_number": item["issue_number"],
        "title": item["title"],
        "text": item["text"],
        "score": float(score)
    })


# Sort from most similar to least similar
results.sort(
    key=lambda x: x["score"],
    reverse=True
)


# Display top 3 results
print("\nMost similar issues:")

for result in results[:3]:

    print("\n----------------------------------------")

    print(f"Issue #{result['issue_number']}")
    print(f"Title: {result['title']}")
    print(f"Similarity: {result['score']:.4f}")

    print("\nIssue Context:")
    print(result["text"])

    print("----------------------------------------")