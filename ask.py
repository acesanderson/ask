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
from time import time
import pickle

# use relative path for the pickle file so code can be used anywhere
dir_path = os.path.dirname(os.path.realpath(__file__))
# Construct the path to the .env file
env_path = os.path.join(dir_path, 'message_store.pkl')

preferred_model = "gpt-3.5-turbo-0125"  # cheaper
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

def query(messages):
	"""
	Very simple chat function; pass messages to the model and return the response.
	"""
	response = Model(preferred_model).chat(messages)
	return response

def get_messages(message_store: list[list]) -> list[dict]:
	"""
	Takes a message store object (which is a list of lists, each list has timestamp (0th element) + a message object (1st element)),
	return a list of messages.
	"""
	messages = [s[1] for s in message_store]
	return messages

def save_message_store(message_store: list[list]):
	"""
	Saves the message to a file.
	Takes the message a dict with "user"  
	"""
	# pickle the message_store
	with open(message_store_path, "wb") as f:
		pickle.dump(message_store, f)

def load_message_store() -> list[list]:
	"""
	Returns a list of lists, with each list containing a timestamp and a message object.
	We want a lightly persistent memory for this, i.e. one hour for sustained chats.
	"""
	try:
		with open(message_store_path, "rb") as f:
			message_store = pickle.load(f)
	except FileNotFoundError:
		print(f"Can't find pickle: {message_store_path}.")
		message_store = []
	# for each message, if time is more than 1 hour, remove it
	current_time = time()
	message_store = [[timestamp, messages] for timestamp, messages in message_store if current_time - timestamp <= 3600]
	# if messages is empty, add the system message to the top.
	if not message_store:
		message_store.append([time(), {"role": "system", "content": f"{system_instructions}\n============================\n{get_system_info()}\n============================\n"}])
	return message_store

if __name__ == '__main__':
	message_store: list[list] = load_message_store()	# what the admin sees
	if len(sys.argv) > 1:
		if sys.argv[1] == "system_info":
			print(get_system_info())
			sys.exit(0)
		if sys.argv[1] == "messages":					# for debugging
			print(get_messages(message_store))
			sys.exit(0)
		if sys.argv[1] == "clear":						# to wipe memory
			save_message_store([])
			sys.exit()
		input_prompt = " ".join(sys.argv[1:])
		message_store.append([time(), {'role': 'user', 'content': input_prompt}])
		query_response = query(get_messages(message_store))
		print(query_response)
		message_store.append([time(), {'role': 'assistant', 'content': query_response}])
		save_message_store(message_store)
	else:
		print("Either type a prompt, or type 'system_info' to get system information.")
