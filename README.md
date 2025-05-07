# About 


## Installation

First, make sure you have uv installed. You can install it by following their guide [here](https://docs.astral.sh/uv/getting-started/installation/)

Then you can run the project using:
```bash
uv run -m src.main --help
```

If you plan on running anything from /scripts, you can install their dependencies using:
```bash
uv sync --extra scripts
```

## Config 

Rename the `config.example.toml` to `config.toml` and look inside for how to properly set up the project. 
When running an embedding model locally, make sure it's compatible with [sentence_transformers](https://www.sbert.net/). You can usually find this on models hugging face page

## Embedding Data 

> Note: This project only works with Markdown (.md) files, as it uses its structure to split the data in to meaningful chunks. If you have data in different format, you will have to convert them first.

The first step in having the AI be able to answer questions about your files is to provide those files. You have two options either use the `create` or `update` subcommands. 

### Create

The `create` subcommand will create a new database table and populate it with Markdown files from provided directory. **If table already exsists for that embedding model, the current data will be removed**. This commands serves as a way to restart data set or create it for the first time. 

Example Usage:
```bash
## This will embedded all data from the directory /data and load it in to postgres database
uv run -m src.main embedding create data
```


### Update 
The `update` subcommand is way safer as it only updates an existing table in a database, if file is new or was edited after last update, it will delete that file associated embedding and embed it again. This command still creates database if it doesn't exists so it should be used instead of `create` in most cases.

Example Usage:
```bash
## This will embedded all data from the directory /data and update the postgres database according
uv run -m src.main embedding update data
```


