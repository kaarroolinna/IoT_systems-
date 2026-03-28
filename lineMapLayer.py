from kivy_garden.mapview import MapLayer, MapMarker
from kivy.graphics import Color, Line
from kivy.graphics.context_instructions import Translate, Scale, PushMatrix, PopMatrix
from kivy_garden.mapview.utils import clamp
from kivy_garden.mapview.constants import (MIN_LONGITUDE, MAX_LONGITUDE, MIN_LATITUDE, MAX_LATITUDE)
from math import radians, log, tan, cos, pi


class LineMapLayer(MapLayer):
    def __init__(self, coordinates=None, color=[0, 0, 1, 1], width=2, **kwargs):
        super().__init__(**kwargs)
        self._coordinates = coordinates
        self.color = color
        self._line_points = None
        self._line_points_offset = (0, 0)
        self.zoom = 0
        self.lon = 0
        self.lat = 0
        self.ms = 0
        self._width = width

    @property
    def coordinates(self):
        return self._coordinates

    @coordinates.setter
    def coordinates(self, coordinates):
        self._coordinates = coordinates
        self.invalidate_line_points()
        self.clear_and_redraw()

    def add_point(self, point):
        if self._coordinates is None:
            self._coordinates = []
        self._coordinates.append(point)
        self.invalidate_line_points()
        self.clear_and_redraw()

    @property
    def line_points(self):
        if self._line_points is None:
            self.calc_line_points()
        return self._line_points

    @property
    def line_points_offset(self):
        if self._line_points is None:
            self.calc_line_points()
        return self._line_points_offset

    def calc_line_points(self):
        self._line_points_offset = (self.get_x(self.coordinates[0][1]),
                                    self.get_y(self.coordinates[0][0]))
        self._line_points = [(self.get_x(lon) - self._line_points_offset[0],
                              self.get_y(lat) - self._line_points_offset[1])
                             for lat, lon in self.coordinates]

    def invalidate_line_points(self):
        self._line_points = None
        self._line_points_offset = (0, 0)

    def get_x(self, lon):
        return clamp(lon, MIN_LONGITUDE, MAX_LONGITUDE) * self.ms / 360.0

    def get_y(self, lat):
        lat = radians(clamp(-lat, MIN_LATITUDE, MAX_LATITUDE))
        return (1.0 - log(tan(lat) + 1.0 / cos(lat)) / pi) * self.ms / 2.0

    def reposition(self):
        map_view = self.parent

        if self.zoom != map_view.zoom or \
                self.lon != round(map_view.lon, 7) or \
                self.lat != round(map_view.lat, 7):
            map_source = map_view.map_source
            self.ms = pow(2.0, map_view.zoom) * map_source.dp_tile_size
            self.invalidate_line_points()
            self.clear_and_redraw()

    def clear_and_redraw(self, *args):
        with self.canvas:
            self.canvas.clear()

        self._draw_line()

    def _draw_line(self, *args):
        if self._coordinates is None:
            return
        map_view = self.parent
        self.zoom = map_view.zoom
        self.lon = map_view.lon
        self.lat = map_view.lat

        scatter = map_view._scatter
        sx, sy, ss = scatter.x, scatter.y, scatter.scale

        vx, vy, vs = map_view.viewport_pos[0], map_view.viewport_pos[1], map_view.scale

        with self.canvas:
            self.opacity = 0.5
            PushMatrix()
            Translate(*map_view.pos)
            Scale(1 / ss, 1 / ss, 1)
            Translate(-sx, -sy)
            Scale(vs, vs, 1)
            Translate(-vx, -vy)
            Translate(self.ms / 2, 0)
            Translate(*self.line_points_offset)
            Color(*self.color)
            Line(points=self.line_points, width=self._width)
            PopMatrix()