import shutil
import tempfile
import urllib.request

import click

from RawDataSource.RawDataSourceInterface import RawDataSourceInterface


class HttpRawDataSource(RawDataSourceInterface):

    def fetch_file(self):
        with urllib.request.urlopen(self.src) as response:
            with tempfile.NamedTemporaryFile(delete=True) as tmp_file:
                shutil.copyfileobj(response, tmp_file)
                click.secho(
                    'Fetched remote raw data file from "{}"'.format(self.src),
                    err=True,
                    fg="green"
                )
                return tmp_file
