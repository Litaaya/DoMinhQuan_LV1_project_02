from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

import json
import time


API_URL = "https://api.tiki.vn/product-detail/api/v1/products/{}"


def load_product_ids(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        return [
            line.strip()
            for line in f
            if line.strip() and line.strip().lower() != "id"
        ]


def main():
    product_ids = load_product_ids("product_ids.txt")[:10000]

    options = Options()
    options.add_argument("--start-maximized")

    driver = webdriver.Chrome(options=options)

    success = 0
    not_json = 0
    errors = 0

    start_time = time.time()

    try:
        for index, product_id in enumerate(product_ids, start=1):
            url = API_URL.format(product_id)

            try:
                driver.get(url)

                # Chrome render JSON response thành text trong body
                body = driver.find_element(By.TAG_NAME, "body").text.strip()

                try:
                    data = json.loads(body)

                    success += 1

                    print(
                        f"[{index}/{len(product_ids)}] "
                        f"{product_id} -> JSON OK | "
                        f"{data.get('name')}"
                    )

                except json.JSONDecodeError:
                    not_json += 1

                    print(
                        f"[{index}/{len(product_ids)}] "
                        f"{product_id} -> NOT JSON | "
                        f"{body[:100]}"
                    )

            except Exception as e:
                errors += 1

                print(
                    f"[{index}/{len(product_ids)}] "
                    f"{product_id} -> ERROR: {e}"
                )

    finally:
        driver.quit()

    print("\n===== RESULT =====")
    print("Total:", len(product_ids))
    print("JSON success:", success)
    print("Not JSON:", not_json)
    print("Errors:", errors)

    elapsed = time.time() - start_time
    print(f"Elapsed: {elapsed:.2f} seconds")
    print(f"Average: {elapsed / len(product_ids):.3f} sec/product")


if __name__ == "__main__":
    main()