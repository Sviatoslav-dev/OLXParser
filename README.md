The database consists of a single table (OLXAdvertisements) with the following fields:
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

The city and page views are extracted from the API, while all other parameters are scraped from HTML using BeautifulSoup.

To run the application, execute:

```docker-compose up --build```

The script will start at the beginning of the next minute.
After, you can check database:

```docker exec -it postgres_db psql -U admin -d olx_parser```
