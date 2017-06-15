mhcflurry-web
============

Web interface to run mhcflurry predictions

Quickstart
----------

```sourceCode
# Activate conda environment
source activate mhcweb

# Download mhcflurry data bundle
mhcflurry-downloads fetch models_class1

# Setup ENV variables (assumes we are in `mhcflurry-web`):
export FLASK_APP=./app.py
flask run   # defaults: --port 5000 --host 127.0.0.1
```

and then browse to http://localhost:5000

Deployment
----------

In your production environment, make sure the `FLASK_DEBUG` environment variable
is unset or is set to `0`, so that `ProdConfig` is used.

Running Tests
-------------

To run all tests, run :

    flask test
