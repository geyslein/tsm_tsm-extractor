import datetime
import math


class Observation:
    """Base class of observation, may be a sqlalchemy model or some adapter class

    Attributes:
        timestamp (datetime): Timestamp of the data point. The point in time, where the value was
            measured.
        value (float):  The measured value.
        origin (str):   The source of the raw data file.
        position (int): Position in the source file, i.g. number of the column in a csv file.
    """
    def __init__(self, timestamp: datetime, value: float, origin: str, position: int,
                 header: str = ''):
        self.timestamp = timestamp
        self.value = value
        self.origin = origin
        self.position = position
        self.header = header

        self.check_value()

    def check_value(self):
        # do not allow python nan for now
        if math.isnan(self.value):
            raise NanNotAllowedHereError('NaN ist not allowed as observation value.')


class NanNotAllowedHereError(ValueError):
    pass
