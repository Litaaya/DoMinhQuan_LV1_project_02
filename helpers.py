import json
from bs4 import BeautifulSoup
import re

# Read file contained 200k product ID and return list cleaned ID
def load_product_ids(filepath) -> list[str]:
    product_ids = []
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            clean_id = line.strip()
            if clean_id and clean_id.lower() not in ("id"):
                product_ids.append(clean_id)
        return product_ids

# Convert html comma in description to text
def clean_description(raw_html: str) -> str:
    if not raw_html or not isinstance(raw_html, str):
        return ""

    soup = BeautifulSoup(raw_html, "html.parser")
    text = soup.get_text(separator=" ")

    clean_text = re.sub(r'\s+', ' ', text).strip()
    return clean_text

# parse product data base on requirements
def parse_product_data(raw_json: dict) -> dict:
    if not raw_json or not isinstance(raw_json, dict):
        return {}

    images_raws = raw_json.get("images", [])
    image_urls = []

    if isinstance(images_raws, list):
        for img in images_raws:
            if isinstance(img, dict) and img.get("base_url"):
                image_urls.append(img["base_url"])

    return {
        "id": raw_json.get("id"),
        "name": raw_json.get("name"),
        "url_key": raw_json.get("url_key"),
        "price": raw_json.get("price"),
        "description": clean_description(raw_json.get("description", "")),
        "images": image_urls,
    }

# print json out
def save_json(data: list | dict, output_path: str) -> None:
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)