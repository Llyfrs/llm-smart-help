"""
This is the main file for the project.
"""
from typing import Dict, Any, Type

from pydantic import BaseModel

from src.document_parsing import Chunker
from src.models import OAEmbedding, EmbeddingModel
from src.models.llmodel import LLModel
from src.models.st_embedding import STEmbedding
from src.routines.cli_routine import cli_routine
from src.routines.embedding_routine import embedding_routine
from src.vectordb.vector_storage import VectorStorage

import argparse
import toml  # assuming you're using toml to load your config

def argparse_args():

    """
    This function parses command line arguments and returns them.
    :return:
    """

    parser = argparse.ArgumentParser(description="My App")
    # global config file argument
    parser.add_argument(
        "--config",
        type=str,
        default="config.toml",
        help="Path to config.toml file (default: config.toml)"
    )

    # Creating subparsers for mutually exclusive commands
    subparsers = parser.add_subparsers(dest="command", required=True, help="Subcommands")

    # Embedding command with subcommands 'update' and 'create'
    embedding_parser = subparsers.add_parser("embedding", help="Embedding related commands")
    embedding_subparsers = embedding_parser.add_subparsers(dest="action", required=True,
                                                           help="Update or create dictionary")

    # embedding update command
    update_parser = embedding_subparsers.add_parser("update", help="Update embedding dictionary")
    update_parser.add_argument(
        "path",
        nargs="?",
        type=str,
        help="Optional path to dictionary"
    )

    # embedding create command
    create_parser = embedding_subparsers.add_parser("create", help="Create embedding dictionary")
    create_parser.add_argument(
        "path",
        nargs="?",
        type=str,
        help="Optional path to dictionary"
    )

    # run-cli command (no extra args)
    subparsers.add_parser("run-cli", help="Run CLI mode")

    # run-discord-module command with optional port/address overrides
    discord_parser = subparsers.add_parser("run-discord-module", help="Run Discord module")
    discord_parser.add_argument("--port", type=int, help="Port for the Discord module")
    discord_parser.add_argument("--address", type=str, help="Address for the Discord module")

    # run-server command with optional port/address overrides
    server_parser = subparsers.add_parser("run-server", help="Run server mode")
    server_parser.add_argument("--port", type=int, help="Port for the server")
    server_parser.add_argument("--address", type=str, help="Address for the server")

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


def load_llmodels(config : Dict[str, Dict[str, str]]) -> Dict[str, LLModel]:
    models = dict()
    for model in config["model"]:
        model_name = config["model"][model]["model_name"]
        endpoint = config["model"][model]["base_url"]
        api_key = config["model"][model]["api_key"]
        ll_model = LLModel(
            model_name=model_name,
            endpoint=endpoint,
            api_key=api_key,
        )
        print(f"Found llm model \"{model}\" in config file")
        models[model] = ll_model

    return models

def load_embedding_model(config: Dict[str, Any]) -> EmbeddingModel | None:
    embed_model_names = list(config["embedding_model"].keys())

    print("What embedding model do you want to use?:")
    for i, name in enumerate(embed_model_names):
        print(f"\t{i}) {name}")

    choice = int(input("Enter the number of your choice: "))
    if choice < 0 or choice >= len(embed_model_names):
        print("Invalid choice. Exiting.")
        exit(1)

    selected_model_key = embed_model_names[choice]
    print("Note: This selection can be skipped by setting the embedding_model under [default] in the config file")

    model_config = config["embedding_model"][selected_model_key]
    name = model_config["model_name"]
    api_key = model_config.get("api_key")
    endpoint = model_config.get("base_url")
    dimension = model_config.get("dimension")
    prompt = model_config.get("prompt")

    if api_key is None or endpoint is None or dimension is None:
        print(f'Loading local embedding model "{name}", this might take a while')
        model = STEmbedding(name, cache_folder="cache_folder", prompt=prompt)
        print("Model loaded successfully")
    else:
        model = OAEmbedding(
            model_name=name,
            api_key=api_key,
            endpoint=endpoint,
            dimension=dimension,
            prompt=prompt,
        )

    return model


def main():

    """
    Main function for the project.
    :return:
    """

    args = argparse_args()

    # Load the config file
    config = load_config(args.config)

    models = load_llmodels(config)

    embedding_model = load_embedding_model(config)

    storage = VectorStorage(
        name="local",
        dimension=embedding_model.get_dimension(),
        connection_string=get_required_config(config, "POSTGRESQL_CONNECTION_STRING"),
    )

    # Based on the command, pull in defaults from config if CLI args aren't provided
    if args.command in ["run-discord-module", "run-server"]:
        port = get_config_or_arg(args.port, config, "port")
        address = get_config_or_arg(args.address, config, "address")
        print(f"Using port: {port}, address: {address}")

    # Handling embedding commands
    if args.command == "embedding":
        data_path = get_config_or_arg(args.path, config, "data_path")

        ## args should make sure that action is chosen
        action = args.action

        chunker = Chunker(
            chunk_size=embedding_model.get_dimension(),
            chunk_strategy="balanced",
            tokenizer=embedding_model.tokenize,
        )

        embedding_routine(data_path=data_path,
                          chunker=chunker,
                          embedding_model=embedding_model,
                          vector_storage=storage,
                          mode=action)


    if args.command == "run-cli":
        print("Running in CLI mode")
        cli_routine(
            model=models["gemma_3_4B"],
            embedding_model=embedding_model,
            vector_storage=storage,
        )

    if args.command == "run-discord-module":
        print("Running Discord module")

    if args.command == "run-server":
        print("Running server")




if __name__ == "__main__":
    main()
