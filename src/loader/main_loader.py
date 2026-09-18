import os
import psycopg
import glob
import json

from pathlib import Path
from dotenv import load_dotenv
from psycopg.types.json import Jsonb
from psycopg import sql

base_dir = Path(__file__).resolve().parents[2]

load_dotenv(base_dir / '.env')

input_pattern = base_dir / "output_data" / "products_batch_*.json"

db_config = {
    "host": os.getenv("db_host"),
    "port": int(os.getenv("db_port")),
    "dbname": os.getenv("db_name"),
    "user": os.getenv("db_user"),
    "password": os.getenv("db_password"),
}

def create_database():
    base_config = {
        "host": os.getenv("db_host"),
        "port": int(os.getenv("db_port")),
        "dbname": "postgres",
        "user": os.getenv("db_user"),
        "password": os.getenv("db_password"),
    }

    with psycopg.connect(**base_config, autocommit=True) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (os.getenv("db_name"),))

            if not cur.fetchone():
                cur.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(os.getenv("db_name"))))
                print("Database created")
            else:
                print("Database already exists")

def create_table(conn):
    with conn.cursor() as cur:
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS products (
                id BIGINT PRIMARY KEY,
                requested_id BIGINT,
                name TEXT,
                url_key TEXT,
                price NUMERIC,
                description TEXT,
                images JSONB
            )
            """
        )
    conn.commit()

def load_products(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)

def insert_products(conn, products):
    rows = [
        (
            product.get("id"),
            product.get("requested_id"),
            product.get("name"),
            product.get("url_key"),
            product.get("price"),
            product.get("description"),
            Jsonb(product.get("images", [])),
        )
        for product in products
    ]

    with conn.cursor() as cur:
        cur.executemany(
            """
            INSERT INTO products (
                id,
                requested_id,
                name,
                url_key,
                price,
                description,
                images
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO NOTHING
            """, rows
        )

    conn.commit()

def main():
    files = sorted(glob.glob(str(input_pattern)))
    print(f"Found {len(files)} files")

    create_database()

    with psycopg.connect(**db_config) as conn:
        create_table(conn)

        total = 0

        for index, file_path in enumerate(files, start=1):
            products = load_products(file_path)
            insert_products(conn, products)

            total += len(products)
            print(f"[{index}/{len(files)}] Loaded {len(products)} products | Total: {total}")

    print("Completed")

if __name__ == "__main__":
    main()