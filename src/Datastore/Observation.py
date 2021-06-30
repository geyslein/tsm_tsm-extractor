import datetime


class Observation:
    """Base class of observation, may be a sqlalchemy model or some adapter class

    Attributes:
        timestamp (datetime): Timestamp of the data point. The point in time, where the value was
            measured.
        value (float):  The measured value.
        origin (str):   The source of the raw data file.
        position (int): Position in the source file, i.g. number of the column in a csv file.
    """
    def __init__(self, timestamp: datetime, value: float, origin: str, position: int):
        self.timestamp = timestamp
        self.value = value
        self.origin = origin
        self.position = position
