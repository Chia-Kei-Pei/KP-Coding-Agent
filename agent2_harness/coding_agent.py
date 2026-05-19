import os
import time
import json
from ollama import Client, ResponseError

# ---------------------------------------------------------------------------
# Harness file loading — read context files at startup
# All files are expected to sit alongside this script.
# ---------------------------------------------------------------------------

SCRIPT_DIR    = os.path.dirname(os.path.abspath(__file__))
HARNESS_FILES = ["AGENTS.md", "init.sh", "feature_list.json", "claude-progress.md"]

def read_harness_files() -> list:
    """Read each harness file and return a list of (filename, content) tuples.
    Missing files are reported but do not abort startup."""
    contents = []
    for filename in HARNESS_FILES:
        filepath = os.path.join(SCRIPT_DIR, filename)
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                contents.append((filename, f.read()))
            print(f"[harness] Read: {filename}")
        except FileNotFoundError:
            print(f"[harness] Warning: {filename} not found — skipping.")
    return contents

def build_harness_context(contents: list) -> str:
    """Format harness file contents into a single context block for the system prompt."""
    sections = [f"=== {filename} ===\n{content}" for filename, content in contents]
    return "\n\n".join(sections)

# ---------------------------------------------------------------------------
# Initialize Ollama client
# ---------------------------------------------------------------------------

OLLAMA_HOST = "http://localhost:11434"
client = Client(host=OLLAMA_HOST)
model  = "gemma4"

# ---------------------------------------------------------------------------
# Tool definitions — read_file and write_file
# ---------------------------------------------------------------------------

tools = [
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read the content of a file from the src folder.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filename": {
                        "type": "string",
                        "description": "The filename only, e.g. 'main.py'. Do not include any folder prefix."
                    }
                },
                "required": ["filename"]
            }
        }
    },
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

# ---------------------------------------------------------------------------
# Tool implementations
# ---------------------------------------------------------------------------

def read_file(filename: str) -> str:
    """Read a file from src/<filename>."""
    safe_name = filename.lstrip("/").lstrip(".")
    file_path = os.path.join(SCRIPT_DIR, "src", safe_name)
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return f"Error: {file_path} not found."
    except Exception as e:
        return f"Error reading {file_path}: {e}"

def write_file(filename: str, content: str) -> str:
    """Write content to src/<filename>, creating directories as needed."""
    safe_name = filename.lstrip("/").lstrip(".")
    file_dir  = os.path.join(SCRIPT_DIR, "src")
    file_path = os.path.join(file_dir, safe_name)
    os.makedirs(file_dir, exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
    return f"Written to {file_path}"

def handle_tool_call(tool_name: str, tool_args: dict) -> str:
    if tool_name == "read_file":
        result = read_file(tool_args["filename"])
        print(f"[tool] Read: {tool_args['filename']}")
        return result
    if tool_name == "write_file":
        result = write_file(tool_args["filename"], tool_args["content"])
        print(f"[tool] {result}")
        return result
    return f"Unknown tool: {tool_name}"

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    harness_contents = read_harness_files()
    harness_context  = build_harness_context(harness_contents)

    system_prompt = (
        "You are a coding assistant operating inside a harness.\n\n"
        "The following files provide your context and instructions:\n\n"
        f"{harness_context}\n\n"
        "When writing code, you MUST use the write_file tool to save it to the 'src' folder. "
        "You may use the read_file tool to read existing files from the 'src' folder. "
        "Never output code blocks in your reply — always call write_file instead."
    )

    user_prompt = input("Enter your prompt: ").strip()
    start_time  = time.time()

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
                fn     = tc["function"]["name"]
                args   = tc["function"]["arguments"]
                result = handle_tool_call(fn, args)
                messages.append({
                    "role":    "tool",
                    "name":    fn,
                    "content": result
                })

    except ResponseError as e:
        raise RuntimeError(f"Ollama error: {e}") from e
    except Exception as e:
        raise RuntimeError(f"Failed to generate response: {e}") from e