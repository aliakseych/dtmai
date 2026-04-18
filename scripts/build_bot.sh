#!/bin/bash

# Building for ARM
docker build --platform linux/arm64 -t ghcr.io/aliakseych/dtmai:bot-latest -f bot.Dockerfile .

read -r -p "Push to GHCR? (y/N)... " dopush
case $dopush in
  [Yy]* ) echo "Pushing!"; docker push ghcr.io/aliakseych/dtmai:bot-latest;;
  * ) ;;
esac
