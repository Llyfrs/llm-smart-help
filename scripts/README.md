
# About 

Here are tools I used for mostly data gathering and preprocessing. Scripts included here are not used in part in any way of the final program, and because of that their documentation is close to nonexistent as they are considered temporary.  


## Scripts

### `html_to_markdown.py`
This script converts HTML files to markdown format. The process is specifically designed to handle HTML pages from the https://wiki.torn.com/ site, as it specifically removes certain sections and handles some table formating that doesn't produce good tables when only converted using the used parser.

### `forum_data_collection.py`

Takes list of thread ids and collects forum posts in to markdown files. Skips any forum posts that have low rating.

### `qan_forum_data_collection.py`

Takes list of threads and collects the associated forum posts, very similar to `forum_data_collection.py` with changed rules. 

### `medal_data_collection.py`

Collects data from the Torn City API, specifically the medals endpoint.

### `item_data_collection.py`

Collects item data from the Torn City API, specifically the items endpoint. 