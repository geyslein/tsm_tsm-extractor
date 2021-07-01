FROM python:3-alpine as base

ARG BUILD_DATE
ARG VCS_REF

LABEL maintainer="Martin Abbrent <martin.abbrent@ufz.de>" \
    org.opencontainers.image.title="DJANGO Base Image" \
    org.opencontainers.image.licenses="HEESIL" \
    org.opencontainers.image.version="0.0.1" \
    org.opencontainers.image.revision=$VCS_REF \
    org.opencontainers.image.created=$BUILD_DATE

RUN apk --no-cache add libpq

FROM base as build

RUN mkdir /install
WORKDIR /install

RUN apk add --no-cache --virtual .build-deps \
    gcc \
    g++ \
    python3-dev \
    musl-dev \
    postgresql-dev

# add requirements
COPY src/requirements.txt /tmp/requirements.txt
RUN pip install --upgrade pip \
    && pip install \
        --prefix /install \
        --no-cache-dir \
        --no-warn-script-location -r \
        /tmp/requirements.txt

FROM base as dist

COPY --from=build /install /usr/local

# Create a group and user
RUN addgroup -S appgroup && adduser -S appuser -G appgroup --uid 1000
# Tell docker that all future commands should run as the appuser user
USER appuser

WORKDIR /home/appuser/app/src

COPY src .

ENTRYPOINT ["python", "main.py"]
