A tiny CLI to ask an LLM quick IT/dev questions or run a lightweight “debug my script” workflow.
	•	Fast to invoke from the terminal
	•	Keeps a local message/history log per project
	•	Optional debug mode: run your script, capture output, and ask the model to help
	•	Minimal dependencies: your Chain library + rich for UX

Requirements
	•	Python 3.11+ (tested with 3.12)
	•	rich
	•	Your Chain library importable on PYTHONPATH (or installed in the environment)

# recommended
python -m venv .venv && source .venv/bin/activate
pip install rich
# Make sure your Chain package is installed or importable
# e.g., pip install -e /path/to/Chain

Install

Place ask/ask.py on your PATH or create a convenience entry point:

# Option A: run directly
python ask/ask.py "How do I set up a venv on Ubuntu?"

# Option B: tiny wrapper
echo '#!/usr/bin/env bash
python "PATH/TO/ask/ask.py" "$@"' > /usr/local/bin/ask && chmod +x /usr/local/bin/ask

Usage

Ask a question

ask "How do I list open ports on Linux?"

Use stdin as additional context:

cat error.log | ask "Summarize the likely root cause."

Raw markdown output (no borders/styling):

ask -r "Give me a one-liner to kill a process on port 8080"

Choose a model (falls back to flash):

ask -m claude "Generate a Dockerfile for a simple Flask app"

Debug mode

Runs the first script, captures stdout+stderr, includes the source of all provided files, and asks the model to help debug.

ask -d script.py util.py

Add a specific question about the script:

ask -d script.py -q "Why does this crash on Python 3.12?"

Raw output is often useful here:

ask -d app.py helpers.py -q "Diagnose the stack trace" -r

History & system info

ask -s             # print system info the prompt uses
ask -l             # show the last answer
ask -hi            # show the last 10 messages
ask -g 3           # retrieve message #3 (1–10)
ask -c             # clear history

CLI reference

Flag / Arg	Description
prompt (positional, *)	Your question. Can be empty if piping stdin.
-r, --raw	Print raw markdown (no Rich formatting).
-m, --model MODEL	Select model (default: flash).
-s, --system	Print system info (OS, Python, CPU, memory, GPU, local IP, shell).
-l, -last	Show the last message.
-hi, --history	Show the last 10 messages.
-g N, --get N	Get message N (1–10).
-c, --clear	Clear message history.
-d FILE ..., --debug	Debug mode: include source + run first file and capture output.
-q TEXT, --query_about_script TEXT	Extra question to guide debug mode.

Run ask -h for argparse’s built-in help.

How it works
	•	On first conversational run, ask injects a short IT-admin system prompt and system details (OS, Python, CPU, memory, GPU, local IP, shell, terminal).
	•	Conversation state, logs, and cache live alongside ask.py:
	•	.ask_history.json – rolling message history
	•	.ask_log.txt – plain-text log
	•	.cache.db – cache used by ChainCache
	•	Debug mode builds a templated prompt with:
	•	Inline source for each file you pass
	•	Captured stdout+stderr from running the first file via python first_file.py

Notes & limitations
	•	System info collection supports Linux and macOS; other OSes print “Unsupported OS” for details.
	•	Make sure Chain is importable (install it into the same venv or set PYTHONPATH).
	•	The -m/--model value must match a model your Chain.Model recognizes.

Examples

# Quick Linux how-to
ask "Show me a one-liner to tail the last 100 lines of a file."

# Pipe context and ask a specific question
journalctl -u myservice --no-pager | ask "What recurring error pattern do you see?"

# Debug a failing script
ask -d train.py utils.py -q "Why do I get CUDA OOM after ~200 steps?" -r

# Retrieve a past answer as raw markdown, suitable for copy/paste
ask -l -r

License

MIT (or choose your preferred license).
