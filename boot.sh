#!/bin/sh
exec gunicorn -e SCRIPT_NAME=/mhcflurry -b :5000 --access-logfile - --error-logfile - app:app
