FROM postgres:latest

ADD ./init.sh /docker-entrypoint-initdb.d/
RUN chown postgres:postgres /docker-entrypoint-initdb.d/init.sh
RUN chmod +x /docker-entrypoint-initdb.d/init.sh

USER postgres
CMD ["postgres"]
