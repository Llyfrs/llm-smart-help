# About 

This program represents a set of tools that allow for creation of topic aware system that is able to answer user questions based on provided dataset. It implements basic RAG with embedding and added iterative search to allow for deeper exploration of topics. 

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


## Running the Q&A pipline 

There are multiple ways to run the Q&A pipline, in each case the process of research is the same only the way you can interact with it changes. 

### CLI 

Simplest interface and quick way to debug / test the system. You will be prompted to ask a question, then the models gets to work and when it comes up with an answer it will be printed with all the steps that lead to that answer. It's a bit messy, but reading the reasoning's and questions asked is good way to see what the model does't get and what prompt could improve it. 

```bash
uv run -m src.main run-cli
```

### Server

Allows running the system as a server accepting queries at the endpoint `/query`, with the data format bellow. This allows for asynch processing of each query, and integration with other services. The response data contains all the information about the run, the final answer is in `final_answer`


```bash
# Runs server on localhost on port 12412
uv run -m src.main run-server --address 127.0.0.1 --port 12412
```

Example of a request:
```bash
curl -X POST http://127.0.0.1:12412/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What are the main causes of climate change?",
    "iterations": 5
}'
```
### Discord

Integrates the Q&A pipline in to a discord bot, that when mentioned will answer the user asked question. 
You can limit it by defining discord guild and / or discord channel that it will answer in and ignore mentions anywhere else.  
This mode was used to collect user feedback and currently comes with a rating option after each answer.
You can set global limit to limit how many questions in total the bot is allowed to answer and per user limit to limit single user from using up all of global limit. 

```bash
# Runs Q&A pipeline inside of discord bot 
uv run -m src.main run-discord --guild-id 123124 --channel-id 11124 --per-user-limi 5 --global-limit 100
```

## Evaluation 

You can use a csv file that includes collum named `query`, to generate answer to each question and save it again in csv file. 
This processes preservers any other existing values and saves the final product in to a new file.  
Be warned that this process runs in parallel to speed up the generation so if order of question is important include ID field in your csv, otherwise you will lose the order. 

```bash
# generates answers for questions from csv files
uv run -m src.main generate-answers eval_set.csv
```

## Choosing Models

Internally, there are 3 different agents and they each use different model, these are the agents and my recommendation on how capable the model should be:

- `main_model` - This model is responsible for the final answer, it should be able to piece together information from long context.
- `main_researcher_model` - This model is going to iterate over the researched data and decide what data to collect next. Reasoning model that follows instructions is the best option.
- `query_researcher_model`- Only needs to answer one question based on context, generally can be smaller. Cheap input is key for this model to keeping costs somewhat low.