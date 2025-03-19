
import os
from bs4 import BeautifulSoup
import html2text
from tqdm import tqdm
import time
from typing import Dict

def extract_meta_data(soup: BeautifulSoup) -> Dict[str, str]:
    """
    This function extracts relevant data like title, the page url, and other possible information.
    :param soup:
    :return dict:
    """

    head = soup.find('head')

    title = head.find('title').text
    url = soup.find('link', {'rel': 'canonical'}).get('href')

    url = None if not url else url
    title = None if not title else title

    return {
        'title': title,
        'url': url
    }

def process_wiki_pages(raw_folder_path: str, save_folder_path: str):
    """
    This function processes a raw html of a wiki page, specifically from Torn Wiki. Might work with other wikipedia pages. Especially if they are run using MediaWiki.
    :param raw_folder_path:
    :param save_folder_path:
    :return:
    """
    os.makedirs(save_folder_path, exist_ok=True)

    if not os.path.exists(raw_folder_path):
        raise FileNotFoundError(f"Folder not found: {raw_folder_path}")

    files = os.listdir(raw_folder_path)

    # Create a cool progress bar
    pbar = tqdm(files, desc="Processing wiki pages",
                bar_format="{l_bar}{bar:30}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}]",
                colour="green")

    for file in pbar:
        # Update progress bar description to show current file
        pbar.set_description(f"Processing {file}")

        with open(os.path.join(raw_folder_path, file), 'r') as f:
            html = f.read()
            soup = BeautifulSoup(html, 'html.parser')

            ## Get 'content'
            content = soup.find('div', {'id': 'content'})

            ## Get 'title'
            meta_data = extract_meta_data(soup)

            ## Wikis has a header row in the table. It needs to be removed before converting to markdown
            for tr in soup.find_all("tr"):
                th = tr.find("th", class_="header")
                if th:
                    table_caption = f'**Table: {th.text.rstrip()}**:'
                    new_caption = soup.new_tag("p")  # Create a new <p> tag
                    new_caption.string = table_caption  # Set its text
                    tr.insert_before(new_caption)  # Insert it before the <tr> (will work as table caption)
                    tr.decompose()  # Remove the original <tr>



            h = html2text.HTML2Text()
            h.ignore_links = True

            ## Convert HTML to markdown
            markdown = ("---\n"
                        "source: {}\n"
                        "url: {}\n"
                        "updated: {}\n"
                        "---\n").format("Torn Wiki", meta_data['url'], "2025-07-15")

            markdown += h.handle(str(content))

            ## Save the processed page
            with open(os.path.join(save_folder_path, f"{meta_data['title'].replace('/', '')}.md"), 'w') as f:
                f.write(markdown)

        # Add a small delay to make the progress bar more visible
        time.sleep(0.01)

    print("\n✅ All wiki pages processed successfully!")


if __name__ == '__main__':
    """
    For personal testing purposes
    """
    raw_path = 'wiki'
    save_path = 'data'
    process_wiki_pages(raw_path, save_path)