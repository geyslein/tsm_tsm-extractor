```
python src/main.py parse -p AnotherCustomParser -t postgresql://postgres:postgres@localhost/postgres -s https://www.ufz.de/static/custom/weblayout/DefaultInternetLayout/img/logos/ufz_transparent_de_blue.png -d 1

# Or with docker
docker build . -t pythnparser

```

# @TODO

- [ ] Decision if "POSITION" should be a generic integer field in
      datastream. Keep in mind, that position is also a string like an
      xml path or something similar.
- [ ] Generic "POSTITION" field should get part of a unique constraint
      with "THING_ID"
- [ ] Report progress to scheduler
- [ ] UUID as (additional) ThingId

# Ressources

- SQLAlchemy Quick Start: https://gist.github.com/DmitryBe/805fb35e3472b8985c654c8dfb8aa127
