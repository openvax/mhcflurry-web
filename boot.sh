#!/bin/sh
exec gunicorn -b :5000 --workers=4 --access-logfile - --error-logfile - dash-app:server
# 