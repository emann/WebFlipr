import os
import json

path = 'LatLong.json'
data = {'vertical_steps': 0, 'horizontal_steps': 0, 'lat': 7, 'long': 7}


def generate_next_coords():
    with open(path, 'r+', encoding='utf-8') as f:
        last_coords = json.load(f)
        next_coords = 7  # Do math here
        f.seek(0)
        json.dump(next_coords, f, ensure_ascii=False, indent=4)


if __name__ == '__main__':
    generate_next_coords()
