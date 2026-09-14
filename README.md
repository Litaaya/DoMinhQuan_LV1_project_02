# Project 2 - Tiki Product Crawler

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

# Installation
```shell
pip install -r requirements.txt
```

# Run
```shell
python main_selenium.py
```

# Crawl result:
- Total products: 200,000
- Successful products: 124,299
- Failed products: 75,701
- Runtime: ~9 hours
- Average: ~0.162s/product

> Most failed products returned `HTTP 404 - Product not found`