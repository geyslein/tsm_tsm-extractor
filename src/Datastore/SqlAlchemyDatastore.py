import click
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from .DatastoreInterface import DatastoreInterface
from . import Observation
from .SqlAlchemy.Model import Thing, Datastream
from .SqlAlchemy.Model.Observation import Observation as SqlaObservation

CHUNK_SIZE = 1000


class SqlAlchemyDatastore(DatastoreInterface):

    session: Session
    sqla_thing: Thing

    def __init__(self, uri: str, device_id: int):
        super().__init__(uri, device_id)
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
            result_time=observation.timestamp, result_type=1,
            result_number=observation.value, datastream=sqla_datastream,
            parameters={"origin": observation.origin}
        )

        self.chunk.append(sqla_obs)
        # Flush chunk when chunk size is arrived
        if self.current_chunk_idx % CHUNK_SIZE == 0:
            self.insert_commit_chunk()

    def store_observations(self, observations: [Observation]) -> None:
        for i in observations:
            self.store_observation(i)

    def fetch_or_create_datastream(self, observation):

        sqla_datastream = self.session.query(Datastream).join(Thing).filter(
            Datastream.position == str(observation.position)
        ).first()

        if sqla_datastream is None:
            sqla_datastream = Datastream(
                thing=self.sqla_thing, position=observation.position,
                name='{}/{}'.format(self.sqla_thing.name, observation.position)
            )
            self.session.add(sqla_datastream)

        return sqla_datastream

    def insert_commit_chunk(self):
        if len(self.chunk) > 0:
            self.session.add_all(self.chunk)
            self.chunk.clear()
            self.session.flush()
            self.session.commit()

    def finalize(self):
        # insert last chunk
        self.insert_commit_chunk()

        click.echo('Doing final commit.', err=True)
        self.session.commit()

        click.echo('Pushed {} new observations to database.'.format(self.current_chunk_idx), err=True)

        click.echo('Close database session.', err=True)
        self.session.close()

    def __del__(self):
        pass

