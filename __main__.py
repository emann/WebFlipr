from flask import Flask, flash, redirect, render_template, request, session, abort, jsonify

from places_scraper.places_scraper import PlacesScraper
from config import GOOGLE_PLACES, MONGODB

app = Flask(__name__)
places_scraper = PlacesScraper(places_interface_config=GOOGLE_PLACES, database_config=MONGODB, min_doc_count=100)


@app.route('/')
def home():
    return 'hello'


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=80)
