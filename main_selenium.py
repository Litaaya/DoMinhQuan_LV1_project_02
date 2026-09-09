from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

from helpers import (
    load_product_ids,
    parse_product_data,
    save_json
)

import json
import os
import time


API_URL = "https://api.tiki.vn/product-detail/api/v1/products/{}"

INPUT_FILE = "product_ids.txt"
OUTPUT_DIR = "output_data"

TEST_LIMIT = 200000
BATCH_SIZE = 1000


def create_driver():
    options = Options()
    options.add_argument("--start-maximized")

    return webdriver.Chrome(options=options)


def save_batch(products, batch_number):
    output_path = os.path.join(OUTPUT_DIR, f"products_batch_{batch_number:03d}.json")

    save_json(products, output_path)

    print(
        f"Saved batch {batch_number}: "
        f"{len(products)} products -> {output_path}"
    )

def save_failed_products(failed_products):
    failed_path = os.path.join(OUTPUT_DIR, "failed_products.json")
    save_json(failed_products, failed_path)

def save_failed_summary(failed_summary):
    summary_path = os.path.join(OUTPUT_DIR, "failed_summary.json")
    save_json(failed_summary, summary_path)

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    product_ids = load_product_ids(INPUT_FILE)[:TEST_LIMIT]

    print(f"Total ids: {len(product_ids)}")

    driver = create_driver()

    all_failed_products = []

    total_success = 0
    total_failed = 0

    failed_summary = {
        "HTTP 404 - Product not found": 0,
        "Response is not valid JSON": 0,
        "Missing product id": 0,
        "Missing product name": 0,
        "Selenium/network exception": 0
    }

    start_time = time.time()

    try:
        # Process by batch
        for batch_start in range(0, len(product_ids), BATCH_SIZE):
            batch_number = (batch_start // BATCH_SIZE) + 1

            batch_ids = product_ids[batch_start:batch_start + BATCH_SIZE]

            print(
                f"\n===== BATCH {batch_number} ====="
            )

            print(
                f"IDs in batch: {len(batch_ids)}"
            )

            batch_products = []
            batch_failed = []

            # Process products
            for index, product_id in enumerate(batch_ids, start=1):
                global_index = (batch_start + index)

                url = API_URL.format(product_id)

                try:
                    driver.get(url)

                    body = driver.find_element(By.TAG_NAME, "body").text.strip()

                    # Parse JSON
                    try:
                        raw_data = json.loads(body)

                    except json.JSONDecodeError:
                        reason = ("Response is not valid JSON")

                        batch_failed.append({
                            "product_id": product_id,
                            "reason": reason,
                            "body_preview": body[:200]
                        })

                        total_failed += 1

                        failed_summary["Response is not valid JSON"] += 1

                        print(
                            f"[{global_index}/"
                            f"{len(product_ids)}] "
                            f"{product_id} "
                            f"-> FAILED | {reason}"
                        )
                        continue

                    # API 404
                    if raw_data.get("status") == 404:
                        reason = ("HTTP 404 - Product not found")

                        batch_failed.append({
                            "product_id": product_id,
                            "reason": reason,
                            "api_error": raw_data.get("errors")
                        })

                        total_failed += 1

                        failed_summary["HTTP 404 - Product not found"] += 1

                        print(
                            f"[{global_index}/"
                            f"{len(product_ids)}] "
                            f"{product_id} "
                            f"-> FAILED | {reason}"
                        )
                        continue

                    # Parse required fields
                    product = parse_product_data(raw_data)

                    # Missing product ID
                    if not product.get("id"):
                        reason = ("Missing product id")

                        batch_failed.append({
                            "product_id": product_id,
                            "reason": reason
                        })

                        total_failed += 1

                        failed_summary["Missing product id"] += 1

                        print(
                            f"[{global_index}/"
                            f"{len(product_ids)}] "
                            f"{product_id} "
                            f"-> FAILED | {reason}"
                        )
                        continue

                    # Missing product name
                    if not product.get("name"):
                        reason = ("Missing product name")

                        batch_failed.append({
                            "product_id": product_id,
                            "reason": reason
                        })

                        total_failed += 1

                        failed_summary["Missing product name"] += 1

                        print(
                            f"[{global_index}/"
                            f"{len(product_ids)}] "
                            f"{product_id} "
                            f"-> FAILED | {reason}"
                        )
                        continue

                    # Success
                    batch_products.append(product)

                    total_success += 1

                    print(
                        f"[{global_index}/"
                        f"{len(product_ids)}] "
                        f"{product_id} -> OK"
                    )

                except Exception as e:
                    reason = (
                        f"Selenium/network exception: "
                        f"{str(e)}"
                    )

                    batch_failed.append({
                        "product_id": product_id,
                        "reason": reason
                    })

                    total_failed += 1

                    failed_summary["Selenium/network exception"] += 1

                    print(
                        f"[{global_index}/"
                        f"{len(product_ids)}] "
                        f"{product_id} "
                        f"-> FAILED | {reason}"
                    )

            # Save successful batch
            save_batch(batch_products, batch_number)

            # Append failed of batch
            all_failed_products.extend(batch_failed)

            # Save failed immediately
            save_failed_products(all_failed_products)

            # Save failed summary
            save_failed_summary(failed_summary)

            print(
                f"Batch {batch_number} completed"
            )

            print(
                f"Success: "
                f"{len(batch_products)}"
            )

            print(
                f"Failed: "
                f"{len(batch_failed)}"
            )

    finally:
        driver.quit()

    # Final statistics
    elapsed = time.time() - start_time

    print("\n===== RESULT =====")

    print(
        f"Total: {len(product_ids)}"
    )

    print(
        f"Successful products: "
        f"{total_success}"
    )

    print(
        f"Failed products: "
        f"{total_failed}"
    )

    print(
        f"Elapsed: "
        f"{elapsed:.2f} seconds"
    )

    if product_ids:
        print(
            f"Average: "
            f"{elapsed / len(product_ids):.3f} "
            f"sec/product"
        )

    # Failed summary
    print("\n===== FAILED SUMMARY =====")

    for reason, count in failed_summary.items():
        print(
            f"{reason}: {count}"
        )


if __name__ == "__main__":
    main()