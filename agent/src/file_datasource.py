from csv import reader
from datetime import datetime
from domain.accelerometer import Accelerometer
from domain.gps import Gps
from domain.parking import Parking
from domain.aggregated_data import AggregatedData


class FileDatasource:
    def __init__(self, accelerometer_filename: str, gps_filename: str, parking_filename: str) -> None:
        self.accelerometer_filename = accelerometer_filename
        self.gps_filename = gps_filename
        self.parking_filename = parking_filename

        self.acc_file = None
        self.gps_file = None
        self.parking_file = None

        self.acc_reader = None
        self.gps_reader = None
        self.parking_reader = None

        self.batch_size = 5

    def startReading(self):
        self.acc_file = open(self.accelerometer_filename, newline="", encoding="utf-8")
        self.gps_file = open(self.gps_filename, newline="", encoding="utf-8")
        self.parking_file = open(self.parking_filename, newline="", encoding="utf-8")

        self.acc_reader = reader(self.acc_file)
        self.gps_reader = reader(self.gps_file)
        self.parking_reader = reader(self.parking_file)

        self._skip_header_if_needed()

    def stopReading(self):
        if self.acc_file:
            self.acc_file.close()
            self.acc_file = None
        if self.gps_file:
            self.gps_file.close()
            self.gps_file = None
        if self.parking_file:
            self.parking_file.close()
            self.parking_file = None

        self.acc_reader = None
        self.gps_reader = None
        self.parking_reader = None

    def read(self) -> AggregatedData:
        if self.acc_reader is None or self.gps_reader is None or self.parking_reader is None:
            raise RuntimeError("Datasource is not started. Call startReading() first.")

        acc_row = self._read_last_valid_row("acc", 3)
        gps_row = self._read_last_valid_row("gps", 2)
        parking_row = self._read_last_valid_row("par", 3)

        accelerometer = Accelerometer(
            x=int(float(acc_row[0])),
            y=int(float(acc_row[1])),
            z=int(float(acc_row[2])),
        )

        gps = Gps(
            longitude=float(gps_row[0]),
            latitude=float(gps_row[1]),
        )

        parking = Parking(
            empty_count=int(parking_row[0]),
            gps=Gps(
                longitude=float(parking_row[1]),
                latitude=float(parking_row[2]),
            )
        )

        return AggregatedData(
            accelerometer=accelerometer,
            gps=gps,
            parking=parking,
            timestamp=datetime.utcnow(),
        )

    def _read_last_valid_row(self, kind: str, min_cols: int):
        last_valid = None
        for _ in range(self.batch_size):
            row = self._next_valid_row(kind, min_cols)
            last_valid = row
        return last_valid

    def _next_valid_row(self, kind: str, min_cols: int):
        while True:
            try:
                reader_option = None
                match kind:
                    case "acc":
                        reader_option = self.acc_reader
                    case "gps":
                        reader_option = self.gps_reader
                    case "par":
                        reader_option = self.parking_reader
                row = next(reader_option)
            except StopIteration:
                self.stopReading()
                self.startReading()
                continue

            row = [str(c).strip() for c in row]

            if not row or all(c == "" for c in row):
                continue

            if len(row) < min_cols:
                continue

            if any(row[i] == "" for i in range(min_cols)):
                continue

            try:
                for i in range(min_cols):
                    float(row[i])
            except Exception:
                continue

            return row

    def _skip_header_if_needed(self):
        if self.acc_reader is not None:
            first = next(self.acc_reader, None)
            if first is not None and self._row_has_non_numeric(first):
                pass
            else:
                self._restart_readers()

        if self.gps_reader is not None:
            first = next(self.gps_reader, None)
            if first is not None and self._row_has_non_numeric(first):
                pass
            else:
                self._restart_readers()

        if self.parking_reader is not None:
            first = next(self.parking_reader, None)
            if first is not None and self._row_has_non_numeric(first):
                pass
            else:
                self._restart_readers()

    def _row_has_non_numeric(self, row):
        try:
            for c in row:
                s = str(c).strip()
                if s == "":
                    continue
                float(s)
            return False
        except Exception:
            return True

    def _restart_readers(self):
        self.stopReading()
        self.acc_file = open(self.accelerometer_filename, newline="", encoding="utf-8")
        self.gps_file = open(self.gps_filename, newline="", encoding="utf-8")
        self.parking_file = open(self.parking_filename, newline="", encoding="utf-8")

        self.acc_reader = reader(self.acc_file)
        self.gps_reader = reader(self.gps_file)
        self.parking_reader = reader(self.parking_file)
