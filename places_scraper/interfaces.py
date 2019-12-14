import requests
import time
import pymongo
from bson.objectid import ObjectId


class GooglePlacesInterface:
    def __init__(self, api_key: str, search_radius: int, type_blacklist: list, details_fields: list):
        self.api_key = api_key
        self.search_radius = search_radius
        self.type_blacklist = set(type_blacklist)
        self.details_fields = details_fields

    def filter_by_type(self, place):
        return self.type_blacklist.isdisjoint(set(place['types']))

    def search_from_lat_long(self, location, radius=None, auto_filter_types=True):
        endpoint_url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
        params = {
            'location': location,
            'radius': radius or self.search_radius,
            'key': self.api_key
        }
        res = requests.get(endpoint_url, params=params)
        results = res.json()
        places = []
        places.extend(results['results'])
        time.sleep(2)
        while "next_page_token" in results:
            params['pagetoken'] = results['next_page_token'],
            res = requests.get(endpoint_url, params=params)
            results = res.json()
            places.extend(results['results'])
            time.sleep(2)
        if auto_filter_types:
            return list(filter(self.filter_by_type, places))
        else:
            return places

    def get_place_details(self, place_id):
        endpoint_url = "https://maps.googleapis.com/maps/api/place/details/json"
        params = {
            'placeid': place_id,
            'fields': ",".join(self.details_fields),
            'key': self.api_key
        }
        res = requests.get(endpoint_url, params=params)
        place_details = res.json()['result']
        return place_details

    def filtered_search(self, location):
        search_results = [self.get_place_details(p['place_id']) for p in self.search_from_lat_long(location)]
        return search_results


class DatabaseInterface:
    def __init__(self, url, user, password, database_name, collection):
        self._url = url.format(user, password)
        self.safe_url = url.format('USER', 'PASS')
        self.client = pymongo.MongoClient(self._url)
        self.db = self.client[database_name]
        self.collection = self.db[collection]
        self.collection_archive = self.db[f'{collection}_archive']

    def __repr__(self):
        return f'Connected to {self.db.name}:{self.collection.name} on {self.safe_url}'

    @property
    def count(self):
        return self.collection.count_documents()

    def add(self, docs):
        if type(docs) is not list:
            docs = [docs]
        self.collection.insert_many(docs)
        self.collection_archive.insert_many(docs)

    def retrieve_next(self, num_to_retrieve):
        sort = {'_id': -1}
        search = self.collection.find({}, limit=num_to_retrieve).sort(sort)
        return search

    def remove(self, ids):
        if type(ids) is not list:
            ids = [ids]
        object_ids = [ObjectId(id) for id in ids]
        self.collection.delete_many({'_id': {'$in': object_ids}})

if __name__ == '__main__':
    from config import GOOGLE_PLACES, MONGODB
    g = GooglePlacesInterface(**GOOGLE_PLACES)
    db = DatabaseInterface(**MONGODB)
    p = g.filtered_search(location='41.138257, -73.297804')  # Downtown Westport
    print(len(p))
    print(db)
