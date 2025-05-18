import json
import urllib.parse
import os
from markdownify import markdownify as md
from bs4 import BeautifulSoup, NavigableString
import re

# item_data_collection.py must exist in the same directory or be in PYTHONPATH
# and must contain get(url) and save_to_file(content, filename, path) functions.
from item_data_collection import get, save_to_file


def preprocess_html_for_markdown(soup, base_url=None):
    if base_url:
        for tag in soup.find_all(['a', 'img'], href=lambda x: x is not None and not urllib.parse.urlparse(x).scheme):
            attr = 'href' if tag.name == 'a' else 'src'
            try:
                tag[attr] = urllib.parse.urljoin(base_url, tag[attr])
            except Exception:
                pass
    for tag in soup.find_all(True):
        if 'style' in tag.attrs: del tag.attrs['style']
        for attr in ['align', 'size', 'color', 'face']:
            if attr in tag.attrs: del tag.attrs[attr]
    for div in soup.find_all("div"): div.unwrap()
    for tag in soup.find_all(
            lambda t: not isinstance(t, NavigableString) and not t.contents and not t.text.strip() and t.name not in [
                'br', 'hr', 'img']):
        tag.decompose()
    return soup


def tornhtml_to_markdown(html_content: str, base_url: str = None, **md_options) -> str:
    if not isinstance(html_content, str): return ""
    if not html_content.strip(): return ""
    try:
        html_body = re.sub(r"^---\s*$.*?^---\s*$\n?", "", html_content, flags=re.MULTILINE | re.DOTALL).strip()
        html_body = re.sub(r"^## .*?\n+", "", html_body).strip()
        if not html_body: return ""
        soup = BeautifulSoup(html_body, 'html.parser')
        cleaned_soup = preprocess_html_for_markdown(soup, base_url)
        final_html = str(cleaned_soup)
        default_md_options = {
            'heading_style': 'ATX', 'strip': ['script', 'style'],
            'keep_inline_images_in': ['p', 'li', 'td', 'th'], 'newline_style': 'unix',
            'strong_em_symbol': '*', 'bullets': '-*', 'escape_underscores': True,
        }
        final_md_options = {**default_md_options, **md_options}
        return md(final_html, **final_md_options)
    except Exception as e:
        raise Exception(f"Conversion Error during tornhtml_to_markdown for content: '{html_content[:100]}...'") from e


def bbcode_html_to_markdown(raw_input: str) -> str:
    return tornhtml_to_markdown(raw_input, base_url="https://www.torn.com")


