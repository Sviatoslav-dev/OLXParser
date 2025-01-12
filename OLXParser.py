import requests
from bs4 import BeautifulSoup

from logger import logger


class OLXParser:
    def __init__(self, db):
        self.olx_link = "https://www.olx.ua"
        self.db = db

    def parse(self, pages: int):
        """
        :param pages - number of pages to parse
        """
        self.db.connect()
        links = []
        for i in range(pages):
            links.extend(self.parse_advertisements_list_page(i + 1))
        for (link, ad_id) in links:
            ad = self.parse_advertisement(self.olx_link + link, ad_id)
            self.db.save_ad(ad)
        self.db.disconnect()

    def parse_advertisement(self, url: str, ad_id: str) -> dict[str, str] | None:
        """
        parse advertisement page
        """
        logger.info(f"Fetching URL {url}")
        response = requests.get(url, headers=self.headers)
        if response.status_code != 200:
            logger.error(f"Failed to fetch {url}: {response.status_code} ({response.reason})")
            return None

        soup = BeautifulSoup(response.text, "html.parser")

        return {
            "url": url,
            "publication_date": self.parse_field(soup, {"data-cy": "ad-posted-at"}, []),
            "title": self.parse_field(soup, {"data-cy": "ad_title"}, ["h4"]),
            "price": self.parse_field(soup, {"data-testid": "ad-price-container"}, ["h3"]),
            "tags": self.parse_tags(soup),
            "images": self.parse_images(soup),
            "description": self.parse_field(soup, {"data-cy": "ad_description"}, ["div"]),
            "ad_id": ad_id,
            "seller_name": self.parse_field(soup, {"data-testid": "user-profile-link"}, ["div", "h4"]),
            "seller_registration_date": self.parse_field(soup, {"data-testid": "user-profile-link"},
                                                         ["div", "p", "span"]),
            "seller_last_seen": self.parse_field(soup, {"data-testid": "lastSeenBox"},
                                                 ["span"]),
            "phone_number": self.parse_phone_number(soup),
            "page_views": self.parse_page_views(ad_id),
            "city": self.parse_city(ad_id)
        }

    def parse_advertisements_list_page(self, page: int) -> list[tuple[str, int]] | None:
        """
        parse advertisements list page
        """
        url = self.advertisements_list_link(page)
        logger.info(f"Fetching URL {url}")
        response = requests.get(url, headers=self.headers)

        if response.status_code != 200:
            logger.error(f"Failed to fetch {url}: {response.status_code} ({response.reason})")
            return None

        soup = BeautifulSoup(response.text, "html.parser")
        ad_divs = soup.find_all(attrs={"data-testid": "l-card"})

        links = []
        for ad_div in ad_divs:
            a = ad_div.find("a")
            ad_id = int(ad_div.get("id"))
            href = a.get("href")
            if href[0] != "/":
                continue
            if not self.db.advertisement_exists(ad_id):
                links.append((href, ad_id))
            else:
                logger.info(f"Advertisement {url} skipped, it already exist in DB")

        return links

    def parse_field(self, soup: BeautifulSoup, attrs: dict[str, str], path: list[str]) -> str | None:
        """
        Parse field by attr value and path with tags

        :param soup: BeautifulSoup object
        :param attrs: attr param for soup.find method
        :param path: tag names list, path to element
        """
        element = soup.find(attrs=attrs)

        if element is None:
            return None

        for tag_name in path:
            element = element.find(tag_name)
            if element is None:
                return None

        return element.text.strip()

    def advertisements_list_link(self, page: int = 1) -> str | None:
        return f"{self.olx_link}/uk/list/?page={page}"

    def parse_tags(self, soup: BeautifulSoup) -> list[str]:
        main_div = soup.find(attrs={"data-testid": "main"})
        if main_div is None:
            return None
        lis = main_div.find("ul").find_all("li")

        return [li.text.strip() for li in lis if li is not None]

    def parse_images(self, soup: BeautifulSoup) -> list[str] | None:
        elements = soup.find_all(attrs={"data-testid": "ad-photo"})
        if not elements:
            return None

        img_urls = []
        for element in elements:
            img_urls.append(element.find("img").get("src"))
        return img_urls

    def parse_phone_number(self, soup: BeautifulSoup) -> str | None:
        number = self.parse_field(soup, {"data-testid": "phones-container"}, ["div", "p"])
        if number == "xxx xxx xxx":
            return None
        return number

    def parse_page_views(self, ad_id: int) -> str | None:
        """
        parse page views via olx api
        """
        url = 'https://production-graphql.eu-sharedservices.olxcdn.com/graphql'
        json_data = {
            'operationName': 'PageViews',
            'variables': {
                'adId': str(ad_id),
            },
            'query': 'query PageViews($adId: String!) {\n  myAds {\n    '
                     'pageViews(adId: $adId) {\n      pageViews\n    }\n  }\n}',
        }

        response = requests.post(url, headers=self.headers, json=json_data)
        if response.status_code != 200:
            logger.error(f"Failed to receive pageViews for {ad_id}: {response.status_code}"
                         f" ({response.reason})")
            return None
        try:
            return response.json()["data"]["myAds"]["pageViews"]["pageViews"]
        except TypeError:  # if some keys are absent
            return None

    def parse_city(self, ad_id: int) -> str | None:
        """
        parse city via olx api
        """
        url = 'https://www.olx.ua/api/v1/targeting/data/'
        params = {
            'page': 'ad',
            'params[ad_id]': str(ad_id),
        }

        response = requests.get(url, params=params, headers=self.headers)
        if response.status_code != 200:
            logger.error(f"Failed to receive city for {ad_id}: {response.status_code} "
                         f"({response.reason})")
            return None
        try:
            return response.json()["data"]["targeting"].get("city", None)
        except TypeError:  # if some keys are absent
            return None

    @property
    def headers(self):
        return {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                          "(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            'authorization': 'ANONYMOUS',
            'site': 'olxua',
        }
