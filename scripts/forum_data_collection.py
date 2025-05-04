import json
import urllib
from urllib.parse import urlparse, parse_qs




from item_data_collection import get, save_to_file
import os


import urllib.parse # For handling relative URLs if needed

from markdownify import markdownify as md
from bs4 import BeautifulSoup, NavigableString
import urllib.parse
import re


def preprocess_html_for_markdown(soup, base_url=None):
    """
    Cleans and simplifies HTML specifically for better Markdown conversion.
    - Resolves relative URLs.
    - Tries to convert simple style spans (bold/italic) to semantic tags.
    - Removes problematic style attributes.
    - Handles divs used for alignment (removes alignment, keeps content).
    """

    # 1. Resolve relative URLs
    if base_url:
        for tag in soup.find_all(['a', 'img'], href=lambda x: x is not None and not urllib.parse.urlparse(x).scheme):
            attr = 'href' if tag.name == 'a' else 'src'
            try:
                tag[attr] = urllib.parse.urljoin(base_url, tag[attr])
            except Exception:
                pass  # Ignore if URL joining fails

    # 2. Simplify common styling spans (basic example, can be expanded)
    #    Note: This is tricky and might not catch all cases or have side effects.
    #    It's often better to let markdownify handle strong/em directly if possible.
    # for span in soup.find_all("span"):
    #    style = span.get("style", "").lower()
    #    if "font-weight:bold" in style or "font-weight: 700" in style:
    #         span.wrap(soup.new_tag("strong"))
    #         span.unwrap() # Remove the span itself
    #    elif "font-style:italic" in style:
    #        span.wrap(soup.new_tag("em"))
    #        span.unwrap()

    # 3. Remove complex style attributes that confuse Markdown converters
    #    Focus on keeping structure, not visual styles.
    for tag in soup.find_all(True):  # Find all tags
        if 'style' in tag.attrs:
            # Keep the tag, but ditch the style that markdown can't use
            # Exception: Maybe keep simple list-style-type if needed? (rare)
            del tag.attrs['style']
        # Remove specific attributes that don't map well
        for attr in ['align', 'size', 'color', 'face']:  # Deprecated HTML attributes
            if attr in tag.attrs:
                del tag.attrs[attr]

    # 4. Handle DIVs used mainly for alignment/structure
    #    Replace divs with paragraphs or just unwrap if they add no semantic value.
    for div in soup.find_all("div"):
        # If div contains only inline content or phrasing content, maybe convert to <p>
        # If it contains block content (like lists, other divs), just remove the div wrapper
        # This is heuristic. A simple approach is often just to unwrap.
        div.unwrap()  # Removes the <div> tag, keeping its content in place

    # 5. Remove empty tags that might result from cleaning
    for tag in soup.find_all(
            lambda t: not isinstance(t, NavigableString) and not t.contents and not t.text.strip() and t.name not in [
                'br', 'hr', 'img']):
        tag.decompose()

    return soup


def tornhtml_to_markdown(html_content: str, base_url: str = None, **md_options) -> str:
    """
    Converts Torn City Forum HTML (potentially with BBCode remnants) to Markdown.
    Focuses on structure and semantics, styling will be lost.

    Args:
        html_content: The raw HTML string.
        base_url: The base URL (e.g., "https://www.torn.com") to resolve relative links.
        **md_options: Additional options for the markdownify converter.

    Returns:
        Markdown string or an error message.
    """
    if not isinstance(html_content, str):
        return "Error: Input must be a string."
    if not html_content.strip():
        return ""

    try:
        # --- Metadata Extraction (Optional) ---
        source = None
        url = None
        match_source = re.search(r"^---\s*\n^source:\s*(.*?)\s*$", html_content, re.MULTILINE)
        match_url = re.search(r"^url:\s*(.*?)\s*$", html_content, re.MULTILINE)
        if match_source:
            source = match_source.group(1).strip()
        if match_url:
            url = match_url.group(1).strip()

        # Remove the metadata block for cleaner HTML parsing
        html_body = re.sub(r"^---\s*$.*?^---\s*$\n?", "", html_content, flags=re.MULTILINE | re.DOTALL).strip()
        # Also remove the initial H2 if it exists right after metadata
        html_body = re.sub(r"^## .*?\n+", "", html_body).strip()

        # 1. Parse the core HTML content
        soup = BeautifulSoup(html_body, 'html.parser')

        # 2. Preprocess: Clean HTML, fix URLs
        cleaned_soup = preprocess_html_for_markdown(soup, base_url)
        final_html = str(cleaned_soup)

        # 3. Convert cleaned HTML to Markdown
        default_md_options = {
            'heading_style': 'ATX',
            'strip': ['script', 'style'],  # Strip remaining styles if any
            'keep_inline_images_in': ['p', 'li', 'td', 'th'],
            'newline_style': 'unix',
            'strong_em_symbol': '*',  # Use '*' for both bold/italic if desired, or default is usually fine
            'bullets': '-*',  # Use - or * for list items
            'escape_underscores': True,  # Prevent underscores in text from being italics
        }
        final_md_options = {**default_md_options, **md_options}

        markdown_output = md(final_html, **final_md_options)

        # --- Re-add Metadata (Optional) ---
        metadata_prefix = ""
        if source or url:
            metadata_prefix = "---\n"
            if source: metadata_prefix += f"source: {source}\n"
            if url: metadata_prefix += f"url: {url}\n"
            metadata_prefix += "---\n\n"

        # Add back the initial H2 if it was removed (optional, depends if you want it)
        # title_match = re.search(r"^## (.*?)\n", html_content)
        # title_prefix = title_match.group(0) if title_match else ""

        return metadata_prefix + markdown_output  # + title_prefix

    except Exception as e:
        import traceback
        # print(f"Conversion Error: {e}\n{traceback.format_exc()}") # Uncomment for debugging
        raise "Conversion Error" from e


def bbcode_html_to_markdown(raw_input: str) -> str:
    return tornhtml_to_markdown(raw_input, base_url="https://www.torn.com", heading_style="ATX",
                                strip=["script", "style"], keep_inline_images_in=["p", "li", "td", "th"],
                                newline_style="unix", strong_em_symbol="*", bullets="-*", escape_underscores=True)


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
