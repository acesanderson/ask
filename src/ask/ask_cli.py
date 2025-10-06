"""
This is a customization of Twig's CLI tool to create a specialized assistant for IT administration tasks.

Still needs work, and solutions we develop here (particularly re: system prompts) should be migrated upstream to Twig.
"""

from twig.twig_class import Twig, Verbosity
from twig.handlers import Conduit, Prompt, Model, Response
from ask.system_info import get_system_info
from conduit.prompt.prompt_loader import PromptLoader
from conduit.message.textmessage import create_system_message

# Configs
PREFERRED_MODEL = "claude"
DESCRIPTION = "Your friendly IT administrator."
VERBOSITY = Verbosity.PROGRESS


def query_function(
    inputs: dict[str, str],
    preferred_model: str,
    nopersist: bool,
    verbose: Verbosity,
) -> Response:
    """
    Load our system prompt from the prompts directory and set up the Conduit with the provided input.
    """

    # Unpack inputs dictionary
    query_input = inputs.get("query_input", "")
    context = inputs.get("context", "")
    append = inputs.get("append", "")

    # Generate combined query
    combined_query = "\n\n".join(
        [query_input, f"<context>\n{context}\n</context>" if context else "", append]
    ).strip()

    # Load system prompt from file
    def _load_system_prompt() -> str:
        from pathlib import Path

        dir_path = Path(__file__).parent
        prompts_dir = dir_path / "prompts"

        prompt_loader = PromptLoader(prompts_dir)
        system_prompt = prompt_loader["system_prompt"]

        system_info = get_system_info()
        system_prompt_str = system_prompt.render(
            input_variables={"system_info": system_info}
        )
        return system_prompt_str

    def _insert_system_prompt(system_prompt_str: str) -> None:
        """
        Insert system prompt into message store if not already present.
        """

        if not Conduit._message_store:
            raise ValueError("No message store found.")
        if not Conduit._message_store.system_message:
            system_message = create_system_message(system_prompt_str)
            Conduit._message_store.append(system_message[0])

    # Set up system prompt
    assert Conduit._message_store, "No message store found."
    system_prompt: str = _load_system_prompt()
    _insert_system_prompt(system_prompt)
    # Run our query
    prompt = Prompt(combined_query)
    model = Model(PREFERRED_MODEL)
    conduit = Conduit(model=model, prompt=prompt)
    response = conduit.run(verbose=VERBOSITY)
    assert isinstance(response, Response), "Response is not of type Response"
    return response


def main():
    ask = Twig(
        query_function=query_function,
        verbosity=VERBOSITY,
        description="Ask questions to the AI model with context.",
        preferred_model=PREFERRED_MODEL,
    )
    ask.run()


if __name__ == "__main__":
    main()
