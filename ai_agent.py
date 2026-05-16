import os
from ollama import Client, ResponseError

# Initialize Ollama Client with configurable host
OLLAMA_HOST = "http://localhost:11434"
client = Client(host=OLLAMA_HOST)
model = "gemma4"

if __name__ == "__main__":
    system_prompt = "You are my assistant"
    user_prompt = input("Enter your prompt: ").strip()

    messages = [
        {
            "role": "system",
            "content": system_prompt
        },
        {
            "role": "user",
            "content": user_prompt
        }
    ]
    
    try:
        response = client.chat(model=model, messages=messages)
        # return response["message"]["content"].strip()
        print(response["message"]["content"])
    except ResponseError as e:
        raise RuntimeError(f"Ollama error: {e}") from e
    except Exception as e:
        raise RuntimeError(f"Failed to generate response: {e}") from e
