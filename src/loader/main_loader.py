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
    try:
        conn = psycopg.connect(**base_config, autocommit=True)
    except psycopg.OperationalError as e:
        print(f"Database connection failed: {e}")
        raise

    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (os.getenv("db_name"),))

                if not cur.fetchone():
                    cur.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(os.getenv("db_name"))))
                    print("Database created")
                else:
                    print("Database already exists")
    except psycopg.DatabaseError as e:
        print(f"Database operation failed: {e}")
        raise

def create_table(conn):
    try:
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
    except psycopg.DatabaseError as e:
        conn.rollback()
        print(f"Create table failed: {e}")
        raise

def load_products(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)

    except FileNotFoundError as e:
        print(f"File not found: {e}")
        raise

    except json.JSONDecodeError as e:
        print(f"JSON decode error: {e}")
        raise

def insert_products(conn, products):
    try:
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
    except Exception as e:
        print(f"Prepare rows failed: {e}")
        raise

    try:
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
    except psycopg.DatabaseError as e:
        conn.rollback()
        print(f"Insert products failed: {e}")
        raise

def main():
    files = sorted(glob.glob(str(input_pattern)))
    if not files:
        raise FileNotFoundError("No input files found")
    print(f"Found {len(files)} files")

    create_database()

    try:
        conn = psycopg.connect(**db_config)
    except psycopg.OperationalError as e:
        print(f"Database connection failed: {e}")
        raise

    create_table(conn)

    total = 0

    for index, file_path in enumerate(files, start=1):
        try:
            products = load_products(file_path)
        except (FileNotFoundError, json.JSONDecodeError):
            print(f"Skipped filed: {file_path}")
            continue

        insert_products(conn, products)

        total += len(products)
        print(f"[{index}/{len(files)}] Loaded {len(products)} products | Total: {total}")

    print("Completed")

if __name__ == "__main__":
    main()