# mhcflurry-web
Webapp for MHCflurry predictions

To run locally:

```
FLASK_ENV=development FLASK_APP=app.py flask run --without-threads --no-reload
```

Or using docker:
```
docker build -t mhcflurry-web:latest .
docker run -p 80:5000  --rm  mhcflurry-web:latest
```
