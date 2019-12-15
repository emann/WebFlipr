import threading
import time
import io
import requests
from selenium import webdriver


from .interfaces import GooglePlacesInterface, DatabaseInterface
from .lat_long_generator import generate_next_coords


options = webdriver.ChromeOptions()
options.add_argument("--window-size=1920,1080")
options.add_argument("--headless")


class PlacesScraper:
    def __init__(self, places_interface_config: dict, database_config: dict, img_host_config:dict, min_doc_count: int, autostart=True):
        self.places_interface = GooglePlacesInterface(**places_interface_config)
        self.database = DatabaseInterface(**database_config)
        self.img_host_config = img_host_config
        self.min_doc_count = min_doc_count
        self.running = autostart
        self.watcher_thread = threading.Thread(target=self.doc_count_watcher).start()

    def enable(self):
        self.running = True

    def disable(self):
        self.running = False

    def filter_from_database(self, place: dict):
        database_search = self.database.collection_archive.find({'website': place['website']}, limit=2)
        return database_search.count()

    def doc_count_watcher(self):
        while True:
            if self.running:
                while self.database.count < self.min_doc_count:
                    coords = generate_next_coords()
                    new_items = self.places_interface.filtered_search(coords)
                    filtered_items = list(filter(self.filter_from_database, new_items))
                    self.add_screenshot_links(filtered_items)
                    self.database.add(filtered_items)
            time.sleep(10)

    def add_screenshot_links(self, business_info_dicts):
        selenium_browser = webdriver.Chrome(options=options)
        for business_info_dict in business_info_dicts:
            url = business_info_dict['website']
            selenium_browser.get(url)
            image_bytes = selenium_browser.get_screenshot_as_png()
            r = requests.post(
                'https://api.imgur.com/3/upload',
                data={'image': image_bytes},
                headers={'Authorization': 'Client-ID 073fc8b9422a4cb'}
            )
            if r.ok:
                business_info_dict['screenshot_url'] = r.json()['data']['link']
        selenium_browser.quit()
