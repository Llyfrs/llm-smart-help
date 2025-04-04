"""
html_to_markdown.py

This script converts HTML wiki pages to Markdown format, including metadata extraction.

⚡ Designed for Torn Wiki but may work with other MediaWiki-based pages.
🛠 Fixes table formatting and auto-detects the 'content' element.

Author: Llyfr
Date: 2025-03-20

Dependencies:
- BeautifulSoup (`pip install beautifulsoup4`)
- markdownify (`pip install markdownify`)

Usage:
    python html_to_markdown.py input.html output.md

Example:
    python html_to_markdown.py wiki_page.html converted.md
"""

import os
from bs4 import BeautifulSoup
from tqdm import tqdm
import time
from typing import Dict


def _extract_meta_data(soup: BeautifulSoup) -> Dict[str, str]:
    """
    This function extracts relevant data like title, the page url, and other possible information.
    :param soup:
    :return dict:
    """

    head = soup.find("head")

    title = head.find("title").text
    url = soup.find("link", {"rel": "canonical"}).get("href")

    url = None if not url else url
    title = None if not title else title

    return {"title": title, "url": url}


from markdownify import MarkdownConverter, markdownify


# Create shorthand method for conversion
def _md(soup: BeautifulSoup, **options):
    """
    Convert a BeautifulSoup object to markdown
    :param soup: BeautifulSoup object
    :param options: MarkdownConverter options
    :return:
    """
    return MarkdownConverter(**options).convert_soup(soup)


def _fix_markdown_tables(soup):
    """
    This function fixes the markdown tables by converting td elements in the first row to th elements.
    :param soup:
    :return:
    """

    # Find all tables
    for table in soup.find_all("table"):
        # Check if the table has rows
        rows = table.find_all("tr")
        if rows:
            # Check if the first row is already a header (has th elements)
            first_row = rows[0]
            has_header = len(first_row.find_all("th")) > 0

            # If no header exists but there's at least one row, treat first row as header
            if not has_header:
                # Convert all td elements in the first row to th
                for td in first_row.find_all("td"):
                    # Create a new th element
                    th = soup.new_tag("th")
                    th.string = td.get_text()
                    # Replace td with th
                    td.replace_with(th)

    return soup


def _fix_signs(soup):
    """
    This function encloses any text in <li> containing '-' or '+' to be enclosed with '' to not be converted to a list.
    When we keep them they get latter detected as a list and converted to a list in markdown, loosing information.
    :param soup:
    :return:
    """

    # Find all <li> elements
    for li in soup.find_all("li"):
        # Check if the text contains '-' or '+'
        if "-" in li.text or "+" in li.text:
            # Create a new <span> element
            new = soup.new_tag("li")
            new.string = '\'' + li.text + '\''
            # Replace li with span
            li.replace_with(new)

    return soup

def __remove_patch_history(soup):
    """
    This function removes all elements after  patch history from the soup object. Specifically the <span class="mw-headline" id="Patch_History">Patch History</span> element
    Patch history usually doesnẗ contain any relevant information.
    :param soup:
    :return:
    """
    # Find all <span> elements with class "mw-headline" and id "Patch_History"
    patch_history = soup.find("span", {"class": "mw-headline", "id": "Patch_History"})
    if patch_history:
        # Remove all elements after the patch history
        for element in patch_history.find_all_next():
            element.decompose()
        # Remove the patch history element itself
        patch_history.decompose()

    return soup

def process_wiki_pages(
    raw_folder_path: str, save_folder_path: str, meta_data: Dict[str, str] = None
) -> None:
    """
    This function processes a raw html of a wiki page, specifically from Torn Wiki. Might work with other wikipedia pages. Especially if they are run using MediaWiki.
    But in general you will want to use our own parser so you can clean the data in any way you want.


    :param raw_folder_path: Folder with raw html files
    :param save_folder_path: Folder to save the processed markdown files
    :param meta_data: Metadata to be added to the markdown files, url is added automatically if found in the html
    :return:
    """
    os.makedirs(save_folder_path, exist_ok=True)

    if not os.path.exists(raw_folder_path):
        raise FileNotFoundError(f"Folder not found: {raw_folder_path}")

    files = os.listdir(raw_folder_path)

    # Create a cool progress bar
    pbar = tqdm(
        files,
        desc="Processing wiki pages",
        bar_format="{l_bar}{bar:30}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}]",
        colour="green",
    )

    for file in pbar:
        # Update progress bar description to show current file
        pbar.set_description(f"Processing {file}")

        with open(os.path.join(raw_folder_path, file), "r") as f:
            html = f.read()
            soup = BeautifulSoup(html, "html.parser")

            ## Get 'content'
            content = soup.find("div", {"id": "content"})

            ## Get 'title'
            url = _extract_meta_data(soup)["url"]
            title = _extract_meta_data(soup)["title"]

            ## Wikis has a header row in the table. It needs to be removed before converting to markdown
            for tr in soup.find_all("tr"):
                th = tr.find("th", class_="header")
                if th:
                    table_caption = f"**Table: {th.text.rstrip()}**:"
                    new_caption = soup.new_tag("p")  # Create a new <p> tag
                    new_caption.string = table_caption  # Set its text
                    tr.insert_before(
                        new_caption
                    )  # Insert it before the <tr> (will work as table caption)
                    tr.decompose()  # Remove the original <tr>


            ## Remove new-infobox class
            for div in soup.find_all("div", class_="new-infobox"):
                div.decompose()



            soup = _fix_markdown_tables(soup)
            soup = _fix_signs(soup)
            soup = __remove_patch_history(soup)

            ## Convert HTML to markdown
            #            markdown = (
            #                "---\n" "source: {}\n" "url: {}\n" "updated: {}\n" "---\n"
            #           ).format(source, meta_data["url"], "2025-07-15")

            ## add metadata to the file
            metadata_str = "".join(
                [f"{key}: {value}\n" for key, value in meta_data.items()]
            )
            metadata_str += f"url: {url}\n"
            markdown = f"---\n{metadata_str}---\n"

            markdown += _md(content)

            ## Save the processed page
            with open(
                os.path.join(save_folder_path, f"{title.replace('/', '')}.md"),
                "w",
            ) as f:
                f.write(markdown)

        # Add a small delay to make the progress bar more visible
        time.sleep(0.01)

    print("\n✅ All wiki pages processed successfully!")


if __name__ == "__main__":
    """
    For personal testing purposes
    """
    raw_path = "../wiki"
    save_path = "../data"
    process_wiki_pages(
        raw_path, save_path, {"source": "Torn Wiki", "updated": "2025-07-15"}
    )
