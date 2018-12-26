#!/bin/sh

source env/bin/activate
gunicorn -w 4 -b :5000 api:app
