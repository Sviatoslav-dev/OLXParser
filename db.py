import os
import subprocess
import time

import psycopg2

from config import DB_CONFIG
from logger import logger

CREATE_TABLE_QUERY = """
CREATE TABLE IF NOT EXISTS OLXAdvertisements (
    ad_id INT PRIMARY KEY,
    url TEXT,
    publication_date TEXT,
    title TEXT,
    price TEXT,
    tags TEXT[],
    images TEXT[],
    description TEXT,
    seller_name TEXT,
    seller_registration_date TEXT,
    seller_last_seen TEXT,
    phone_number TEXT,
    page_views INT,
    city TEXT
);
"""

INSERT_QUERY = """
INSERT INTO OLXAdvertisements (
    ad_id, url, publication_date, title, price, tags, images, description, seller_name, 
    seller_registration_date, seller_last_seen, phone_number, page_views, city
) VALUES (
    %(ad_id)s, %(url)s, %(publication_date)s, %(title)s, %(price)s, %(tags)s, %(images)s, 
    %(description)s,%(seller_name)s, %(seller_registration_date)s, %(seller_last_seen)s,
    %(phone_number)s, %(page_views)s, %(city)s
) ON CONFLICT (ad_id) DO NOTHING;
"""

CHECK_URL_QUERY = """
SELECT EXISTS (
    SELECT 1 FROM OLXAdvertisements WHERE ad_id = %(ad_id)s
);
"""

class OLXAdsDatabase:
    def __init__(self):
        self.conn = None
        self.cursor = None

    def connect(self):
        self.conn = psycopg2.connect(**DB_CONFIG)
        self.cursor = self.conn.cursor()

        try:
            self.cursor.execute(CREATE_TABLE_QUERY)
            self.conn.commit()
        except psycopg2.Error as e:
            logger.error(f"Failed to create database: {e}")

    def save_ad(self, ad):
        try:
            self.cursor.execute(INSERT_QUERY, ad)
            self.conn.commit()
        except psycopg2.Error as e:
            logger.error(f"Failed to save advertisement: {e}")

    def advertisement_exists(self, ad_id):
        try:
            self.cursor.execute(CHECK_URL_QUERY, {"ad_id": ad_id})
            return self.cursor.fetchone()[0]
        except psycopg2.Error as e:
            logger.error(f"Failed to check advertisement: {e}")
            return False

    def disconnect(self):
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()

    def create_dump(self):
        dump_path = "./db_dumps"
        if not os.path.exists(dump_path):
            os.makedirs(dump_path)

        dump_file = os.path.join(dump_path, f"dump_{time.strftime('%Y%m%d_%H%M%S')}.sql")

        command = [
            "pg_dump",
            "--dbname=postgresql://{user}:{password}@{host}:{port}/{dbname}".format(**DB_CONFIG),
            "-f", dump_file
        ]

        try:
            subprocess.run(command, check=True)
            logger.info("Dump was created")
        except subprocess.CalledProcessError as e:
            logger.info(f"Error occured during dump creating{e}")
