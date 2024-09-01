"""
Simple command line interface for asking questions to the chatbot.
Useful for me since I don't know Linux very well.
"""

from Chain import Chain, Model, Prompt
import platform
import subprocess
import sys
import os
import textwrap
from time import time
import pickle
import argparse
from rich.console import Console
from rich.markdown import Markdown

# use relative path for the pickle file so code can be used anywhere
dir_path = os.path.dirname(os.path.realpath(__file__))
# Construct the path to the .env file
message_store_path = os.path.join(dir_path, 'message_store.pkl')

preferred_model = "gpt-4o-mini"

frontline_worker = """
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
""".strip()

manager = """
You are now the manager of a team of IT admins who help people with computer problems.

Your customers usually fit this description:

They use Python and Linux. They are experienced with Python programming but don't know much about how to do the following:
- package scripts into proper applications
- use git and GitHub
- set up a development environment
- use things like Docker, virtual environments, or networking tools
- write shell scripts
- use a terminal effectively
- the linux filesystem or basic linux commands (beyond ls, mkdir, cd, mv, etc.)

One of your employees has been helping a user (me!) and getting nowhere.
Take a deep look at the message history and do the following:
- summarize the converstation in a sentence
- write a short description of what you think is the underlying issue
- leveraging your considerable expertise in this area, come up with a suggestion to solve my problem.
Be aware that I am short on time and already frustrated.

Here are details about my hardware, OS, and software:
""".strip()

system_instructions = frontline_worker

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
	response = Model(preferred_model).query(messages, verbose = False)
	return response

def escalate(message_store):
	"""
	User calls this when they're frustrated; it's like "speaking with the manager."
	"""
	global preferred_model
	if preferred_model == "gpt-3.5-turbo-0125":
		preferred_model = "gpt-4o"
		print("You're now talking to the manager.")
		message_store.append([time(), {"role": "system", "content": manager}])
	else:
		print("You're already talking to the manager.")
	return message_store

def get_messages(message_store: list[list]) -> list[dict]:
	"""
	Takes a message store object (which is a list of lists, each list has timestamp (0th element) + a message object (1st element)),
	return a list of messages.
	"""
	messages = [s[1] for s in message_store]
	return messages

def get_history(message_store: list[list]) -> tuple[str, dict]:
	"""
	Takes the message store, grabs all the assistant messages, and returns a tuple of:
	- a formatted string with the # of the messages (going backwards in time with 1 being the latest) with the first 100 characters of each message, for the last ten messages.
	- a dict with key as the message number and value as the full message, this is if the user is retrieving a specific message.
	"""
	answers = [s[1] for s in message_store if s[1]['role'] == 'assistant']
	history_string = ""
	history_dict = {}
	for index, answer in enumerate(answers[::-1][:10]):
		answer_string = repr(answer['content'])[:100]
		history_string += f"{index}:\t{answer_string}\n"
		history_dict[index] = answer
	return history_string, history_dict

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

def print_markdown(markdown_string: str):
	"""
	Prints formatted markdown to the console.
	"""
	console = Console(width=80)
	# Create a Markdown object
	border = "-" * 80
	markdown_string = f"{border}\n{markdown_string}\n\n{border}"
	md = Markdown(markdown_string)
	console.print(md)

if __name__ == "__main__":
	# Load the message store
	message_store: list[list] = load_message_store()	# what the admin sees
	# Check if the last message is a system, as part of the escalate flag.
	if message_store[-1][1]['role'] == "system":
		if message_store[-1][1]['content'].startswith("You are now the manager"):
			preferred_model = "gpt-4o"
	# Our argparse code:
	parser = argparse.ArgumentParser()
	parser.add_argument("-s", "-system", dest="system", action="store_true", help="Print system information.")
	parser.add_argument("-m", "-messages", dest="messages", action="store_true", help="Print messages; this is for debugging.")
	parser.add_argument("-c", "-clear", dest="clear", action="store_true", help="Clear messages.")
	parser.add_argument("-e", "-escalate", dest="escalate", action="store_true", help="Talk to the manager.")
	parser.add_argument("-l", "-last", dest="last", action="store_true", help="Print the last message.")
	parser.add_argument("-hi", "-history", dest="history", action="store_true", help="Print the last 10 messages.")
	parser.add_argument("-g", "-get", dest="get", type=str, help="Get a specific answer from the history.")
	parser.add_argument("-r", "-raw", dest="raw", action="store_true", help="Output raw markdown.")
	parser.add_argument("prompt", nargs="*", help="Ask IT a question.")
	# parser.add_argument("-t", "-tutorialize", dest="tutorialize", type=str, help="Generate a tutorial for a given topic.")
	args = parser.parse_args()
	if args.system:									# print system information
		print(get_system_info())
		sys.exit(0)
	if args.messages:								# for debugging
		print(get_messages(message_store))
		sys.exit(0)
	if args.clear:									# to wipe memory
		save_message_store([])
		sys.exit()
	if args.escalate:								# escalate to the manager
		message_store = escalate(message_store)
		query_response = query(get_messages(message_store))
		print_markdown(query_response)
		message_store.append([time(), {'role': 'assistant', 'content': query_response}])
		save_message_store(message_store)
		sys.exit()
	if args.last:									# print the last message
		if args.raw:
			print(get_messages(message_store)[-1]['content'])
		else:
			print_markdown(get_messages(message_store)[-1]['content'])
		sys.exit()
	if args.history:								# print the last 10 messages backwards in time
		history_string, history_dict = get_history(message_store)
		print(history_string)
		sys.exit()
	if args.get:									# get a specific message 1-10
		history_string, history_dict = get_history(message_store)
		try:
			if args.raw:
				print(history_dict[int(args.get)]['content'])
			else:
				print_markdown(history_dict[int(args.get)]['content'])
		except:
			print("Message not found.")
		sys.exit()
	if args.prompt:									# ask the chatbot a question
		input_prompt = " ".join(args.prompt)
		message_store.append([time(), {'role': 'user', 'content': input_prompt}])
		query_response = query(get_messages(message_store))
		if args.raw:
			print(query_response)
		else:
			print_markdown(query_response)
		message_store.append([time(), {'role': 'assistant', 'content': query_response}])
		save_message_store(message_store)
	else:
		print("Either type a prompt, or type -h to see the options.")

	
	



