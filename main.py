import csv
from kivy.app import App
from kivy_garden.mapview import MapMarker, MapView
from kivy.clock import Clock
from scipy.signal import find_peaks
from lineMapLayer import LineMapLayer


ACCEL_WINDOW = 100  # кількість показників для аналізу
UPDATE_INTERVAL = 0.1  # секунди між оновленнями (100 мс)

# cтартова точка маршруту (Київ)
BASE_LAT = 50.4501
BASE_LON = 30.5234

# крок між точками маршруту (~1 м на крок при 100 мс інтервалі = ~10 м/с)
LAT_STEP = 0.000009
LON_STEP = 0.000009


def load_csv(path):
    """
    Зчитує data.csv.
    Колонки у файлі: lat (= x акселерометра), lon (= y акселерометра), z.
    GPS-координати генеруються автоматично, бо у файлі їх немає.
    """
    accel_x = []
    accel_y = []
    accel_z = []

    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            accel_x.append(float(row["x"]))
            accel_y.append(float(row["y"]))
            accel_z.append(float(row["z"]))

    n = len(accel_z)

    # генеруємо GPS-трек: рухаємось по діагоналі
    gps_points = [(BASE_LAT + i * LAT_STEP, BASE_LON + i * LON_STEP) for i in range(n)]

    print(f"[CSV] Завантажено {n} рядків акселерометра")
    print(f"[CSV] GPS згенерований автоматично від {gps_points[0]} до {gps_points[-1]}")
    return gps_points, accel_z


class MapViewApp(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.gps_points, self.accel_z = load_csv("data.csv")
        self.index = 0
        self.accel_buffer = []
        self.car_marker = None
        self.line_layer = LineMapLayer()

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
        """Додає точку до лінії тільки якщо шар вже готовий."""
        if self.line_layer.parent is None or self.line_layer.ms <= 0:
            return
        try:
            self.line_layer.add_point(point)
        except (ValueError, ZeroDivisionError) as e:
            print(f"[LineLayer] Пропущено точку {point}: {e}")

    def check_road_quality(self):
        data = self.accel_buffer[:]
        base_idx = self.index - len(data)

        # ями — локальні мінімуми осі Z
        # (значення спокою ~16667, при ямі Z різко падає)
        inverted = [-v for v in data]
        potholes, _ = find_peaks(
            inverted,
            height=-15000,  # було -16400
            distance=15,
            prominence=800,  # було 200
        )
        for i in potholes:
            gps_i = base_idx + i
            if gps_i < len(self.gps_points):
                self.set_pothole_marker(self.gps_points[gps_i])

        # лежачі поліцейські — локальні максимуми осі Z
        # (при наїзді Z різко зростає вище ~17000)
        bumps, _ = find_peaks(
            data, height=18500, distance=15, prominence=800  # було 17200  # було 200
        )
        for i in bumps:
            gps_i = base_idx + i
            if gps_i < len(self.gps_points):
                self.set_bump_marker(self.gps_points[gps_i])

    def update_car_marker(self, point):
        self.car_marker.lat = point[0]
        self.car_marker.lon = point[1]

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
