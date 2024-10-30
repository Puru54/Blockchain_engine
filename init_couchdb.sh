#!/bin/bash
set -e

# Start CouchDB in the background
couchdb &

# Wait for CouchDB to start
until curl -s http://localhost:5984/ > /dev/null; do
  sleep 1
done

# Create the _users database
curl -X PUT http://admin:admin@localhost:5984/_users

# Bring CouchDB to the foreground
fg %1
