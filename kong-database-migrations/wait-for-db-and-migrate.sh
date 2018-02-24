#!/usr/bin/env bash

./wait-for-it.sh konga-database:27017 -t 0
./wait-for-it.sh kong-database:9042 -t 0
kong migrations up