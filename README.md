# ask-project

## Project Purpose

A command-line AI assistant specialized for IT administration tasks, designed to help users with Linux system administration, Python development environment setup, shell scripting, and debugging. The tool uses LLM models to provide contextual assistance based on system information and conversation history.

## Architecture Overview

- **ask_cli.py**: CLI entry point that configures and launches the Twig-based conversational interface with IT admin specialization.
- **ask_function.py**: Core query handler that processes user inputs, manages system prompts, loads conversation context, and executes LLM queries through the Conduit interface.
- **system_info.py**: System introspection module that collects hardware, OS, and environment details (CPU, memory, GPU, IP, shell, terminal) for macOS and Linux platforms.

## Dependencies

Major dependencies (inferred from imports):

- **twig** - Local dependency providing the CLI framework and conversational interface (`Twig` class, `Verbosity`)
- **conduit** - Local dependency providing LLM integration (`Conduit`, `Prompt`, `Model`, `Response`, message management, prompt loading)
- Standard library: `os`, `platform`, `subprocess`, `pathlib`, `logging`

## API Documentation

### query_function

```python
def query_function(
    inputs: dict[str, str],
    preferred_model: str,
    include_history: bool,
    verbose: Verbosity,
) -> Response
```

Primary query handler for processing user requests through the LLM.

**Parameters:**
- `inputs`: Dictionary containing `query_input` (main query), `context` (optional context wrapped in XML tags), and `append` (additional text)
- `preferred_model`: Model identifier string (e.g., "claude", "flash")
- `include_history`: Whether to include conversation history in the request
- `verbose`: Verbosity level for output display

**Returns:** `Response` object containing the LLM's answer

### get_system_info

```python
def get_system_info() -> str
```

Collects system information for context injection into prompts.

**Returns:** Formatted string containing OS, Python version, CPU, memory, GPU, local IP, shell, and terminal information

### main

```python
def main() -> None
```

CLI entry point that initializes and runs the Twig assistant with IT admin configuration.

## Usage Examples

### Basic Query

```python
from ask.ask_function import query_function
from conduit.sync import Verbosity

inputs = {
    "query_input": "How do I create a Python virtual environment?",
    "context": "",
    "append": ""
}

response = query_function(
    inputs=inputs,
    preferred_model="claude",
    include_history=True,
    verbose=Verbosity.PROGRESS
)

print(response.content)
```

### Query with Context

```python
from ask.ask_function import query_function
from conduit.sync import Verbosity

error_log = """
Traceback (most recent call last):
  File "script.py", line 10
    print("Hello"
         ^
SyntaxError: '(' was never closed
"""

inputs = {
    "query_input": "Why is this script failing?",
    "context": error_log,
    "append": "I'm using Python 3.11"
}

response = query_function(
    inputs=inputs,
    preferred_model="claude",
    include_history=False,
    verbose=Verbosity.QUIET
)

print(response.content)
```

### Running the CLI

```python
from ask.ask_cli import main

# Launch interactive IT admin assistant
if __name__ == "__main__":
    main()
```

Or from command line:

```bash
python -m ask.ask_cli
```