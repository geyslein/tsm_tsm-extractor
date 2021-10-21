#! /usr/bin/env python
# -*- coding: utf-8 -*-


from RawDataSource.AbstractRawDataSource import AbstractRawDataSource


class MockDataSource(AbstractRawDataSource):
    def __init__(self, data: str):
        self.data = data
        super().__init__(src="")

    def fetch(self):
        self.temp_file.write(self.data)
        self.temp_file.seek(0)

