FROM debian:bullseye-slim as base

ARG BUILD_DATE
ARG VCS_REF

LABEL maintainer="Martin Abbrent <martin.abbrent@ufz.de>" \
    org.opencontainers.image.title="DJANGO Base Image" \
    org.opencontainers.image.licenses="HEESIL" \
    org.opencontainers.image.version="0.0.1" \
    org.opencontainers.image.revision=$VCS_REF \
    org.opencontainers.image.created=$BUILD_DATE

RUN apt-get -y update \
    && apt-get -y dist-upgrade \
    && apt-get -y --no-install-recommends install \
      python3 \
      libaio1 \
      ca-certificates \
    && apt-get -y autoremove \
    && apt-get -y autoclean \
    && rm -rf /var/lib/apt

FROM base as build

RUN apt-get -y update \
    && apt-get -y install \
      curl \
      unzip

# fetch oracle instant client
RUN curl "https://download.oracle.com/otn_software/linux/instantclient/213000/instantclient-basiclite-linux.x64-21.3.0.0.0.zip" > /tmp/instantclient-basiclite-linux.x64.zip \
    && unzip /tmp/instantclient-basiclite-linux.x64.zip -d /usr/lib/oracle

RUN echo "NAMES.DIRECTORY_PATH = ( TNSNAMES, LDAP )"          >> /usr/lib/oracle/instantclient_21_3/network/admin/sqlnet.ora && \
    echo "NAMES.DEFAULT_DOMAIN = UFZ.DE"                      >> /usr/lib/oracle/instantclient_21_3/network/admin/sqlnet.ora && \
    echo "NAMES.LDAP_CONN_TIMEOUT = 1"                        >> /usr/lib/oracle/instantclient_21_3/network/admin/sqlnet.ora && \
    echo "DIRECTORY_SERVERS = (tnsnames.intranet.ufz.de:389)" >> /usr/lib/oracle/instantclient_21_3/network/admin/ldap.ora && \
    echo "DEFAULT_ADMIN_CONTEXT = \"ou=oracle,dc=ufz,dc=de\"" >> /usr/lib/oracle/instantclient_21_3/network/admin/ldap.ora && \
    echo "DIRECTORY_SERVER_TYPE = OID"                        >> /usr/lib/oracle/instantclient_21_3/network/admin/ldap.ora

FROM base as dist

RUN apt-get -y update \
    && apt-get -y install python3-pip

# add requirements as root, otherwise they won't
# be found when the image is run by singularity
COPY src/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir --upgrade pip \
    && pip install \
        --no-cache-dir \
        --no-warn-script-location -r \
        /tmp/requirements.txt

COPY --from=build /usr/lib/oracle/ /usr/lib/oracle/
RUN echo /usr/lib/oracle/instantclient_21_3 > /etc/ld.so.conf.d/oracle-instantclient.conf \
    && ldconfig

# Create a group and user
RUN useradd --uid 1000 -m appuser

# Tell docker that all future commands should run as the appuser user
USER appuser

WORKDIR /home/appuser/app/src

COPY src .

# singularity needs full paths
ENTRYPOINT ["python3", "/home/appuser/app/src/main.py"]
