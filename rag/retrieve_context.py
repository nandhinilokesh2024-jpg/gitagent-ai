import json
import os

from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity


# Load variables from .env
load_dotenv()


# Default repository name
DEFAULT_REPO = os.getenv("GITHUB_REPO")


def retrieve_similar_issues(
    query,
    repository=None,
    top_k=3,
    similarity_threshold=0.60
):

    # Use the default repository if no repository is specified
    if repository is None:
        repository = DEFAULT_REPO

    # Repository-specific embedding file
    embedding_filename = f"{repository}_issue_embeddings.json"

    embedding_path = os.path.join(
        os.path.dirname(__file__),
        "vector_db",
        embedding_filename
    )

    # Load stored embeddings
    with open(
        embedding_path,
        "r",
        encoding="utf-8"
    ) as file:

        data = json.load(file)

    # Load embedding model
    model = SentenceTransformer(
        "all-MiniLM-L6-v2"
    )

    # Convert query into embedding
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

    results = []

    for item, score in zip(
        data,
        similarities
    ):

        score = float(score)

        results.append({
            "issue_number": item["issue_number"],
            "title": item["title"],
            "text": item["text"],
            "score": score,
            "is_related": score >= similarity_threshold
        })

    # Sort by similarity
    results.sort(
        key=lambda x: x["score"],
        reverse=True
    )

    return results[:top_k]