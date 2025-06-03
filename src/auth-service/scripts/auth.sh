#!/bin/bash

# load .env.local if it exists
if [ -f .env.local ]; then
    set -a ; . ./.env.local ; set +a
fi

flask --app main.py run --debug