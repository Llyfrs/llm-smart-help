from time import sleep

import requests


def get(url):
    """
    Simple GET request with parsing and error handling added for easier use.
    :param url:
    :return: Parsed JSON response
    """
    response = requests.get(url).json()
    while response.get("error") is not None:

        ## 5 is the error code for when API key runs out of requests, we can wait for it to reset, otherwise we just break and log the error
        if response.get("error").get("code") != 5:
            break

        response = requests.get(url).json()
        sleep(10)

    return response

def save_to_file(content: str, file_name: str, path: str) -> None:
    """
    Save content to a file.
    :param content: The content to save.
    :param file_name: The name of the file.
    :param path: The path to the directory where the file will be saved.
    """
    with open(f"{path}/{file_name}.md", "w") as file:
        file.write(content)

"""
Example of a item from the API:
                "1": {
                        "name": "Hammer",
                        "description": "A small, lightweight tool used in the building industry. Can also be used as a weapon.",
                        "effect": "",
                        "requirement": "",
                        "type": "Melee",
                        "weapon_type": "Clubbing",
                        "buy_price": 75,
                        "sell_price": 50,
                        "market_value": 43,
                        "circulation": 2494041,
                        "image": "https://www.torn.com/images/items/1/large.png",
                        "tradeable": true,
                },
                
Also used https://tornapi.tornplayground.eu/torn/items for reference
"""

def item_data_collection(path: str, api_key: str) -> None:
    """
    Collects item data from the Torn City API and saves it to markdown files.
    :param path: Where to save the files.
    :param api_key: API key for authentication.
    :return: None
    """
    url = "https://api.torn.com/torn/?selections=items&key=" + api_key
    items = get(url)["items"]

    for item in items:

        item = items[item]

        document = "---\n source: Torn City API\n---\n\n"

        document += f"## Item: {item['name']}\n\n"
        document += "This is a Item file generated from the Torn City API. Descriptions are generally to not be taken seriously.\n\n"
        document += f"Description: {item['description']}\n\n"
        document += f"Effect: {item['effect']}\n\n"
        document += f"Requirement: {item['requirement']}\n\n"
        document += f"Type: {item['type']}\n\n"
        document += f"Weapon Type: {item['weapon_type']}\n\n" if item["weapon_type"] else ""
        document += f"Buy Price from in game shops: ${item['buy_price']}\n\n"
        document += f"Sell Price from in game shops: ${item['sell_price']}\n\n"
        document += f"Price on the Item Market: ${item['market_value']}\n\n"
        document += f"Circulation: {item['circulation']}\n\n"
        document += "This items can be traded" if item["tradeable"] else "This is item cannot be traded" + "\n"

        clean_name = item["name"].replace(" ", "_").replace("'", "").replace("-", "_").replace("/", "_").lower()
        save_to_file(document, clean_name, path)

    pass


if __name__ == "__main__":
    import os

    api_key = os.getenv("API_KEY")
    if api_key is None:
        raise ValueError("API_KEY environment variable is not set.")

    path = "items"

    item_data_collection(path, api_key)