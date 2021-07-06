import shutil
import click
import urllib.request

import humanfriendly

from RawDataSource.RawDataSourceInterface import RawDataSourceInterface


class HttpRawDataSource(RawDataSourceInterface):

    def fetch_file(self):
        with urllib.request.urlopen(self.src) as response:
            shutil.copyfileobj(response, self.temp_file)
            click.secho(
                'Fetched remote raw data file from "{}". Size: {}'.format(
                    self.src,
                    humanfriendly.format_size(self.temp_file.tell())
                ),
                err=True,
                fg="green"
            )
