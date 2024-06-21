"""
Simple command line interface for asking questions to the chatbot.
Useful for me since I don't know Linux very well.
"""

from Chain import Chain, Model, Prompt
import sys
import platform
import subprocess
import os
import textwrap

preferred_model = "gpt-3.5-turbo-0125"  # cheaper
# preferred_model = "gpt" # more expensive

preferred_model = "gpt-3.5-turbo-0125" # cheaper
# preferred_model = "gpt" # more expensive

system_instructions = """
You are a helpful IT admin. You are helping a new programmer.
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
""".strip()

def get_system_info():
    os_info = platform.system() + " " + platform.release()
    python_version = platform.python_version()
    cpu_model = platform.processor()

    if platform.system() == "Darwin":
        memory_cmd = ['sysctl', 'hw.memsize']
        gpu_cmd = ['system_profiler', 'SPDisplaysDataType']
        shell_config_files = ['.zshrc', '.zprofile']
    elif platform.system() == "Linux":
        memory_cmd = ['grep', 'MemTotal', '/proc/meminfo']
        gpu_cmd = ['lshw', '-C', 'display']
        shell_config_files = ['.bashrc', '.bash_profile']

    try:
        memory_size = subprocess.run(memory_cmd, capture_output=True, text=True).stdout.strip()
    except:
        memory_size = 'Unknown'

    try:
        gpu_info = subprocess.run(gpu_cmd, capture_output=True, text=True).stdout.strip()
    except:
        gpu_info = 'Unknown'

    try:
        local_ip = subprocess.run(['hostname', '-I'], capture_output=True, text=True).stdout.strip()
    except:
        local_ip = 'Unknown'

    shell = os.environ.get('SHELL')
    terminal = os.environ.get('TERM_PROGRAM', 'Unknown')
    
    shell_info = "\n".join([read_file_content(os.path.expanduser(f'~/{f}')) for f in shell_config_files])

    return textwrap.dedent(f"""
OS: {os_info}
Python: {python_version}
CPU: {cpu_model}
Memory: {memory_size}
GPU: {gpu_info}
Local IP: {local_ip}
Shell: {shell}
Terminal: {terminal}
""").strip()

def read_file_content(file_path):
    try:
        with open(file_path, 'r') as file:
            return f"{file_path} Content:\n{file.read()}"
    except FileNotFoundError:
        return f"{file_path} Content: File not found"
    except Exception as e:
        return f"Error reading file: {e}"

def query(prompt, system_info):
    """
    Very simply query function.
    """
    model = Model(preferred_model)
    full_prompt = f"{system_instructions}\n============================\n{system_info}\n============================\n\nUser Query: {prompt}"
    prompt = Prompt(full_prompt)
    chain = Chain(prompt, model)
    response = chain.run(verbose=False)
    return response

if __name__ == '__main__':
    if len(sys.argv) > 1:
        if sys.argv[1] == "system_info":
            print(get_system_info())
            sys.exit(0)
        input_prompt = " ".join(sys.argv[1:])
        system_info = get_system_info()
        print(query(input_prompt, system_info))
    else:
        print("Either type a prompt, or type 'system_info' to get system information.")
