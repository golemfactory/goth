#!/usr/bin/env bash
set -eu

# Move up current dir's parents until one of them has the specified subdir (or fs root is reached)
find_parent_dir() {
    if [ $# -eq 0 ]; then
        return 1
    fi

    local pwd=$(pwd)

    while [ "$pwd" != "/" ]; do
        pwd=$(dirname "$pwd")
        if [ -d "$pwd/$1" ]; then
            echo "$pwd"
            return 0
        fi
    done

    return 1
}

ROOT_DIR="$(find_parent_dir .git)"
TEST_DIR="$(find_parent_dir asset)"
DOCKER_DIR="$ROOT_DIR/src/docker"

# Clean up asset dir from src/docker on termination
trap "rm -r $DOCKER_DIR/asset 2>/dev/null" EXIT SIGINT SIGTERM
cp -r "$TEST_DIR/asset" "$DOCKER_DIR"

docker-compose -f "$DOCKER_DIR/docker-compose.yml" up