def save_forum_conversation(thread_id: str, category_id: str, title: str, output_path: str, api_key: str):
    """
    Fetches all posts from a forum thread and saves them as a single Markdown conversation file.
    Adapts to the new API structure where "posts" is a list of post objects.
    """
    api_url = f"https://api.torn.com/v2/forum/{thread_id}/posts?striptags=false&key={api_key}"
    thread_url_on_torn = f"https://www.torn.com/forums.php#/p=threads&f={category_id}&t={thread_id}"

    print(f"Fetching posts for thread: '{title}' (ID: {thread_id})")
    response_data = get(api_url)

    if not response_data:
        print(f"  No response data received for thread: '{title}' (ID: {thread_id})")
        return
    if "error" in response_data:
        api_error = response_data['error']
        print(
            f"  API Error for thread '{title}': Code {api_error.get('code', 'N/A')} - {api_error.get('error', 'Unknown error')}")
        return
    if "posts" not in response_data or not response_data["posts"]:  # Check if posts exists and is not empty
        print(f"  No posts found or 'posts' field empty/missing for thread: '{title}' (ID: {thread_id})")
        return

    posts_list = response_data["posts"]

    if not isinstance(posts_list, list):
        print(
            f"  Error: 'posts' field is not a list as expected for thread '{title}'. Type: {type(posts_list)}. Skipping.")
        # You could add a fallback here if the old dictionary format might still occur,
        # but based on your new info, a list is the primary expectation.
        return

    if not posts_list:  # Empty list
        print(f"  'posts' list is empty for thread: '{title}' (ID: {thread_id}).")
        return

    # Sort posts by creation time
    try:
        # Ensure all items are dicts and have 'created_time' before sorting
        valid_posts_for_sorting = [p for p in posts_list if isinstance(p, dict) and 'created_time' in p]
        if len(valid_posts_for_sorting) != len(posts_list):
            print(
                f"  Warning: Some items in 'posts' list were not valid dictionaries or lacked 'created_time' for thread '{title}'.")

        sorted_posts = sorted(
            valid_posts_for_sorting,
            key=lambda p: p.get('created_time', 0)
            # Default to 0 if created_time is missing (shouldn't happen for valid posts)
        )
    except Exception as e_sort:
        print(f"  Error sorting posts for thread '{title}': {e_sort}. Processing in received order.")
        sorted_posts = [p for p in posts_list if isinstance(p, dict)]  # Fallback to original order of valid dicts

    if not sorted_posts:
        print(f"  No valid posts to process after sorting/filtering for thread '{title}'.")
        return

    document_parts = []
    # YAML Frontmatter for the thread
    document_parts.append(f"---\n")
    document_parts.append(f"source: Torn City Forums Q&A\n")  # UPDATED SOURCE
    document_parts.append(f"thread_title: \"{title.replace('"', '""')}\"\n")
    document_parts.append(f"thread_id: {thread_id}\n")
    document_parts.append(f"category_id: {category_id}\n")
    document_parts.append(f"thread_url: {thread_url_on_torn}\n")
    document_parts.append(f"---\n\n")
    document_parts.append(f"## {title}\n\n")

    has_actual_content = False
    for post_item in sorted_posts:
        author_info = post_item.get("author", {})
        poster_name = author_info.get("username", "Unknown User")
        poster_id = author_info.get("id", "N/A")

        html_content = post_item.get("content", "")
        # post_id_val = post_item.get("id", "N/A") # Individual post ID, can be used if needed
        # post_timestamp = post_item.get("created_time", "N/A") # Timestamp

        if not html_content or not html_content.strip():
            continue
        try:
            markdown_body = bbcode_html_to_markdown(html_content)
            if not markdown_body.strip():
                continue

            document_parts.append(f"**{poster_name} (ID: {poster_id}) wrote:**\n\n")
            document_parts.append(markdown_body.strip() + "\n\n")
            document_parts.append("---\n\n")
            has_actual_content = True

        except Exception as e_post_proc:
            print(f"    Error converting content for a post by '{poster_name}' in thread '{title}': {e_post_proc}")
            document_parts.append(f"**{poster_name} (ID: {poster_id}) wrote:**\n\n")
            document_parts.append(f"*Error: Could not convert post content.*\n\n")
            document_parts.append("---\n\n")
            has_actual_content = True
            continue

    if not has_actual_content:
        print(f"  Skipping thread '{title}' as no valid post content was found after processing.")
        return

    clear_title_for_filename = re.sub(r'[^\w\-_.\s]', '_', title)
    clear_title_for_filename = "_".join(clear_title_for_filename.split()).strip()
    if not clear_title_for_filename:
        clear_title_for_filename = f"thread_{thread_id}"

    final_document = "".join(document_parts)

    print(f"  Saving conversation for thread: '{title}' as {clear_title_for_filename}.md")
    save_to_file(final_document, clear_title_for_filename, output_path)


## This is broken as there is a bug in the API at the time of writing this commnet
def forum_data_collection(path: str, api_key: str):
    print("forum_data_collection is noted as potentially broken and was not modified further.")
    pass


def extract_forum_and_thread_ids(url):
    parsed_url = urllib.parse.urlparse(url)
    params_str = parsed_url.fragment if parsed_url.fragment else parsed_url.query
    params = urllib.parse.parse_qs(params_str)
    forum_id = params.get('f', [None])[0]
    thread_id = params.get('t', [None])[0]
    return forum_id, thread_id


if __name__ == "__main__":
    api_key = os.getenv("API_KEY")
    if not api_key:
        print("Error: API_KEY environment variable is not set. This is required.")
        exit(1)

    main_output_path = "forum_conversations"
    if not os.path.exists(main_output_path):
        os.makedirs(main_output_path)
        print(f"Created output directory: {main_output_path}")

    threads_file_path = "collected_threads.json"
    try:
        with open(threads_file_path, "r") as f:
            threads_to_process = json.load(f)
    except FileNotFoundError:
        print(f"Error: Threads file '{threads_file_path}' not found.")
        exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Could not decode JSON from '{threads_file_path}': {e}")
        exit(1)
    if not threads_to_process:
        print(f"Threads file '{threads_file_path}' is empty. No threads to process.")
        exit(0)

    skip = 3324 + 2104
    threads_to_process = threads_to_process[skip:]
    _tqdm = None
    try:
        from tqdm import tqdm as imported_tqdm

        _tqdm = imported_tqdm
    except ImportError:
        pass

    print(f"Processing {len(threads_to_process)} threads from {threads_file_path}...")
    iterable_threads = _tqdm(threads_to_process, desc="Processing threads") if _tqdm else threads_to_process

    for thread_info in iterable_threads:
        try:
            link = thread_info.get("Link")
            title = thread_info.get("Title", "Untitled Thread")
            if not link:
                print(f"Skipping entry with missing link: {title}")
                continue
            category_id, thread_id = extract_forum_and_thread_ids(link)
            if not thread_id or not category_id:
                print(f"Could not extract valid category/thread ID from link: {link} for '{title}'. Skipping.")
                continue
            rating_str = thread_info.get("Rating", "0")
            try:
                rating = int(rating_str)
            except (ValueError, TypeError):
                rating = 0
                print(f"Warning: Invalid rating '{rating_str}' for thread '{title}'. Defaulting to 0.")

            if rating >= 0:
                save_forum_conversation(thread_id, category_id, title, main_output_path, api_key)
            else:
                status_msg = f"Skipping low rating: {title[:30]}..."
                if _tqdm:
                    iterable_threads.set_postfix_str(status_msg)
                else:
                    print(f"Skipping thread: '{title}' due to low rating (Rating: {rating})")
        except Exception as e:
            print(f"MAJOR UNEXPECTED ERROR while processing thread '{thread_info.get('Title', 'N/A')}': {e}")
            import traceback

            print("--- TRACEBACK ---")
            print(traceback.format_exc())
            print("--- END TRACEBACK ---")
            continue
    print("Finished processing all threads.")