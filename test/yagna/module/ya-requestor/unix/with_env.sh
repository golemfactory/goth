#!/bin/bash
# Export environment variables from $1 and run $2 in the resulting environment

if [[ -z "$1" || -z "$2" ]]; then
    echo "Usage: $0 VARS COMMAND [ARGS]" >> /dev/stderr
    exit 1;
fi

set -o allexport
ENV_FILE="$(dirname "$1")/$(basename "$1")"
. $ENV_FILE
set +o allexport

shift
/bin/bash "$*"
