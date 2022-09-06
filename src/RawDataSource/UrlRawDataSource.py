import logging
import shutil
import urllib.request

import humanfriendly

from RawDataSource.AbstractRawDataSource import AbstractRawDataSource


class UrlRawDataSource(AbstractRawDataSource):

    def fetch(self):
        with urllib.request.urlopen(self.src) as response:
            shutil.copyfileobj(response, self.temp_file)
            sz = humanfriendly.format_size(self.temp_file.tell())
            logging.info(f'Fetched remote raw data file from "{self.src}". Size: {sz}')
