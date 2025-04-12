import requests

# Get user query
query = input("Enter your legal query: ")

# Send POST request to your running FastAPI endpoint
response = requests.post(
    "http://localhost:8000/search",
    json={"query": query, "top_k": 5}
)

# Check response and print results nicely
if response.status_code == 200:
    data = response.json()
    for res in data["results"]:
        print(f"\nArticle Number: {res['article_number']}")
        print(f"Full Article Text: {res['full_article']}")
        print(f"Relevant Chunk: {res['chunk_content']}")
        print("-" * 40)
else:
    print("Error:", response.status_code, response.text)
