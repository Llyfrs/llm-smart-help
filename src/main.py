"""
This is the main file for the project.
"""
from typing import Dict, Any, Union

from src.document_parsing import Chunker
from src.models import OAEmbedding, EmbeddingModel
from src.models.agents import Agents
from src.models.llmodel import LLModel
from src.models.qna_pipline import QAPipeline
from src.models.st_embedding import STEmbedding
from src.routines.cli_routine import cli_routine
from src.routines.discord_routine import run_discord_routine
from src.routines.embedding_routine import embedding_routine
from src.routines.generate_answers_routine import generate_answers
from src.vectordb.rating_storage import RatingStorage
from src.vectordb.vector_storage import VectorStorage
from src.routines.server_routine import run_server

import toml  # assuming you're using toml to load your config
import argparse


def argparse_args():
    """
    This function parses command line arguments and returns them.
    """

    parser = argparse.ArgumentParser(description="My App")

    parser.add_argument(
        "--config",
        type=str,
        default="config.toml",
        help="Path to config.toml file (default: config.toml)"
    )

    subparsers = parser.add_subparsers(dest="command", required=True, help="Subcommands")

    # embedding with update/create
    embedding_parser = subparsers.add_parser("embedding", help="Embedding related commands")
    embedding_subparsers = embedding_parser.add_subparsers(dest="action", required=True,
                                                           help="Update or create dictionary")
    update_parser = embedding_subparsers.add_parser("update", help="Update embedding dictionary")
    update_parser.add_argument("path", nargs="?", type=str, help="Optional path to dictionary")
    create_parser = embedding_subparsers.add_parser("create", help="Create embedding dictionary")
    create_parser.add_argument("path", nargs="?", type=str, help="Optional path to dictionary")

    # run-cli
    subparsers.add_parser("run-cli", help="Run CLI mode")

    # run-discord-module
    discord_parser = subparsers.add_parser("run-discord", help="Run Discord module")
    discord_parser.add_argument("--guild-id", type=int, help="Limit Discord Bot to this guild")
    discord_parser.add_argument("--channel-id", type=str, help="Limit Discord Bot to this chat")
    discord_parser.add_argument("--per-user-limit", type=int, help="Limits how many queries can one user have before being blocked, if not set, no limit is applied")
    discord_parser.add_argument("--global-limit", type=int,
                                help="Limits how many queries can be asked of the bot in total. If not set, no limit is applied")

    # run-server
    server_parser = subparsers.add_parser("run-server", help="Run server mode")
    server_parser.add_argument("--port", type=int, help="Port for the Discord module")
    server_parser.add_argument("--address", type=str, help="Address for the Discord module")

    # ✨ new subcommands
    gen_parser = subparsers.add_parser("generate-answers", help="Generate answers from CSV")
    gen_parser.add_argument(
        "path",
        type=str,
        help="Path to CSV file for generating answers"
    )

    eval_parser = subparsers.add_parser("evaluate", help="Evaluate results from CSV")
    eval_parser.add_argument(
        "path",
        type=str,
        help="Path to CSV file for evaluation"
    )

    return parser.parse_args()


def get_config_or_arg(arg_value, config, key, error_msg=None):
    if arg_value is not None:
        return arg_value
    config_value = config.get(key)
    if config_value is not None:
        return config_value
    raise ValueError(error_msg or f"Parameter '{key}' needs to be set either in config or as a command line argument --{key} [value]")


def load_config(config_path):
    try:
        with open(config_path, "r") as f:
            config = toml.load(f)
    except Exception as e:
        raise ValueError(f"Error loading config file: {e}")
    return config

def get_required_config(config, key, error_msg=None):
    value = config.get(key)
    if value is None:
        raise ValueError(error_msg or f"{key} not found in config. Please provide a valid value.")
    return value


