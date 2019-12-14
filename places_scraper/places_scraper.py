import threading
import time

from .interfaces import GooglePlacesInterface, DatabaseInterface
from .lat_long_generator import generate_next_coords


class PlacesScraper:
    def __init__(self, places_interface_config: dict, database_config: dict, min_doc_count: int, autostart=True):
        self.places_interface = GooglePlacesInterface(**places_interface_config)
        self.database = DatabaseInterface(**database_config)
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
                    self.database.add(filtered_items)
            time.sleep(10)
