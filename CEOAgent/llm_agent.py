import requests


OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "llama3.1:8b"


def generate_response(prompt: str) -> str:
    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.2,
            "top_p": 0.8,
            "num_predict": 2048,
            "num_ctx": 4096
        }
    }

    response = requests.post(
        OLLAMA_URL,
        json=payload,
        timeout=600
    )

    response.raise_for_status()

    return response.json()["response"]