def load_llmodels(config: Dict[str, Dict[str, Union[str, float]]]) -> Dict[str, LLModel]:
    models = dict()
    for model in config["model"]:
        model_name = config["model"][model]["model_name"]
        endpoint = config["model"][model]["base_url"]
        api_key = config["model"][model]["api_key"]
        input_cost = config["model"][model].get("input_cost", 0)
        output_cost = config["model"][model].get("output_cost", 0)
        ll_model = LLModel(
            model_name=model_name,
            endpoint=endpoint,
            api_key=api_key,
            input_cost=input_cost,
            output_cost=output_cost,
        )
        models[model] = ll_model

    return models

def load_embedding_model(config: Dict[str, Any]) -> EmbeddingModel | None:
    """
    Looks if default embedding model is selected and if not asks user what embedding model to use.
    :param config:
    :return: embedding model
    """

    embed_model_names = list(config["embedding_model"].keys())

    model_name = config.get("default", {}).get("embedding_model", None)

    if model_name is None :
        print("What embedding model do you want to use?:")
        for i, name in enumerate(embed_model_names):
            print(f"\t{i}) {name}")

        choice = int(input("Enter the number of your choice: "))
        if choice < 0 or choice >= len(embed_model_names):
            print("Invalid choice. Exiting.")
            exit(1)

        model_name = embed_model_names[choice]
        print("Note: This selection can be skipped by setting the embedding_model under [default] in the config file")

    model_config = config["embedding_model"][model_name]
    name = model_config["model_name"]
    api_key = model_config.get("api_key")
    endpoint = model_config.get("base_url")
    dimension = model_config.get("dimension")
    max_tokens = model_config.get("max_tokens")
    prompt = model_config.get("prompt")
    strategy = model_config.get("chunk_strategy", "max_tokens")

    print("Loading embedding model...")
    print( f"Model name: {name}")
    print( f"API key: {api_key}")
    print( f"Endpoint: {endpoint}")
    print( f"Dimension: {dimension}")
    print( f"Max tokens: {max_tokens}")
    print( f"Prompt: {prompt}")
    print( f"Chunk strategy: {strategy}")


    if strategy not in ["max_tokens", "min_tokens", "balanced"]:
        raise ValueError(f"Invalid chunk strategy: {strategy}. Choose from 'max_tokens', 'min_tokens', or 'balanced'.")

    if api_key is None or endpoint is None or dimension is None:
        print(f'Loading local embedding model "{name}", this might take a while')
        model = STEmbedding(model_name=name, cache_folder="cache_folder", prompt=prompt)
        print("Model loaded successfully")
    else:
        model = OAEmbedding(
            model_name=name,
            api_key=api_key,
            endpoint=endpoint,
            dimension=dimension,
            max_tokens=max_tokens,
            prompt=prompt,
        )

    return model, model_name, strategy


def select_agent_models(models: Dict[str, LLModel], config: Dict) -> Agents:
    """
    Select models for each agent role, checking config defaults first.

    :param models: Dictionary of available LLModels
    :param config: Configuration dictionary that might contain defaults
    :return: Agents dataclass with selected models
    """
    model_names = list(models.keys())
    agent_roles = {
        "main_model": "Model that will use all provided information and actually answer the question to the user. "
                      "Quality of this model will impact the quality of response and preferable capable models should be chosen. ",
        "main_researcher_model": "Generates search queries (needs good instruction following but doesn't need to be large)",
        "query_researcher_model": "Processes search results (needs strong comprehension)",
    }

    selected_models = {}
    default_section = config.get("default", {})

    # Check if roles are defined in config defaults
    for role in agent_roles:
        default_model_name = default_section.get(role)
        if default_model_name and default_model_name in models:
            original = models[default_model_name]
            selected_models[role] = LLModel(
                model_name=original.model_name,
                api_key=original.api_key,
                endpoint=original.endpoint,
                input_cost=original.input_cost,
                output_cost=original.output_cost,
            )
            print(f"Using default model for {role}: {default_model_name}")
        else:
            # Ask user to select a model for this role
            print(f"\nChoose a model for {role}:")
            print(f"Description: {agent_roles[role]}")
            for i, name in enumerate(model_names):
                print(f"\t{i}) {name}")

            while True:
                try:
                    choice = int(input(f"Enter number for {role}: "))
                    if 0 <= choice < len(model_names):
                        original = models[model_names[choice]]
                        selected_models[role] = LLModel(
                            model_name=original.model_name,
                            api_key=original.api_key,
                            endpoint=original.endpoint,
                            input_cost=original.input_cost,
                            output_cost=original.output_cost,
                        )
                        break
                    else:
                        print(f"Please enter a number between 0 and {len(model_names) - 1}")
                except ValueError:
                    print("Please enter a valid number")

    return Agents(**selected_models)

