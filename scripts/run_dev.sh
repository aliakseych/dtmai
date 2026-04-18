#!/bin/bash

# checking if there is .env file
if [ ! -f ".env" ]; then
  echo "There is no dev.env file in current folder."
  echo "You can passthrough env variables, but you should create dev.env file";
  exit 2
fi

# get all variables from .env
set -e
export $(grep -v '^#' .env | xargs)
export MONGO_URI=mongodb://${MONGO_USER}:${MONGO_PASSWORD}@${MONGO_HOSTS}/${MONGO_OPTIONS}

# Starting dev docker compose
docker compose -f docker-compose.dev.yaml up -d

# Running the bot
python3 -m src bot
