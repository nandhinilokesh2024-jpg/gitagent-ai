from retrieve_context import retrieve_similar_issues


query = "The email notification service failed while trying to send an email."


print("Searching for similar issues...")
print("Query:", query)


results = retrieve_similar_issues(query, top_k=3)


print("\nRetrieved Context:\n")


for result in results:

    print("----------------------------------------")
    print(f"Issue #{result['issue_number']}")
    print(f"Title: {result['title']}")
    print(f"Similarity: {result['score']:.4f}")

    print("\nContext:")
    print(result["text"])

    print("----------------------------------------")