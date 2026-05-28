import os
import time
import json
from openai import OpenAI
import tools as tools

# ---------------------------------------------------------------------------
# Harness file loading — read context files at startup
# All files are expected to sit alongside this script.
# ---------------------------------------------------------------------------

WORKING_DIR = os.path.dirname(os.path.abspath(__file__))
HARNESS_FILES = ["AGENTS.md", "init.sh", "feature_list.json", "progress.md"]

# ---------------------------------------------------------------------------
# Initialize OpenAI client pointed at OpenRouter
# Using the OpenAI SDK with OpenRouter's base URL is the recommended approach
# for accessing OpenRouter-specific parameters (e.g. include_reasoning) via
# extra_body, which the native OpenRouter SDK does not yet support.
# See: https://github.com/openai/openai-python
#      https://openrouter.ai (OpenAI-compatible API)
# ---------------------------------------------------------------------------

# If Environment variables fail I WANT IT TO CRASH so I know the problem is with this
LLM_API_KEY = os.environ["LLM_API_KEY"]
LLM_BASE_URL = os.environ["LLM_BASE_URL"]
LLM_MODEL = os.environ["LLM_MODEL"]
client = OpenAI(
    api_key = LLM_API_KEY,
    base_url = LLM_BASE_URL
)

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("\n================= Working Directory ===============================\n")

    WORKING_DIR = os.path.abspath(input("Enter Working Directory: ").strip())
    print("")

    # Read each harness file and build a single context block for the system prompt.
    # Missing files are reported but do not abort startup.
    sections = []
    for filename in HARNESS_FILES:
        filepath = os.path.join(WORKING_DIR, filename)
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                sections.append(f"=== {filepath} ===\n{f.read()}")
            print(f"[harness] Read: {filepath}")
        except FileNotFoundError:
            print(f"[harness] Warning: {filepath} not found — skipping.")
    harness_context = "\n\n".join(sections)
    print("")

    system_prompt = (
        "You are a coding assistant operating inside a harness.\n\n"
        "The following files provide your context and instructions:\n\n"
        f"{harness_context}\n\n"
        "When writing code, you MUST use the write_file tool to save it to the 'src' folder. "
        "You may use the read_file tool to read existing files from the 'src' folder. "
        "Never output code blocks in your reply — always call write_file instead. "
        f"Your Working Directory is {WORKING_DIR}, search from here if user asks to read/write files while specifying a relative directory. "
        "Always use absolute file paths when using read_file/write_file tools, never relative file paths. "
        "When calling write_file, you MUST always provide both file_path AND content. Never call write_file with only content. "
        "ALWAYS WRITE CODE TO A FILE, NEVER WRITE CODE IN YOUR REPLY."
        "FOLLOW THE AGENTS.md file TO THE LETTER."
        "FINISH MAKING ALL THE FEATURES IN THE FEATURE LIST BEFORE ENDING YOUR REPLY"
    )

    print("================= User Prompt ===============================", end="\n\n")
    user_prompt = input("> ").strip()
    print("")
    print("================= Agent Output ===============================", end="\n\n")
    start_time = time.time()

    messages: list = [
        {"role": "system", "content": system_prompt},
        {"role": "user",   "content": user_prompt}
    ]

    try:
        # Agentic loop: keep going until the model stops calling tools.
        # extra_body passes OpenRouter-specific parameters not in the OpenAI spec.
        # include_reasoning exposes the model's reasoning tokens in reply.reasoning.
        # See: https://openrouter.ai/docs/guides/best-practices/reasoning-tokens
        while True:
            response = client.chat.completions.create(
                model=LLM_MODEL,
                messages=messages,
                tools=tools.schema,
                extra_body={
                    "reasoning": {
                        "effort": "low"  # Maps to thinkingLevel: "low"
                    }
                },
            )

            # OpenAI SDK response schema: response.choices[0].message
            reply = response.choices[0].message
            # getattr(reply, "reasoning", None)

            if reply.reasoning: # pyright: ignore[reportAttributeAccessIssue]
                print("Thinking: ", reply.reasoning, end="\n\n") # pyright: ignore[reportAttributeAccessIssue]
            print("Content: ", reply.content, end="\n\n")

            # Append assistant turn to history as a plain dict
            messages.append({
                "role":       "assistant",
                "content":    reply.content or "",
                "tool_calls": [
                    {
                        "id":   tc.id,
                        "type": "function",
                        "function": {
                            "name":      tc.function.name, # pyright: ignore[reportAttributeAccessIssue]
                            "arguments": tc.function.arguments # pyright: ignore[reportAttributeAccessIssue]
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
                fn_name = tc.function.name # pyright: ignore[reportAttributeAccessIssue]
                # arguments may be a dict already or a JSON string depending on the model
                fn_args = tc.function.arguments # pyright: ignore[reportAttributeAccessIssue]
                if isinstance(fn_args, str):
                    fn_args = json.loads(fn_args)

                msg = f"Calling {fn_name} with arguments {fn_args}"
                print(msg if len(msg) <= 200 else msg[:200] + "… … …", end="\n\n")

                if fn_name in tools.available_functions:
                    try:
                        result = tools.available_functions[fn_name](**fn_args)
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