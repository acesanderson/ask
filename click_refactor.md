Okay, you're right. The previous version mapped the `argparse` flags directly to Click options within a single `main` function, mimicking the original structure.

To fully embrace Click's philosophy, we should break down each distinct action into its own command function, decorated and attached to a main command group. This leads to a more modular and discoverable CLI structure.

Here's a refactored version using Click subcommands:

```python
"""
Simple command line interface for asking questions to the chatbot using Click subcommands.
Useful for me since I don't know Linux very well.
"""

# Imports - keeping the spinner for potentially slow Chain imports later
# -----------------------------------------------------------------
import sys
import os
import platform
import subprocess
from pathlib import Path
import click
from rich.console import Console
from rich.markdown import Markdown

console = Console(width=100)

# Global state and lazy loading setup
# -----------------------------------------------------------------
Chain = None
Model = None
Prompt = None
create_system_message = None
ChainCache = None
MessageStore = None

# Global constants (consider moving to a config if it grows)
dir_path = Path(__file__).parent
history_file_path = dir_path / ".ask_history.pkl"
log_file_path = dir_path / ".ask_log.txt"
cache_path = dir_path / ".cache.db"
messagestore = None # Will be initialized after imports

# --- Helper Functions (Mostly unchanged) ---

def _lazy_load_dependencies():
    """Loads heavy dependencies only when needed."""
    global Chain, Model, Prompt, create_system_message, ChainCache, MessageStore, messagestore
    if Chain is None: # Check if already loaded
        with console.status("[green]Loading AI components...", spinner="dots"):
            from Chain import (
                Chain as C,
                Model as M,
                Prompt as P,
                create_system_message as cs,
                ChainCache as CC,
                MessageStore as MS
            )
            Chain = C
            Model = M
            Prompt = P
            create_system_message = cs
            ChainCache = CC
            MessageStore = MS

            # Initialize MessageStore now that the class is loaded
            messagestore = MessageStore(
                console=console,
                history_file=history_file_path,
                log_file=log_file_path,
                pruning=True,
            )
            # Assign singletons only after MessageStore is initialized
            Chain._message_store = messagestore
            Model._chain_cache = ChainCache(str(cache_path))
            # Load history after initialization
            messagestore.load()

def get_system_info():
    # (Keep the get_system_info function as it was)
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
        click.echo("Unsupported OS", err=True)
        sys.exit(1)

    try:
        memory_size = subprocess.run(
            memory_cmd, capture_output=True, text=True, check=False
        ).stdout.strip()
    except Exception:
        memory_size = "Unknown"

    try:
        gpu_info = subprocess.run(
            gpu_cmd, capture_output=True, text=True, check=False
        ).stdout.strip()
    except Exception:
        gpu_info = "Unknown"

    try:
        local_ip = subprocess.run(
            ["hostname", "-I"], capture_output=True, text=True, check=False
        ).stdout.strip()
    except Exception:
        local_ip = "Unknown"

    shell = os.environ.get("SHELL", "Unknown")
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

def print_markdown(string_to_display: str, use_raw: bool):
    """Prints formatted markdown or raw string to the console."""
    if use_raw:
        click.echo(string_to_display)
    else:
        border = "-" * 80
        markdown_string = f"{border}\n{string_to_display}\n\n{border}"
        md = Markdown(markdown_string)
        console.print(md)

def generate_script_contents(files: tuple[str]) -> list[tuple[str, str]] | None:
    """For debug mode. Reads file contents."""
    file_data = []
    for script_file in files:
        try:
            # No need to check exists=True here as click.Path does it
            with open(script_file, "r") as file:
                file_data.append((Path(script_file).name, file.read())) # Use filename only
        except Exception as e:
            click.echo(f"Error reading file {script_file}: {e}", err=True)
            return None # Indicate failure
    return file_data

def generate_script_output(script_file: str) -> str:
    """For debug mode. Runs script and captures output."""
    command = [sys.executable, script_file] # Use sys.executable for robustness
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=False)
        output = result.stdout.strip() + "\n" + result.stderr.strip()
    except Exception as e:
        output = f"Error running script {script_file}: {e}"
    return output

# --- Click Command Group ---

@click.group()
def cli():
    """
    AI-powered CLI assistant for Linux/Python tasks and debugging.

    Examples:\n
      ask 'How do I find large files?'\n
      ask -o 'Explain git rebase'\n
      debug main.py utils.py -q 'Why does it crash?'\n
      history\n
      last --raw\n
    """
    # Ensure dependencies are loaded for commands that might need them
    # We load history here for commands like 'last', 'history', 'get'
    # The full AI components load lazily if 'ask' or 'debug' is called.
    global messagestore
    if messagestore is None and MessageStore is None:
        # Need MessageStore class for basic history operations even if AI isn't used yet
        from Chain import MessageStore as MS
        MessageStore = MS
        messagestore = MessageStore(
            console=console,
            history_file=history_file_path,
            log_file=log_file_path,
            pruning=True,
        )
        messagestore.load()
    elif messagestore:
        messagestore.load() # Ensure history is loaded if already initialized

# --- Individual Commands ---

@cli.command()
def system():
    """Prints detailed system information."""
    click.echo(get_system_info())

@cli.command()
@click.option("-r", "--raw", is_flag=True, help="Output raw content without markdown formatting.")
def last(raw):
    """Prints the last recorded assistant message."""
    if not messagestore:
        click.echo("History not loaded.", err=True)
        sys.exit(1)
    last_msg = messagestore.last()
    if last_msg:
        print_markdown(last_msg.content, raw)
    else:
        click.echo("No history found.")

@cli.command()
def history():
    """Prints the last 10 messages (most recent first)."""
    if not messagestore:
        click.echo("History not loaded.", err=True)
        sys.exit(1)
    messagestore.view_history() # Assumes this method prints directly

@cli.command()
@click.argument("index", type=click.IntRange(min=1)) # Use IntRange for validation
@click.option("-r", "--raw", is_flag=True, help="Output raw content without markdown formatting.")
def get(index, raw):
    """Retrieves a specific message from history (1 = most recent)."""
    if not messagestore:
        click.echo("History not loaded.", err=True)
        sys.exit(1)
    try:
        retrieved_message = messagestore.get(index) # Assuming get uses 1-based index
        if retrieved_message:
            print_markdown(retrieved_message.content, raw)
        else:
            click.echo(f"Message at index {index} not found.")
    except IndexError:
         click.echo(f"Message index {index} out of range.")
    except Exception as e:
        click.echo(f"Error retrieving message: {e}", err=True)


@cli.command()
@click.confirmation_option(prompt='Are you sure you want to clear the entire message history?')
def clear():
    """Clears the entire message history."""
    if not messagestore:
        # Load MessageStore class if not already loaded
        _lazy_load_dependencies() # This ensures messagestore is initialized
    messagestore.clear()
    click.echo("Message history cleared.")

@cli.command()
@click.argument("prompt_words", nargs=-1) # Captures all words as a tuple
@click.option("-o", "--ollama", is_flag=True, help="Use local Ollama model (llama3.1:latest).")
@click.option("-e", "--escalate", is_flag=True, help="Use a more powerful model (gemini).")
@click.option("-m", "--model", type=str, help="Specify an exact model name to use.")
@click.option("-r", "--raw", is_flag=True, help="Output raw response without markdown formatting.")
def ask(prompt_words, ollama, escalate, model, raw):
    """Asks the AI assistant a question."""
    _lazy_load_dependencies() # Ensure AI components are loaded

    preferred_model = "gemini2.5" # Default
    if ollama:
        preferred_model = "llama3.1:latest"
    if model:
        try:
            # Test model validity implicitly when creating the Model object
            Model(model)
            preferred_model = model
        except Exception as e: # Catch potential errors from Model init
            click.echo(f"Model '{model}' might not be valid or accessible: {e}", err=True)
            sys.exit(1)
    if escalate:
        preferred_model = "gemini" # More powerful Gemini

    # Grab stdin if piped
    piped_input = ""
    if not sys.stdin.isatty():
        piped_input = sys.stdin.read()

    # Combine args and piped input
    user_prompt_text = " ".join(prompt_words)
    if piped_input:
        combined_prompt = f"{user_prompt_text}\n\n<context_from_pipe>\n{piped_input}\n</context_from_pipe>"
    else:
        combined_prompt = user_prompt_text

    if not combined_prompt.strip():
        click.echo("Error: No prompt provided via arguments or stdin.", err=True)
        sys.exit(1)

    with console.status("[green]Querying AI...", spinner="dots"):
        # Ensure system prompt is added if needed
        if not messagestore.messages or messagestore.messages[0].role != "system":
             system_info = get_system_info()
             system_message = create_system_message(
                 system_prompt=system_prompt_string,
                 input_variables={"system_info": system_info},
             )
             # Prepend system message safely
             current_messages = messagestore.messages[:] # Get a copy
             messagestore.messages = system_message + current_messages

        # Add user prompt
        messagestore.add_new(role="user", content=combined_prompt)

        # Run query
        try:
            model_instance = Model(preferred_model)
            response_content = model_instance.query(messagestore.messages)
            messagestore.add_new(role="assistant", content=response_content)
            print_markdown(response_content, raw)
        except Exception as e:
            click.echo(f"\nError during AI query: {e}", err=True)
            # Optionally remove the last user message if query failed
            if messagestore.messages and messagestore.messages[-1].role == "user":
                messagestore.messages.pop()
            sys.exit(1)


@cli.command()
@click.argument("files", nargs=-1, required=True, type=click.Path(exists=True, dir_okay=False, readable=True))
@click.option("-q", "--query", help="Specific question about the code for the debugger.")
@click.option("-r", "--raw", is_flag=True, help="Output raw response without markdown formatting.")
def debug(files, query, raw):
    """Debugs Python script(s) using AI analysis."""
    _lazy_load_dependencies() # Ensure AI components are loaded

    # Clear message store for a fresh debug session
    messagestore.clear()

    with console.status("[green]Analyzing code and running script...", spinner="dots"):
        # Generate file contents (files tuple is already validated by click.Path)
        file_data = generate_script_contents(files)
        if file_data is None: # Error during file reading
             sys.exit(1)

        # Run the first script and capture output
        script_output = generate_script_output(files[0])

        # Prepare prompt strings
        current_debug_prompt = debug_prompt_string # Base prompt
        if query:
            current_debug_prompt += f"\n\nThe user has added this specific query:\n<user_query>{query}</user_query>"

        # Create system message and prompt object
        system_message = create_system_message(system_prompt=debug_system_prompt)
        prompt_obj = Prompt(current_debug_prompt)
        model_obj = Model("claude") # Debug mode uses Claude specifically per original logic
        chain = Chain(prompt_obj, model_obj) # Assuming Chain setup requires prompt and model

    with console.status("[green]Querying AI debugger...", spinner="dots"):
        try:
            # Run the debug chain
            response = chain.run(
                input_variables={
                    "file_data": file_data,
                    "script_output": script_output,
                },
                # Pass the system message explicitly if chain.run doesn't automatically use MessageStore's start
                messages=system_message, # Start with the debug system prompt
            )
            # Note: The chain.run might add messages to the store itself.
            # If not, you might need to manually add user-context and assistant response
            # messagestore.add_new(role='assistant', content=response.content) # If needed
            print_markdown(response.content, raw)

        except Exception as e:
            click.echo(f"\nError during AI debug query: {e}", err=True)
            sys.exit(1)

# --- Script Entry Point ---

if __name__ == "__main__":
    # Global messagestore initialization happens within cli() or _lazy_load_dependencies
    # to ensure MessageStore class is available.
    cli()
```

