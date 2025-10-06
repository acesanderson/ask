import os
import platform
import subprocess


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
    except Exception as e:
        memory_size = "Unknown"

    try:
        gpu_info = subprocess.run(
            gpu_cmd, capture_output=True, text=True
        ).stdout.strip()
    except Exception as e:
        gpu_info = "Unknown"

    try:
        local_ip = subprocess.run(
            ["hostname", "-I"], capture_output=True, text=True
        ).stdout.strip()
    except Exception as e:
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
