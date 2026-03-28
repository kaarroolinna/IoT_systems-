import csv


class FileDatasource:
    def __init__(self, accel_path: str, gps_path: str):
        self.accel_path = accel_path
        self.gps_path = gps_path

    def read(self):
        accel_z = []

        with open(self.accel_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                accel_z.append(float(row["z"]))

        gps_points = []
        with open(self.gps_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                # колонки переплутані в файлі
                lat = float(row["longitude"])
                lon = float(row["latitude"])
                gps_points.append((lat, lon))

        n = len(accel_z)
        gps_points = [gps_points[i % len(gps_points)] for i in range(n)]

        print(f"[FileDatasource] Акселерометр: {n} рядків")
        print(f"[FileDatasource] GPS: від {gps_points[0]} до {gps_points[-1]}")

        return gps_points, accel_z