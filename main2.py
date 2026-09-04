import asyncio
import aiohttp
from aiohttp import ClientSession
import os
from helpers import load_product_ids, parse_product_data, save_json

api_url = "https://api.tiki.vn/product-detail/api/v1/products/{}"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
}

batch_size = 20
semaphore_limit = 30

async def fetch_product(session: ClientSession, product_id: str, semaphore: asyncio.Semaphore) -> tuple[str, dict]:
    url = api_url.format(product_id)

    async with semaphore:
        try:
            async with session.get(url, headers=headers, timeout=10) as response:
                if response.status == 200:
                    try:
                        raw_json = await response.json(content_type=None)
                        cleaned_data = parse_product_data(raw_json)
                        return ("success", cleaned_data)
                    except Exception as json_err:
                        error_log = {
                            "product_id": product_id,
                            "status_code": response.status,
                            "reason": f"Response is not valid JSON: {str(json_err)}"
                        }
                        return ("error", error_log)
                else:
                    error_log = {
                        "product_id": product_id,
                        "status_code": response.status,
                        "reason": f"HTTP Error: {response.status}"
                    }
                    return ("error", error_log)
        except Exception as e:
            error_log = {
                "product_id": product_id,
                "status_code": None,
                "reason": str(e)
            }
            return ("error", error_log)

async def run_pipeline(input_filepath: str, output_dir: str):
    os.makedirs(output_dir, exist_ok=True)

    # load product_id list from file
    product_ids = load_product_ids(input_filepath)[:100]
    total_ids = len(product_ids)
    print(f"Total ids: {total_ids}")

    semaphore = asyncio.Semaphore(semaphore_limit)
    all_failed_products = []

    # init clientsession for pipeline
    async with aiohttp.ClientSession() as session:
        for i in range(0, total_ids, batch_size):
            batch_ids = product_ids[i : i + batch_size]
            batch_number = (i // batch_size) + 1
            print(f"Batch number: {batch_number}")

            #  create list of task async for current batch
            tasks = [fetch_product(session, pid, semaphore) for pid in batch_ids]

            # run request in batch parallel
            results = await asyncio.gather(*tasks)

            # classify success and fail
            successful_products = []
            for status, data in results:
                if status == "success":
                    successful_products.append(data)
                else:
                    all_failed_products.append(data)

            # write successful batch to file json
            batch_file_path = os.path.join(output_dir, f"products_batch_{batch_number:03d}.json")
            save_json(successful_products, batch_file_path)
            print(f"Successful products: append {len(successful_products)} in {batch_file_path}")

        # write failed products to file.json
        if all_failed_products:
            failed_file_path = os.path.join(output_dir, "failed_products.json")
            save_json(all_failed_products, failed_file_path)
            print(f"Failed products: append {len(all_failed_products)} in {failed_file_path}")

if __name__ == "__main__":
    asyncio.run(run_pipeline("product_ids.txt", "output_data"))