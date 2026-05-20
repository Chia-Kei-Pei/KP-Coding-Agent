import os
import time
import json
from ollama import Client, ChatResponse, ResponseError

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
        filepath = os.path.join(SCRIPT_DIR, "harness", filename)
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
MODEL  = "gemma4"
client = Client(host=OLLAMA_HOST)

# ---------------------------------------------------------------------------
# Tool implementations
# See https://docs.ollama.com/capabilities/tool-calling#python
# ---------------------------------------------------------------------------

def read_file(file_path: str) -> str:
    """Read a file and return its contents.
    REQUIRED: file_path must always be provided as an absolute path, e.g. 'C:/Users/User/project/src/file.py'.
    Never use a relative path."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return f"Error: {file_path} not found."
    except Exception as e:
        return f"Error reading {file_path}: {e}"

def write_file(file_path: str, content: str) -> str:
    """Write content to a file, creating directories as needed.
    REQUIRED: file_path must always be provided as an absolute path, e.g. 'C:/Users/User/project/src/file.py'.
    content is the full file content to write.
    Never use a relative path. Always use this tool to save code — never output code in your reply."""
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
    return f"Written to {file_path}"

available_functions = {
    "read_file": read_file,
    "write_file": write_file
}

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
        "Never output code blocks in your reply — always call write_file instead. "
        f"Your working directory is {SCRIPT_DIR}, search from here if user asks to read/write files while specifying a relative directory. "
        "Always use absolute file paths when using read_file/write_file tools, never relative file paths. "
        "When calling write_file, you MUST always provide both file_path AND content arguments. Never call write_file with only content. "
    )

    print("\n================= User Prompt ===============================\n")
    user_prompt = input("> ").strip()
    print("\n================= Agent Output ===============================\n")
    start_time  = time.time()

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user",   "content": user_prompt}
    ]

    try:
        # Agentic loop: keep going until the model stops calling tools
        while True:
            response: ChatResponse = client.chat(model=MODEL, messages=messages, tools=[read_file, write_file], think=True)

            # Append the assistant turn to history
            messages.append(response.message.model_dump())

            print("Thinking: ", response.message.thinking)
            print("Content: ", response.message.content)

            tool_calls = response.message.tool_calls

            if not tool_calls:
                # No more tool calls — print the final reply and exit
                print(response.message.content)
                elapsed = time.time() - start_time
                hours, rem = divmod(elapsed, 3600)
                minutes, seconds = divmod(rem, 60)
                print(f"\nTime taken: {int(hours):02}:{int(minutes):02}:{seconds:05.2f}")
                break

            # Execute each tool call and feed results back
            for tc in tool_calls:
                if tc.function.name in available_functions:
                    msg = f"Calling {tc.function.name} with arguments {tc.function.arguments}"
                    if len(msg) <= 200:
                        print(msg)
                    else:
                        print(msg[:200] + "… … …")
                    try:
                        result = available_functions[tc.function.name](**tc.function.arguments)
                    except TypeError as e:
                        result = f"Error calling {tc.function.name}: {e}. Please retry with all required arguments."
                    print(f"Result: {result}")
                    messages.append({"role": "tool", "tool_name": tc.function.name, "content": str(result)})
                else:
                    print(f"Unknown tool {tc.function.name} with arguments {tc.function.arguments}")

    except ResponseError as e:
        raise RuntimeError(f"Ollama error: {e}") from e
    except Exception as e:
        raise RuntimeError(f"Failed to generate response: {e}") from e