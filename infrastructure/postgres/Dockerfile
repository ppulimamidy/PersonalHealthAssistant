FROM postgres:14

# Install necessary packages
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    postgresql-server-dev-14 \
    postgresql-contrib \
    libcurl4-openssl-dev \
    libxml2-dev \
    && rm -rf /var/lib/apt/lists/*

# Install pgvector
RUN git clone --branch v0.4.4 https://github.com/pgvector/pgvector.git \
    && cd pgvector \
    && make \
    && make install

# Install http extension
RUN git clone --branch v1.4.0 https://github.com/pramsey/pgsql-http.git \
    && cd pgsql-http \
    && make \
    && make install

# Create extension control files
RUN echo "comment = 'generate universally unique identifiers (UUIDs)'" > /usr/share/postgresql/14/extension/uuid-ossp.control \
    && echo "default_version = '1.1'" >> /usr/share/postgresql/14/extension/uuid-ossp.control \
    && echo "module_pathname = '\$libdir/uuid-ossp'" >> /usr/share/postgresql/14/extension/uuid-ossp.control \
    && echo "relocatable = true" >> /usr/share/postgresql/14/extension/uuid-ossp.control

# Copy extension files
RUN cp /usr/lib/postgresql/14/lib/uuid-ossp.so /usr/lib/postgresql/14/lib/ \
    && cp /usr/share/postgresql/14/extension/uuid-ossp--1.1.sql /usr/share/postgresql/14/extension/

# Clean up
RUN apt-get purge -y build-essential git postgresql-server-dev-14 \
    && apt-get autoremove -y \
    && apt-get clean

# Create initialization script
COPY ./init-extensions.sh /docker-entrypoint-initdb.d/
RUN chmod +x /docker-entrypoint-initdb.d/init-extensions.sh

# (Optional) To install pg_kafka or duckdb_fdw, you must build from source.
# Example for duckdb_fdw:
# RUN git clone https://github.com/alitrack/duckdb_fdw.git /duckdb_fdw && \
#     cd /duckdb_fdw && make && make install
# Example for pg_kafka:
# RUN git clone https://github.com/confluentinc/pg_kafka.git /pg_kafka && \
#     cd /pg_kafka && make && make install 