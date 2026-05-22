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

def build_harness_context() -> str:
    """Read each harness file and build a single context block for the system prompt.
    Missing files are reported but do not abort startup."""
    sections = []
    for filename in HARNESS_FILES:
        filepath = os.path.join(SCRIPT_DIR, filename)
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                sections.append(f"=== {filename} ===\n{f.read()}")
            print(f"[harness] Read: {filename}")
        except FileNotFoundError:
            print(f"[harness] Warning: {filename} not found — skipping.")
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
            "description": "Read the content of a file.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "The absolute file path including file directory and file name, e.g. 'C:\\Users\\User\\Documents\\file.txt'. Never use relative file path such as '.\\Documents\\file.txt'."
                    }
                },
                "required": ["file_path"]
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
                    "file_path": {
                        "type": "string",
                        "description": "The absolute file path including file directory and file name, e.g. 'C:\\Users\\User\\Documents\\file.txt'. Never use relative file path such as '.\\Documents\\file.txt'."
                    },
                    "content": {
                        "type": "string",
                        "description": "The full file content to write."
                    }
                },
                "required": ["file_path", "content"]
            }
        }
    }
]

# ---------------------------------------------------------------------------
# Tool implementations
# ---------------------------------------------------------------------------

def read_file(file_path: str) -> str:
    """Read a file from <file_path>. Always use absolute file path."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return f"Error: {file_path} not found."
    except Exception as e:
        return f"Error reading {file_path}: {e}"

def write_file(file_path: str, content: str) -> str:
    """Write content to <file_path>, creating directories as needed. Always use absolute file path."""
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
    return f"Written to {file_path}"

def handle_tool_call(tool_name: str, tool_args: dict) -> str:
    if tool_name == "read_file":
        result = read_file(tool_args["file_path"])
        print(f"[tool] read_file: {tool_args["file_path"]}")
        return result
    if tool_name == "write_file":
        result = write_file(tool_args["file_path"], tool_args["content"])
        print(f"[tool] write_file: {tool_args["file_path"]}")
        return result
    return f"[tool] {tool_name}: UNKNOWN"

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    harness_context = build_harness_context()

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