"""
Simple command line interface for asking questions to the chatbot.
Useful for me since I don't know Linux very well.
"""

# Imports can take a while, so we'll give the user a spinner.
# -----------------------------------------------------------------

from rich.console import Console

console = Console(width=100)  # for spinner

with console.status("[green]Loading...", spinner="dots"):
    from Chain import Chain, Model, MessageStore, create_system_message
    import platform
    import subprocess
    import sys
    import os
    from time import time
    import argparse
    from rich.markdown import Markdown
    from pathlib import Path

# Constants + Message Store initialization
# -----------------------------------------------------------------

dir_path = Path(__file__).parent
history_file_path = dir_path / ".ask_history.pkl"
log_file_path = dir_path / ".ask_log.txt"
messagestore = MessageStore(
    console=console,
    history_file=history_file_path,
    log_file=log_file_path,
    pruning=True,
)
Chain._message_store = messagestore
preferred_model = "claude-3-haiku-20240307"

# Our prompts
# -----------------------------------------------------------------

system_prompt_string = """
You are a helpful IT admin. You are a frontline worker at your company.
You are helping a new programmer.
They use Python and Linux. They are experienced with Python programming but don't know much about how to do the following:
- package scripts into proper applications
- use git and GitHub
- set up a development environment
- use things like Docker, virtual environments, or networking tools
- write shell scripts
- use a terminal effectively
- the linux filesystem or basic linux commands (beyond ls, mkdir, cd, mv, etc.)
Your answers should be very short and to the point.
Only provide a solution to the user's problem.
Do not introduce yourself or provide emotional support.
If a code snippet is all that the user needs, just provide the code snippet.

Here are details about the user's hardware, OS, and software:

<system_detail>
{{system_info}}
</system_detail>
""".strip()

# Our functions
# -----------------------------------------------------------------


def get_system_info():
    os_info = platform.system() + " " + platform.release()
    python_version = platform.python_version()
    cpu_model = platform.processor()
    if platform.system() == "Darwin":
        memory_cmd = ["sysctl", "hw.memsize"]
        gpu_cmd = ["system_profiler", "SPDisplaysDataType"]
    elif platform.system() == "Linux":
        memory_cmd = ["grep", "MemTotal", "/proc/meminfo"]
        gpu_cmd = ["lshw", "-C", "display"]

    try:
        memory_size = subprocess.run(
            memory_cmd, capture_output=True, text=True
        ).stdout.strip()
    except:
        memory_size = "Unknown"

    try:
        gpu_info = subprocess.run(
            gpu_cmd, capture_output=True, text=True
        ).stdout.strip()
    except:
        gpu_info = "Unknown"

    try:
        local_ip = subprocess.run(
            ["hostname", "-I"], capture_output=True, text=True
        ).stdout.strip()
    except:
        local_ip = "Unknown"

    shell = os.environ.get("SHELL")
    terminal = os.environ.get("TERM_PROGRAM", "Unknown")

    system_info = f"""
OS: {os_info}
Python: {python_version}
CPU: {cpu_model}
Memory: {memory_size}
GPU: {gpu_info}
Local IP: {local_ip}
Shell: {shell}
Terminal: {terminal}
""".strip()
    return system_info


def read_file_content(file_path):
    """
    Reads the content of a file and returns it as a string.
    Needed for reading shell configuration files.
    """
    try:
        with open(file_path, "r") as file:
            return f"{file_path} Content:\n{file.read()}"
    except FileNotFoundError:
        return f"{file_path} Content: File not found"
    except Exception as e:
        return f"Error reading file: {e}"


def print_markdown(string_to_display: str, console: Console | None = None):
    """
    Prints formatted markdown to the console.
    """
    if not Console:
        console = Console(width=80)
    # Create a Markdown object
    border = "-" * 80
    markdown_string = f"{border}\n{string_to_display}\n\n{border}"
    md = Markdown(markdown_string)
    console.print(md)


if __name__ == "__main__":
    # Load message store history.
    messagestore.load()
    # Grab stdin in it is piped in
    if not sys.stdin.isatty():
        context = "\n\n" + "<context>" + sys.stdin.read() + "</context>"
    else:
        context = ""
    # Our argparse code:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-s",
        "--system",
        action="store_true",
        help="Print system information.",
    )
    parser.add_argument(
        "-l", "-last", dest="last", action="store_true", help="Print the last message."
    )
    parser.add_argument(
        "-hi",
        "--history",
        action="store_true",
        help="Print the last 10 messages.",
    )
    parser.add_argument(
        "-g",
        "--get",
        type=str,
        help="Get a specific answer from the history.",
    )
    parser.add_argument(
        "-c",
        "--clear",
        action="store_true",
        help="Clear the message history.",
    )
    parser.add_argument("-r", "--raw", action="store_true", help="Output raw markdown.")
    parser.add_argument("-o", "--ollama", action="store_true", help="Use local model.")
    parser.add_argument(
        "-e",
        "--escalate",
        action="store_true",
        help="Speak to the manager (3.5 sonnet).",
    )
    parser.add_argument("prompt", nargs="*", help="Ask IT a question.")
    # parser.add_argument("-t", "-tutorialize", dest="tutorialize", type=str, help="Generate a tutorial for a given topic.")
    args = parser.parse_args()
    if args.ollama:
        preferred_model = "llama3.1:latest"
    if args.escalate:  # default is haiku, choose this is you need oomph
        preferred_model = "claude-3-5-sonnet-20241022"
    if args.clear:
        messagestore.clear()
        sys.exit()
    if args.system:  # print system information
        print(get_system_info())
        sys.exit()
    if args.last:  # print the last message
        last_message = messagestore.last()
        if args.raw:
            print(last_message.content)
        else:
            print_markdown(last_message.content, console=console)
        sys.exit()
    if args.history:  # print the last 10 messages backwards in time
        messagestore.view_history()
        sys.exit()
    if args.get:  # get a specific message 1-10
        retrieved_message = messagestore.get(int(args.get))
        try:
            if args.raw:
                print(retrieved_message.content)
            else:
                print_markdown(retrieved_message.content, console=console)
        except:
            print("Message not found.")
        sys.exit()
    # Construct the prompt from a combination of stdin (if it was in fact piped into the script) and prompt (if in fact there was a prompt). If both are None, it will be a single newline, so strip will give us an empty string (i.e. False).
    combined_prompt = "\n".join(
        [
            " ".join(args.prompt) if args.prompt is not None else "",
            context if context is not None else "",
        ]
    )
    #
    if combined_prompt.strip():  # ask the chatbot a question
        with console.status("[green]Query...", spinner="dots"):
            # Check if we need system prompt.
            if messagestore.messages:
                if messagestore.messages[0].role != "system":
                    system_info = get_system_info()
                    system_message = create_system_message(
                        system_prompt=system_prompt_string,
                        input_variables={"system_info": system_info},
                    )
                    messagestore.messages = system_message + messagestore.messages
            # Initialize user prompt
            messagestore.add_new(role="user", content=combined_prompt)
            # Run our query with our messages.
            model = Model(preferred_model)
            response = model.query(messagestore.messages)
            messagestore.add_new(role="assistant", content=response)
            if args.raw:
                print(response)
            else:
                print_markdown(response, console=console)
