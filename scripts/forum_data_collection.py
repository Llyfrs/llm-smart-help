import json
from urllib.parse import urlparse, parse_qs

from bs4 import BeautifulSoup

from item_data_collection import get, save_to_file
from markdownify import markdownify as md
import html2text
import os

import bbcode


def bbcode_html_to_markdown(raw_input: str) -> str:
    # 1. Parse & fix broken HTML
    soup = BeautifulSoup(raw_input, 'html.parser')
    cleaned_html = str(soup)

    # 2. Convert to Markdown
    return md(cleaned_html, heading_style="ATX")

"""
{
      "id": 15977639,
      "title": "Stock Analyst",
      "forum_id": 61,
      "posts": 65,
      "rating": 88,
      "views": 11310,
      "author": {
        "id": 258120,
        "username": "Harley",
        "karma": 23929
      },
      "last_poster": {
        "id": 3391134,
        "username": "Tamirys",
        "karma": 87
      },
      "first_post_time": 1468939924,
      "last_post_time": 1744581675,
      "has_poll": false,
      "is_locked": false,
      "is_sticky": false
    }
"""

def safe_forum_post(id : str, category_id: str, title:str, path: str, api_key: str):
    url = f"https://api.torn.com/v2/forum/{id}/posts?striptags=false" + f"&key={api_key}"
    post_url = f"https://www.torn.com/forums.php#/p=threads&f={category_id}&t={id}"
    response = get(url)["posts"]
    poster_id = None

    document = f"---\nsource: Torn City Forums\nurl: {post_url}\n---\n\n"
    document += f"## {title}\n\n"
    content = ""



    for post in response:
        if poster_id is None:
            if (post["likes"] - post["dislikes"]) < 30:
                break
            poster_id = post["id"]

        if post["id"] != poster_id:
            break

        content += post["content"]

    if content == "":
        # print(f"Skipping Thread: {title}")
        return


    content = bbcode_html_to_markdown(content)
    document += content

    clear_title = title.replace(" ", "_").replace(":", "_").replace("?", "_").replace("/", "_")

    save_to_file(document, clear_title, path)



    pass



## This is broken as there is a bug in the API at the time of writing this commnet
def forum_data_collection(path: str, api_key: str):
    guide_section_id = 61
    url = f"https://api.torn.com/v2/forum/{guide_section_id}/threads?limit=100&sort=ASC&key={api_key}"

    unique_threads = set()

    for _ in range(18): ## 1000 forums posts tested
        response = get(url)
        first_post_time = 0

        if response.get("threads") is None:
            print(f"Got {response} threads")
            break

        for threads in response["threads"]:
            first_post_time = max(first_post_time, threads["first_post_time"])
            unique_threads.add(threads["id"])
            if threads["rating"] > 50:
                print(f"Saving Thread: {threads['title']}")
                safe_forum_post(threads["id"], guide_section_id , threads["title"], path, api_key)
            else:
                print(f"Skipping Thread: {threads['title']}")

        print("Got next page")

        url = f"https://api.torn.com/v2/forum/{guide_section_id}/threads?limit=100&sort=ASC&key={api_key}&from={first_post_time}"

    print("Got all threads")
    print(f"Got {len(unique_threads)} unique threads")
    pass


def extract_forum_and_thread_ids(url):
    parsed_url = urlparse(url)
    query_params = parse_qs(parsed_url.query)

    forum_id = query_params.get('f', [None])[0]
    thread_id = query_params.get('t', [None])[0]

    return forum_id, thread_id

if __name__ == "__main__":


    api_key = os.getenv("API_KEY")
    if api_key is None:
        raise ValueError("API_KEY environment variable is not set.")

    path = "items"

    threads = "scripts/threads.json"

    with open(threads, "r") as f:
        threads = json.load(f)

    from tqdm import tqdm

    for thread in tqdm(threads, desc="Processing threads"):
        try:
            category, thread_id = extract_forum_and_thread_ids(thread["Link"])
            if int(thread.get("Rating", 0) or 0) >= 30:
                safe_forum_post(thread_id, category, thread["Title"], path, api_key)
        except (ValueError, TypeError):
            continue  # Skip threads with invalid Rating
