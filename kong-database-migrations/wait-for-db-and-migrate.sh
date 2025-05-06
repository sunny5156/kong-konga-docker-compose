#!/usr/bin/bash

./wait-for-it.sh konga-database:27017 -t 0
./wait-for-it.sh kong-database:5432 -t 0
kong migrations bootstrap