from ask.system_info import get_system_info
from conduit.prompt.prompt_loader import PromptLoader
from conduit.progress.verbosity import Verbosity
from argparse import ArgumentParser
from rich.console import Console
from pathlib import Path
import sys

PREFERRED_MODEL = "haiku"
VERBOSITY = Verbosity.COMPLETE
CACHE_PATH = Path(__file__).parent / ".cache.db"


class Ask:
    def __init__(self):
        self.console = Console()
        # Flags
        self.preferred_model = PREFERRED_MODEL
        # Control flow
        self.parser = self._setup_parser()
        self._process_args(self.parser)

    def _load_system_prompt(self):
        from pathlib import Path

        dir_path = Path(__file__).parent
        prompts_dir = dir_path / "prompts"

        prompt_loader = PromptLoader(prompts_dir)
        system_prompt = prompt_loader["system_prompt"]
        system_info = get_system_info()
        system_prompt = system_prompt.render(
            input_variables={"system_info": system_info}
        )
        return system_prompt

    def _get_stdin(self) -> str:
        """
        Get implicit context from clipboard or other sources.
        """
        context = sys.stdin.read() if not sys.stdin.isatty() else ""
        return context

    def _coerce_query_input(self, query_input: str | list) -> str:
        """
        Coerce query input to a string.
        If input is a list, join with spaces.
        """
        if not query_input:
            self.console.print("[bold red]No query provided.[/bold red]")
            sys.exit(1)
        elif isinstance(query_input, list):
            coerced_query_input = " ".join(query_input)
        elif isinstance(query_input, str):
            coerced_query_input = query_input
        return coerced_query_input

    def _setup_parser(self) -> ArgumentParser:
        """
        Setup the argument parser based on the configuration.
        """
        parser = ArgumentParser()
        parser.add_argument(
            "query",
            nargs="*",
            help="The query to ask the AI. If not provided, reads from stdin.",
        )
        parser.add_argument(
            "-m",
            "--model",
            type=str,
            default=self.preferred_model,
            help="The model to use for the query.",
        )
        parser.add_argument(
            "-r",
            "--raw",
            action="store_true",
            help="Output raw response without any formatting.",
        )
        return parser

    def _process_args(self, parser: ArgumentParser):
        """
        Process the arguments and execute the query.
        """
        args = parser.parse_args()
        query_input = self._coerce_query_input(args.query)
        self.preferred_model = args.model or self.preferred_model
        response = self.query(query_input)
        if args.raw:
            print(response)
        else:
            from rich.markdown import Markdown

            markdown = Markdown(str(response.content))
            self.console.print(markdown)

    def query(self, query_input: str):
        from conduit.sync import Prompt, Model, Conduit
        from conduit.message.textmessage import create_system_message
        from conduit.cache.cache import ConduitCache

        Model._console = self.console
        Model._conduit_cache = ConduitCache(CACHE_PATH)

        # Set up system prompt
        self.system_prompt = self._load_system_prompt()
        system_message = create_system_message(self.system_prompt)
        messages = system_message
        prompt = Prompt(query_input)
        model = Model(self.preferred_model)
        conduit = Conduit(model=model, prompt=prompt)
        response = conduit.run(messages=messages, verbose=VERBOSITY)
        return response


def main():
    Ask()


if __name__ == "__main__":
    main()
