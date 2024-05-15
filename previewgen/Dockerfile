FROM python:3.9-slim

WORKDIR /app

# install pipenv
ENV PIP_NO_CACHE_DIR 1
ENV PIPENV_VENV_IN_PROJECT 1
RUN pip install pipenv wheel

RUN apt-get update \
 && apt-get install -y curl \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/*

# create user
RUN adduser --system --uid 1001 --group --disabled-login --gecos "" --home /home/user user

# install deps, copy project
COPY Pipfile* ./
RUN pipenv install --deploy
COPY . .

ENV PYTHONUNBUFFERED 1
ENV WORKERS 3

USER user
CMD pipenv run gunicorn previewgen.main:app -w $WORKERS -k uvicorn.workers.UvicornH11Worker --bind 0.0.0.0:80
