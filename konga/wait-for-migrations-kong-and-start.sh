#!/usr/bin/bash

#./wait-for-stop.sh -h kong-database-migrations
./wait-for-it.sh kong:8000 -t 0
npm start
