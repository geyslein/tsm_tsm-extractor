# Scratchpad

```
python src/main.py parse -p AnotherCustomParser -t postgresql://postgres:postgres@localhost/postgres -s https://www.ufz.de/static/custom/weblayout/DefaultInternetLayout/img/logos/ufz_transparent_de_blue.png -d ce2b4fb6-d9de-11eb-a236-125e5a40a845

# Or with docker
docker-compose up -d
docker-compose run --rm app main.py parse -p AnotherCustomParser -t postgresql://postgres:postgres@db/postgres -s https://www.ufz.de/static/custom/weblayout/DefaultInternetLayout/img/logos/ufz_transparent_de_blue.png -d ce2b4fb6-d9de-11eb-a236-125e5a40a845

```

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

# How to implement a new custom parser


# run linting

> docker-compose run app -m pylint Datastore Parser RawDataSource main.py --exit-zero

# run code formatting

> docker-compose run app -m black .

# Ressources

- SQLAlchemy Quick Start: https://gist.github.com/DmitryBe/805fb35e3472b8985c654c8dfb8aa127

# ORACLE

```bash
docker-compose run --rm app main.py parse -p AnotherCustomParser -t oracle://ZID_SQLALCHEMY_TEST:XXXXXXXXX@COMADEV -s https://www.ufz.de/static/custom/weblayout/DefaultInternetLayout/img/logos/ufz_transparent_de_blue.png -d 7f384bcc-ea5d-11eb-9d12-54e1ad7c5c19
```

## ORACLE Todos

- [ ] Save milliseconds in timestamp and use them in the unique
      constraint on stream-id/result-time
