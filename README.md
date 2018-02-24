# kong-konga-docker-compose

Start Kong (https://getkong.org) and Konga (https://pantsel.github.io/konga/) with a compose script version 3.
It uses Cassandra as database. The script starts the database, performs the migrations and then starts kong.
The script has been made to perform the correct start up sequence. It doensn't use the condition on the depends_on since that is not allowed anymore in docker-compose version 3 files.

Used the wonderful wait-for-it.sh script (https://github.com/vishnubob/wait-for-it) to wait for Cassandra datbase to start. I used it as a template for the wait-for-stop.sh script.