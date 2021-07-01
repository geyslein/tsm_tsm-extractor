import shutil
import tempfile
import urllib.request

import click

from RawDataSource.RawDataSourceInterface import RawDataSourceInterface


class HttpRawDataSource(RawDataSourceInterface):

    def fetch_file(self):

        tmp_file = None

        with urllib.request.urlopen(self.src) as response:
            tmp_file = tempfile.NamedTemporaryFile(delete=True)
            shutil.copyfileobj(response, tmp_file)
            click.secho(
                'Fetched remote raw data file from "{}"'.format(self.src),
                err=True,
                fg="green"
            )
        return tmp_file
