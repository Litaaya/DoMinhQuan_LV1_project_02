import asyncio
import os
import random

from curl_cffi.requests import AsyncSession

from helpers import load_product_ids, parse_product_data, save_json

api_url = "https://api.tiki.vn/product-detail/api/v1/products/{}"

batch_size = 1
semaphore_limit = 1


async def fetch_product(session: AsyncSession, product_id: str, semaphore: asyncio.Semaphore):
    url = api_url.format(product_id)

    try:
        async with semaphore:
            await asyncio.sleep(random.uniform(1.0, 2.0))
            response = await session.get(
                url,
                impersonate="chrome",
                timeout=15
            )

        status_code = response.status_code
        content_type = response.headers.get("content-type", "").lower()

        if status_code == 200:
            if "application/json" in content_type:
                raw_json = response.json()

                cleaned_data = parse_product_data(raw_json)

                return ("success", cleaned_data)

            return (
                "error",
                {
                    "product_id": product_id,
                    "status_code": status_code,
                    "content_type": content_type,
                    "body_preview": response.text[:500],
                    "reason": "Response is not JSON"
                }
            )

        return (
            "error",
            {
                "product_id": product_id,
                "status_code": status_code,
                "reason": f"HTTP Error: {status_code}"
            }
        )

    except Exception as e:
        return (
            "error",
            {
                "product_id": product_id,
                "status_code": None,
                "reason": str(e)
            }
        )


async def run_pipeline(input_filepath: str,output_dir: str):
    consecutive_html_errors = 0
    MAX_HTML_ERRORS = 5

    os.makedirs(output_dir, exist_ok=True)

    product_ids = load_product_ids(input_filepath)[:10]

    total_ids = len(product_ids)

    print(f"Total ids: {total_ids}")

    semaphore = asyncio.Semaphore(semaphore_limit)

    all_failed_products = []

    async with AsyncSession() as session:

        for i in range(0, total_ids, batch_size):
            batch_ids = product_ids[i:i + batch_size]

            batch_number = (i // batch_size) + 1

            print(f"Batch number: "f"{batch_number}")

            tasks = [fetch_product(session, pid, semaphore) for pid in batch_ids]

            results = await asyncio.gather(*tasks)

            successful_products = []

            for status, data in results:
                if status == "success":
                    successful_products.append(data)
                    consecutive_html_errors = 0
                else:
                    all_failed_products.append(data)

                    if data.get("content_type", "").startswith("text/html"):
                        consecutive_html_errors += 1
                    else:
                        consecutive_html_errors = 0

            if consecutive_html_errors >= MAX_HTML_ERRORS:
                print(f"Stopped: received {MAX_HTML_ERRORS} consecutive HTML responses.")
                break

            batch_file_path = os.path.join(output_dir, f"products_batch_" f"{batch_number:03d}.json")

            save_json(successful_products, batch_file_path)

            print("Successful products: " f"append " f"{len(successful_products)} " f"in {batch_file_path}")

    if all_failed_products:
        failed_file_path = os.path.join(output_dir, "failed_products.json")
        save_json(all_failed_products, failed_file_path)
        print("Failed products: " f"append " f"{len(all_failed_products)} " f"in {failed_file_path}")

if __name__ == "__main__":

    asyncio.run(
        run_pipeline(
            "product_ids.txt",
            "output_data"
        )
    )