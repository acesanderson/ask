from setuptools import setup, find_packages

setup(
    name="Ask",
    version="0.1",
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "ask = ask.ask:main",
        ],
    },
)
