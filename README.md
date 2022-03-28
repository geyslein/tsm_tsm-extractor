# Table of contents

[[_TOC_]]

# Time series management (TSM) Extractor

![RDM Logo](docs/RDM_fullcolor_rgb_xs.png "Logo of the UFZ Research data
management team (RDM)")  
![UFZ Logo](docs/UFZ_Logo_RGB_EN_XS.png "Logo of the Helmholtz-Zentrum
für Umweltforschung GmbH - UFZ")

The Time series management (TSM) Extractor is a cli tool to extract time
series data from classic sources like `csv` or `xml` raw data files
which are usually generated by legacy and current data loggers. It
requires a parser type, a target, a source and a Thing-ID as parameter.

The Time series management (TSM) Extractor is developed by the ZID
development team of the research data management team at the
Helmholtz-Zentrum für Umweltforschung GmbH - UFZ.

# @TODO

- [ ] Check if it should be result_time or phenomenon_time_start for the
      timestamps
- [ ] Naming: Maybe tsm-ingest-dispatcher is better?
- [ ] What about the data model changes from FROST STA (e.g. "position")
- [ ] Strictness: What to do with violated unique constraints, for
      example when a raw data source that contains data a second time or
      when the process fails and it already committed some chunks?
- [ ] Check general limits like maximum file size and maximum number of
      lines or elements per job
- [ ] Report progress to scheduler

# How to run the TSM Extractor

You can run the TSM Extractor in your local python environment, with
docker or with the provided docker-compose setup. The most convenient
way for quickstart, testing and development is using docker-compose, as
it provides a prepared database. For production use you have to use a
custom docker-compose file.

## With local python environment

You may have to install the requirements at first:

```bash
pip install --user -r src/requirements.txt
```

### List usage information

```bash
python src/main.py
# or
python src/main.py  --help
Usage: main.py [OPTIONS] COMMAND [ARGS]...

Options:
  --help  Show this message and exit.

Commands:
  list     Display available datastore, parser and raw data source types.
  parse    Parse data of a raw data source to a data store.
  version  Display the current version.

```

### Display available datastore, parser and raw data source types

```bash
python src/main.py list
```

### Parse data of a raw data source to a data store

You have to provide a postgres database with the basic STA schema
(tables). See section [Database model](#database-model).

When you are using the recommended
[docker-compose](#with-docker-compose) setup a database for testing
purposes is already provided.

```bash
python src/main.py parse -p AnotherCustomParser -t postgresql://postgres:postgres@localhost/postgres -s https://example.com/ -d ce2b4fb6-d9de-11eb-a236-125e5a40a845
# -p, --parser        The parser type to be be used. Should be available from `list` command.
# -t, --target-uri    URI of the datastore where the parsed data should be written.
# -s, --source        URI of the raw data file to parse.
# -d, --device-id     UUID of the device (or "thing") which generated the raw data.
```

#### With ORACLE database as target

Replace `XXXXXXXXX` by a valid password.

```bash
python src/main.py parse -p AnotherCustomParser -t oracle://ZID_SQLALCHEMY_TEST:XXXXXXXXX@COMADEV -s https://example.com/ -d 7f384bcc-ea5d-11eb-9d12-54e1ad7c5c19
```

## With docker

### Take the ready to use image from the registry

```bash
docker run --rm git.ufz.de:4567/rdm-software/timeseries-management/tsm-extractor/extractor:latest parse -p AnotherCustomParser -t postgresql://postgres:postgres@postgres.example.com/postgres -s https://example.com/ -d ce2b4fb6-d9de-11eb-a236-125e5a40a845
```

Note, that it is not possible to access any database with `localhost` as
address. You may use `--network="host"` but that is not recommended from
security perspective. If you are not experienced in docker networking
better use the docker-compose setup below.

### Or build the image yourself

```bash
docker build -t tsm-extractor .
docker run --rm tsm-extractor parse -p AnotherCustomParser -t postgresql://postgres:postgres@postgres.example.com/postgres -s https://example.com/ -d ce2b4fb6-d9de-11eb-a236-125e5a40a845
```

## With docker-compose

At first use docker-compose to build the container, start the database
and deploy the basic database tables with one command:

```bash
docker-compose up -d
```

From then you can use all the commands described in paragraph
"[With local python environment](#with-local-python-environment)", but
note the slight difference in the database URI:

```bash
docker-compose run --rm app main.py parse -p AnotherCustomParser -t postgresql://postgres:postgres@db/postgres -s https://example.com/ -d ce2b4fb6-d9de-11eb-a236-125e5a40a845
```
## Running the TSM Extractor on EVE

The main difference when running the extractor on EVE, compared to the methods outlined above, is the containerization technology. Docker and the related tooling is not available and instead [Singularity](https://apptainer.org/) is used to manage and run containers. Fortunately Singularity is able to convert many Docker images on the fly and run them accordingly. In order to start the extractor on an interactive login shell run the following command:

```shell
singularity run \
            --docker-username GITLAB-USER \
            --docker-password GITLAB-PASSWORD \
            docker://git.ufz.de:4567/rdm-software/timeseries-management/tsm-extractor/extractor:latest parse \
            -p AnotherCustomParser \
            -t postgresql://postgres:postgres@postgres.example.com/postgres
            -s https://example.com/ \
            -d ce2b4fb6-d9de-11eb-a236-125e5a40a845
```

To run an extractor job using the [SLURM scheduler](https://slurm.schedmd.com/documentation.html) write the following content into a file (e.g. `run.sh`):
```shell
#!/bin/bash

#SBATCH --job-name=extractor
#SBATCH --time=0-00:30:00
#SBATCH --mem-per-cpu=1G
#SBATCH --output=/work/%u/%x-%j.log

singularity run \
            --docker-username GITLAB-USER \
            --docker-password GITLAB-PASSWORD \
            docker://git.ufz.de:4567/rdm-software/timeseries-management/tsm-extractor/extractor:latest parse \
            -p AnotherCustomParser \
            -t postgresql://postgres:postgres@postgres.example.com/postgres
            -s https://example.com/ \
            -d ce2b4fb6-d9de-11eb-a236-125e5a40a845
```
 and instruct SLURM to execute this job defintion with:

 ```shell
 sbatch run.sh
 ```

For more details about the scheduling process, please refer to the [EVE Wiki](https://wiki.ufz.de/eve/index.php/Submitting_Jobs_SLURM).

# Database model

The TSM Extractor depends on the Basic STA Model which is based on the
entities that are really used for storing normalized (in the meaning of
data structure) raw data. The entities we are currently using are
`THING`, `DATASTREAM` and `OBSERVATION`:

![Diagram of the Basic STA Model](docs/BASIC-STA-Model.png "Diagram of
the Basic STA Model")

You can find the DDL (for postgres) in this repo:
`postgres/postgres-ddl.sql`.

# Developing custom modules

## General resources

- SQLAlchemy Quick Start: https://gist.github.com/DmitryBe/805fb35e3472b8985c654c8dfb8aa127

## How to implement a new custom parser

To implement a new custom parser you have to create a parser class in the
`src/Parser` directory and inherit the `AbstractParser` class:

```python
class MyCustomParser(AbstractParser):
    pass
```

The custom parser class should implement the abstract method `do_parse`, which
needs to implement the actual processing logic.
A parser objects receives instances of `RawData` and `Datastore` on
initialization. Use the latter to retrieve the parser settings:

```python
self.datastore.get_parser_parameters(self.__class__.__name__)
```

Do not forget to call the constructor of the parent class when
overriding the constructor:

```python
super().__init__(rawdata_source, datastore)
```

You can use the `rawdata_source` object to get the data from previously
fetched source:

```python
data = self.rawdata_source.read()
```

To persist one or more observations, create new `Observation` instances
and pass them such a collection to the `store_observations` method of
the datastore:

```python
# <timestamp> datetime object
# <value>     measured value as float
# <position>  position inside the the source as int number       
v = Observation(<timestamp>, <value>, self.rawdata_source.src, <position>)
self.datastore.store_observations([v])
```

To allow better debugging and monitoring for the scheduler your parser
should report the progress when possible. For example when iterating
over a collection of elements.

You should use the abstract parsers method `set_progress_length` to
define the total number of elements before starting to iterate:

```python
self.set_progress_length(self.number_of_values)
```

While iterating over the elements you can report every single step or
chunks to the abstract parsers *progress* implementation:

```python
self.update_progress()   # report one step
self.update_progress(10) # report ten steps in one call
```

## Run linting

```bash
docker-compose run app -m pylint Parser RawDataSource main.py --exit-zero
```

## Run code formatting

```bash
docker-compose run app -m black .
```
