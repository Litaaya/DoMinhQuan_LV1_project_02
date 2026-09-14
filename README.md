# Project 2 - Tiki Product Crawler

---
# Feature:

- Crawl 200,000 product data using Selenium
- Save results in batches of 1,000 products
- Save failed product IDs and failure reasons
- Generate failed-product summary
- Get checkpoint detect and resume

# Product fileds:
```text
id
requested_id
name
url_key
price
description
images
```

---
# Installation
```shell
pip install -r requirements.txt
```

# Run
```shell
python main_selenium.py
```

---
# Crawl result:
- Total products: 200,000
- Successful products: 124,299
- Failed products: 75,701
- Runtime: ~9 hours
- Average: ~0.162s/product

> Most failed products returned `HTTP 404 - Product not found`

---
# Codebase:

`main_selenium.py`: The main file for controlling the product crawling process from Tiki using Selenium. It features batch processing, result saving, error logging, and checkpoint-based resume support.

```text
create_driver()
Initializes the Chrome WebDriver.

save_batch()
Saves product data for each batch to a JSON file.

load_json_file()
Reads the JSON file if it exists.

load_checkpoint()
Reads the status of completed batches.

save_checkpoint()
Saves the checkpoint status to enable resuming.

save_failed_products()
Saves the list of products that failed to crawl.

save_failed_summary()
Saves error statistics categorized by type.

main()
Orchestrates the entire pipeline: crawling, data parsing, error handling, and saving batches and checkpoints.
```

`helper.py`: Contains helper functions for reading input, processing product data, and saving output.

```text
load_product_ids()
Reads the list of product IDs from a file.

clean_description()
Converts HTML descriptions into clean text.

parse_product_data()
Extracts the necessary fields from the JSON response.

save_json()
Saves data to a JSON file.
```