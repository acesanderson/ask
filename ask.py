"""
Simple command line interface for asking questions to the chatbot.
Useful for me since I don't know Linux very well.
"""

# Imports can take a while, so we'll give the user a spinner.
# -----------------------------------------------------------------

from rich.console import Console

console = Console()  # for spinner

with console.status("[green]Loading...", spinner="dots"):
    from Chain import Model, MessageStore, ChainCache, Chain, Prompt, create_system_message, Response, ChainError
    from pathlib import Path
    import platform, subprocess, sys, os, argparse


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

# These are our prompts for the software engineer.
debug_system_prompt = """
You are an experienced software engineer, and are helping a junior programmer debug their code. They are using Python and Linux.

You will be provided with the the user's code. This may be a single script, or a set of scripts. The first script is the script they're trying to run; the rest are helper scripts that the first script may depend on.

You will also be given the terminal output of the code (both stdout and stderr).

Your goal is to help the user debug their code. You can ask for more information if needed.
"""

# Input variables are file_data: list[tuple[file_name, file_content]], output: str
debug_prompt_string = """
Here is the user's code:
<user_code>
{% for file_name, file_content in file_data %}
<{{file_name}}>
{{file_content}}
</{{file_name}}>
{% endfor %}
</user_code>

And here is the output of the first script that they are trying to debug:
<script_output>
{{script_output}}
</script_output>
"""


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
    else:
        print("Unsupported OS")
        return

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
    Needed for reading shell configuration files for base mode.
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
    from rich.markdown import Markdown

    if not console:
        console = Console(width=80)
    # Create a Markdown object
    border = "-" * 80
    markdown_string = f"{border}\n{string_to_display}\n\n{border}"
    md = Markdown(markdown_string)
    console.print(md)


def generate_script_contents(files: list[str]) -> list[tuple[str, str]] | None:
    """
    For debug mode.
    Given a list of file paths, return a list of tuples containing the file name and its content.
    """
    file_data = []
    for script_file in files:
        try:
            with open(script_file, "r") as file:
                file_data.append((script_file, file.read()))
        except FileNotFoundError:
            print(f"File not found: {script_file}")
            return
    return file_data


def generate_script_output(script_file: str) -> str:
    """
    For debug mode.
    Given a script file, run it and return the output.
    """
    command = ["python", script_file]
    try:
        # Run the command directly and capture both stdout and stderr
        result = subprocess.run(command, capture_output=True, text=True)
        output = result.stdout.strip() + "\n" + result.stderr.strip()
    except Exception as e:
        output = f"Error running script: {e}"
    return output


# Main
# -----------------------------------------------------------------


def main():
    preferred_model = "flash"
    # Load message store history.
    Model._console = console
    dir_path = Path(__file__).parent
    history_file_path = dir_path / ".ask_history.json"
    log_file_path = dir_path / ".ask_log.txt"
    cache_path = dir_path / ".cache.db"
    Model._chain_cache = ChainCache(str(cache_path))
    messagestore = MessageStore(
        console=console,
        history_file=history_file_path,
        log_file=log_file_path,
        pruning=True,
    )
    Chain._message_store = messagestore
    messagestore.load()
    # Grab stdin if it is piped in
    if not sys.stdin.isatty():
        context = "\n\n" + "<context>" + sys.stdin.read() + "</context>"
    else:
        context = ""
    # Our argparse code:
    parser = argparse.ArgumentParser()
    # Messagestore and other light queries -- no need for LLM interactions.
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
    parser.add_argument("-m", "--model", type=str, help="Specify a model.")
    # LLM options -- this will lazy load the Chain package.
    parser.add_argument("prompt", nargs="*", help="Ask IT a question.")
    parser.add_argument("-d", "--debug", nargs="+", help="Debug mode.")
    parser.add_argument(
        "-q",
        "--query_about_script",
        help="Add a query about your script for debug mode.",
    )
    args = parser.parse_args()
    if args.model:
        try:
            Model(args.model)
            preferred_model = args.model
        except:
            print(f"Model not recognized: {args.model}.")
            sys.exit()
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
    if args.debug:
        # Clear the message store, since the debug mode is a new conversation.
        messagestore.clear()
        # Verify that the files exist.
        files = args.debug
        for file in files:
            if not os.path.exists(file):
                print(f"File not found: {file}")
                sys.exit()
        with console.status("[green]Analyzing code...", spinner="dots"):
            # Generate our file_data list of tuples.
            file_data = generate_script_contents(files)
            # Run the first script and capture the output.
            script_output = generate_script_output(files[0])
            # Create the debug prompt.
            system_message = create_system_message(
                system_prompt=debug_system_prompt,
            )
            if args.query_about_script:  # Add custom user query if provided.
                debug_prompt_string += f"\nThe user has added this custom note:\n<user_query>{args.query_about_script}</user_query>"
            prompt = Prompt(debug_prompt_string)
            model = Model("claude")
            chain = Chain(prompt, model)
            response = chain.run(
                input_variables={
                    "file_data": file_data,
                    "script_output": script_output,
                },
                messages=messagestore,
            )
        if args.raw:
            print(response.content)
        else:
            print_markdown(response.content, console=console)
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
        # Check if we need system prompt.
        if len(messagestore) == 0 or messagestore[0].role != "system":
            system_info = get_system_info()
            system_message = create_system_message(
                system_prompt=system_prompt_string,
                input_variables={"system_info": system_info},
            )
            messagestore.insert(0, system_message[0])
        # Run our query with our messages.
        model = Model(preferred_model)
        prompt = Prompt(combined_prompt)
        chain = Chain(prompt = prompt, model = model)
        response = chain.run()
        if args.raw:
            print(response)
        else:
            print_markdown(response, console=console)


if __name__ == "__main__":
    main()
