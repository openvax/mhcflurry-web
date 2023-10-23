FROM continuumio/miniconda3:latest

LABEL maintainer="Tim O'Donnell timodonnell@gmail.com"

# Install system dependencies
RUN apt-get update -y && apt-get install -y gcc && apt-get clean

COPY requirements.txt requirements.txt
RUN pip install --upgrade pip
RUN pip install -r requirements.txt
RUN pip install gunicorn
RUN mhcflurry-downloads fetch

COPY static/ static/
COPY templates/ templates/
COPY dash-app.py .
COPY boot.sh .

RUN chmod +x boot.sh

ENV FLASK_APP app.py

EXPOSE 5000
ENTRYPOINT ["./boot.sh"]