def main():
    """
    Main function for the project. Loads all the models based on the config file and moves work to the correct routine based on the command line argument.
    :return:
    """

    args = argparse_args()

    # Load the config file
    config = load_config(args.config)

    models = load_llmodels(config)

    embedding_model, model_name, strategy = load_embedding_model(config)

    agents = select_agent_models(models,config)

    global_prompt = config.get("GLOBAL_CONTEXT", "")




    storage = VectorStorage(
        name=model_name,
        dimension=embedding_model.get_dimension(),
        connection_string=get_required_config(config, "POSTGRESQL_CONNECTION_STRING"),
    )

    rating_storage = RatingStorage(
        name="ratings",
        connection_string=get_required_config(config, "POSTGRESQL_CONNECTION_STRING"),
    )

    qan = QAPipeline(
        agents=agents,
        embedding_model=embedding_model,
        vector_storage=storage,
        global_prompt=global_prompt,
        max_iterations=config.get("ITERATIONS", 5),
    )

    # Based on the command, pull in defaults from config if CLI args aren't provided
    if args.command in ["run-server"]:
        port = get_config_or_arg(args.port, config, "port")
        address = get_config_or_arg(args.address, config, "address")
        print(f"Using port: {port}, address: {address}")

    # Handling embedding commands
    if args.command == "embedding":
        data_path = get_config_or_arg(args.path, config, "data_path")

        ## args should make sure that action is chosen
        action = args.action

        chunker = Chunker(
            chunk_size=embedding_model.max_tokens(),
            chunk_strategy=strategy,
            tokenizer=embedding_model.tokenize,
        )

        embedding_routine(data_path=data_path,
                          chunker=chunker,
                          embedding_model=embedding_model,
                          vector_storage=storage,
                          mode=action)


    if args.command == "run-cli":
        print("Running in CLI mode")
        cli_routine(qan)

    if args.command == "run-discord":

        token = config.get("DISCORD_TOKEN")

        user_limit = args.per_user_limit
        global_limit = args.global_limit
        guild_id = args.guild_id
        channel_id = args.channel_id

        print("Running in Discord mode")
        print("Limit:", user_limit)
        print("Global Limit:", global_limit)
        print("GuildID:", guild_id)
        print("ChannelID:", channel_id)

        guild_id = [guild_id] if guild_id is not None else None
        channel_id = [channel_id] if channel_id is not None else None

        run_discord_routine(
            qna_pipeline=qan,
            bot_token=token,
            rating_storage=rating_storage,
            max_questions_per_user=user_limit,
            max_questions_global=global_limit,
            guild_ids=guild_id,
            channel_ids=channel_id,
        )

    if args.command == "run-server":
        print("Running server module")

        address = get_config_or_arg(args.address, config, "address")
        port = get_config_or_arg(args.port, config, "port")

        run_server(
            qan,
            address=address,
            port=port,
        )

    if args.command == "generate-answers":
        generate_answers(
            path=args.path,
            qan=qan
        )


if __name__ == "__main__":
    main()
