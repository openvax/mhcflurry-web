#!/bin/sh
echo "Serving from /mhcflurry"
exec gunicorn -b :5000 --workers=4 --access-logfile - --error-logfile - app:app
