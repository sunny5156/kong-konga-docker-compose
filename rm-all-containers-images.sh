#!/usr/bin/bash

#docker rm $(docker ps -a -q)
#docker rmi $(docker images -q) -f

docker rm konga kong konga-database kong-database konga kong-database-migrations
docker rmi kong-konga-docker-compose_konga:latest kong-konga-docker-compose_kong:latest kong-konga-docker-compose_kong-database-migrations:latest kong-konga-docker-compose_kong-database:latest kong-konga-docker-compose_konga-database:latest
