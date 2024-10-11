#!/usr/bin/env bash

DOCKER_IMAGE=demo-textfile-collector:1.0.0

if [[ "$(docker images -q $DOCKER_IMAGE 2> /dev/null)" == "" ]]; then
  DOCKER_BUILDKIT=1 docker build \
    --target=runtime -t=$DOCKER_IMAGE .
fi

# Command to execute
CMD="python3 main.py --demo-file=sample.xml"
if [ "$1" = "--debug" ]; then
  CMD="$CMD --dry-run --fruit orange --fruit apple"
else
  CMD="$CMD $*"
fi

# Volumes
DOCKER_OPT_VOLUMES="-v $(pwd)/main.py:/app/main.py\
  -v $(pwd)/sample.xml:/app/sample.xml\
  -v $(pwd)/store.prom:/var/lib/node_exporter/store.prom"

# Launch container
echo "docker run --rm -it $DOCKER_OPT_VOLUMES $DOCKER_IMAGE $CMD"
# shellcheck disable=SC2086
docker run --rm -it $DOCKER_OPT_VOLUMES $DOCKER_IMAGE $CMD
