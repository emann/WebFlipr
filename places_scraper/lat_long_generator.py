import json
import math
import os
from typing import Tuple, List, NamedTuple
from threading import Lock


class OutOfValidPointsError(Exception):
    pass


class LatLong(NamedTuple):
    """A representation of a lat long point, with helpful x and y properties to make math easier"""
    lat: float
    long: float

    @property
    def x(self):
        """Lines of longitude (such as the equator) are technically x values"""
        return self.long

    @property
    def y(self):
        """Lines of latitude go from pole to pole and are technically y values"""
        return self.lat


class BoundaryLine:
    def __init__(self, start: Tuple[float, float], end: Tuple[float, float], less_than: bool):
        self.start = LatLong(*start)
        self.end = LatLong(*end)
        self.slope = (self.end.y-self.start.y) / (self.end.x-self.start.x)
        self.less_than = less_than

    def __repr__(self):
        return f'<BOUNDARY: {self.start}, {self.end}, {self.slope}, {self.less_than}'

    def __str__(self):
        comparison_string = 'less than' if self.less_than else 'greater than'
        return f'Boundary line from {self.start} to {self.end}: ' \
            f'latitude is expected to be {comparison_string} {self.start.y} + {self.slope} * (longitude - {self.start.x})'

    def line_function(self, x):
        """The actual line function - returns the latitude (y) and the given longitude (x)"""
        return self.start.y + self.slope * (x - self.start.x)

    def check_point(self, lat, long):
        if long < self.start.long or long > self.end.long:  # The point is out of the scope of this boundary
            return True
        if self.less_than:  # Points are expected to be less than the boundary line
            return lat < self.line_function(long)
        else:  # Points are expected to be greater than the boundary line
            return lat > self.line_function(long)


class LatLongGenerator:
    def __init__(self, progress_filename: str, origin: Tuple[float, float], search_radius: float, boundary_lines: List[BoundaryLine]):
        self.progress_file = f'{progress_filename}.json'
        self.progress_lock = Lock()
        self.origin = origin
        # Side length of a square inscribed in a search circle (and thus distance between searches) is sqrt((d^2)/2)
        self.distance_between_centers = math.sqrt(((search_radius*2)**2)/2)
        self.boundary_lines = boundary_lines
        self.out_of_bounds = False

    def point_is_valid(self, lat, long):
        """Checks a lat, long against all boundary lines"""
        return all((boundary_func.check_point(lat, long) for boundary_func in self.boundary_lines))

    @property
    def progress(self):
        """The most recent (valid) point searched from, represented by the shell number and step along the shell"""
        if not os.path.exists(self.progress_file):
            return {'shell': None, 'step': None}
        with self.progress_lock:
            with open(self.progress_file, 'r+') as f:
                progress = json.load(f)
        return progress

    def set_progress(self, shell, step):
        with self.progress_lock:
            with open(self.progress_file, 'w+') as f:
                f.seek(0)
                json.dump({'shell': shell, 'step': step}, f, ensure_ascii=False, indent=4)
                f.truncate()

    def _lat_long_from_progress(self, shell, step):
        """Calculates the number of vertical and horizontal steps (and displacements) based off of shell and step
            and returns the new lat and long"""
        if step > (shell + 1):
            lat_steps = (shell - (step % (1 + shell) + 1))
            long_steps = shell
        else:
            lat_steps = shell
            long_steps = step
        new_lat = self.origin[0] + lat_steps*(self.distance_between_centers/111111)
        new_long = self.origin[1] + long_steps*(self.distance_between_centers/(111111*math.cos(math.radians(new_lat))))
        return new_lat, new_long

    def _next_progress_step(self, shell, step):
        if shell is None and step is None:  # No progress has been made, start at the origin
            return 0, 0
        if (step+1) < (shell*2 + 1):
            return shell, step+1
        else:
            return shell+1, 0

    def next_coords(self):
        """Returns the next valid (i.e. not outside of boundaries) lat, long pair"""
        if self.out_of_bounds:
            raise OutOfValidPointsError
        progress = self.progress
        last_valid_shell = progress['shell'] or 0
        shell, step = self._next_progress_step(**progress)
        candidate_point = self._lat_long_from_progress(shell, step)
        if not self.point_is_valid(*candidate_point):
            shell += 1
            step = 0
            while not self.point_is_valid(*candidate_point):
                shell, step = self._next_progress_step(shell, step)
                candidate_point = self._lat_long_from_progress(shell, step)
                if shell - last_valid_shell == 2:  # An entire new shell was checked and no points were valid
                    self.out_of_bounds = True
                    self.set_progress(-1, -1)  # A shell, step of -1, -1 indicates out of bounds
                    raise OutOfValidPointsError
        self.set_progress(shell, step)
        return candidate_point
