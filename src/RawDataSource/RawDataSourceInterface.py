from abc import ABC, abstractmethod


class RawDataSourceInterface(ABC):
    def __init__(self, src: str) -> None:
        self.src = src
        self.temp_file = self.fetch_file()

    @abstractmethod
    def fetch_file(self):
        raise NotImplementedError
