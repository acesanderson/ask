"""
This is a customization of Twig's CLI tool to create a specialized assistant for IT administration tasks.

Still needs work, and solutions we develop here (particularly re: system prompts) should be migrated upstream to Twig.
"""

from twig.twig_class import Twig, Verbosity
from ask.ask_function import query_function

# Configs
NAME = "ask"
DESCRIPTION = "Your friendly IT administrator."
VERBOSITY = Verbosity.PROGRESS
PREFERRED_MODEL = "claude"
QUERY_FUNCTION = query_function


def main():
    ask = Twig(
        name=NAME,
        description=DESCRIPTION,
        query_function=QUERY_FUNCTION,
        verbosity=VERBOSITY,
        preferred_model=PREFERRED_MODEL,
    )
    ask.run()


if __name__ == "__main__":
    main()
