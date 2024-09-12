#!/bin/bash

pg_ctl stop -D /var/lib/postgresql/data -m fast
rm -rf /var/lib/postgresql/data

until pg_isready -h $DB_HOST; do
  echo "Waiting for primary server to be ready..."
  sleep 1
done

pg_basebackup -h $DB_HOST -D /var/lib/postgresql/data -U $DB_REPL_USER -vP -X stream

echo "host replication all 0.0.0.0/0 md5" >> "$PGDATA/pg_hba.conf"
echo "listen_addresses = '*'" >> "$PGDATA/postgresql.conf"

exec postgres