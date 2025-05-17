from time import sleep
import requests
import os


def get(url):
    """
    Simple GET request with parsing and error handling added for easier use.
    :param url:
    :return: Parsed JSON response
    """
    response = requests.get(url).json()
    while response.get("error") is not None:
        # 5 = Key exhausted: wait for reset
        if response.get("error").get("code") != 5:
            break
        sleep(10)
        response = requests.get(url).json()

    return response


def save_to_file(content: str, file_name: str, path: str) -> None:
    """
    Save content to a file.
    :param content: The content to save.
    :param file_name: The name of the file.
    :param path: The path to the directory where the file will be saved.
    """
    os.makedirs(path, exist_ok=True)
    with open(f"{path}/{file_name}.md", "w", encoding="utf-8") as file:
        file.write(content)


def medal_data_collection(path: str, api_key: str) -> None:
    """
    Collects medal data from the Torn City API and saves it to markdown files.
    :param path: Where to save the files.
    :param api_key: API key for authentication.
    :return: None
    """
    url = f"https://api.torn.com/torn/?selections=medals&key={api_key}"
    medals = get(url)["medals"]

    for medal_id in medals:
        medal = medals[medal_id]

        document = "---\nsource: Torn City API\n---\n\n"
        document += f"## Award / Merit: {medal['name']}\n\n"
        document += "This is a Medal file generated from the Torn City API.\n\n"
        document += f"Description: {medal['description']}\n\n"
        document += f"Type: {medal['type']}\n\n"
        document += f"Rarity: {medal['rarity']}\n\n"
        document += f"Circulation: {medal['circulation']}\n\n"

        clean_name = medal["name"].replace(" ", "_").replace("'", "").replace("-", "_").replace("/", "_").lower()
        save_to_file(document, clean_name, path)


if __name__ == "__main__":

    api_key = os.getenv("API_KEY")
    if api_key is None:
        raise ValueError("API_KEY environment variable is not set.")

    path = "items"
    medal_data_collection(path, api_key)
