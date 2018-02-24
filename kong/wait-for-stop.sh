#!/usr/bin/env bash
#   Use this script to test if a given TCP host has stopped

cmdname=$(basename $0)

echoerr() { if [[ $QUIET -ne 1 ]]; then echo "$@" 1>&2; fi }

usage()
{
    cat << USAGE >&2
Usage:
    $cmdname -h host [-- command args]
    -h HOST | --host=HOST       Host or IP under test
    -- COMMAND ARGS             Execute command with args after the test finishes
USAGE
    exit 1
}

# process arguments
while [[ $# -gt 0 ]]
do
    case "$1" in
        --child)
        CHILD=1
        shift 1
        ;;
        -h)
        HOST="$2"
        if [[ $HOST == "" ]]; then break; fi
        shift 2
        ;;
        --host=*)
        HOST="${1#*=}"
        shift 1
        ;;
        --)
        shift
        CLI=("$@")
        break
        ;;
        --help)
        usage
        ;;
        *)
        echoerr "Unknown argument: $1"
        usage
        ;;
    esac
done

if [[ "$HOST" == "" ]]
then
    echoerr "Error: you need to provide a host to test."
    usage
fi


while ping -c1 $HOST &>/dev/null
do
    sleep 1
    echo "Waiting for $HOST to finish."
done

echo "$HOST finished."

if [[ $CLI != "" ]]; then
    if [[ $RESULT -ne 0 && $STRICT -eq 1 ]]; then
        echoerr "$cmdname: strict mode, refusing to execute subprocess"
        exit $RESULT
    fi
    exec "${CLI[@]}"
else
    exit $RESULT
fi