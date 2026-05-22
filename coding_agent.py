import os
import time
import json
from openrouter import OpenRouter

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
                sections.append(f"=== {filepath} ===\n{f.read()}")
            print(f"[harness] Read: {filepath}")
        except FileNotFoundError:
            print(f"[harness] Warning: {filepath} not found — skipping.")
    return "\n\n".join(sections)

# ---------------------------------------------------------------------------
# Initialize OpenRouter client
# See: https://openrouter.ai/docs/client-sdks/python/overview
# ---------------------------------------------------------------------------

LLM_API_KEY = os.environ["LLM_API_KEY"] # If this fails I WANT IT TO CRASH so I know the problem is with this
MODEL  = os.environ["MODEL"]
client = OpenRouter(api_key=LLM_API_KEY)

# ---------------------------------------------------------------------------
# Tool definitions — explicit JSON schema passed to the OpenRouter client.
# See: https://openrouter.ai/docs/client-sdks/python/api-reference/chat
# ---------------------------------------------------------------------------

tools: list = [
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read a file and return its contents. Always use an absolute file path.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": (
                            "The absolute path of the file to read. "
                            "Example: 'C:\\Users\\User\\project\\src\\file.py'. "
                            "Never use a relative path."
                        )
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
            "description": (
                "Write content to a file, creating directories as needed. "
                "Always use this tool to save code — never output code in your reply. "
                "Both file_path and content are required — never call this tool without both."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": (
                            "The absolute path of the file to write. "
                            "Example: 'C:\\Users\\User\\project\\src\\file.py'. "
                            "Never use a relative path."
                        )
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
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return f"Error: {file_path} not found."
    except Exception as e:
        return f"Error reading {file_path}: {e}"

def write_file(file_path: str, content: str) -> str:
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
    return f"Written to {file_path}"

available_functions = {
    "read_file":  read_file,
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
        f"Your Working Directory is {SCRIPT_DIR}, search from here if user asks to read/write files while specifying a relative directory. "
        "Always use absolute file paths when using read_file/write_file tools, never relative file paths. "
        "When calling write_file, you MUST always provide both file_path AND content. Never call write_file with only content. "
        "ALWAYS WRITE CODE TO A FILE, NEVER WRITE CODE IN YOUR REPLY."
    )

    print("\n================= User Prompt ===============================\n")
    user_prompt = input("> ").strip()
    print("\n================= Agent Output ===============================\n")
    start_time = time.time()

    messages: list = [
        {"role": "system", "content": system_prompt},
        {"role": "user",   "content": user_prompt}
    ]

    try:
        # Agentic loop: keep going until the model stops calling tools.
        # See: https://openrouter.ai/docs/client-sdks/python/api-reference/chat
        with client:
            while True:
                response = client.chat.send(model=MODEL, messages=messages, tools=tools)

                # OpenRouter response schema: response.choices[0].message
                reply = response.choices[0].message

                print("Content: ", reply.content, end="\n\n")

                # Append assistant turn to history as a plain dict
                messages.append({
                    "role": "assistant",
                    "content": reply.content or "",
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {
                                "name": tc.function.name,
                                "arguments": tc.function.arguments
                            }
                        }
                        for tc in (reply.tool_calls or [])
                    ] or None
                })

                tool_calls = reply.tool_calls or []

                if not tool_calls:
                    # No more tool calls — print the final reply and exit
                    elapsed = time.time() - start_time
                    hours, rem = divmod(elapsed, 3600)
                    minutes, seconds = divmod(rem, 60)
                    print(f"Time taken: {int(hours):02}:{int(minutes):02}:{seconds:05.2f}", end="\n\n")
                    break

                # Execute each tool call and feed results back
                for tc in tool_calls:
                    fn_name = tc.function.name
                    # arguments may be a dict already or a JSON string depending on the model
                    fn_args = tc.function.arguments
                    if isinstance(fn_args, str):
                        fn_args = json.loads(fn_args)

                    msg = f"Calling {fn_name} with arguments {fn_args}"
                    print(msg if len(msg) <= 200 else msg[:200] + "… … …", end="\n\n") # prevent printing of super long arguments such as file contents

                    if fn_name in available_functions:
                        try:
                            result = available_functions[fn_name](**fn_args)
                        except TypeError as e:
                            result = (
                                f"Error calling {fn_name}: {e}. "
                                "Tool calling must specify all arguments by name\n"
                            )
                    else:
                        result = f"Unknown tool: {fn_name}"

                    print(f"Result: {result}", end="\n\n")

                    # Tool result message — role must be "tool" with matching tool_call_id
                    messages.append({
                        "role":         "tool",
                        "tool_call_id": tc.id,
                        "content":      str(result)
                    })

    except Exception as e:
        raise RuntimeError(f"Failed to generate response: {e}") from e