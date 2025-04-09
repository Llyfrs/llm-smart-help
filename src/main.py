"""
This is the main file for the project.
"""
from typing import Dict, Any, Type

from pydantic import BaseModel

from src.models import OAEmbedding, EmbeddingModel
from src.models.llmodel import LLModel
from src.models.st_embedding import STEmbedding
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
        model_name = config["model"][model]["MODEL_NAME"]
        endpoint = config["model"][model]["END_POINT"]
        api_key = config["model"][model]["API_KEY"]
        ll_model = LLModel(
            model_name=model_name,
            endpoint=endpoint,
            api_key=api_key,
        )
        print(f"Found llm model \"{model}\" in config file")
        models[model] = ll_model

    return models

def load_embedding_model(config : Dict[str, Any], model_name: str) -> Type[EmbeddingModel]:

    model = None

    for m in config["embed_model"]:

        if m != model_name:
            continue

        name = config[m]["MODEL_NAME"] ## Will be needed we might as well crash
        api_key = config[m].get("API_KEY", None)
        endpoint = config[m].get("END_POINT", None)
        dimension = config[m].get("DIMENSION", None)

        if api_key is None or endpoint is None or dimension is None:
            model = STEmbedding(name, cache_folder="cache_folder")
        else:
            model = OAEmbedding(
                model_name=name,
                api_key=api_key,
                endpoint=endpoint,
                dimension=dimension
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

    # Based on the command, pull in defaults from config if CLI args aren't provided
    if args.command in ["run-discord-module", "run-server"]:
        port = get_config_or_arg(args.port, config, "port")
        address = get_config_or_arg(args.address, config, "address")
        print(f"Using port: {port}, address: {address}")

    # Example: Handling embedding commands
    if args.command == "embedding":
        data_path = get_config_or_arg(args.path, config, "data_path")

        ## args should make sure that action is chosen
        action = args.action


    if args.command == "run-cli":
        print("Running in CLI mode")

    if args.command == "run-discord-module":
        print("Running Discord module")

    if args.command == "run-server":
        print("Running server")

    connection_string = get_required_config(config, "POSTGRESQL_CONNECTION_STRING")

    exit(0)

    model = STEmbedding("intfloat/multilingual-e5-large-instruct")

    print("Embedding model loaded successfully!")

    table = VectorStorage(
        name="MiniLM", dimension=model.dimension, connection_string=connection_string
    )

    result = table.get_file(
        "Dual Bushmasters -  Torncity WIKI - The official help and support guide.md"
    )
    print(f"Result: {result}")

    exit(0)

    llmodel = LLModel(
        model_name=config["model"][list(config["model"].keys())[0]]["MODEL_NAME"],
        endpoint=config["model"][list(config["model"].keys())[0]]["ENDPOINT_URL"],
        api_key=config["model"][list(config["model"].keys())[0]]["API_KEY"],
        system_prompt="Based on provided context, answer the question.",
    )

    print("LLM model loaded successfully!")

    # get_chunks(model, table)

    def get_detailed_instruct(task_description: str, query: str) -> str:
        return f"Instruct: {task_description}\nQuery: {query}"

    while True:

        query = input("Enter the query: ")

        query = get_detailed_instruct(
            "Given provided query, retrieve documents that best answer asked question.",
            query,
        )

        query_vector = model.embed([query])[0].tolist()

        results = table.query(query_vector, n=5, distance="cosine")

        context = "Context:\n\n"
        for result in results:
            context += result.content + "\n\n"

        # print(f"Context: {context}")

        context += "Question:\n\n"

        llmodel_response = llmodel.generate_response(prompt=context + query)

        print(f"LLM Response: {llmodel_response}")


if __name__ == "__main__":
    main()
