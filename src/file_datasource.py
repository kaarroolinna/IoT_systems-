from csv import reader
from datetime import datetime
from domain.accelerometer import Accelerometer
from domain.gps import Gps
from domain.aggregated_data import AggregatedData


class FileDatasource:

    def __init__(self, accelerometer_filename: str, gps_filename: str) -> None:
        self.accelerometer_filename = accelerometer_filename
        self.gps_filename = gps_filename

        self.acc_file = None
        self.gps_file = None

        self.acc_reader = None
        self.gps_reader = None

        self.batch_size = 5

    def startReading(self):
        self.acc_file = open(self.accelerometer_filename, newline='')
        self.gps_file = open(self.gps_filename, newline='')

        self.acc_reader = reader(self.acc_file)
        self.gps_reader = reader(self.gps_file)

    def stopReading(self):
        if self.acc_file:
            self.acc_file.close()
        if self.gps_file:
            self.gps_file.close()

    def read(self) -> AggregatedData:

        acc_rows = []
        gps_rows = []

        try:
            for _ in range(self.batch_size):
                acc_rows.append(next(self.acc_reader))
                gps_rows.append(next(self.gps_reader))

        except StopIteration:
            self.stopReading()
            self.startReading()
            return self.read()

        acc_row = acc_rows[-1]
        gps_row = gps_rows[-1]

        accelerometer = Accelerometer(
            x=int(acc_row[0]),
            y=int(acc_row[1]),
            z=int(acc_row[2])
        )

        gps = Gps(
            longitude=float(gps_row[0]),
            latitude=float(gps_row[1])
        )

        aggregated = AggregatedData(
            accelerometer=accelerometer,
            gps=gps,
            time=datetime.utcnow()
        )

        return aggregated
