#!/bin/bash

mkdir -p /var/lib/postgresql/data/archive && chown -R postgres:postgres /var/lib/postgresql/data/archive

echo "host replication all 0.0.0.0/0 md5" >> "$PGDATA/pg_hba.conf"
set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<-EOSQL
	CREATE USER ${DB_REPL_USER} REPLICATION LOGIN CONNECTION LIMIT 100 ENCRYPTED PASSWORD '${DB_REPL_PASSWORD}';
	CREATE DATABASE ${DB_DATABASE};
EOSQL

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$DB_DATABASE" <<-EOSQL
	CREATE table emails(ID SERIAL PRIMARY KEY, email VARCHAR (100) NOT NULL);
	INSERT INTO emails(email) VALUES ('test@test.ru'),('second_test2@test.ru');
	CREATE table phonenumbers(ID SERIAL PRIMARY KEY, phonenumber VARCHAR (100) NOT NULL);
	INSERT INTO phonenumbers(phonenumber) VALUES ('88002253535'),('+79812223344');
EOSQL

cat >> ${PGDATA}/postgresql.conf <<EOF
archive_mode = on
archive_command = 'cp %p /var/lib/postgresql/data/archive/%f'
max_wal_senders = 10
wal_level = replica
wal_log_hints = on
log_replication_commands = on
listen_addresses = '*'
logging_collector = on
log_directory = '/var/log/postgresql'
log_filename = 'postgresql.log'