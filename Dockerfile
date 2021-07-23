FROM oraclelinux:8-slim as base

RUN echo "[python39]" >> /etc/dnf/modules.d/python39.module && \
    echo "name=python39" >> /etc/dnf/modules.d/python39.module && \
    echo "stream=3.9" >> /etc/dnf/modules.d/python39.module && \
    echo "profiles=common" >> /etc/dnf/modules.d/python39.module && \
    echo "state=enabled" >> /etc/dnf/modules.d/python39.module

RUN microdnf install oracle-instantclient-release-el8 oraclelinux-developer-release-el8 && \
    microdnf install libaio \
                     oracle-instantclient-basic \
                     oracle-instantclient-sqlplus \
                     python39 \
                     python39-libs \
                     python39-pip \
                     python39-setuptools && \
    microdnf clean all

CMD ["/bin/python3", "-V"]

ARG BUILD_DATE
ARG VCS_REF

LABEL maintainer="Martin Abbrent <martin.abbrent@ufz.de>" \
    org.opencontainers.image.title="DJANGO Base Image" \
    org.opencontainers.image.licenses="HEESIL" \
    org.opencontainers.image.version="0.0.1" \
    org.opencontainers.image.revision=$VCS_REF \
    org.opencontainers.image.created=$BUILD_DATE


FROM base as build

RUN mkdir /install
WORKDIR /install

# add requirements
COPY src/requirements.txt /tmp/requirements.txt
RUN pip-3 install --upgrade pip \
    && pip-3 install \
        --prefix /install \
        --no-cache-dir \
        --no-warn-script-location -r \
        /tmp/requirements.txt

FROM base as dist

COPY --from=build /install /usr/local

RUN echo "NAMES.DIRECTORY_PATH = ( TNSNAMES, LDAP )" >> /usr/lib/oracle/21/client64/lib/network/admin/sqlnet.ora && \
    echo "NAMES.DEFAULT_DOMAIN = UFZ.DE" >> /usr/lib/oracle/21/client64/lib/network/admin/sqlnet.ora && \
    echo "NAMES.LDAP_CONN_TIMEOUT = 1" >> /usr/lib/oracle/21/client64/lib/network/admin/sqlnet.ora && \
    echo "DIRECTORY_SERVERS = (tnsnames.intranet.ufz.de:389)" >> /usr/lib/oracle/21/client64/lib/network/admin/ldap.ora && \
    echo "DEFAULT_ADMIN_CONTEXT = \"ou=oracle,dc=ufz,dc=de\"" >> /usr/lib/oracle/21/client64/lib/network/admin/ldap.ora && \
    echo "DIRECTORY_SERVER_TYPE = OID" >> /usr/lib/oracle/21/client64/lib/network/admin/ldap.ora

# Create a group and user
RUN useradd --uid 1000 appuser
# Tell docker that all future commands should run as the appuser user
USER appuser

WORKDIR /home/appuser/app/src

COPY src .

ENTRYPOINT ["python3", "main.py"]
