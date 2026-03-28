import csv
from kivy.app import App
from kivy_garden.mapview import MapMarker, MapView
from kivy.clock import Clock
from scipy.signal import find_peaks
from lineMapLayer import LineMapLayer
from store_client import StoreClient
from file_datasource import FileDatasource


ACCEL_WINDOW = 100
UPDATE_INTERVAL = 0.1

BASE_LAT = 50.4501
BASE_LON = 30.5234

POTHOLE_THRESHOLD = 15000
BUMP_THRESHOLD = 18500
PEAK_DISTANCE = 15
PEAK_PROMINENCE = 800


class MapViewApp(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.datasource = FileDatasource("data.csv", "gps.csv")
        self.gps_points, self.accel_z = self.datasource.read()
        self.index = 0
        self.accel_buffer = []
        self.car_marker = None
        self.line_layer = LineMapLayer()
        self.store = StoreClient()

    def on_start(self):
        start = self.gps_points[0]

        self.car_marker = MapMarker(lat=start[0], lon=start[1])
        try:
            self.car_marker.source = "images/car.png"
        except Exception:
            pass

        self.mapview.add_marker(self.car_marker)
        self.mapview.add_layer(self.line_layer, mode="scatter")
        self.mapview.center_on(start[0], start[1])

        Clock.schedule_once(self._start_update, 1.5)

    def _start_update(self, *args):
        Clock.schedule_interval(self.update, UPDATE_INTERVAL)

    def update(self, *args):
        data = self.store.get_data()

        if data:
            point = (data["lat"], data["lon"])
            road_state = data["road_state"]

            self.update_car_marker(point)
            self._safe_add_point(point)

            if road_state == "pothole":
                self.set_pothole_marker(point)
            elif road_state == "bump":
                self.set_bump_marker(point)
        else:
            if self.index >= len(self.gps_points):
                return

            point = self.gps_points[self.index]
            z_val = self.accel_z[self.index]
            self.index += 1

            self.update_car_marker(point)
            self._safe_add_point(point)

            self.accel_buffer.append(z_val)
            if len(self.accel_buffer) >= ACCEL_WINDOW:
                self.check_road_quality()
                self.accel_buffer = []

    def _safe_add_point(self, point):
        if self.line_layer.parent is None or self.line_layer.ms <= 0:
            return
        try:
            self.line_layer.add_point(point)
        except (ValueError, ZeroDivisionError) as e:
            print(f"[LineLayer] Пропущено точку {point}: {e}")

    def check_road_quality(self):
        data = self.accel_buffer[:]
        base_idx = self.index - len(data)

        inverted = [-v for v in data]
        potholes, _ = find_peaks(
            inverted,
            height=-POTHOLE_THRESHOLD,
            distance=PEAK_DISTANCE,
            prominence=PEAK_PROMINENCE,
        )
        for i in potholes:
            gps_i = base_idx + i
            if gps_i < len(self.gps_points):
                self.set_pothole_marker(self.gps_points[gps_i])

        bumps, _ = find_peaks(
            data,
            height=BUMP_THRESHOLD,
            distance=PEAK_DISTANCE,
            prominence=PEAK_PROMINENCE,
        )
        for i in bumps:
            gps_i = base_idx + i
            if gps_i < len(self.gps_points):
                self.set_bump_marker(self.gps_points[gps_i])

    def update_car_marker(self, point):
        self.car_marker.lat = point[0]
        self.car_marker.lon = point[1]
        self.mapview.center_on(point[0], point[1])

    def set_pothole_marker(self, point):
        marker = MapMarker(lat=point[0], lon=point[1])
        try:
            marker.source = "images/pothole.png"
        except Exception:
            pass
        self.mapview.add_marker(marker)
        print(f"[Яма] lat={point[0]:.6f}, lon={point[1]:.6f}")

    def set_bump_marker(self, point):
        marker = MapMarker(lat=point[0], lon=point[1])
        try:
            marker.source = "images/bump.png"
        except Exception:
            pass
        self.mapview.add_marker(marker)
        print(f"[Поліцейський] lat={point[0]:.6f}, lon={point[1]:.6f}")

    def build(self):
        self.mapview = MapView(zoom=17, lat=BASE_LAT, lon=BASE_LON)
        return self.mapview


if __name__ == "__main__":
    MapViewApp().run()