**Key Changes and Refactoring Approach:**

1.  **`@click.group()`:** A main group `cli` is defined. This acts as the entry point.
2.  **Individual Commands:** Each distinct action (`system`, `last`, `history`, `get`, `clear`, `ask`, `debug`) is now its own function decorated with `@cli.command()`.
3.  **Specific Options/Arguments:** Options and arguments relevant only to a specific command are attached directly to that command's decorator stack (e.g., `--raw` is on `last`, `get`, `ask`, `debug`; `INDEX` argument is only on `get`; `FILES` argument is only on `debug`).
4.  **Lazy Loading:** The `_lazy_load_dependencies` function is introduced to handle the import and initialization of the potentially slow `Chain`, `Model`, `Prompt`, `MessageStore`, etc. It's called *inside* the commands that require these components (`ask`, `debug`, and potentially `clear` if the store isn't loaded yet). Basic history operations (`last`, `history`, `get`) attempt to load `MessageStore` and history early in `cli()` if needed.
5.  **Global State Management:** `messagestore` is initialized lazily. Constants remain global.
6.  **Clearer Entry Point:** The `if __name__ == "__main__":` block now simply calls `cli()`.
7.  **Click Types and Validation:** Used `click.Path(exists=True, ...)` for file validation in `debug` and `click.IntRange(min=1)` for the `get` index.
8.  **Context Management:** Handling of piped input (`stdin`) is moved directly into the `ask` command where it's relevant.
9.  **Error Handling:** Added more specific error messages using `click.echo(..., err=True)` and `sys.exit(1)`. Added basic exception handling around AI calls.
10. **Confirmation:** Used `click.confirmation_option` for the `clear` command for safety.
11. **Help Messages:** Click automatically generates help messages based on the decorators and docstrings. The main group docstring provides overview and examples.

This structure is much more aligned with typical Click applications. Each command is self-contained, making the code easier to read, maintain, and extend. The CLI becomes more discoverable as users can run `python your_script.py --help` to see all available commands and `python your_script.py <command> --help` for command-specific options.
