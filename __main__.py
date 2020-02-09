from flask import Flask, flash, redirect, render_template, request, url_for

from places_scraper.lat_long_generator import BoundaryLine, LatLongGenerator
from places_scraper.places_scraper import PlacesScraper
from config import GOOGLE_PLACES, MONGODB, IMGUR

app = Flask(__name__)
bottom1 = BoundaryLine((40.989633, -73.620341), (41.222859, -72.943478), False)
bottom2 = BoundaryLine((41.222859, -72.943478), (41.286869, -72.084409), False)
l = LatLongGenerator(f'test', (41.026531, -73.628548), 250, [bottom1, bottom2])
places_scraper = PlacesScraper(lat_long_generator=l,
                  places_interface_config=GOOGLE_PLACES,
                  database_config=MONGODB,
                  imgur_host_config=IMGUR,
                  min_doc_count=30)


@app.route('/')
def home():
    if request.args.get('rank'):
        rank = request.args.get('rank')
        id = request.args.get('id')
        print(rank, id)
        places_scraper.database.remove(id)
        return redirect(url_for('home'))
    place_info = places_scraper.database.retrieve_next()[0]
    print(place_info)
    return render_template('index.html', place_info=place_info)


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8000)
