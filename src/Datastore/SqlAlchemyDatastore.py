from typing import List
import click
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from .AbstractDatastore import AbstractDatastore
from .Observation import Observation
from .SqlAlchemy.Model import Thing, Datastream
from .SqlAlchemy.Model.Observation import Observation as SqlaObservation, ResultType

CHUNK_SIZE = 1000


class SqlAlchemyDatastore(AbstractDatastore):

    def __init__(self, uri: str, device_id: int):

        super().__init__(uri, device_id)

        self.sqla_datastream_cache = {}
        self.session: Session = None
        self.sqla_thing: Thing = None
        self.chunk = []
        self.current_chunk_idx = 0

    def get_parser_parameters(self, parser_type: str) -> dict:
        return self.sqla_thing.get_parser_parameters(parser_type)

    def initiate_connection(self) -> None:
        click.secho(
            'Connecting to sqlalchemy supported database "{}"'.format(self.uri),
            err=True,
            fg="green"
        )
        engine = create_engine(self.uri)
        Session = sessionmaker(bind=engine)
        self.session = Session()
        click.secho(
            'Successfully connected sqlalchemy to "{}"'.format(self.uri),
            err=True,
            fg="green"
        )
        self.sqla_thing = self.session.query(Thing).filter(
            Thing.uuid == str(self.device_id)
        ).first()

    def store_observation(self, observation: Observation) -> None:

        # increase chunk counter
        self.current_chunk_idx += 1

        sqla_datastream = self.fetch_or_create_datastream(observation)

        sqla_obs = SqlaObservation(
            result_time=observation.timestamp, result_type=ResultType.Number,
            result_number=observation.value, datastream=sqla_datastream,
            parameters={"origin": observation.origin}
        )

        self.chunk.append(sqla_obs)
        # Flush chunk when chunk size is arrived
        if self.current_chunk_idx % CHUNK_SIZE == 0:
            self.insert_commit_chunk()

    def store_observations(self, observations: List[Observation]) -> None:
        for i in observations:
            self.store_observation(i)

    def fetch_or_create_datastream(self, observation):

        # used as name in data stream model and as key for a simple cache as this will not change
        # during one run of the extractor
        datastream_name = '{}/{}'.format(self.sqla_thing.name, observation.position)

        # Lookup simple cache at first
        if datastream_name in self.sqla_datastream_cache:
            sqla_datastream = self.sqla_datastream_cache.get(datastream_name)

        else:
            # Lookup database for existing data stream
            sqla_datastream = self.session.query(Datastream).filter(
                Datastream.position == str(observation.position),
                Datastream.thing == self.sqla_thing
            ).first()

            # create a new one if there is no existing on found on the database
            if sqla_datastream is None:
                sqla_datastream = Datastream(
                    thing=self.sqla_thing,
                    position=observation.position,
                    name=datastream_name
                )
                self.session.add(sqla_datastream)

            # Store the new or selected object in simple cache
            self.sqla_datastream_cache[datastream_name] = sqla_datastream

        return sqla_datastream

    def insert_commit_chunk(self):
        if len(self.chunk) > 0:
            self.session.add_all(self.chunk)
            self.chunk.clear()
            self.session.commit()

    def finalize(self):
        # insert last chunk
        self.insert_commit_chunk()

        click.echo('Pushed {} new observations to database.'.format(
            self.current_chunk_idx), err=True
        )

        click.echo('Close database session.', err=True)
        self.session.close()
