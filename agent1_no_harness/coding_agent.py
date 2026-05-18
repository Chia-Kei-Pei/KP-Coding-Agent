import os
import time
from ollama import Client, ResponseError

# Initialize Ollama Client with configurable host
OLLAMA_HOST = "http://localhost:11434"
client = Client(host=OLLAMA_HOST)
model = "gemma4"

# --- Tool definition ---
tools = [
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Write content to a file. Always use this to save code — never output code in your reply.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filename": {
                        "type": "string",
                        "description": "The filename only, e.g. 'main.py' or 'helpers.js'. Do not include any folder prefix."
                    },
                    "content": {
                        "type": "string",
                        "description": "The full file content to write."
                    }
                },
                "required": ["filename", "content"]
            }
        }
    }
]

def write_file(filename: str, content: str) -> str:
    """Write content to src/<filename>, creating directories as needed."""
    # Sanitize: strip leading slashes/dots to prevent path traversal
    safe_name = filename.lstrip("/").lstrip(".")
    # Resolve src/ relative to this script, not the working directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    filepath = os.path.join(script_dir, "src", safe_name)
    os.makedirs(os.path.dirname(filepath) or os.path.join(script_dir, "src"), exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    return f"Written to {filepath}"

def handle_tool_call(tool_name: str, tool_args: dict) -> str:
    """Dispatch tool calls returned by the model."""
    if tool_name == "write_file":
        result = write_file(tool_args["filename"], tool_args["content"])
        print(f"[tool] {result}")
        return result
    return f"Unknown tool: {tool_name}"

if __name__ == "__main__":
    system_prompt = (
        "You are a coding assistant. "
        "When writing code, you MUST use the write_file tool to save it to the 'src' folder. "
        "Never output code blocks in your reply — always call write_file instead."
    )
    user_prompt = input("Enter your prompt: ").strip()
    start_time = time.time()

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user",   "content": user_prompt}
    ]

    try:
        # Agentic loop: keep going until the model stops calling tools
        while True:
            response = client.chat(model=model, messages=messages, tools=tools)
            msg = response["message"]

            # Append the assistant turn to history
            messages.append({"role": "assistant", "content": msg.get("content", ""), "tool_calls": msg.get("tool_calls")})

            tool_calls = msg.get("tool_calls") or []
            if not tool_calls:
                # No more tool calls — print the final reply and exit
                print(msg.get("content", "").strip())
                elapsed = time.time() - start_time
                hours, rem = divmod(elapsed, 3600)
                minutes, seconds = divmod(rem, 60)
                print(f"\nTime taken: {int(hours):02}:{int(minutes):02}:{seconds:05.2f}")
                break

            # Execute each tool call and feed results back
            for tc in tool_calls:
                fn   = tc["function"]["name"]
                args = tc["function"]["arguments"]
                result = handle_tool_call(fn, args)
                messages.append({
                    "role": "tool",
                    "name": fn,
                    "content": result
                })

    except ResponseError as e:
        raise RuntimeError(f"Ollama error: {e}") from e
    except Exception as e:
        raise RuntimeError(f"Failed to generate response: {e}") from e