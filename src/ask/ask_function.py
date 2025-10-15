from conduit.prompt.prompt_loader import PromptLoader
from conduit.sync import Conduit, Prompt, Model, Response, Verbosity
from conduit.message.textmessage import create_system_message
from ask.system_info import get_system_info
import logging

logger = logging.getLogger(__name__)


def query_function(
    inputs: dict[str, str],
    preferred_model: str,
    include_history: bool,
    verbose: Verbosity,
) -> Response:
    """
    Load our system prompt from the prompts directory and set up the Conduit with the provided input.
    """
    logger.info("Starting query_function")
    logger.debug(f"Inputs received: {inputs}")
    logger.debug(f"Preferred model: {preferred_model}")
    logger.debug(f"Include history: {include_history}")
    logger.debug(f"Verbosity level: {verbose}")

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
        logger.info("Loading system prompt from file")
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
        logger.info("Inserting system prompt into message store")

        if not Conduit.message_store:
            logger.error("No message store found.")
            raise ValueError("No message store found.")
        if not Conduit.message_store.system_message:
            logger.debug(
                "No existing system message found. Inserting new system message."
            )
            system_message = create_system_message(system_prompt_str)
            Conduit.message_store.append(system_message[0])
        else:
            logger.debug("System message already exists. Skipping insertion.")

    # Set up system prompt
    assert Conduit.message_store, "No message store found."
    system_prompt: str = _load_system_prompt()
    _insert_system_prompt(system_prompt)
    # Run our query
    logger.info("Running query through Conduit")
    prompt = Prompt(combined_query)
    model = Model(preferred_model)
    conduit = Conduit(model=model, prompt=prompt)
    response = conduit.run(verbose=verbose, include_history=include_history)
    assert isinstance(response, Response), "Response is not of type Response"
    logger.info("Query completed successfully")
    return response
