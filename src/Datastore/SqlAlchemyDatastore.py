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
        # self.session = None
        self.chunk = []
        self.current_chunk_idx = 0

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
        self.sqla_thing = self.session.query(Thing).filter(Thing.id == self.device_id).first()

    def store_observation(self, observation: Observation) -> None:

        # increase chunk counter
        self.current_chunk_idx += 1

        sqla_datastream = self.fetch_or_create_datastream(observation)

        sqla_obs = SqlaObservation(
            result_time=observation.timestamp, result_type=1,
            result_number=observation.value, datastream=sqla_datastream
        )

        self.chunk.append(sqla_obs)
        # Flush chunk when chunk size is arrived
        if self.current_chunk_idx % CHUNK_SIZE == 0:
            self.insert_commit_chunk()

        # self.session.add(sqla_obs)
        # self.session.commit()

        # click.secho('{}/{}: {} {}'.format(
        #     self.device_id, observation.position,
        #     observation.timestamp,
        #     observation.value
        # ), fg='green')

    def fetch_or_create_datastream(self, observation):

        sqla_datastream = self.session.query(Datastream).join(Thing).filter(
            Datastream.properties['position'].as_integer() == observation.position
        ).first()

        if sqla_datastream is None:
            sqla_datastream = Datastream(
                thing=self.sqla_thing, properties={'position': observation.position},
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
            # click.echo('Flushed chunk number {}.'.format(
            #     int(self.current_chunk_idx/CHUNK_SIZE)
            # ), err=True)

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

