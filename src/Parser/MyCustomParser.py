import Datastore
# import numpy as np
from datetime import datetime
from Parser.AbstractParser import AbstractParser


class MyCustomParser(AbstractParser):

    def do_parse(self):

        # your custom numpy magic
        # dataset = np.loadtxt('path', dtype=np.str, delimiter=',')  # Read file
        dataset = [{
            "datetime": datetime.now(),
            "value": 23,
            "origin": self.rawdata_source.src,
            "position": 42
        }]

        for item in dataset:
            v = Datastore.Observation(
                item["datetime"],
                item["value"],
                item["origin"],
                item["position"]
            )
            self.datastore.store_observations([v])
