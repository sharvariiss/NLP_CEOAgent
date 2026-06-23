import requests

r = requests.post(
    "http://localhost:11434/api/generate",
    json={
        "model": "llama3.1:8b",
        "prompt": "hello",
        "stream": False
    }
)

print(r.json()["response"])