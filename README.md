# Scratchpad

```
python src/main.py parse -p AnotherCustomParser -t postgresql://postgres:postgres@localhost/postgres -s https://www.ufz.de/static/custom/weblayout/DefaultInternetLayout/img/logos/ufz_transparent_de_blue.png -d ce2b4fb6-d9de-11eb-a236-125e5a40a845

# Or with docker
docker-compose up -d
docker-compose run app main.py parse -p AnotherCustomParser -t postgresql://postgres:postgres@db/postgres -s https://www.ufz.de/static/custom/weblayout/DefaultInternetLayout/img/logos/ufz_transparent_de_blue.png -d ce2b4fb6-d9de-11eb-a236-125e5a40a845

```

# @TODO

- [ ] Where optional parser arguments (like "delimter", "timestamp
      fromat" and so on) should come from?
  - JSON Object as command line parameter? Then the scheduler has to
    manage this
  - Or querying the DSM backend? Then we have do add another component
  - Current favorite: Get them from thing properties (JSON)
- [ ] Naming: Maybe tsm-ingest-dispatcher is better?
- [ ] What about the data model changes from FROST STA (e.g. "position")
- [ ] Strictness: What to do with violated unique constraints, for
      example when a raw data source that contains data a second time or
      when the process fails and it already committed some chunks?
- [ ] Check general limits like maximum file size and maximum number of
      lines or elements per job
- [ ] Report progress to scheduler

# How to implement a new custom parser


# Ressources

- SQLAlchemy Quick Start: https://gist.github.com/DmitryBe/805fb35e3472b8985c654c8dfb8aa127
