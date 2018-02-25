#!/usr/bin/env bash

./wait-for-stop.sh -h kong-database-migrations
./wait-for-it.sh kong:800 -t 0
npm start
