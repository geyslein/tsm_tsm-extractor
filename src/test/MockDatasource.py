#! /usr/bin/env python
# -*- coding: utf-8 -*-


from RawDataSource.AbstractRawDataSource import AbstractRawDataSource


class MockDataSource(AbstractRawDataSource):
    def __init__(self, data: bytes = b""):
        self.data = data
        super().__init__(src="/mock/source")

    def fetch(self):
        self.temp_file.write(self.data)
        self.temp_file.seek(0)
