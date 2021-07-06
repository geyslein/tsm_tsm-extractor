import tempfile
from abc import ABC, abstractmethod

import humanfriendly

MAX_FILE_SIZE = 1000*1000*32  # Maximum file size is 32M


class RawDataSourceInterface(ABC):
    def __init__(self, src: str):
        self.src = src
        # Keep 32M in memory before writing to disk
        self.temp_file = tempfile.SpooledTemporaryFile(max_size=1024*1024*32)
        self.fetch_file()
        self.check_max_file_size()

    @abstractmethod
    def fetch_file(self):
        """Load file and copy it to self.temp_file"""
        raise NotImplementedError

    def check_max_file_size(self):
        """Check the fetched file for maximum file size nad raise exception when it is to large"""
        size = self.temp_file.tell()
        if size > MAX_FILE_SIZE:
            raise MaximumFileSizeError(size)


class MaximumFileSizeError(Exception):
    def __init__(self, size: int):
        self.size = size
        self.message = 'Maximum filesize ({}) exceeded: Current size is {}'.format(
            humanfriendly.format_size(MAX_FILE_SIZE),
            humanfriendly.format_size(self.size)
        )
        super().__init__(self.message)